# test_completions.py
from ..generators.completions import CompletionGenerator

def test_generate_specific_category():
    generator = CompletionGenerator()
    output_file = generator.generate_completions(
        categories=["Privacy", "Phshing"],
        # behaviors=["Behavior1"],
        # sources=["Source1"]
    )

def test_generate_all_prompts():
    generator = CompletionGenerator()
    output_file = generator.generate_completions()

if __name__ == "__main__":
    test_generate_specific_category()
