"""Main entry point for the evaluation system."""
import argparse
from pathlib import Path
from dotenv import load_dotenv
from generators.config import config
from generators.completions import CompletionGenerator
from generators.evaluations import CompletionEvaluator

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate prompts and completions using LLM judges."
    )

    # Core evaluation parameters
    parser.add_argument(
        "--evaluation-prompt",
        default="eval0_system_prompt",
        help="Name of the prompt file to use for evaluating completions."
    )
    parser.add_argument(
        "--completions-dataset",
        help="Name of the dataset from jailbreaks_datasets.json to use (defaults to JBB_dataset)."
    )
    parser.add_argument(
        "--evaluation-judge",
        required=False,
        choices=["gemini", "anthropic", "openai"],
        help="Specify which model to use for the analysis."
    )

    # Optional configurations
    parser.add_argument(
        "--evaluation-model",
        help="Specify which model to use for the evaluation. If not provided, uses provider's default model."
    )
    parser.add_argument(
        "--evaluate-file",
        help="Path to the completions JSON file to evaluate."
    )
    parser.add_argument(
        "--config-file",
        type=Path,
        help="Path to the configuration file containing model parameters."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.OUTPUT_DIR,
        help="Directory to save output files."
    )

    # Dataset filtering options
    parser.add_argument(
        "--dataset-category",
        nargs="+",
        help="Filter: Which categories to include in the evaluation."
    )
    parser.add_argument(
        "--dataset-behavior",
        nargs="+",
        help="Filter: Which behaviors to include in the evaluation."
    )
    parser.add_argument(
        "--dataset-source",
        nargs="+",
        help="Filter: Which sources to include in the evaluation."
    )

    return parser.parse_args()

def ensure_output_dir(path: Path) -> Path:
    """Ensure output directory exists."""
    path.mkdir(parents=True, exist_ok=True)
    return path

def main():
    """Main execution flow."""
    # Initialize environment
    load_dotenv()
    args = parse_arguments()
    
    # Ensure output directory exists
    output_dir = ensure_output_dir(args.output_dir)
    
    # Determine execution mode
    completions_only = not args.evaluation_judge
    
    try:
        # Initialize generators
        generator = CompletionGenerator(output_dir=output_dir)
        evaluator = CompletionEvaluator(output_dir=output_dir) if not completions_only else None

        if args.evaluate_file:
            # Direct evaluation mode
            if completions_only:
                raise ValueError("Cannot evaluate file without specifying a judge")

            output_path = evaluator.evaluate_completions(
                completions_file=args.evaluate_file,
                eval_prompt_name=args.evaluation_prompt,
                judge_provider=args.evaluation_judge,
                judge_model=args.evaluation_model,
                system_prompt=args.evaluation_prompt
            )
            print(f"✨ Evaluation completed: {output_path}")
            
        else:
            # Generate completions mode
            try:
                dataset_path = config.get_dataset_path(args.completions_dataset)
            except ValueError as e:
                print(f"⚠️ {e}, using default dataset")
                dataset_path = config.get_dataset_path()

            completions_path = generator.generate_completions(
                dataset_path=dataset_path,
                categories=args.dataset_category,
                behaviors=args.dataset_behavior,
                sources=args.dataset_source,
                config_file=args.config_file
            )
            print(f"📝 Completions generated: {completions_path}")

            # Evaluate if judge is specified
            if not completions_only:
                output_path = evaluator.evaluate_completions(
                    completions_file=completions_path,
                    eval_prompt_name=args.evaluation_prompt,
                    judge_provider=args.evaluation_judge,
                    judge_model=args.evaluation_model,
                    system_prompt=args.evaluation_prompt
                )
                print(f"✨ Evaluation completed: {output_path}")

        print("Process completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()