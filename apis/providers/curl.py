from typing import Any, Dict, Optional
import requests
import tiktoken
from ..base import LLMProvider


class CurlProvider(LLMProvider):
    def initialize(self, api_key: str, model: str, **kwargs) -> None:
        if "base_url" not in kwargs:
            raise ValueError("CurlProvider requires 'base_url' parameter")
            
        self.base_url = kwargs["base_url"]
        self.api_key = api_key
        self.model = model

    def count_tokens(self, text: str) -> int:
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            return len(encoding.encode(text))
        except:
            return len(text) // 4

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "temperature": 0.7,
            "max_tokens": 8096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stream": False
        }

    def generate(
        self, prompt: str, system_prompt: str, config: Optional[Dict[str, Any]] = None
    ) -> Any:
        headers = {
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
        
        payload = {
            "modelId": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        if config:
            for key, value in config.items():
                if key not in ["modelId", "messages", "stream", "system"]:
                    payload[key] = value
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Making request (attempt {attempt + 1}/{max_retries})")
                
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=60,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Create response object for PromptAnalyzer
                return {
                    'choices': [{'text': result.get('text', '')}],
                    'total_tokens': result.get('total_tokens', self.count_tokens(result.get('text', '')))
                }
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"Request timed out, retrying ({attempt + 1}/{max_retries})")
                    continue
                raise Exception(f"API request failed: timeout after {max_retries} attempts")
                
            except requests.exceptions.RequestException as e:
                print(f"Request failed with error: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response text: {e.response.text}")
                raise Exception(f"API request failed: {str(e)}")