# NaniDAO/evals

A Python library for generating completions and evaluations of NaniDAO models using different datasets, prompts and configuration files.

Provides both CLI and PythonAPI for running prompt completions and evaluations.

Use `main.py` for CLI.

`/apis` contains wrappers for sending prompts to OpenAI, Anthropic, Google, HuggingFace and custom curl endpoints

`/data` directory:
  - `/configs` contains example prompt configs to use for generating completions
  - `/datasets` contains example datasets to generate completions for
  - `/info` contains the past runs data
  - `/prompts` constains example system prompts to use for generating evaluations of completions

`/generators` contain PythonAPI methods to build your own custom completion<>evaluation pipelines

`/test` contain custom completion<>evaluations tests built on top off PythonAPI

`/utils` contain helper scripts

# AI Response Evaluation CLI

A command-line tool for generating and evaluating AI model responses using different LLM providers.

## Features

- Generate completions using NANI model
- Evaluate completions using different judge models (Gemini, Anthropic, or OpenAI)
- Filter input prompts by category, behavior, and source
- Configurable rate limiting
- JSON output with timestamps
- Support for custom system prompts and evaluation prompts

## Prerequisites

1. Set up environment variables in `.env`:
```
NANI_API_KEY=your_nani_api_key
NANI_BASE_URL=http://nani.ooo/api/chat
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

2. Ensure required data files are present:
- Evaluation prompts collection: `data/prompts/eval_prompts.json`
- Jailbreaks dataset: `data/datasets/JBB_dataset.json`

## Usage Modes

### 1. Generate Completions Only

Generate completions using the NANI model without evaluation:

```bash
python main.py \
  --jailbreaks-dataset data/datasets/JBB_dataset.json \
  --category "Category1" "Category2" \
  --behavior "Behavior1" \
  --source "Source1" \
  --output-dir out
```

To only generate completions from Nani endpoint you can just run `python main.py`. It will use a `/data/datasets/jailbreaks_data.json` by default to generated completions.

### 2. Evaluate Existing Completions

Evaluate previously generated completions using a specified judge model:

```bash
python main.py \
  --evaluate-candidates-file path/to/completions.json \
  --eval-prompt eval0_system_prompt \
  --judge anthropic \
  --model claude-3-5-sonnet-20241022 \
  --output-dir out
```

To only generated evaluation from previously generated completions file you can just run `python main.py --judge gemini --evaluate-candidates-file out/<timestamp>.json`.

### 3. Generate and Evaluate Completions

Generate completions and immediately evaluate them:

```bash
python main.py \
  --jailbreaks-dataset data/datasets/JBB_dataset.json \
  --eval-prompt eval0_system_prompt \
  --judge anthropic \
  --source "Source1" \
  --output-dir out
```

You can generate both completions and evaluations in the single run with `python main.py --judge gemini`

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--eval-prompt` | Name of the prompt file for evaluation | eval0_system_prompt |
| `--jailbreaks-dataset` | Path to the jailbreaks dataset | data/datasets/JBB_dataset.json |
| `--judge` | Model provider for evaluation (gemini/anthropic/openai) | None |
| `--model` | Specific model to use for evaluation | Provider's default model |
| `--evaluate-candidates-file` | Path to existing completions file | None |
| `--config-file` | Path to configuration file | None |
| `--rate-limit` | Number of requests per rate period | 5 |
| `--rate-period` | Rate limit period in seconds | 60 |
| `--output-dir` | Directory for output files | out |
| `--system-prompt` | System prompt for evaluation | "" |
| `--category` | Categories to include (multiple allowed) | None |
| `--behavior` | Behaviors to include (multiple allowed) | None |
| `--source` | Sources to include (multiple allowed) | None |

## Default Models

```json
{
    "gemini": "gemini-2.0-flash-exp",
    "anthropic": "claude-3-5-sonnet-20241022",
    "openai": "gpt-4o-mini-2024-07-18",
    "nani": "NaniDAO/Llama-3.3-70B-Instruct-ablated"
}
```

## Output Format

Results are saved in JSON format with timestamps:
```
out/YYYYMMDD_HHMMSS_category1_category2.json
```

## Error Handling

- The tool validates required arguments based on the execution mode
- Failed evaluations are logged with error messages in the output JSON
- Missing environment variables or data files will trigger appropriate error messages

# Layer Evaluation (OLD/INFORMATIONAL ONLY)

Visit [data/old_evals](./data/old_evals) to inspect old results from previous runs