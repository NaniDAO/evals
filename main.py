import argparse
from dotenv import load_dotenv
from generators.completions import CompletionGenerator
from generators.evaluations import CompletionEvaluator

OUTPUT_DIR = "out"
DATA_DIR = "data"

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Evaluate prompts and completions using LLM judges."
    )

    parser.add_argument(
        "--eval-prompt",
        default="eval0_system_prompt",
        help="Name of the prompt file to use for evaluating completions.",
    )
    parser.add_argument(
        "--dataset",
        default="data/datasets/JBB_dataset.json",
        help="Name of the jailbreaks file to use for generating completions.",
    )
    parser.add_argument(
        "--judge",
        required=False,
        choices=["gemini", "anthropic", "openai"],
        help="Specify which model to use for the analysis.",
    )
    parser.add_argument(
        "--model",
        help="Specify which model to use for the evaluation. If not provided, uses provider's default model.",
    )
    parser.add_argument(
        "--evaluate-candidates-file",
        help="Path to the layer candidates JSON file to evaluate.",
    )
    parser.add_argument(
        "--config-file",
        help="Path to the configuration file for the evaluation.",
    )
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help="Directory to save output files.",
    )
    # JBB dataset filtering options
    parser.add_argument(
        "--category",
        nargs="+",
        help="Specify which categories to include in the evaluation.",
    )
    parser.add_argument(
        "--behavior",
        nargs="+",
        help="Specify which behaviors to include in the evaluation.",
    )
    parser.add_argument(
        "--source",
        nargs="+",
        help="Specify which sources (of jailbreak) to include in the evaluation.",
    )

    return parser.parse_args()

def main():
    # Initialize environment and parse arguments
    load_dotenv()
    args = parse_arguments()

    # Add completions-only mode flag
    completions_only = not args.judge

    # Initialize generators with output directory
    generator = CompletionGenerator(output_dir=args.output_dir)
    evaluator = CompletionEvaluator(output_dir=args.output_dir) if not completions_only else None

    # Handle different execution modes
    if args.evaluate_candidates_file:
        if completions_only:
            print("Error: Cannot evaluate candidates file in completions-only mode")
            return

        # Evaluate existing completions file
        output_path = evaluator.evaluate_completions(
            completions_file=args.evaluate_candidates_file,
            eval_prompt_name=args.eval_prompt,
            judge_provider=args.judge,
            judge_model=args.model,
            system_prompt=args.eval_prompt,
        )
    else:
        # Generate completions
        completions_path = generator.generate_completions(
            categories=args.category,
            behaviors=args.behavior,
            sources=args.source,
            dataset_path=args.dataset,
            config_file=args.config_file,
        )

        # Evaluate completions if not in completions-only mode
        if not completions_only:
            output_path = evaluator.evaluate_completions(
                completions_file=completions_path,
                eval_prompt_name=args.eval_prompt,
                judge_provider=args.judge,
                judge_model=args.model,
                system_prompt=args.eval_prompt,
            )

    print(f"Process completed successfully!")

if __name__ == "__main__":
    main()