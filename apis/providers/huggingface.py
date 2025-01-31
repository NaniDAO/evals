from typing import Any, Dict, Optional
import openai
import tiktoken
from ..base import LLMProvider


class HuggingFaceProvider(LLMProvider):
    def initialize(self, api_key: str, model: str, **kwargs) -> None:
        """
        Initialize OpenAI client with API key, model and base_url

        Args:
            api_key: API key for authentication
            model: Model identifier
            **kwargs: Must contain 'base_url' for HuggingFace endpoint
        """
        if "base_url" not in kwargs:
            raise ValueError("HuggingFaceProvider requires 'base_url' parameter")

        self.client = openai.OpenAI(base_url=kwargs["base_url"], api_key=api_key)
        self.model = model

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except:
            # Fallback approximation if tiktoken fails
            return len(text) // 4

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration that works with most HuggingFace models"""
        return {
            "temperature": 0.7,  # Standard temperature for balanced output
            "max_tokens": 8096,  # Conservative max token limit
            "frequency_penalty": 0.0,  # No frequency penalty by default
            "presence_penalty": 0.0,  # No presence penalty by default
            # Uncomment if your specific model supports these:
            # "top_p": 1.0,
            # "stop": None,
            # "n": 1,
        }

    def generate(
        self, prompt: str, system_prompt: str, config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Generate completion using OpenAI API"""
        generation_config = self.get_default_config()
        if config:
            generation_config.update(config)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model, messages=messages, **generation_config
        )

        return response
