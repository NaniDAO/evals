"""Handles generation of completions from datasets."""

from typing import List, Dict, Any, Optional, TypedDict
import os
from pathlib import Path
from .base import BaseTestClass
from apis.analyzer import create_handler, PROVIDERS
from .config import config


class CompletionResults(TypedDict):
    instructions: List[Dict[str, Any]]


class CompletionGenerator(BaseTestClass):
    def __init__(
        self,
        output_dir: str = None,
        providers: List[str] = None,
        provider_configs: Dict[str, Dict[str, Any]] = None,
    ):
        """Initialize completion generator."""
        super().__init__(output_dir)

        self.providers = providers or ["nani"]
        self.analyzers = {}
        provider_configs = provider_configs or {}

        for provider in self.providers:
            if provider not in PROVIDERS:
                raise ValueError(f"Unsupported provider: {provider}")

            # Get provider-specific configuration
            provider_config = provider_configs.get(provider, {})

            # Initialize analyzer with all config in provider_kwargs
            self.analyzers[provider] = create_handler(
                provider=provider,
                rate_limit=config.DEFAULT_RATE_LIMIT,
                rate_period=config.DEFAULT_RATE_PERIOD,
                **provider_config,  # This includes api_key, model, base_url etc.
            )
            
            self.model = provider_configs.get("model", None) or PROVIDERS[provider][2]

        self.last_results: Optional[CompletionResults] = None
        self.last_output_path: Optional[str] = None

    def generate_completions(
        self,
        dataset_path: str,
        categories: List[str] = None,
        behaviors: List[str] = None,
        sources: List[str] = None,
        config_file: Optional[str] = None,
        save_output: bool = True,
    ) -> CompletionResults:
        """Generate completions for dataset using configured providers."""
        # Load configurations
        base_configs = self._load_file(config_file) if config_file else []
        provider_configs = {}

        # Initialize configs for each provider
        for provider in self.providers:
            if not base_configs:
                provider_configs[provider] = [
                    self.analyzers[provider].provider.get_default_config()
                ]
            else:
                provider_configs[provider] = base_configs

        print(f"📋 Loaded configurations for {len(self.providers)} provider(s)")

        # Load and filter prompts
        dataset = self._load_file(dataset_path)
        prompts = self._filter_prompts(dataset["rows"], categories, behaviors, sources)

        print(f"\n📋 Starting generation of {len(prompts)} prompts")
        results = []

        # Process prompts
        for idx, prompt in enumerate(prompts, 1):
            print(f"\n🔍 Processing prompt {idx}/{len(prompts)}")
            completions = []

            for provider in self.providers:
                print(f"\n📝 Using provider: {provider}")
                analyzer = self.analyzers[provider]

                for config_idx, cfg in enumerate(provider_configs[provider], 1):
                    print(f"⚙️ Using configuration #{config_idx}: {cfg}")

                    try:
                        analyzer.config = cfg
                        completion = analyzer.generate_response(prompt["instruction"])
                        
                        # Ensure completion is JSON serializable
                        completion_data = {
                            "provider": provider,
                            "model": self.model,
                            "config": cfg
                        }
                        
                        # Handle non-string completions or errors
                        try:
                            if isinstance(completion, str):
                                completion_data["completion"] = completion
                            elif isinstance(completion, dict):
                                completion_data["completion"] = completion
                            else:
                                # Convert non-string, non-dict completions to string
                                completion_data["completion"] = str(completion)
                                
                        except Exception as e:
                            completion_data["completion"] = {
                                "error": f"Failed to serialize completion: {str(e)}"
                            }
                        
                        completions.append(completion_data)
                        print(f"✓ {provider} configuration #{config_idx} complete")

                    except Exception as e:
                        error_msg = str(e)
                        print(f"❌ Generation failed for {provider} configuration #{config_idx}: {error_msg}")
                        completions.append({
                            "provider": provider,
                            "model": self.model,
                            "config": cfg,
                            "completion": {
                                "error": error_msg
                            }
                        })

            prompt["completions"] = completions
            results.append(prompt)
            print(f"✓ Prompt {idx}/{len(prompts)} complete")

        # Add metadata about providers and models used
        self.last_results = {
            "metadata": {
                "providers": [
                    {
                        "name": provider,
                        "model": self.model,
                    } for provider in self.providers
                ]
            },
            "instructions": results
        }

        if save_output:
            output_path = self.output_dir / self._get_output_filename(
                "completions", categories
            )
            try:
                self._save_file(self.last_results, output_path)
                self.last_output_path = str(output_path)
                print(f"💫 Generated completions saved to: {self.last_output_path}")
            except Exception as e:
                print(f"❌ Failed to save results: {str(e)}")
                # Create a clean, serializable copy of the results
                clean_results = self._create_serializable_copy(self.last_results)
                backup_path = self.output_dir / f"backup_{self._get_output_filename('completions', categories)}"
                self._save_file(clean_results, backup_path)
                print(f"💫 Backup results saved to: {backup_path}")
                
        return self.last_results

    def _create_serializable_copy(self, data: Any) -> Any:
        """Create a JSON-serializable copy of the data structure."""
        if isinstance(data, dict):
            return {k: self._create_serializable_copy(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._create_serializable_copy(v) for v in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            return str(data)  # Convert any non-serializable objects to strings
        
    def get_last_output_path(self) -> Optional[str]:
        """Get path of last saved output file."""
        return self.last_output_path

    def get_last_results(self) -> Optional[CompletionResults]:
        """Get results from last generation run."""
        return self.last_results
