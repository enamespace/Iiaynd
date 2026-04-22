#!/usr/bin/env python
"""
推理游戏世界生成器 v1

输入：stories/<name>/story.txt
输出：stories/<name>/runs/<timestamp>/enriched_story.json, game_world.json

用法：python generate.py <story_name> [--skip-enrich]
示例：python generate.py island
      python generate.py island --skip-enrich  # 跳过故事丰富化
"""

import sys
import logging
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv

from src.llm_client import ZhipuLLMClient, clean_json_response, llm_call_with_retry
from src.models import GameWorld, get_model_schema_desc, World
from src.generators.validator import WorldValidator
from src.generators.enricher import StoryEnricher

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


def generate_game_world(
    llm: ZhipuLLMClient,
    story_prompt: str,
    previous_errors: list = None,
    mode: str = "conversation"
) -> World:
    """使用 LLM 生成游戏世界

    Args:
        llm: LLM客户端
        story_prompt: 故事提示词
        previous_errors: 前次验证失败的错误列表，用于反馈给LLM修正
        mode: 重试模式 - "conversation"（优先）或 "single"（备选）
    """
    template = load_prompt_template()
    prompt = template.replace("{story}", story_prompt)

    # 如果有前次错误，附加到提示词
    if previous_errors:
        error_feedback = "\n\n【上次生成的问题，请修正】\n" + "\n".join(f"- {e}" for e in previous_errors)
        prompt += error_feedback
        system_prompt = (
            "你是一位专业的推理游戏设计师。上次生成存在以下问题，请仔细分析并修正。"
            "确保所有key_clue都分配到某个source的hidden_clues中，并确保有线索的source都有对应的interact行动。"
            "请输出修正后的完整JSON数据对象，不要输出Schema定义或添加任何说明文字。"
        )
        logger.info(f"Retrying with {len(previous_errors)} error feedbacks")
        # Validator 错误修正使用单次模式
        mode = "single"
    else:
        system_prompt = (
            "你是一位专业的推理游戏设计师。请根据故事内容生成具体的游戏世界数据。"
            "直接输出 JSON 数据对象，不要输出 Schema 定义或添加任何说明文字。"
        )

    # 使用 retry utility 处理 JSON 解析和 Pydantic 验证
    world = llm_call_with_retry(
        llm=llm,
        prompt=prompt,
        system_prompt=system_prompt,
        model_class=World,
        max_retries=2,
        error_context="游戏世界生成",
        mode=mode
    )

    return world


def generate_game_world_with_retry(
    llm: ZhipuLLMClient,
    story_prompt: str,
    validator: WorldValidator,
    max_retries: int = 3
) -> World:
    """生成游戏世界，验证失败时自动重试并反馈错误信息

    采用双模式 Retry:
    - 初次生成：使用多轮对话模式 (conversation)，LLM 能理解修正上下文
    - Validator 错误：使用单次调用模式 (single)，传递上次完整 JSON 输出

    Args:
        llm: LLM客户端
        story_prompt: 故事提示词
        validator: 世界验证器
        max_retries: 最大重试次数（包括 validator 验证）

    Returns:
        验证通过的游戏世界

    Raises:
        ValueError: 达到最大重试次数仍未通过验证
    """
    errors_feedback = []

    for attempt in range(1, max_retries + 1):
        logger.info(f"Generation attempt {attempt}/{max_retries}")

        # 初次生成用 conversation 模式，后续 validator 错误用 single 模式
        mode = "conversation" if not errors_feedback else "single"
        world = generate_game_world(llm, story_prompt, previous_errors=errors_feedback, mode=mode)
        valid, errors = validator.validate(world)

        if valid:
            logger.info(f"Validation passed on attempt {attempt}")
            return world

        errors_feedback = errors
        logger.warning(f"Attempt {attempt} failed with {len(errors)} errors:")
        for err in errors:
            logger.warning(f"  - {err}")

    raise ValueError(f"生成失败，达到最大重试次数 {max_retries}。最终错误:\n" + "\n".join(f"- {e}" for e in errors_feedback))


def create_run_dir(story_name: str) -> Path:
    """创建运行目录（生成记录）"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = Path(f"stories/{story_name}/runs/gen_{timestamp}")
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_results(run_dir: Path, enriched_prompt: str = None, game_world: World = None) -> None:
    """保存结果到 runs 目录"""
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


def main():
    parser = argparse.ArgumentParser(description="推理游戏世界生成器")
    parser.add_argument("story_name", help="故事名称（对应 stories/<name>/story.txt）")
    parser.add_argument("--skip-enrich", action="store_true", help="跳过故事丰富化步骤")
    args = parser.parse_args()

    try:
        story_prompt = load_story_prompt(args.story_name)
        logger.info(f"Loaded: stories/{args.story_name}/story.txt")

        # 创建运行目录并设置 LLM 日志目录
        run_dir = create_run_dir(args.story_name)
        llm = ZhipuLLMClient()
        llm.set_log_dir(run_dir / "logs")
        logger.info(f"Run directory: {run_dir}")

        # 丰富故事（可选）
        enriched_prompt = None
        if not args.skip_enrich:
            enriched_prompt = enrich_story(llm, story_prompt)
            final_prompt = enriched_prompt
        else:
            final_prompt = story_prompt

        # 生成游戏世界（带重试）
        validator = WorldValidator()
        world = generate_game_world_with_retry(llm, final_prompt, validator)

        # 保存结果
        save_results(run_dir, enriched_prompt, world)

        print(f"\n✅ Generated: {run_dir}")
        print(f"   Scenes: {len(world.scenes)}, Sources: {len(world.sources)}, Clues: {len(world.clues)}")
        print(f"\n   Play: python play.py {run_dir / 'game_world.json'}")

    except Exception as e:
        logger.error(f"Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()