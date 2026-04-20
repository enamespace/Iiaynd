# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Reasoning Game Generator** - an AI-powered pipeline that transforms story prompts into structured deduction games. The system uses ZhipuAI's LLM (via `zai` SDK) to generate game designs, simulate player reasoning, and evaluate design quality.

## Commands

```bash
# Run the full pipeline for a story
python main.py

# Requires ZHIPUAI_API_KEY in .env file
cp .env.example .env  # Then add your API key
```

## Architecture

The system follows a **5-stage pipeline** orchestrated by `PipelineRunner`:

1. **StoryBuilder** (`src/modules/story_builder.py`) - Enriches raw story prompts
2. **Generator** (`src/modules/generator.py`) - Creates candidate game designs with truth/evidence/actions
3. **Validator** (`src/modules/validator.py`) - Filters designs for logical validity
4. **Simulator** (`src/modules/simulator.py`) - Simulates logical player reasoning (5 steps)
5. **Evaluator** (`src/modules/evaluator.py`) - Scores design quality

### Key Files

- `main.py` - Entry point; wires all components together
- `src/runner.py` - `PipelineRunner` class orchestrates the workflow
- `src/llm_client.py` - `ZhipuLLMClient` wraps ZhipuAI API with JSON response handling
- `src/models.py` - Pydantic models: `GameDesign`, `EnrichedStory`, `SimulationLog`, `EvaluationReport`
- `src/interfaces.py` - Abstract base classes for each pipeline stage
- `src/modules/` - Concrete implementations of interfaces

### Data Flow

```
stories/<name>/story.txt → StoryBuilder → Generator → Validator → Simulator → Evaluator
                                                    ↓
                              stories/<name>/runs/<run_id>/{enriched_story.json, design.json, simulations.json, evaluation.json, trace.log}
```

## Data Models

**GameDesign** is the core output containing:
- `truth`: Dict[str, str] - The unique correct answer (e.g., {'murderer': 'Butler'})
- `evidence`: List[EvidenceItem] - Each evidence must have ≥2 possible explanations
- `actions`: List[ActionItem] - Player actions with costs
- `outcomes`: Dict[str, List[OutcomeEffect]] - Action→result mapping with probabilities
- `initial_state`: Dict - Starting game state

## Prompt Templates

Prompts are stored in `prompts/*.txt` and use `{schema}` placeholder for dynamic Pydantic schema injection via `get_model_schema_desc()`. This ensures LLM outputs conform to expected JSON structures.

## Validation Rules

`BaseValidator` enforces:
1. Each evidence must have at least 2 possible explanations (ambiguity requirement)
2. All outcomes must reference existing action IDs
3. Actions cannot have identical outcome distributions (decision value)

## Running for Different Stories

To run with a new story:
1. Create `stories/<name>/story.txt` with your story prompt
2. Update `story_name` in `main.py` or pass it programmatically to `runner.run("<name>")`