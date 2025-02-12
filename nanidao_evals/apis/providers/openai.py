from typing import Any, Dict, Optional
import openai
import tiktoken
from ..base import LLMProvider

class OpenAIProvider(LLMProvider):
    def initialize(self, api_key: str, model: str) -> None:
        """Initialize OpenAI client with API key and model"""
        self.client = openai.OpenAI(api_key=api_key)
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
        """Get OpenAI-specific default configuration"""
        return {
            "temperature": 0.9,
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
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
            model=self.model,
            messages=messages,
            **generation_config
        )
        
        return response