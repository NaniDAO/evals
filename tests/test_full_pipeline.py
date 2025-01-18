# test_full_pipeline.py
from ..generators.completions import CompletionGenerator
from ..generators.evaluations import CompletionEvaluator

def test_generate_and_evaluate():
    # Generate completions
    generator = CompletionGenerator()
    completions_file = generator.generate_completions(
        categories=["Category1"],
        behaviors=["Behavior1"]
    )

    # Evaluate completions
    evaluator = CompletionEvaluator()
    eval_file = evaluator.evaluate_completions(
        completions_file=completions_file,
        judge_provider="anthropic"
    )

if __name__ == "__main__":
    test_generate_and_evaluate()