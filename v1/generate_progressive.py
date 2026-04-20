#!/usr/bin/env python
"""
渐进式游戏世界生成器

分步骤生成，每步保存日志，更可控可调试。

用法：python generate_progressive.py <story_name> [--skip-enrich]
"""

import sys
import logging
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv

from src.llm_client import ZhipuLLMClient
from src.modules.progressive_generator import ProgressiveGenerator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("generate_progressive")


def load_story(story_name: str) -> str:
    """加载故事提示词"""
    story_path = Path(f"stories/{story_name}/story.txt")
    if not story_path.exists():
        raise FileNotFoundError(f"Story not found: {story_path}")
    return story_path.read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="渐进式游戏世界生成器")
    parser.add_argument("story_name", help="故事名称")
    args = parser.parse_args()

    try:
        story = load_story(args.story_name)
        logger.info(f"Loaded: stories/{args.story_name}/story.txt")

        # 创建运行目录
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        run_dir = Path(f"stories/{args.story_name}/runs/{timestamp}")
        run_dir.mkdir(parents=True, exist_ok=True)

        # 初始化生成器
        llm = ZhipuLLMClient()
        generator = ProgressiveGenerator(llm, run_dir)

        # Step 1: 生成真相
        logger.info("=== Step 1: 生成真相 ===")
        truth = generator.generate_truth(story)
        logger.info(f"真相: {truth}")

        # Step 2: 生成场景
        logger.info("=== Step 2: 生成场景 ===")
        scenes = generator.generate_scenes(story, truth)
        logger.info(f"场景数量: {len(scenes)}")

        # Step 3: 生成关键线索
        logger.info("=== Step 3: 生成关键线索 ===")
        clues = generator.generate_key_clues(story, truth, scenes)
        logger.info(f"线索数量: {len(clues)}")

        # Step 4: 生成来源
        logger.info("=== Step 4: 生成来源 ===")
        sources = generator.generate_sources(story, scenes, clues)
        logger.info(f"来源数量: {len(sources)}")

        # Step 5: 生成行动
        logger.info("=== Step 5: 生成行动 ===")
        actions = generator.generate_actions(scenes, sources)
        logger.info(f"行动数量: {len(actions)}")

        # 整合生成 GameWorld
        logger.info("=== 整合游戏世界 ===")
        world = generator.build_game_world()

        # 保存结果
        world_file = run_dir / "game_world.json"
        world_file.write_text(world.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"GameWorld saved: {world_file}")

        # 保存生成摘要
        generator.save_summary()

        # 打印结果
        print(f"\n✅ Generated: {run_dir}")
        print(f"   Scenes: {len(world.scenes)}, Sources: {len(world.sources)}, Clues: {len(world.clues)}, Actions: {len(world.actions)}")
        print(f"   Logs: {generator.log_dir}")
        print(f"\n   Play: python play_main.py {world_file}")

    except Exception as e:
        logger.error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()