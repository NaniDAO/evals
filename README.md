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

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Basic Usage

### Exploring Datasets
```bash
# List available behaviors
python main.py --list-behaviors

# List categories in a specific dataset
python main.py --completions-dataset NANI --list-categories

# Show prompts that match specific criteria
python main.py --show-prompts --dataset-category Hardware
```

### Generating Completions

```bash
# Generate completions using default settings
python main.py

# Generate completions from specific dataset
python main.py --completions-dataset NANI
```

### Evaluating Completions

```bash
# Generate and evaluate completions using Gemini
python main.py --evaluation-judge gemini

# Evaluate existing completions file
python main.py --evaluation-judge anthropic --evaluate-file out/completions.json
```

Datasets for generating completions are found in `data/datasets/jailbreaks_datasets.json`.

Prompts for generating evaluations are found in `data/prompts/eval_prompts.json`.

## Advanced Usage

### 1. Filtered Completion Generation

Generate completions for specific categories/behaviors:
```bash
python main.py \
  --completions-dataset NANI \
  --dataset-category Hardware \
  --dataset-behavior Engineering
```

### 2. Custom Evaluation Settings

Evaluate with specific model and prompt:
```bash
python main.py \
  --evaluation-judge anthropic \
  --evaluation-model claude-3-5-sonnet-20241022 \
  --evaluation-prompt eval0_system_prompt
```

### 3. Combined Generation and Evaluation

Generate and evaluate in one run with filters:
```bash
python main.py \
  --completions-dataset NANI \
  --evaluation-judge gemini \
  --dataset-category Hardware \
  --dataset-source Original
```

## Arguments Reference

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
- `--config-file`: Custom model configuration

### Evaluation
- `--evaluation-judge`: Judge provider (gemini/anthropic/openai)
- `--evaluation-model`: Specific judge model
- `--evaluation-prompt`: Evaluation prompt (default: eval0_system_prompt)
- `--evaluate-file`: Existing completions file to evaluate

## Default Models

| Provider  | Model |
|-----------|-------|
| gemini    | gemini-2.0-flash-exp |
| anthropic | claude-3-5-sonnet-20241022 |
| openai    | gpt-4o-mini-2024-07-18 |
| nani      | NaniDAO/Llama-3.3-70B-Instruct-ablated |

## Project Structure

```
/apis           - LLM provider implementations
/data
  /configs     - Model configurations
  /datasets    - Input datasets
  /info        - Historical data
  /prompts     - Evaluation prompts
/generators    - Core generation/evaluation logic
/tests         - Test suite
/utils         - Helper utilities
```

## Output Format

Results are saved with timestamps:
```
out/YYYYMMDD_HHMMSS_completions.json  # For completions
out/YYYYMMDD_HHMMSS_eval_gemini.json  # For evaluations
```

Previous evaluation results are available in `data/info/old_evals/`.