import os
import time
import json
import re
from threading import Lock
from typing import Optional, Dict, Any, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from .providers.gemini import GeminiProvider
from .providers.anthropic import AnthropicProvider
from .providers.openai import OpenAIProvider
from .providers.huggingface import HuggingFaceProvider
from .providers.curl import CurlProvider

PROVIDERS = {
    "gemini": (GeminiProvider, "GEMINI_API_KEY", "gemini-2.0-flash-exp"),
    "anthropic": (
        AnthropicProvider,
        "ANTHROPIC_API_KEY",
        "claude-3-5-sonnet-20241022",
    ),
    "openai": (OpenAIProvider, "OPENAI_API_KEY", "gpt-4o-mini-2024-07-18"),
    "huggingface": (HuggingFaceProvider, "HUGGINGFACE_API_KEY", "tgi"),
    "nani": (CurlProvider, "NANI_API_KEY", "NaniDAO/deepseek-r1-qwen-2.5-32B-ablated"),
}


def _should_retry_error(exception: Exception) -> bool:
    error_str = str(exception).lower()
    return any(
        msg in error_str
        for msg in [
            "rate limit",
            "429",
            "too many requests",
            "quota exceeded",
            "resource exhaust",
            "service unavailable",
            "internal server error",
            "503",
            "500",
        ]
    )


class RateLimiter:
    def __init__(self, rate: int, per: int):
        self.rate = rate
        self.per = per
        self.tokens = rate
        self.last_update = time.time()
        self.lock = Lock()

    def acquire(self) -> float:
        with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            new_tokens = time_passed * (self.rate / self.per)

            if new_tokens > 0:
                self.tokens = min(self.rate, self.tokens + new_tokens)
                self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return 0.0

            return (1 - self.tokens) * (self.per / self.rate)


class PromptAnalyzer:
    def __init__(
        self,
        provider: str,
        model: Optional[str] = None,
        system_prompt: str = "",
        config: Optional[Dict[str, Any]] = None,
        rate_limit: int = 5,
        rate_period: int = 60,
        **provider_kwargs,
    ):
        if provider not in PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        # Extract provider class and default model
        Provider, env_key, default_model = PROVIDERS[provider]
        
        # Get API key from kwargs or environment
        if "api_key" not in provider_kwargs:
            api_key = os.getenv(env_key)
            if not api_key:
                raise ValueError(f"No API key provided for {provider} - set {env_key} or provide via api_key parameter")
            provider_kwargs["api_key"] = api_key
        
        # Initialize provider
        self.provider = Provider()
        
        # First spread provider_kwargs, then set model only if not already present
        provider_init_kwargs = {
            **provider_kwargs  # This includes api_key and potentially model
        }
        if "model" not in provider_init_kwargs:
            provider_init_kwargs["model"] = model or default_model
                        
        self.provider.initialize(**provider_init_kwargs)
        
        # Set up analyzer configuration
        self.system_prompt = system_prompt
        self.token_count = 0
        self.prompt_count = 0
        self.config = config or self.provider.get_default_config()
        self.rate_limiter = RateLimiter(rate_limit, rate_period)

    def _clean_json_response(self, response_text: str) -> str:
        if "```" in response_text:
            match = re.search(r"```(?:json)?\n(.*?)```", response_text, re.DOTALL)
            if match:
                return match.group(1).strip()
        return response_text.strip()

    @retry(
        retry=retry_if_exception(_should_retry_error),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=120),
    )
    def _rate_limited_generate(
        self,
        prompt: str,
    ) -> Any:
        while True:
            wait_time = self.rate_limiter.acquire()
            if wait_time == 0:
                try:
                    return self.provider.generate(
                        prompt, self.system_prompt, self.config
                    )
                except Exception as e:
                    if _should_retry_error(e):
                        raise
                    print(f"Non-retryable error: {str(e)}")
                    raise
            time.sleep(wait_time)

    def generate_response(
        self,
        prompt: str,
    ) -> str:
        try:
            self.prompt_count += 1
            print(f"\n📝 Processing prompt #{self.prompt_count}...")

            input_tokens = self.provider.count_tokens(prompt)
            print(f"📝 Using Provider {self.provider.__class__.__name__}")
            print(f"📊 Sending prompt with {input_tokens:,} tokens...")

            start_time = time.time()
            response = self._rate_limited_generate(prompt)
            elapsed_time = time.time() - start_time

            response_text, output_tokens = self._process_response(response)
            self.token_count += input_tokens + output_tokens

            self._log_token_usage(input_tokens, output_tokens, elapsed_time)
            return response_text

        except Exception as e:
            print(f"Failed to generate response: {str(e)}")
            raise

    def generate_json_response(
        self,
        prompt: str,
    ) -> Dict[str, Any]:
        max_json_retries = 3
        last_response = None
        last_error = None

        for attempt in range(max_json_retries):
            try:
                response_text = self.generate_response(prompt)
                last_response = response_text
                result = self._clean_json_response(response_text)
                return json.loads(result)

            except json.JSONDecodeError as e:
                last_error = e
                if attempt < max_json_retries - 1:
                    print(
                        f"⚠️  Attempt {attempt + 1}/{max_json_retries}: JSON parsing failed, retrying with feedback..."
                    )
                    prompt = self._get_json_error_feedback(e, prompt)
                    continue

                print(f"❌ Failed to parse JSON after {max_json_retries} attempts")
                print("Last response received:", last_response)
                print("Last error:", str(last_error))
                raise

        raise Exception("Failed to generate valid JSON response")

    def _process_response(self, response: Any) -> Tuple[str, int]:
        if isinstance(self.provider, GeminiProvider):
            return response.text, response.usage_metadata.total_token_count
        if isinstance(self.provider, AnthropicProvider):
            return response.content[0].text, response.usage.output_tokens
        if isinstance(self.provider, (HuggingFaceProvider, OpenAIProvider)):
            message_content = response.choices[0].message.content
            total_tokens = (
                response.usage.total_tokens
                if hasattr(response, "usage")
                else self.provider.count_tokens(message_content)
            )
            return message_content, total_tokens
        if isinstance(self.provider, CurlProvider):
            return response["choices"][0]["text"], response["total_tokens"]
        raise ValueError(f"Unsupported provider type: {type(self.provider)}")

    def _log_token_usage(
        self, input_tokens: int, output_tokens: int, elapsed_time: float
    ) -> None:
        prompt_total_tokens = input_tokens + output_tokens
        print(f"✓ Response received in {elapsed_time:.2f} seconds")
        print(f"📊 Prompt #{self.prompt_count} token usage:")
        print(f"   - Input tokens:  {input_tokens:,}")
        print(f"   - Output tokens: {output_tokens:,}")
        print(f"   - Total tokens:  {prompt_total_tokens:,}")
        print(f"📈 Cumulative token usage: {self.token_count:,}")

    def _get_json_error_feedback(self, error: json.JSONDecodeError, prompt: str) -> str:
        return f"""Your previous response could not be parsed as valid JSON. The specific error was: {str(error)}

        IMPORTANT: You must provide a response that:
        1. Contains ONLY valid JSON
        2. Has NO markdown code blocks
        3. Has NO explanatory text
        4. Follows the exact schema requested
        5. Uses proper JSON syntax (quotes, commas, brackets)
        6. AVOID falling into recursive loops when retrieving data from the prompt

        Here is the original prompt again:
        {prompt}"""


def create_handler(
    provider: str,
    model: Optional[str] = None,
    system_prompt: str = "",
    config: Optional[Dict[str, Any]] = None,
    **provider_kwargs
) -> PromptAnalyzer:
    """Create a prompt analyzer instance.
    
    Args:
        provider: Name of the provider to use
        model: Optional model identifier (falls back to provider default)
        system_prompt: Optional system prompt
        config: Optional generation configuration
        **provider_kwargs: Provider-specific configuration including credentials
    """
    return PromptAnalyzer(
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        config=config,
        **provider_kwargs
    )
