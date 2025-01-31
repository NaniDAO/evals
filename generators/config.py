"""Global configuration for the evaluation system."""
from typing import Dict, Any, Optional
import os
import json
from pathlib import Path

class Config:
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    OUTPUT_DIR = BASE_DIR / "out"
    
    # Configuration paths
    DATASETS_CONFIG = DATA_DIR / "datasets" / "jailbreaks_datasets.json"
    PROMPTS_CONFIG = DATA_DIR / "prompts" / "eval_prompts.json"
    
    # Rate limiting defaults
    DEFAULT_RATE_LIMIT = 5
    DEFAULT_RATE_PERIOD = 60
    
    def __init__(self):
        self._datasets = self._load_json(
            self.DATASETS_CONFIG, 
            default=[{"JBB": str(self.DATA_DIR / "datasets" / "JBB_dataset.json")}]
        )
        self._prompts = self._load_json(self.PROMPTS_CONFIG)
        
    def _load_json(self, path: Path, default: Any = None) -> Dict[str, Any]:
        """Load JSON configuration file."""
        try:
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading config from {path}: {e}")
            return default if default is not None else {}

    def get_dataset_path(self, name: Optional[str] = None) -> str:
        """Get dataset path from configuration."""
        dataset = name or "JBB"
        dataset_info = next((item for item in self._datasets if dataset in item), None)
        if not dataset_info:
            raise ValueError(f"Dataset '{dataset}' not found in configuration")
        
        # Convert relative path to absolute using BASE_DIR
        rel_path = dataset_info[dataset].replace("../../", "")
        return str(self.BASE_DIR / rel_path)

    def get_prompt_path(self, name: str) -> str:
        """Get evaluation prompt path from configuration."""
        prompt_info = next((item for item in self._prompts if name in item), None)
        if not prompt_info:
            raise ValueError(f"Prompt '{name}' not found in configuration")
            
        # Convert relative path to absolute using BASE_DIR
        rel_path = prompt_info[name].replace("../../", "")
        return str(self.BASE_DIR / rel_path)

# Global configuration instance
config = Config()