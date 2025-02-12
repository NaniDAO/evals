"""Handles evaluation of completions using LLM judges."""
from typing import List, Dict, Any, Optional, TypedDict
import json
from .base import BaseTestClass
from ..apis.analyzer import create_handler, PROVIDERS
from .config import config

class EvaluationResults(TypedDict):
    instructions: List[Dict[str, Any]]

class CompletionEvaluator(BaseTestClass):
    def __init__(self, output_dir: str = None):
        """Initialize evaluator."""
        super().__init__(output_dir)
        self.last_results: Optional[EvaluationResults] = None
        self.last_output_path: Optional[str] = None

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
        save_output: bool = True,
        **provider_kwargs
    ) -> EvaluationResults:
        """
        Evaluate completions using specified judge.
        
        Args:
            completions_file: Path to completions file to evaluate
            eval_prompt_name: Name of evaluation prompt to use
            judge_provider: Provider for evaluation (gemini/anthropic/openai)
            judge_model: Optional specific model to use (takes precedence over provider_kwargs['model'])
            system_prompt: Optional system prompt
            save_output: Whether to save results to file (default: True)
            **provider_kwargs: Provider-specific configuration
            
        Returns:
            EvaluationResults containing evaluations
        """
        if judge_provider not in PROVIDERS:
            raise ValueError(f"Unsupported provider: {judge_provider}")
            
        # Load evaluation prompt
        eval_prompt = self._load_eval_prompt(eval_prompt_name)
        
        # Update provider_kwargs with judge_model if provided
        if judge_model is not None:
            provider_kwargs = {**provider_kwargs, "model": judge_model}
        
        # Initialize judge with merged configuration
        judge = create_handler(
            provider=judge_provider,
            system_prompt=system_prompt,
            rate_limit=config.DEFAULT_RATE_LIMIT,
            rate_period=config.DEFAULT_RATE_PERIOD,
            **provider_kwargs
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
        
        self.last_results = {"instructions": results}
        
        if save_output:
            output_path = self.output_dir / self._get_output_filename(f"eval_{judge_provider}")
            self._save_file(self.last_results, output_path)
            self.last_output_path = str(output_path)
            print(f"✨ Evaluations saved to: {output_path}")
            
        return self.last_results

    def get_last_output_path(self) -> Optional[str]:
        """Get path of last saved output file."""
        return self.last_output_path

    def get_last_results(self) -> Optional[EvaluationResults]:
        """Get results from last evaluation run."""
        return self.last_results