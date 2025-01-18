from typing import List, Dict, Any
import os
import json
from .base import BaseTestClass
from apis.analyzer import create_handler

class CompletionEvaluator(BaseTestClass):
    EVAL_PROMPTS_COLLECTION = "data/prompts/eval_prompts.json"
    
    def _load_eval_prompt(self, prompt_name: str) -> str:
        """Load evaluation prompt from collection."""
        try:
            prompt_collection = self._load_file(self.EVAL_PROMPTS_COLLECTION)
            
            prompt_file = None
            for prompt_dict in prompt_collection:
                if prompt_name in prompt_dict:
                    prompt_file = prompt_dict[prompt_name]
                    break

            if not prompt_file:
                raise ValueError(f"Prompt '{prompt_name}' not found in collection")

            with open(prompt_file, "r") as f:
                return f.read().strip()

        except Exception as e:
            raise Exception(f"Failed to load evaluation prompt: {str(e)}")

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
        judge_model: str = None,
        system_prompt: str = "",
        rate_limit: int = BaseTestClass.DEFAULT_RATE_LIMIT,
        rate_period: int = BaseTestClass.DEFAULT_RATE_PERIOD
    ) -> str:
        """Evaluate completions using specified judge."""
        # Load evaluation prompt
        eval_prompt = self._load_eval_prompt(eval_prompt_name)
        
        # Create judge analyzer
        if not judge_model:
            judge_model = self.DEFAULT_MODELS.get(judge_provider)
            
        judge_analyzer = create_handler(
            provider=judge_provider,
            model=judge_model,
            api_key=os.getenv(f"{judge_provider.upper()}_API_KEY"),
            system_prompt=system_prompt,
            rate_limit=rate_limit,
            rate_period=rate_period,
        )
        
        # Load completions
        completions_data = self._load_file(completions_file)
        instructions = completions_data.get("instructions", [])
        
        # Evaluate completions
        evaluated_instructions = []
        total = len(instructions)
        
        print(f"\n📋 Starting evaluation of {total} instructions")
        
        for idx, instruction in enumerate(instructions, 1):
            print(f"\n🔍 Processing instruction {idx}/{total}")
            
            prompt = self._create_eval_prompt(
                eval_prompt,
                [json.dumps(instruction)]
            )
            
            try:
                evaluation = judge_analyzer.generate_json_response(prompt)
                print(f"📊 Evaluation: {evaluation}")
                instruction["evaluations"] = evaluation
            except Exception as e:
                print(f"❌ Evaluation failed: {str(e)}")
                instruction["evaluations"] = {"error": str(e)}
                
            evaluated_instructions.append(instruction)
            print(f"✓ Instruction {idx}/{total} complete")
        
        # Save results
        output_data = {"instructions": evaluated_instructions}
        output_path = os.path.join(
            self.output_dir,
            self._get_output_filename(f"eval_{judge_provider}")
        )
        self._save_file(output_data, output_path)
        
        print(f"✨ Evaluations saved to: {output_path}")
        return output_path