"""Tests for completion evaluation functionality."""
from pathlib import Path
from ..generators.evaluations import CompletionEvaluator
from ..generators.completions import CompletionGenerator

def _generate_test_completions() -> str:
    """Helper to generate completions for testing."""
    generator = CompletionGenerator()
    generator.generate_completions(
        dataset_path=generator.config.get_dataset_path(),
        categories=["Privacy"]
    )
    return generator.get_last_output_path()

def test_evaluate_with_anthropic():
    """Test evaluation using Anthropic's Claude."""
    evaluator = CompletionEvaluator()
    completions_file = _generate_test_completions()
    
    results = evaluator.evaluate_completions(
        completions_file=completions_file,
        judge_provider="anthropic",
        system_prompt="You are an expert evaluator."
    )
    
    # Verify results structure
    assert isinstance(results, dict)
    assert "instructions" in results
    
    # Verify evaluations exist
    for instruction in results["instructions"]:
        assert "evaluations" in instruction
    
    # Verify file was saved
    assert evaluator.get_last_output_path() is not None
    assert Path(evaluator.get_last_output_path()).exists()

def test_evaluate_with_gemini():
    """Test evaluation using Google's Gemini."""
    evaluator = CompletionEvaluator()
    completions_file = _generate_test_completions()
    
    results = evaluator.evaluate_completions(
        completions_file=completions_file,
        judge_provider="gemini"
    )
    
    # Verify results
    assert isinstance(results, dict)
    assert "instructions" in results
    assert len(results["instructions"]) > 0

def test_evaluate_without_saving():
    """Test evaluation without saving to file."""
    evaluator = CompletionEvaluator()
    completions_file = _generate_test_completions()
    
    results = evaluator.evaluate_completions(
        completions_file=completions_file,
        judge_provider="gemini",
        save_output=False
    )
    
    # Verify results exist but weren't saved
    assert isinstance(results, dict)
    assert evaluator.get_last_results() == results
    assert evaluator.get_last_output_path() is None

if __name__ == "__main__":
    test_evaluate_with_anthropic()