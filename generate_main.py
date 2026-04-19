#!/usr/bin/env python
"""
推理游戏世界生成器

输入：stories/<name>/story.txt
输出：stories/<name>/game_world.json

用法：python generate_main.py <story_name>
示例：python generate_main.py island
"""

import json
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

from src.llm_client import ZhipuLLMClient
from src.models import GameWorld, get_model_schema_desc
from src.modules.world_validator import WorldValidator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("generate_main")


def load_story_prompt(story_name: str) -> str:
    """加载故事提示词"""
    story_path = Path(f"stories/{story_name}/story.txt")
    if not story_path.exists():
        raise FileNotFoundError(f"Story file not found: {story_path}")

    with open(story_path, "r", encoding="utf-8") as f:
        return f.read()


def load_prompt_template() -> str:
    """加载提示词模板"""
    template_path = Path("prompts/game_world_generator.txt")
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_game_world(llm_client: ZhipuLLMClient, story_prompt: str) -> GameWorld:
    """使用 LLM 生成游戏世界"""
    template = load_prompt_template()
    schema_desc = get_model_schema_desc(GameWorld)

    full_prompt = template.format(story=story_prompt, schema=schema_desc)

    logger.info("Calling LLM to generate game world...")

    response_json = llm_client.call_with_json(
        prompt=full_prompt,
        system_prompt="你是一位专业的推理游戏设计师。你需要设计逻辑严密、体验流畅的推理游戏世界。请确保所有线索都能指向唯一的真相。"
    )

    try:
        game_world = GameWorld(**response_json)
        logger.info(f"Successfully generated game world with {len(game_world.clues)} clues and {len(game_world.scenes)} scenes")
        return game_world
    except Exception as e:
        logger.error(f"Failed to parse LLM response as GameWorld: {e}")
        raise


def validate_and_fix(game_world: GameWorld) -> GameWorld:
    """验证游戏世界，如有问题则尝试修复"""
    validator = WorldValidator()
    is_valid, errors = validator.validate(game_world)

    if is_valid:
        logger.info("Game world validation passed")
        return game_world

    logger.warning(f"Validation issues found: {errors}")

    # 尝试简单修复：确保每个真相维度都有 key_clue
    truth_dims = set(game_world.truth.keys())
    covered_dims = set()

    for clue in game_world.clues:
        if clue.deduction_link:
            covered_dims.add(clue.deduction_link.truth_dimension)

    missing_dims = truth_dims - covered_dims
    if missing_dims:
        logger.warning(f"Missing key_clues for dimensions: {missing_dims}")
        # 这里不自动修复，需要重新生成或手动调整

    return game_world


def save_game_world(game_world: GameWorld, story_name: str):
    """保存游戏世界到文件"""
    output_path = Path(f"stories/{story_name}/game_world.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(game_world.model_dump_json(indent=2))

    logger.info(f"Game world saved to {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_main.py <story_name>")
        print("Example: python generate_main.py island")
        sys.exit(1)

    story_name = sys.argv[1]

    try:
        # 加载故事提示词
        story_prompt = load_story_prompt(story_name)
        logger.info(f"Loaded story prompt from stories/{story_name}/story.txt")

        # 初始化 LLM 客户端
        llm_client = ZhipuLLMClient()

        # 生成游戏世界
        game_world = generate_game_world(llm_client, story_prompt)

        # 验证
        game_world = validate_and_fix(game_world)

        # 保存
        save_game_world(game_world, story_name)

        print(f"\n✅ Game world generated successfully!")
        print(f"   Output: stories/{story_name}/game_world.json")
        print(f"\n   Run with: python play_main.py stories/{story_name}/game_world.json")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()