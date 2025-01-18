from typing import List, Dict, Any
from .base import BaseTestClass
import os
import json
from apis.analyzer import create_handler

class CompletionGenerator(BaseTestClass):
    DEFAULT_JAILBREAKS_DATASET = "data/datasets/JBB_dataset.json"
    DEFAULT_CONFIG = [{
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1.0
    }]
    
    def _load_configs(self, config_file: str = None) -> List[Dict[str, Any]]:
        """Load configuration file or return default config."""
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading config file: {str(e)}")
                print("Using default configuration instead.")
        return self.DEFAULT_CONFIG

    def generate_completions(
        self,
        categories: List[str] = None,
        behaviors: List[str] = None,
        sources: List[str] = None,
        dataset_path: str = DEFAULT_JAILBREAKS_DATASET,
        config_file: str = None,
        rate_limit: int = BaseTestClass.DEFAULT_RATE_LIMIT,
        rate_period: int = BaseTestClass.DEFAULT_RATE_PERIOD
    ) -> str:
        """Generate completions using NANI with multiple configurations."""
        # Load configurations
        configs = self._load_configs(config_file)
        print(f"📋 Loaded {len(configs)} configuration(s)")
        
        # Load and filter prompts
        jailbreaks = self._load_file(dataset_path)
        filtered_prompts = self._filter_prompts(
            jailbreaks["rows"],
            categories,
            behaviors,
            sources
        )
        
        total_prompts = len(filtered_prompts)
        results = []
        
        print(f"\n📋 Starting generation of {total_prompts} prompts with {len(configs)} configuration(s) each")
        
        for idx, prompt in enumerate(filtered_prompts, 1):
            print(f"\n🔍 Processing prompt {idx}/{total_prompts}")
            
            # Store completions for each configuration
            prompt_completions = []
            
            for config_idx, config in enumerate(configs, 1):
                print(f"⚙️ Using configuration #{config_idx}: {config}")
                
                try:
                    # Initialize NANI analyzer with current config
                    nani_analyzer = create_handler(
                        provider="nani",
                        api_key=os.getenv("NANI_API_KEY"),
                        base_url=os.getenv("NANI_BASE_URL", "http://nani.ooo/api/chat"),
                        model=self.DEFAULT_MODELS["nani"],
                        rate_limit=rate_limit,
                        rate_period=rate_period,
                        config=config
                    )
                    
                    completion = nani_analyzer.generate_response(prompt["instruction"])
                    prompt_completions.append({
                        "config": config,
                        "completion": completion
                    })
                    print(f"✓ Configuration #{config_idx} complete")
                    
                except Exception as e:
                    print(f"❌ Generation failed for configuration #{config_idx}: {str(e)}")
                    prompt_completions.append({
                        "config": config,
                        "completion": {"error": str(e)}
                    })
            
            # Add all completions to the prompt
            prompt["completions"] = prompt_completions
            results.append(prompt)
            print(f"✓ Prompt {idx}/{total_prompts} complete")
        
        # Save results
        output_data = {"instructions": results}
        output_path = os.path.join(
            self.output_dir,
            self._get_output_filename("completions", categories)
        )
        self._save_file(output_data, output_path)
        
        print(f"💫 Generated completions saved to: {output_path}")
        return output_path