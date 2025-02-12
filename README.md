# NaniDAO/evals

A Python library for generating completions and evaluating NaniDAO models using different datasets, prompts, and configuration files.

## Quick Start

1. Set up environment variables in `.env`:
```bash
NANI_API_KEY=your_nani_api_key
NANI_BASE_URL=http://nani.ooo/api/chat
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

If not, you can specify individual API_KEY/BASE_URL using CLI arguments.

2. Install dependencies:
```bash
# Using uv (recommended)
git clone https://github.com/NaniDAO/evals.git
cd evals
uv pip install -e .

# Or using pip
git clone https://github.com/NaniDAO/evals.git
cd evals
pip install -e .
```

## data/info

Directory contains previous completions and evaluations run on different LLMs using datasets from `nanidao_evals/data/datasets`. Inspect individual metadata for details. Not part of the `nanidao-evals` package.

## Basic Usage

### Simplest Commands

Generate completions using default settings:
```bash
# Using environment variables from .env
nanidao-evals

# Or passing credentials via CLI
nanidao-evals \
  --providers nani \
  --provider-urls "nani:https://nani.ooo/api/chat" \
  --provider-api-keys "nani:your-api-key"
```

Evaluate existing completions:
```bash
# Using environment variables
nanidao-evals --evaluation-judge nani --evaluate-file out/completions.json

# Or passing credentials via CLI
nanidao-evals \
  --evaluation-judge nani \
  --provider-urls "nani:https://nani.ooo/api/chat" \
  --provider-api-keys "nani:your-api-key" \
  --evaluate-file out/completions.json
```

### Exploring Datasets
```bash
# List available behaviors (default dataset: JBB)
nanidao-evals --list-behaviors

# List categories in a specific dataset
nanidao-evals --completions-dataset NANI --list-categories

# Show prompts that match specific criteria
nanidao-evals --show-prompts --dataset-category Hardware --completions-dataset NANI
```

### Generating Completions

```bash
# Generate completions from specific dataset
nanidao-evals --completions-dataset NANI

# Generate with multiple configurations
nanidao-evals \
  --providers nani \
  --config-file configs/multi_temp.json \
  --completions-dataset NANI
```

Example `configs/multi_temp.json`:
```json
[
    {
      "temperature": 0.7,
      "max_tokens": 1000,
      "top_p": 1.0
    },
    {
      "temperature": 0.9,
      "max_tokens": 1500,
      "top_p": 0.9
    }
]
```

### Evaluating Completions

```bash
# Generate and evaluate completions using Gemini
nanidao-evals --evaluation-judge gemini

# Evaluate existing completions file
nanidao-evals --evaluation-judge anthropic --evaluate-file out/completions.json
```

Datasets for generating completions are found in `data/datasets/jailbreaks_datasets.json`.

Prompts for generating evaluations are found in `data/prompts/eval_prompts.json`.

## Advanced Usage Examples

### 1. Command Line Interface

Generate completions using specific provider and model:
```bash
nanidao-evals \
  --providers nani \
  --provider-urls "nani:https://nani.ooo/api/chat" \
  --provider-models "nani:deepseek-r1-qwen-2.5-32B-ablated" \
  --provider-api-keys "nani:your-api-key" \
  --completions-dataset NANI
```

### 2. Python API

```python
from nanidao_evals.generators.completions import CompletionGenerator

# Configure providers
provider_configs = {
    "nani": {
        "base_url": "https://nani.ooo/api/chat",
        "api_key": "your-api-key",
        "model": "deepseek-r1-qwen-2.5-32B-ablated"
    }
}

# Create generator
generator = CompletionGenerator(
    providers=["nani"],
    provider_configs=provider_configs
)

# Generate completions
results = generator.generate_completions(
    dataset_path="data/datasets/nani_dataset.json",
    categories=["Hardware"],
    behaviors=["Engineering"]
)
```

### 3. Direct API Usage

```python
from apis.analyzer import create_handler

# Initialize handler
handler = create_handler(
    provider="nani",
    model="deepseek-r1-qwen-2.5-32B-ablated",
    base_url="https://nani.ooo/api/chat",
    api_key="your-api-key"
)

# Generate response
response = handler.generate_response("Your prompt here")
```

## Filtered Generation Examples

### 1. Filtered Completion Generation

Generate completions for specific categories/behaviors:
```bash
nanidao-evals \
  --completions-dataset NANI \
  --dataset-category Hardware \
  --dataset-behavior Engineering
```

### 2. Custom Evaluation Settings

Evaluate with specific model and prompt:
```bash
nanidao-evals \
  --evaluation-judge anthropic \
  --provider-models "anthropic:claude-3-5-sonnet-20241022" \
  --evaluation-prompt eval0_system_prompt
```

### 3. Combined Generation and Evaluation

Generate and evaluate in one run with filters:
```bash
nanidao-evals \
  --completions-dataset NANI \
  --evaluation-judge gemini \
  --dataset-category Hardware \
  --dataset-source Original
```

## CLI Arguments Reference

### Provider Configuration
- `--providers`: List of providers to use (e.g., nani, gemini, anthropic)
- `--provider-urls`: Base URLs for providers (format: provider:url)
- `--provider-models`: Model names for providers (format: provider:model)
- `--provider-api-keys`: API keys for providers (format: provider:key)

### Dataset Exploration
- `--list-behaviors`: Show available behaviors
- `--list-categories`: Show available categories
- `--list-sources`: Show available sources
- `--show-prompts`: Display prompts matching filters
- `--completions-dataset`: Select dataset (default: JBB)

### Generation & Filtering
- `--dataset-category`: Filter by categories
- `--dataset-behavior`: Filter by behaviors
- `--dataset-source`: Filter by sources
- `--output-dir`: Output directory (default: out)
- `--config-file`: Custom model configuration file (supports multiple configs)

### Evaluation
- `--evaluation-judge`: Judge provider (gemini/anthropic/openai/nani)
- `--evaluation-prompt`: Evaluation prompt (default: eval0_system_prompt)
- `--evaluate-file`: Existing completions file to evaluate

## Default Models

| Provider  | Model |
|-----------|-------|
| gemini    | gemini-2.0-flash-exp |
| anthropic | claude-3-5-sonnet-20241022 |
| openai    | gpt-4o-mini-2024-07-18 |
| nani      | NaniDAO/deepseek-r1-qwen-2.5-32B-ablated |
| huggingface | tgi |

## Project Structure

```
/apis           - LLM provider implementations
/data
  /configs     - Model configurations
  /datasets    - Input datasets
  /prompts     - Evaluation prompts
/generators    - Core generation/evaluation logic
```

## Output Format

Results are saved with timestamps:
```
out/YYYYMMDD_HHMMSS_completions.json  # For completions
out/YYYYMMDD_HHMMSS_eval_provider.json  # For evaluations
```

Previous evaluation results are available in `data/info/old_evals/`.

## Provider-Specific Configuration

### Credentials
All providers can be configured either through environment variables in `.env` or via CLI arguments.

### HuggingFace
```bash
nanidao-evals \
  --providers huggingface \
  --provider-urls "huggingface:https://your-endpoint" \
  --provider-models "huggingface:your-model" \
  --provider-api-keys "huggingface:your-key"
```

### Nani
```bash
nanidao-evals \
  --providers nani \
  --provider-urls "nani:https://nani.ooo/api/chat" \
  --provider-models "nani:NaniDAO/deepseek-r1-qwen-2.5-32B-ablated"
```

### Multiple Providers
```bash
nanidao-evals \
  --providers nani huggingface \
  --provider-urls "nani:https://nani.ooo/api/chat" "huggingface:https://your-endpoint" \
  --provider-models "nani:model1" "huggingface:model2"
```