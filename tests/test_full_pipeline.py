"""Tests for the complete generation and evaluation pipeline."""
from pathlib import Path
from ..generators.completions import CompletionGenerator
from ..generators.evaluations import CompletionEvaluator

def test_generate_and_evaluate():
    """Test the complete pipeline: generation followed by evaluation."""
    # Generate completions
    generator = CompletionGenerator()
    completion_results = generator.generate_completions(
        dataset_path=generator.config.get_dataset_path(),
        categories=["Privacy"],
        behaviors=["Social Engineering"]
    )
    
    assert isinstance(completion_results, dict)
    assert generator.get_last_output_path() is not None
    completion_file = generator.get_last_output_path()
    
    # Evaluate completions
    evaluator = CompletionEvaluator()
    evaluation_results = evaluator.evaluate_completions(
        completions_file=completion_file,
        judge_provider="anthropic"
    )
    
    # Verify complete pipeline
    assert isinstance(evaluation_results, dict)
    assert "instructions" in evaluation_results
    assert all(
        "evaluations" in instruction
        for instruction in evaluation_results["instructions"]
    )
    
    # Verify output files exist
    assert Path(completion_file).exists()
    assert Path(evaluator.get_last_output_path()).exists()

def test_pipeline_without_saving():
    """Test pipeline without saving intermediate files."""
    generator = CompletionGenerator()
    evaluator = CompletionEvaluator()
    
    # Generate without saving
    completion_results = generator.generate_completions(
        dataset_path=generator.config.get_dataset_path(),
        save_output=False
    )
    
    # Use results directly for evaluation
    evaluation_results = evaluator.evaluate_completions(
        completions_file=generator.get_last_output_path(),
        judge_provider="gemini",
        save_output=False
    )
    
    # Verify pipeline worked but didn't save files
    assert isinstance(completion_results, dict)
    assert isinstance(evaluation_results, dict)
    assert generator.get_last_output_path() is None
    assert evaluator.get_last_output_path() is None

if __name__ == "__main__":
    test_generate_and_evaluate()