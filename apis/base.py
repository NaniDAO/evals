from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def initialize(self, api_key: str, model: str, **kwargs) -> None:
        """
        Initialize the LLM client
        
        Args:
            api_key: API key for authentication
            model: Model identifier
            **kwargs: Additional provider-specific initialization parameters
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        pass

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """Get provider-specific default configuration"""
        pass

    @abstractmethod
    def generate(
        self, prompt: str, system_prompt: str, config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Generate completion from the LLM

        Args:
            prompt: Input prompt text
            system_prompt: System instructions
            config: Optional provider-specific configuration
        """
        pass