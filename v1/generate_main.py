#!/usr/bin/env python
"""
推理游戏世界生成器 v1

输入：stories/<name>/story.txt
输出：stories/<name>/runs/<timestamp>/game_world.json

用法：python generate_main.py <story_name>
示例：python generate_main.py island
"""

import json
import sys
import logging
import time
from pathlib import Path
from dotenv import load_dotenv

from src.llm_client import ZhipuLLMClient
from src.models import GameWorld, get_model_schema_desc
from src.modules.world_validator import WorldValidator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("generate")


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
        raise FileNotFoundError(f"Template not found: {template_path}")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_game_world(llm_client: ZhipuLLMClient, story_prompt: str) -> GameWorld:
    """使用 LLM 生成游戏世界"""
    template = load_prompt_template()
    schema = get_model_schema_desc(GameWorld)
    prompt = template.format(story=story_prompt, schema=schema)

    logger.info("Calling LLM...")
    response = llm_client.call_with_json(
        prompt=prompt,
        system_prompt="你是一位专业的推理游戏设计师。设计逻辑严密的推理游戏世界。"
    )
    return GameWorld(**response)


def save_game_world(game_world: GameWorld, story_name: str) -> Path:
    """保存到 runs 目录（时间戳区分）"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = Path(f"stories/{story_name}/runs/{timestamp}")
    run_dir.mkdir(parents=True, exist_ok=True)

    output_path = run_dir / "game_world.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(game_world.model_dump_json(indent=2))

    logger.info(f"Saved to {output_path}")
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_main.py <story_name>")
        print("Example: python generate_main.py island")
        sys.exit(1)

    story_name = sys.argv[1]

    try:
        story_prompt = load_story_prompt(story_name)
        logger.info(f"Loaded: stories/{story_name}/story.txt")

        llm = ZhipuLLMClient()
        world = generate_game_world(llm, story_prompt)

        # Validate
        validator = WorldValidator()
        valid, errors = validator.validate(world)
        if not valid:
            logger.warning(f"Validation issues: {errors}")

        output_path = save_game_world(world, story_name)

        print(f"\n✅ Generated: {output_path}")
        print(f"   Scenes: {len(world.scenes)}, Sources: {len(world.sources)}, Clues: {len(world.clues)}")
        print(f"\n   Play: python play_main.py {output_path}")

    except Exception as e:
        logger.error(f"Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()