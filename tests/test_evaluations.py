# test_evaluations.py
from ..generators.evaluations import CompletionEvaluator

def test_evaluate_with_anthropic():
    evaluator = CompletionEvaluator()
    output_file = evaluator.evaluate_completions(
        completions_file="out/20240116_120000_completions.json",
        judge_provider="anthropic",
        system_prompt="You are an expert evaluator."
    )

def test_evaluate_with_gemini():
    evaluator = CompletionEvaluator()
    output_file = evaluator.evaluate_completions(
        completions_file="out/20240116_120000_completions.json",
        judge_provider="gemini"
    )

if __name__ == "__main__":
    test_evaluate_with_anthropic()