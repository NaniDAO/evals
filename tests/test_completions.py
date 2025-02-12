"""Tests for completion generation functionality."""
from typing import Dict, Any
from pathlib import Path
from ..generators.completions import CompletionGenerator

def test_generate_specific_category():
    """Test generating completions for specific categories."""
    generator = CompletionGenerator()
    results = generator.generate_completions(
        dataset_path=generator.config.get_dataset_path(),
        categories=["Privacy", "Phishing"]
    )
    
    # Verify results structure
    assert isinstance(results, dict)
    assert "instructions" in results
    assert all(
        instruction["category"] in ["Privacy", "Phishing"]
        for instruction in results["instructions"]
    )
    
    # Verify file was saved
    assert generator.get_last_output_path() is not None
    assert Path(generator.get_last_output_path()).exists()

def test_generate_all_prompts():
    """Test generating completions for all prompts."""
    generator = CompletionGenerator()
    results = generator.generate_completions(
        dataset_path=generator.config.get_dataset_path()
    )
    
    # Verify results
    assert isinstance(results, dict)
    assert "instructions" in results
    assert len(results["instructions"]) > 0
    
    # Verify each instruction has required fields
    for instruction in results["instructions"]:
        assert "instruction" in instruction
        assert "completions" in instruction
        assert isinstance(instruction["completions"], list)

def test_generate_without_saving():
    """Test generating completions without saving to file."""
    generator = CompletionGenerator()
    results = generator.generate_completions(
        dataset_path=generator.config.get_dataset_path(),
        save_output=False
    )
    
    # Verify results exist but weren't saved
    assert isinstance(results, dict)
    assert generator.get_last_results() == results
    assert generator.get_last_output_path() is None

if __name__ == "__main__":
    test_generate_specific_category()