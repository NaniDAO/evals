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
    def __init__(self, output_dir: str = None, providers: List[str] = None):
        """Initialize completion generator."""
        super().__init__(output_dir)
        
        self.providers = providers or ["nani"]
        self.analyzers = {}
        
        for provider in self.providers:
            if provider not in PROVIDERS:
                raise ValueError(f"Unsupported provider: {provider}")
                
            # Prepare provider-specific kwargs
            provider_kwargs = {
                "rate_limit": config.DEFAULT_RATE_LIMIT,
                "rate_period": config.DEFAULT_RATE_PERIOD
            }
            
            # Add base_url only for providers that need it (like nani/CurlProvider)
            if provider == "nani":
                provider_kwargs["base_url"] = os.getenv(f"{provider.upper()}_BASE_URL")
            
            self.analyzers[provider] = create_handler(
                provider=provider,
                api_key=os.getenv(f"{provider.upper()}_API_KEY"),
                model=PROVIDERS[provider][2],
                **provider_kwargs
            )
            
        self.last_results: Optional[CompletionResults] = None
        self.last_output_path: Optional[str] = None

    def generate_completions(
        self,
        dataset_path: str,
        categories: List[str] = None,
        behaviors: List[str] = None,
        sources: List[str] = None,
        config_file: Optional[str] = None,
        save_output: bool = True
    ) -> CompletionResults:
        """Generate completions for dataset using configured providers."""
        # Load configurations
        base_configs = self._load_file(config_file) if config_file else []
        provider_configs = {}
        
        # Initialize configs for each provider
        for provider in self.providers:
            if not base_configs:
                provider_configs[provider] = [self.analyzers[provider].provider.get_default_config()]
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
                        completions.append({
                            "provider": provider,
                            "model": PROVIDERS[provider][2],  # Add model metadata
                            "config": cfg,
                            "completion": completion
                        })
                        print(f"✓ {provider} configuration #{config_idx} complete")
                        
                    except Exception as e:
                        print(f"❌ Generation failed for {provider} configuration #{config_idx}: {str(e)}")
                        completions.append({
                            "provider": provider,
                            "model": PROVIDERS[provider][2],  # Add model metadata even for errors
                            "config": cfg,
                            "completion": {"error": str(e)}
                        })
            
            prompt["completions"] = completions
            results.append(prompt)
            print(f"✓ Prompt {idx}/{len(prompts)} complete")
        
        # Add metadata about providers and models used
        self.last_results = {
            "metadata": {
                "providers": [{
                    "name": provider,
                    "model": PROVIDERS[provider][2]
                } for provider in self.providers]
            },
            "instructions": results
        }
        
        if save_output:
            output_path = self.output_dir / self._get_output_filename("completions", categories)
            self._save_file(self.last_results, output_path)
            self.last_output_path = str(output_path)
            print(f"💫 Generated completions saved to: {self.last_output_path}")
            
        return self.last_results

    def get_last_output_path(self) -> Optional[str]:
        """Get path of last saved output file."""
        return self.last_output_path

    def get_last_results(self) -> Optional[CompletionResults]:
        """Get results from last generation run."""
        return self.last_results