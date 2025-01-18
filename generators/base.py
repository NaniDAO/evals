import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from apis.analyzer import create_handler

class BaseTestClass:
    # Default configurations
    OUTPUT_DIR = "out"
    DATA_DIR = "data"
    DEFAULT_RATE_LIMIT = 5
    DEFAULT_RATE_PERIOD = 60
    
    DEFAULT_MODELS = {
        "gemini": "gemini-2.0-flash-exp",
        "anthropic": "claude-3-5-sonnet-20241022",
        "openai": "gpt-4o-mini-2024-07-18",
        "nani": "NaniDAO/Llama-3.3-70B-Instruct-ablated",
    }

    def __init__(self, output_dir: str = OUTPUT_DIR):
        """Initialize with basic setup."""
        load_dotenv()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def _load_file(self, file_path: str) -> Dict[str, Any]:
        """Load JSON file."""
        with open(file_path, "r") as file:
            return json.load(file)

    def _save_file(self, data: Dict[str, Any], output_path: str) -> None:
        """Save data to JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as file:
            json.dump(data, file, indent=2)

    def _get_output_filename(self, prefix: str = "", categories: List[str] = None) -> str:
        """Generate timestamped output filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parts = [timestamp]
        
        if prefix:
            parts.append(prefix)
            
        if categories:
            sanitized_categories = [
                cat.replace("/", "_").replace(" ", "_")
                for cat in categories
            ]
            parts.extend(sanitized_categories)
            
        return f"{'_'.join(parts)}.json"

    def _create_instruction_object(
        self,
        goal: str,
        category: str = None,
        behavior: str = None,
        source: str = None
    ) -> Dict[str, Any]:
        """Create a standardized instruction object."""
        return {
            "instruction": goal,
            "category": category,
            "behavior": behavior,
            "source": source,
        }

    def _filter_prompts(
        self,
        rows: List[Dict[str, Any]],
        categories: List[str] = None,
        behaviors: List[str] = None,
        sources: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Filter prompts based on categories, behaviors, and sources."""
        filtered_prompts = []

        for row in rows:
            row_data = row["row"]
            include_row = True

            if categories:
                include_row = include_row and row_data["Category"] in categories
            if behaviors:
                include_row = include_row and row_data["Behavior"] in behaviors
            if sources:
                include_row = include_row and row_data["Source"] in sources

            if include_row:
                filtered_prompts.append(
                    self._create_instruction_object(
                        row_data["Goal"],
                        row_data.get("Category"),
                        row_data.get("Behavior"),
                        row_data.get("Source"),
                    )
                )

        return filtered_prompts