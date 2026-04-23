# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Generate game world (single-shot)
python v1/generate.py <story_name> [--skip-enrich]

# Generate game world (progressive, step-by-step with logs)
python v1/generate_progressive.py <story_name>

# Play generated game
python v1/play.py v1/stories/<story_name>/runs/<timestamp>/game_world.json

# Run all tests
python -m pytest v1/tests/ -v

# Run single test file
python -m pytest v1/tests/test_models.py -v
```

Requires `ZHIPUAI_API_KEY` in `v1/.env` file.

## Architecture

### Generation Pipeline

Two generation modes in `v1/`:
1. **Single-shot** (`generate.py`): Uses `prompts/game_world_generator.txt` to generate complete World in one LLM call
2. **Progressive** (`generate_progressive.py`): 5-step pipeline with separate prompts (step1-5), each step logged to `runs/<timestamp>/logs/`

Steps: truth → scenes → key_clues → sources → actions

### Core Models (`v1/src/models.py`)

- **World**: Contains truth, scenes, sources, clues, actions; has query methods `get_scene_by_id()`, `get_source_by_id()`, `get_clue_by_id()`, `get_action_by_id()`
- **Clue**: `clue_type` is `key_clue`, `pre_clue`, or `filler_clue`; only `key_clue` has `deduction_link`
- **Action**: `action_type` is `move` (target_scene_id) or `interact` (target_source_id)

Backward compatibility aliases: `GameWorld = World`, `GameAction = Action`

### ID Format

Use `prefix_number` format: `scene_1`, `npc_1`, `item_1`, `clue_1`, `action_1`

### Game Engine (`v1/src/game/`)

- **GameEngine**: Orchestrates ClueManager and DeductionEngine
- **DeductionEngine**: `process_clue()` locks truth dimension when key_clue collected; `check_victory()` when all dimensions locked
- **ClueManager**: Handles unlock conditions (required_clues chain)

### LLM Integration (`v1/src/llm_client.py`)

Uses ZhipuAI via `zai` SDK. `clean_json_response()` utility removes Markdown code blocks from LLM output.

### Prompts

Templates use `{placeholder}` syntax (not f-string `{}`). `get_model_schema_desc()` generates JSON schema for LLM prompt injection.

## Key Concepts

- **Reverse Generation**: Start from truth, generate key_clues that lock each dimension, then build evidence chain backward
- **DeductionLink**: `truth_dimension` + `target_value` must match World.truth exactly
- **Victory Condition**: `PlayerState.is_all_locked()` - all truth dimensions have locked values

## Creating New Stories

1. Create `v1/stories/<name>/story.txt` with your story prompt
2. Run `python v1/generate.py <name>` or `python v1/generate_progressive.py <name>`
3. Run generated JSON with `python v1/play.py <path_to_json>`