"""Handles generation of completions from datasets."""
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from .base import BaseTestClass
from apis.analyzer import create_handler, PROVIDERS
from .config import config

class CompletionGenerator(BaseTestClass):
    def __init__(self, output_dir: str = None, provider: str = "nani"):
        """Initialize completion generator."""
        super().__init__(output_dir)
        
        if provider not in PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
            
        self.provider = provider
        self.analyzer = create_handler(
            provider=provider,
            api_key=os.getenv(f"{provider.upper()}_API_KEY"),
            base_url=os.getenv(f"{provider.upper()}_BASE_URL"),
            model=PROVIDERS[provider][2],
            rate_limit=config.DEFAULT_RATE_LIMIT,
            rate_period=config.DEFAULT_RATE_PERIOD
        )

    def generate_completions(
        self,
        dataset_path: str,
        categories: List[str] = None,
        behaviors: List[str] = None,
        sources: List[str] = None,
        config_file: Optional[str] = None
    ) -> str:
        """Generate completions for dataset."""
        # Load configurations
        configs = self._load_file(config_file) if config_file else [self.analyzer.provider.get_default_config()]
        print(f"📋 Loaded {len(configs)} configuration(s)")
        
        # Load and filter prompts
        dataset = self._load_file(dataset_path)
        prompts = self._filter_prompts(dataset["rows"], categories, behaviors, sources)
        
        print(f"\n📋 Starting generation of {len(prompts)} prompts")
        results = []
        
        # Process prompts
        for idx, prompt in enumerate(prompts, 1):
            print(f"\n🔍 Processing prompt {idx}/{len(prompts)}")
            completions = []
            
            for config_idx, cfg in enumerate(configs, 1):
                print(f"⚙️ Using configuration #{config_idx}: {cfg}")
                
                try:
                    self.analyzer.config = cfg
                    completion = self.analyzer.generate_response(prompt["instruction"])
                    completions.append({
                        "config": cfg,
                        "completion": completion
                    })
                    print(f"✓ Configuration #{config_idx} complete")
                    
                except Exception as e:
                    print(f"❌ Generation failed for configuration #{config_idx}: {str(e)}")
                    completions.append({
                        "config": cfg,
                        "completion": {"error": str(e)}
                    })
            
            prompt["completions"] = completions
            results.append(prompt)
            print(f"✓ Prompt {idx}/{len(prompts)} complete")
        
        # Save results
        output_path = self.output_dir / self._get_output_filename("completions", categories)
        self._save_file({"instructions": results}, output_path)
        
        print(f"💫 Generated completions saved to: {output_path}")
        return str(output_path)