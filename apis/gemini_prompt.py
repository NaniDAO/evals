import os
import re
import json
import time
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from threading import Lock
import traceback


SYSTEM_PROMPT = """"""


def _should_retry_error(exception: Exception) -> bool:
    """Check if the exception is one we should retry"""
    error_str = str(exception).lower()
    return any(
        msg in error_str
        for msg in [
            "resource exhaust",
            "429",
            "too many requests",
            "quota exceeded",
            "rate limit",
        ]
    )


class RateLimiter:
    """Token bucket rate limiter implementation"""

    def __init__(self, rate: int, per: int):
        self.rate = rate  # Number of requests allowed per time period
        self.per = per  # Time period in seconds
        self.tokens = rate  # Current token count
        self.last_update = time.time()
        self.lock = Lock()

    def _add_tokens(self):
        """Add tokens based on time elapsed"""
        now = time.time()
        time_passed = now - self.last_update
        new_tokens = time_passed * (self.rate / self.per)
        if new_tokens > 0:
            self.tokens = min(self.rate, self.tokens + new_tokens)
            self.last_update = now

    def acquire(self) -> float:
        """
        Try to acquire a token. Returns the time to wait if no token is available.
        """
        with self.lock:
            self._add_tokens()

            if self.tokens >= 1:
                self.tokens -= 1
                return 0.0

            # Calculate wait time needed for next token
            wait_time = (1 - self.tokens) * (self.per / self.rate)
            return wait_time


class PromptAnalyzer:
    """Handles LLM prompting for code analysis tasks"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-pro-001",
        system_prompt: str = SYSTEM_PROMPT,
    ):
        """Initialize Gemini handler with API key"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key must be provided or set in GEMINI_API_KEY environment variable"
            )

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name, system_instruction=system_prompt
        )
        self.token_count = 0
        self.prompt_count = 0
        self.rate_limiter = RateLimiter(rate=5, per=60)

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        try:
            token_count = self.model.count_tokens(text)
            return token_count.total_tokens
        except Exception as e:
            print(f"Warning: Error counting tokens: {str(e)}")
            # Fallback to approximate count if token counting fails
            return len(text) // 4  # Rough approximation

    def _clean_json_response(self, response_text: str) -> str:
        """Clean up response text to extract JSON content"""
        if "```" in response_text:
            match = re.search(r"```(?:json)?\n(.*?)```", response_text, re.DOTALL)
            if match:
                return match.group(1).strip()
        return response_text.strip()

    @retry(
        retry=retry_if_exception(_should_retry_error),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        before_sleep=lambda retry_state: print(
            f"Retrying due to rate limit/resource exhaustion... (attempt {retry_state.attempt_number})"
        ),
    )
    def _rate_limited_generate(self, prompt: str) -> Any:
        """Handle rate-limited generation with waiting and resource exhaustion"""
        while True:
            wait_time = self.rate_limiter.acquire()

            if wait_time == 0:
                try:
                    # Direct call to generate_content instead of using chat
                    return self.model.generate_content(prompt)
                except Exception as e:
                    if _should_retry_error(e):
                        print(
                            f"Rate limit/resource exhaustion error, will retry: {str(e)}"
                        )
                        raise  # Let the retry decorator handle it
                    else:
                        print(f"Non-retryable error occurred: {str(e)}")
                        raise

            print(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
            time.sleep(wait_time)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_json_response(self, prompt: str) -> Dict[str, Any]:
        """Generate and parse JSON response with robust error handling"""
        try:
            self.prompt_count += 1
            print(f"\n📝 Processing prompt #{self.prompt_count}...")

            # Count input tokens
            token_count = self.model.count_tokens(prompt)
            input_tokens = token_count.total_tokens
            print(f"📊 Sending prompt with {input_tokens:,} tokens...")

            # Track retries for JSON parsing
            max_json_retries = 3
            last_response = None
            last_error = None

            for attempt in range(max_json_retries):
                try:
                    # Generate with rate limiting
                    start_time = time.time()
                    # Here's the actual model call
                    response = self._rate_limited_generate(prompt)
                    elapsed_time = time.time() - start_time

                    # Track token usage
                    output_token_count = response.usage_metadata.total_token_count
                    prompt_total_tokens = input_tokens + output_token_count
                    self.token_count += prompt_total_tokens

                    print(f"✓ Response received in {elapsed_time:.2f} seconds")
                    print(f"📊 Prompt #{self.prompt_count} token usage:")
                    print(f"   - Input tokens:  {input_tokens:,}")
                    print(f"   - Output tokens: {output_token_count:,}")
                    print(f"   - Total tokens:  {prompt_total_tokens:,}")
                    print(f"📈 Cumulative token usage: {self.token_count:,}")

                    # Try to parse JSON with advanced error recovery
                    last_response = response.text
                    result = self._clean_json_response(last_response)
                    return json.loads(result)

                except json.JSONDecodeError as e:
                    last_error = e

                    if attempt < max_json_retries - 1:
                        print(
                            f"⚠️  Attempt {attempt + 1}/{max_json_retries}: JSON parsing failed, retrying with feedback..."
                        )

                        # Add feedback about the JSON parsing failure and retry
                        error_feedback = f"""Your previous response could not be parsed as valid JSON. The specific error was: {str(e)}

                        IMPORTANT: You must provide a response that:
                        1. Contains ONLY valid JSON
                        2. Has NO markdown code blocks
                        3. Has NO explanatory text
                        4. Follows the exact schema requested
                        5. Uses proper JSON syntax (quotes, commas, brackets)
                        6. AVOID falling into recursive loops when retrieving data from the prompt

                        Here is the original prompt again:
                        """
                        # Combine feedback with original prompt
                        prompt = error_feedback + prompt
                        continue
                    else:
                        print(
                            f"❌ Failed to parse JSON after {max_json_retries} attempts"
                        )
                        print("Last response received:")
                        print(last_response)
                        print(f"Last error: {str(last_error)}")
                        raise

        except Exception as e:
            print(f"❌ Error in generate_json_response: {str(e)}")
            print("Stack trace:")
            print(traceback.format_exc())
            if "last_response" in locals():
                print("\nLast response received:")
                print(last_response)
            raise


def create_handler(
    api_key: Optional[str] = None,
    model_name: str = "gemini-1.5-pro-001",
    system_prompt: str = SYSTEM_PROMPT,
) -> PromptAnalyzer:
    """
    Factory function to create a PromptAnalyzer instance.
    """
    return PromptAnalyzer(api_key, model_name, system_prompt)
