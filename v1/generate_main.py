#!/usr/bin/env python
"""
推理游戏世界生成器 v1

输入：stories/<name>/story.txt
输出：stories/<name>/runs/<timestamp>/enriched_story.json, game_world.json

用法：python generate_main.py <story_name> [--skip-enrich]
示例：python generate_main.py island
      python generate_main.py island --skip-enrich  # 跳过故事丰富化
"""

import json
import sys
import logging
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv

from src.llm_client import ZhipuLLMClient
from src.models import GameWorld, get_model_schema_desc
from src.modules.world_validator import WorldValidator
from src.modules.story_enricher import StoryEnricher

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
    return story_path.read_text(encoding="utf-8")


def load_prompt_template() -> str:
    """加载提示词模板"""
    template_path = Path("prompts/game_world_generator.txt")
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def enrich_story(llm: ZhipuLLMClient, story_prompt: str) -> str:
    """丰富故事内容，返回丰富后的提示词"""
    enricher = StoryEnricher(llm)
    enriched = enricher.enrich(story_prompt)
    return enricher.to_prompt_text(enriched)


def generate_game_world(llm: ZhipuLLMClient, story_prompt: str) -> GameWorld:
    """使用 LLM 生成游戏世界"""
    template = load_prompt_template()
    prompt = template.replace("{story}", story_prompt)

    logger.info("Generating game world...")
    response = llm.call(
        prompt=prompt,
        system_prompt="你是一位专业的推理游戏设计师。请根据故事内容生成具体的游戏世界数据。直接输出 JSON 数据对象，不要输出 Schema 定义或添加任何说明文字。"
    )
    content = response.content

    # 清洗可能的 Markdown 代码块
    cleaned = content.strip()
    # 移除开头的代码块标记
    for prefix in ["```json\n", "```JSON\n", "```json", "```JSON", "```\n", "```"]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    # 移除结尾的代码块标记
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        response = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.error(f"Content[:1000]: {content[:1000]}")
        # 尝试提取 JSON 部分
        import re
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            try:
                response = json.loads(match.group())
                logger.info("Successfully extracted JSON from response")
            except:
                raise ValueError(f"Failed to parse JSON: {e}")
        else:
            raise ValueError(f"Failed to parse JSON: {e}")

    return GameWorld(**response)


def save_results(story_name: str, enriched_prompt: str = None, game_world: GameWorld = None) -> Path:
    """保存结果到 runs 目录"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = Path(f"stories/{story_name}/runs/{timestamp}")
    run_dir.mkdir(parents=True, exist_ok=True)

    # 保存丰富后的故事
    if enriched_prompt:
        enriched_path = run_dir / "enriched_story.txt"
        enriched_path.write_text(enriched_prompt, encoding="utf-8")
        logger.info(f"Saved enriched story to {enriched_path}")

    # 保存游戏世界
    if game_world:
        world_path = run_dir / "game_world.json"
        world_path.write_text(game_world.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"Saved game world to {world_path}")

    return run_dir


def main():
    parser = argparse.ArgumentParser(description="推理游戏世界生成器")
    parser.add_argument("story_name", help="故事名称（对应 stories/<name>/story.txt）")
    parser.add_argument("--skip-enrich", action="store_true", help="跳过故事丰富化步骤")
    args = parser.parse_args()

    try:
        story_prompt = load_story_prompt(args.story_name)
        logger.info(f"Loaded: stories/{args.story_name}/story.txt")

        llm = ZhipuLLMClient()

        # 丰富故事（可选）
        enriched_prompt = None
        if not args.skip_enrich:
            enriched_prompt = enrich_story(llm, story_prompt)
            final_prompt = enriched_prompt
        else:
            final_prompt = story_prompt

        # 生成游戏世界
        world = generate_game_world(llm, final_prompt)

        # 验证
        validator = WorldValidator()
        valid, errors = validator.validate(world)
        if not valid:
            logger.warning(f"Validation issues: {errors}")

        # 保存结果
        run_dir = save_results(args.story_name, enriched_prompt, world)

        print(f"\n✅ Generated: {run_dir}")
        print(f"   Scenes: {len(world.scenes)}, Sources: {len(world.sources)}, Clues: {len(world.clues)}")
        print(f"\n   Play: python play_main.py {run_dir / 'game_world.json'}")

    except Exception as e:
        logger.error(f"Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()