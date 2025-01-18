"""Handles evaluation of completions using LLM judges."""
from typing import List, Dict, Any, Optional
import os
import json
from .base import BaseTestClass
from apis.analyzer import create_handler, PROVIDERS
from .config import config

class CompletionEvaluator(BaseTestClass):
    def _load_eval_prompt(self, prompt_name: str) -> str:
        """Load evaluation prompt."""
        try:
            prompt_path = config.get_prompt_path(prompt_name)
            with open(prompt_path) as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Failed to load evaluation prompt: {e}")

    def _create_eval_prompt(self, base_prompt: str, instructions: List[str]) -> str:
        """Create evaluation prompt with instructions."""
        if instructions:
            base_prompt += "\n\nIncluded Samples:\n" + "\n".join(instructions)
        return base_prompt

    def evaluate_completions(
        self,
        completions_file: str,
        eval_prompt_name: str = "eval0_system_prompt",
        judge_provider: str = "gemini",
        judge_model: Optional[str] = None,
        system_prompt: str = "",
    ) -> str:
        """Evaluate completions using specified judge."""
        if judge_provider not in PROVIDERS:
            raise ValueError(f"Unsupported provider: {judge_provider}")
            
        # Load evaluation prompt
        eval_prompt = self._load_eval_prompt(eval_prompt_name)
        
        # Initialize judge
        judge = create_handler(
            provider=judge_provider,
            api_key=os.getenv(f"{judge_provider.upper()}_API_KEY"),
            model=judge_model or PROVIDERS[judge_provider][2],
            system_prompt=system_prompt,
            rate_limit=config.DEFAULT_RATE_LIMIT,
            rate_period=config.DEFAULT_RATE_PERIOD
        )
        
        # Load and evaluate completions
        data = self._load_file(completions_file)
        instructions = data.get("instructions", [])
        results = []
        
        print(f"\n📋 Starting evaluation of {len(instructions)} instructions")
        
        for idx, instruction in enumerate(instructions, 1):
            print(f"\n🔍 Processing instruction {idx}/{len(instructions)}")
            
            prompt = self._create_eval_prompt(
                eval_prompt,
                [json.dumps(instruction)]
            )
            
            try:
                evaluation = judge.generate_json_response(prompt)
                print(f"📊 Evaluation: {evaluation}")
                instruction["evaluations"] = evaluation
            except Exception as e:
                print(f"❌ Evaluation failed: {e}")
                instruction["evaluations"] = {"error": str(e)}
                
            results.append(instruction)
            print(f"✓ Instruction {idx}/{len(instructions)} complete")
        
        # Save results
        output_path = self.output_dir / self._get_output_filename(f"eval_{judge_provider}")
        self._save_file({"instructions": results}, output_path)
        
        print(f"✨ Evaluations saved to: {output_path}")
        return str(output_path)