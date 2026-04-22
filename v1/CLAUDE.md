# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Generate game world (single-shot)
python generate.py <story_name> [--skip-enrich]

# Generate game world (progressive, step-by-step with logs)
python generate_progressive.py <story_name>

# Play generated game
python play.py stories/<story_name>/runs/gen_<timestamp>/game_world.json

# Run all tests
python -m pytest tests/ -v

# Run single test file
python -m pytest tests/test_models.py -v
```

Requires `ZHIPUAI_API_KEY` in `.env` file.

## Architecture

### Generation Pipeline

Two generation modes:
1. **Single-shot** (`generate.py`): Uses `prompts/game_world_generator.txt` to generate complete World in one LLM call
2. **Progressive** (`generate_progressive.py`): 5-step pipeline with separate prompts (step1-5), each step logged to `runs/gen_<timestamp>/logs/`

Steps: truth → scenes → key_clues → sources → actions

### Directory Structure

```
stories/<name>/runs/
├── gen_<timestamp>/     # 生成记录
│   ├── logs/            # LLM调用日志（仅progressive模式）
│   ├── game_world.json  # 生成的游戏世界
│   └── enriched_story.txt  # 丰富后的故事（仅generate.py）
├── play_<timestamp>/    # 游玩记录
│   ├── game_world.json  # 游戏副本
│   └── result.json      # 游玩结果
```

### Core Models (`src/models.py`)

- **World**: Contains truth, scenes, sources, clues, actions; has query methods `get_scene_by_id()`, `get_source_by_id()`, `get_clue_by_id()`, `get_action_by_id()`
- **Clue**: `clue_type` is `key_clue`, `pre_clue`, or `filler_clue`; only `key_clue` has `deduction_link`
- **Action**: `action_type` is `move` (target_scene_id) or `interact` (target_source_id)

Backward compatibility aliases: `GameWorld = World`, `GameAction = Action`

### ID Format

Use `prefix_number` format: `scene_1`, `npc_1`, `item_1`, `clue_1`, `action_1`

### Game Engine (`src/game/`)

- **GameEngine**: Orchestrates ClueManager and DeductionEngine
- **DeductionEngine**: `process_clue()` locks truth dimension when key_clue collected; `check_victory()` when all dimensions locked
- **ClueManager**: Handles unlock conditions (required_clues chain)

### LLM Integration (`src/llm_client.py`)

Uses ZhipuAI via `zai` SDK. `clean_json_response()` utility removes Markdown code blocks from LLM output.

### Prompts

Templates use `{placeholder}` syntax (not f-string `{}`). `get_model_schema_desc()` generates JSON schema for LLM prompt injection.

## Key Concepts

- **Reverse Generation**: Start from truth, generate key_clues that lock each dimension, then build evidence chain backward
- **DeductionLink**: `truth_dimension` + `target_value` must match World.truth exactly
- **Victory Condition**: `PlayerState.is_all_locked()` - all truth dimensions have locked values