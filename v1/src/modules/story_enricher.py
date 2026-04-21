"""故事丰富化模块"""
import json
import logging
import traceback
from pathlib import Path
from typing import Optional

from src.llm_client import ZhipuLLMClient
from src.models import EnrichedStory

logger = logging.getLogger("story_enricher")


class StoryEnricher:
    """将简短故事丰富化，增加细节和悬念"""

    def __init__(self, llm_client: ZhipuLLMClient):
        self.llm = llm_client
        self.template_path = Path("prompts/story_enricher.txt")

    def load_template(self) -> str:
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        return self.template_path.read_text(encoding="utf-8")

    def enrich(self, story_prompt: str) -> EnrichedStory:
        """丰富故事内容"""
        template = self.load_template()
        # 使用 replace 避免 JSON 中的 {} 被误解析
        prompt = template.replace("{story}", story_prompt)

        logger.info("Enriching story...")
        response = self.llm.call(
            prompt=prompt,
            system_prompt="你是一位专业的推理小说作家。擅长创作悬疑、紧凑、逻辑严密的推理故事。请严格按照 JSON 格式输出，不要添加任何额外的文字说明。"
        )
        content = response.content

        # 清洗 Markdown 代码块
        cleaned = content.strip()
        for prefix in ["```json\n", "```JSON\n", "```\n"]:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Raw content[:500]: {content[:500]}")
            logger.error(f"Cleaned content[:500]: {cleaned[:500]}")
            raise

        try:
            enriched = EnrichedStory(**data)
        except Exception as e:
            logger.error(f"EnrichedStory creation error: {e}")
            logger.error(f"Data keys: {list(data.keys())}")
            logger.error(traceback.format_exc())
            raise

        logger.info(f"Enriched story: {enriched.title}")
        logger.info(f"  Characters: {len(enriched.characters)}, Scenes: {len(enriched.scenes)}")

        return enriched

    def to_prompt_text(self, enriched: EnrichedStory) -> str:
        """将丰富后的故事转换为生成器可用的提示词"""
        lines = [
            f"# {enriched.title}",
            "",
            f"## 背景",
            enriched.background,
            "",
            f"## 氛围",
            enriched.atmosphere,
            "",
            f"## 事件",
            f"- 时间：{enriched.event.when}",
            f"- 地点：{enriched.event.where}",
            f"- 详情：{enriched.event.details}",
            "",
            f"## 人物",
        ]
        for char in enriched.characters:
            lines.append(f"- {char.name}（{char.role}）：{char.description}，与事件关系：{char.relationship}")

        lines.append("")
        lines.append("## 场景")
        for scene in enriched.scenes:
            lines.append(f"- {scene.name}：{scene.description}")

        lines.append("")
        lines.append("## 真相（用于生成游戏）")
        lines.append(f"- 凶手：{enriched.truth.culprit}")
        lines.append(f"- 手法：{enriched.truth.method}")
        lines.append(f"- 动机：{enriched.truth.motive}")

        if enriched.red_herrings:
            lines.append("")
            lines.append("## 误导线索")
            for h in enriched.red_herrings:
                lines.append(f"- {h}")

        return "\n".join(lines)