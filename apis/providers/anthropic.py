from typing import Any, Dict, Optional
from anthropic import Anthropic
from ..base import LLMProvider


class AnthropicProvider(LLMProvider):
    def initialize(self, api_key: str, model: str) -> None:
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def count_tokens(self, text: str) -> int:
        try:
            response = self.client.beta.messages.count_tokens(
                model=self.model, messages=[{"role": "user", "content": text}]
            )
            return response.input_tokens
        except:
            return len(text) // 4

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "max_tokens": 8096,
            "temperature": 0.7,
            "top_p": 1.0,
        }

    def generate(
        self, prompt: str, system_prompt: str, config: Optional[Dict[str, Any]] = None
    ) -> Any:
        generation_config = self.get_default_config()
        if config:
            generation_config.update(config)

        return self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            **generation_config
        )
