# NaniDAO/evals

A Python library for generating completions and evaluations of NaniDAO models using different datasets, prompts and configuration files.

Provides both CLI and Python API for running prompt completions and evaluations.

Use `main.py` for CLI.

## Project Structure

`/apis` - LLM provider wrappers for:
- OpenAI
- Anthropic
- Google (Gemini)
- HuggingFace
- Custom curl endpoints

`/data` directory:
- `/configs` - Configuration files for completion generation
- `/datasets` - Input datasets for completion generation
- `/info` - Historical run data
- `/prompts` - System prompts for completion evaluation

`/generators` - Python API for building custom completion/evaluation pipelines

`/tests` - Test suite for the evaluation system

`/utils` - Helper utilities

## Prerequisites

1. Set up environment variables in `.env`:
```bash
NANI_API_KEY=your_nani_api_key
NANI_BASE_URL=http://nani.ooo/api/chat
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

2. Required data files:
- Evaluation prompts: `data/prompts/eval_prompts.json`
- Default dataset: `data/datasets/JBB_dataset.json`

## Usage Modes

### 1. Generate Completions Only

Generate completions using the NANI model:

```bash
python main.py \
  --completions-dataset JBB_dataset \
  --dataset-category "Category1" "Category2" \
  --dataset-behavior "Behavior1" \
  --dataset-source "Source1" \
  --output-dir out
```

For default dataset completions, simply run:
```bash
python main.py
```

### 2. Evaluate Existing Completions

Evaluate previously generated completions:

```bash
python main.py \
  --evaluate-file path/to/completions.json \
  --evaluation-prompt eval0_system_prompt \
  --evaluation-judge anthropic \
  --evaluation-model claude-3-5-sonnet-20241022 \
  --output-dir out
```

Quick evaluation of existing completions:
```bash
python main.py --evaluation-judge gemini --evaluate-file out/<timestamp>.json
```

### 3. Generate and Evaluate Completions

Generate and evaluate in one run:

```bash
python main.py \
  --completions-dataset JBB_dataset \
  --evaluation-prompt eval0_system_prompt \
  --evaluation-judge anthropic \
  --dataset-source "Source1" \
  --output-dir out
```

Quick generation and evaluation:
```bash
python main.py --evaluation-judge gemini
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--evaluation-prompt` | Evaluation prompt name | eval0_system_prompt |
| `--completions-dataset` | Dataset name from config | JBB_dataset |
| `--evaluation-judge` | Judge model provider (gemini/anthropic/openai) | None |
| `--evaluation-model` | Specific judge model | Provider's default |
| `--evaluate-file` | Existing completions file to evaluate | None |
| `--config-file` | Model configuration file | Default config |
| `--output-dir` | Output directory | out |
| `--dataset-category` | Categories to include (multiple) | None |
| `--dataset-behavior` | Behaviors to include (multiple) | None |
| `--dataset-source` | Sources to include (multiple) | None |

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

Results are saved with timestamps:
```
out/YYYYMMDD_HHMMSS_category1_category2.json
```

## Error Handling

- Validates arguments based on execution mode
- Failed operations are logged in output JSON
- Clear error messages for missing prerequisites
- Fallback to default dataset when none specified

## Historical Results

Previous evaluation results are available in [data/info/old_evals](./data/info/old_evals).