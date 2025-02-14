"""Main entry point for the evaluation system."""

import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from .generators.config import config
from .generators.completions import CompletionGenerator
from .generators.evaluations import CompletionEvaluator
from .apis.analyzer import PROVIDERS


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate prompts and completions using LLM judges."
    )

    # Core evaluation parameters
    parser.add_argument(
        "--evaluation-prompt",
        default="eval0_system_prompt",
        help="Name of the prompt file to use for evaluating completions. (default: eval0_system_prompt)",
    )
    parser.add_argument(
        "--completions-dataset",
        help="Name of the dataset from jailbreaks_datasets.json to use (default: JBB).",
    )
    parser.add_argument(
        "--evaluation-judge",  # NOTE: change to --evaluation-provider
        required=False,
        choices=["gemini", "anthropic", "openai", "nani", "huggingface"],
        help="Specify which model to use for the analysis.",
    )

    # Provider-specific configuration
    parser.add_argument(
        "--providers",  # NOTE: change to --completion-providers
        nargs="+",
        choices=list(PROVIDERS.keys()),
        default=["nani"],
        help="List of providers to use for completions generation (default: nani)",
    )
    parser.add_argument(
        "--provider-urls",
        nargs="+",
        help="Base URLs for providers that require it (format: provider:url, e.g., huggingface:https://my-endpoint)",
    )
    parser.add_argument(
        "--provider-models",
        nargs="+",
        help="Model names for specific providers (format: provider:model, e.g., huggingface:my-model)",
    )
    parser.add_argument(
        "--provider-api-keys",
        nargs="+",
        help="API keys for specific providers (format: provider:key, e.g., huggingface:my-key)",
    )

    # Optional configurations
    parser.add_argument(
        "--evaluate-file", help="Path to the completions JSON file to evaluate."
    )
    parser.add_argument(
        "--config-file",
        type=Path,
        help="Path to the configuration file containing model parameters.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.OUTPUT_DIR,
        help="Directory to save output files.",
    )

    # Dataset filtering options
    parser.add_argument(
        "--dataset-category",
        nargs="+",
        help="Filter: Which categories to include in the evaluation.",
    )
    parser.add_argument(
        "--dataset-behavior",
        nargs="+",
        help="Filter: Which behaviors to include in the evaluation.",
    )
    parser.add_argument(
        "--dataset-source",
        nargs="+",
        help="Filter: Which sources to include in the evaluation.",
    )

    # Dataset feature listing options
    parser.add_argument(
        "--list-behaviors",
        action="store_true",
        help="List all available behaviors in the selected dataset",
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all available categories in the selected dataset",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List all available sources in the selected dataset",
    )
    parser.add_argument(
        "--show-prompts",
        action="store_true",
        help="Show prompts that match the specified behavior/category/source filters",
    )

    return parser.parse_args()


def print_unique_features(dataset_path: str, feature_type: str) -> None:
    """Print unique features from dataset."""
    try:
        with open(dataset_path) as f:
            data = json.load(f)

        # First try to get from unique_features
        if "unique_features" in data and feature_type in data["unique_features"]:
            features = set(data["unique_features"][feature_type])
        # If not found, extract from rows
        elif "rows" in data:
            features = set()
            for item in data["rows"]:
                if "row" in item and feature_type in item["row"]:
                    feature = item["row"][feature_type]
                    if feature:
                        features.add(feature)
        else:
            print(f"⚠️ No rows or unique_features found in dataset")
            return

        if not features:
            print(f"⚠️ No {feature_type.lower()} features found in dataset")
            return

        print(f"\n📋 Available {feature_type}s:")
        for idx, feature in enumerate(sorted(features), 1):
            print(f"{idx}. {feature}")

    except Exception as e:
        print(f"❌ Error reading dataset: {str(e)}")


def show_matching_prompts(
    dataset_path: str,
    *,
    categories: list = None,
    behaviors: list = None,
    sources: list = None,
) -> None:
    """Show prompts that match the specified filters."""
    try:
        with open(dataset_path) as f:
            data = json.load(f)

        if "rows" not in data:
            print(f"⚠️ No rows found in dataset")
            return

        matching_prompts = []
        for item in data.get("rows", []):
            if "row" not in item:
                continue

            row = item["row"]
            matches = True

            # Only apply filters that are specified
            if categories:
                matches = matches and row.get("Category") in categories
            if behaviors:
                matches = matches and row.get("Behavior") in behaviors
            if sources:
                matches = matches and row.get("Source") in sources

            if matches:
                matching_prompts.append(row)

        if not matching_prompts:
            print(f"⚠️ No prompts found matching filters:")
            if categories:
                print(f"  Categories: {categories}")
            if behaviors:
                print(f"  Behaviors: {behaviors}")
            if sources:
                print(f"  Sources: {sources}")
            return

        print(f"\n📝 Found {len(matching_prompts)} matching prompts:")
        for idx, prompt in enumerate(matching_prompts, 1):
            print(f"\nPrompt #{idx}:")
            for field in ["Category", "Behavior", "Source", "Goal"]:
                if field in prompt:
                    print(f"{field}: {prompt[field]}")
            print("-" * 80)

    except Exception as e:
        print(f"❌ Error reading dataset: {str(e)}")


def parse_provider_args(args_list, prefix=""):
    """Parse provider-specific arguments in format provider:value."""
    if not args_list:
        return {}

    result = {}
    for item in args_list:
        if ":" not in item:
            continue
        provider, value = item.split(":", 1)
        if prefix:
            # For environment variables
            value = os.getenv(f"{prefix}{value}", value)
        result[provider] = value
    return result


def ensure_output_dir(path: Path) -> Path:
    """Ensure output directory exists."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def main():
    """Main execution flow."""
    # Initialize environment
    load_dotenv()
    args = parse_arguments()
    
    if not any([
        args.evaluate_file,
        args.list_behaviors,
        args.list_categories,
        args.list_sources,
        args.show_prompts,
        args.completions_dataset,
        args.evaluation_judge
    ]):
        print("\n⚠️ No action specified, exiting...")
        print("Run with --help for usage instructions.\n")
        print("You will need to specify at least one of the following:\n")
        print("  1. --providers")
        print("  2. --completions-dataset\n")
        print("Or, if you want to evaluate completions:\n")
        print("  3. --evaluate-file")
        print("  4. --evaluation-judge\n")
        return
    
    # Handle feature listing and prompt inspection requests
    if any([args.list_behaviors, args.list_categories, args.list_sources, args.show_prompts]):
        try:
            dataset_name = args.completions_dataset or "JBB"
            print(f"\n🔍 Using dataset: {dataset_name}")
            dataset_path = config.get_dataset_path(dataset_name)
            
            if args.list_behaviors:
                print_unique_features(dataset_path, "Behavior")
            if args.list_categories:
                print_unique_features(dataset_path, "Category")
            if args.list_sources:
                print_unique_features(dataset_path, "Source")
            if args.show_prompts:
                show_matching_prompts(
                    dataset_path=dataset_path,
                    categories=args.dataset_category,
                    behaviors=args.dataset_behavior,
                    sources=args.dataset_source
                )
            return
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return

    # Parse provider-specific configurations
    provider_urls = parse_provider_args(args.provider_urls)
    provider_models = parse_provider_args(args.provider_models)
    provider_api_keys = parse_provider_args(args.provider_api_keys)
    
    # Continue with normal evaluation flow
    output_dir = ensure_output_dir(args.output_dir)
    completions_only = not args.evaluation_judge

    try:
        if args.evaluate_file:
            # Direct evaluation mode
            if completions_only:
                raise ValueError("Cannot evaluate file without specifying a judge")

            # Configure evaluator with judge provider settings
            judge_provider = args.evaluation_judge
            judge_config = {}
            
            # Add base_url if provided
            if provider_urls.get(judge_provider):
                judge_config["base_url"] = provider_urls[judge_provider]
                
            # Add API key if provided
            if provider_api_keys.get(judge_provider):
                judge_config["api_key"] = provider_api_keys[judge_provider]
                
            # Add model if provided
            if provider_models.get(judge_provider):
                judge_config["model"] = provider_models[judge_provider]
    
            print(f"DEBUG - Judge config: {judge_config}")

            evaluator = CompletionEvaluator(output_dir=output_dir)
            evaluator.evaluate_completions(
                completions_file=args.evaluate_file,
                eval_prompt_name=args.evaluation_prompt,
                judge_provider=judge_provider,
                system_prompt=args.evaluation_prompt,
                **judge_config
            )
            
            output_path = evaluator.get_last_output_path()
            print(f"✨ Evaluation completed: {output_path}")
            
        else:
            # Generate completions mode
            try:
                dataset_path = config.get_dataset_path(args.completions_dataset)
            except ValueError as e:
                print(f"⚠️ {e}, using default dataset")
                dataset_path = config.get_dataset_path()

            # Build provider configurations
            provider_configs = {}
            for provider in args.providers:
                config_dict = {}
                
                # Add base_url if provided
                if provider_urls.get(provider):
                    config_dict["base_url"] = provider_urls[provider]
                    
                # Add API key if provided
                if provider_api_keys.get(provider):
                    config_dict["api_key"] = provider_api_keys[provider]
                    
                # Add model if provided
                if provider_models.get(provider):
                    config_dict["model"] = provider_models[provider]
                    
                provider_configs[provider] = config_dict
                
            print(f"DEBUG - Provider configurations: {provider_configs}")

            # Initialize generator with configurations
            generator = CompletionGenerator(
                output_dir=output_dir,
                providers=args.providers,
                provider_configs=provider_configs
            )

            # Generate completions
            generator.generate_completions(
                dataset_path=dataset_path,
                categories=args.dataset_category,
                behaviors=args.dataset_behavior,
                sources=args.dataset_source,
                config_file=args.config_file,
            )

            completions_path = generator.get_last_output_path()
            print(f"📝 Completions generated: {completions_path}")

            # Handle evaluation if needed
            if not completions_only:
                evaluator = CompletionEvaluator(output_dir=output_dir)
                
                # Configure evaluator with judge provider settings
                judge_provider = args.evaluation_judge
                judge_config = {}
                
                # Add base_url if provided
                if provider_urls.get(judge_provider):
                    judge_config["base_url"] = provider_urls[judge_provider]
                    
                # Add API key if provided
                if provider_api_keys.get(judge_provider):
                    judge_config["api_key"] = provider_api_keys[judge_provider]
                    
                # Add model if provided
                if provider_models.get(judge_provider):
                    judge_config["model"] = provider_models[judge_provider]
                    
                print(f"DEBUG - Judge config: {judge_config}")
                
                evaluator.evaluate_completions(
                    completions_file=completions_path,
                    eval_prompt_name=args.evaluation_prompt,
                    judge_provider=judge_provider,
                    system_prompt=args.evaluation_prompt,
                    **judge_config
                )
                
                output_path = evaluator.get_last_output_path()
                print(f"✨ Evaluation completed: {output_path}")

        print("Process completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    
if __name__ == "__main__":
    main()
