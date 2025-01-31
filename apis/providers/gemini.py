from typing import Any, Dict, Optional
import google.generativeai as genai
from ..base import LLMProvider


class GeminiProvider(LLMProvider):
    def initialize(self, api_key: str, model: str) -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=model)

    def count_tokens(self, text: str) -> int:
        try:
            return self.model.count_tokens(text).total_tokens
        except:
            return len(text) // 4

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "temperature": 0.7,
            "top_p": 1.0,
            "top_k": 40,
            "candidate_count": 1,
        }

    def generate(
        self, prompt: str, system_prompt: str, config: Optional[Dict[str, Any]] = None
    ) -> Any:
        generation_config = self.get_default_config()
        if config:
            generation_config.update(config)

        prompt = f"{system_prompt}\n{prompt}"
        return self.model.generate_content(prompt, generation_config=generation_config)
