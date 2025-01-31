"""Base class for test operations."""
from typing import List, Dict, Any
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from apis.analyzer import PROVIDERS
from .config import config

class BaseTestClass:
    def __init__(self, output_dir: str = None):
        """Initialize base test class."""
        load_dotenv()
        self.output_dir = Path(output_dir or config.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)

    def _load_file(self, file_path: str) -> Dict[str, Any]:
        """Load JSON file."""
        with open(file_path) as f:
            return json.load(f)

    def _save_file(self, data: Dict[str, Any], output_path: str) -> None:
        """Save data to JSON file."""
        path = Path(output_path)
        path.parent.mkdir(exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def _get_output_filename(self, prefix: str = "", categories: List[str] = None) -> str:
        """Generate timestamped output filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parts = [timestamp]
        
        if prefix:
            parts.append(prefix)
            
        if categories:
            parts.extend(cat.replace("/", "_").replace(" ", "_") for cat in categories)
            
        return f"{'_'.join(parts)}.json"

    def _filter_prompts(
        self,
        rows: List[Dict[str, Any]],
        categories: List[str] = None,
        behaviors: List[str] = None,
        sources: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Filter prompts based on criteria."""
        filtered = []
        for row in rows:
            data = row["row"]
            if (not categories or data["Category"] in categories) and \
               (not behaviors or data["Behavior"] in behaviors) and \
               (not sources or data["Source"] in sources):
                filtered.append({
                    "instruction": data["Goal"],
                    "category": data.get("Category"),
                    "behavior": data.get("Behavior"),
                    "source": data.get("Source"),
                })
        return filtered