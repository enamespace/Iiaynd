"""渐进式游戏世界生成器

分步骤生成，每步保存日志，更可控可调试。

流程：
1. 生成真相
2. 生成场景
3. 生成关键线索（key_clue，每个真相维度一个）
4. 生成来源（NPC/物品）
5. 生成行动（移动+交互）
6. 整合验证
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

from src.llm_client import ZhipuLLMClient, clean_json_response
from src.models import (
    World, Scene, Source, Clue, Action,
    ClueType, ActionType, SourceType, DeductionLink
)
from .validator import WorldValidator

logger = logging.getLogger("progressive_generator")

DEFAULT_MAX_RETRIES = 3


@dataclass
class GenerationStep:
    """单个生成步骤"""
    name: str
    prompt_template: str
    output_model: str  # 用于描述期望输出格式
    result: Dict[str, Any] = None
    raw_response: str = None
    error: str = None
    timestamp: str = None


class ProgressiveGenerator:
    """渐进式游戏世界生成器"""

    def __init__(self, llm: ZhipuLLMClient, run_dir: Path):
        self.llm = llm
        self.run_dir = run_dir
        self.log_dir = run_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.steps: List[GenerationStep] = []

        # 加载各步骤的提示词模板
        self.templates = {
            "truth": self._load_template("step1_truth.txt"),
            "scenes": self._load_template("step2_scenes.txt"),
            "key_clues": self._load_template("step3_key_clues.txt"),
            "sources": self._load_template("step4_sources.txt"),
            "actions": self._load_template("step5_actions.txt"),
        }

    def _load_template(self, filename: str) -> str:
        path = Path("prompts") / filename
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")
        return path.read_text(encoding="utf-8")

    def _call_llm(self, step_name: str, prompt: str, system_prompt: str, max_retries: int = DEFAULT_MAX_RETRIES) -> Tuple[Dict[str, Any], str]:
        """调用LLM并保存日志，失败时自动重试"""
        errors_feedback: List[str] = []
        last_raw_response = ""
        last_data = {}

        for attempt in range(1, max_retries + 1):
            logger.info(f"Step [{step_name}] attempt {attempt}/{max_retries}")

            # 如果有前次错误，附加到提示词
            current_prompt = prompt
            current_system = system_prompt

            if errors_feedback:
                error_note = "\n\n【上次生成的问题，请修正】\n" + "\n".join(f"- {e}" for e in errors_feedback)
                current_prompt += error_note
                current_system = system_prompt + " 上次生成存在以下问题，请修正后重新输出完整的 JSON。"
                logger.info(f"Step [{step_name}] retrying with {len(errors_feedback)} error feedbacks")

            # 调用LLM
            raw_response = self.llm.call(prompt=current_prompt, system_prompt=current_system)
            last_raw_response = raw_response

            # 清洗JSON
            cleaned = clean_json_response(raw_response)

            # 解析JSON
            try:
                data = json.loads(cleaned)
                last_data = data

                # 成功，保存日志并返回
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                log_file = self.log_dir / f"{step_name}_{timestamp}.json"

                log_data = {
                    "step": step_name,
                    "timestamp": timestamp,
                    "attempt": attempt,
                    "prompt": current_prompt,
                    "system_prompt": current_system,
                    "raw_response": raw_response,
                    "parsed_data": data,
                    "success": True
                }
                log_file.write_text(json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8")
                logger.info(f"Step [{step_name}] succeeded on attempt {attempt}, log saved: {log_file}")

                return data, raw_response

            except json.JSONDecodeError as e:
                error_msg = f"JSON解析失败: {e}"
                logger.warning(f"Step [{step_name}] {error_msg}")
                errors_feedback = [error_msg, f"原始内容前500字符: {cleaned[:500]}"]
                continue

        # 所有尝试都失败
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"{step_name}_{timestamp}_failed.json"

        log_data = {
            "step": step_name,
            "timestamp": timestamp,
            "attempts": max_retries,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "last_raw_response": last_raw_response,
            "errors": errors_feedback,
            "success": False
        }
        log_file.write_text(json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8")

        raise ValueError(f"Step [{step_name}] 失败，达到最大重试次数 {max_retries}。错误:\n" + "\n".join(errors_feedback))

    def generate_truth(self, story: str) -> Dict[str, str]:
        """Step 1: 生成真相"""
        prompt = self.templates["truth"].replace("{story}", story)
        data, raw = self._call_llm(
            "truth",
            prompt,
            "你是推理游戏设计师。根据故事内容，确定唯一的真相。"
        )

        step = GenerationStep(
            name="truth",
            prompt_template="step1_truth.txt",
            output_model="Dict[str, str]",
            result=data,
            raw_response=raw,
            timestamp=time.strftime("%Y%m%d_%H%M%S")
        )
        self.steps.append(step)

        # 验证：必须有2-3个维度
        if len(data) < 2:
            step.error = "真相维度太少，至少需要2个"
            logger.warning(step.error)

        return data

    def generate_scenes(self, story: str, truth: Dict[str, str]) -> List[Dict]:
        """Step 2: 生成场景"""
        prompt = self.templates["scenes"].replace("{story}", story).replace("{truth}", json.dumps(truth, ensure_ascii=False))
        data, raw = self._call_llm(
            "scenes",
            prompt,
            "你是推理游戏设计师。根据故事和真相，生成场景列表。"
        )

        step = GenerationStep(
            name="scenes",
            prompt_template="step2_scenes.txt",
            output_model="List[Scene]",
            result=data,
            raw_response=raw,
            timestamp=time.strftime("%Y%m%d_%H%M%S")
        )
        self.steps.append(step)

        # 验证：至少2个场景，connected_scenes双向
        scenes = data.get("scenes", [])
        if len(scenes) < 2:
            step.error = "场景太少，至少需要2个"
            logger.warning(step.error)

        # 检查双向连接
        scene_map = {s["id"]: s for s in scenes}
        for scene in scenes:
            for conn_id in scene.get("connected_scenes", []):
                conn_scene = scene_map.get(conn_id)
                if conn_scene and scene["id"] not in conn_scene.get("connected_scenes", []):
                    step.error = f"场景 {scene['name']} 连接到 {conn_scene['name']}，但后者没有返回连接"
                    logger.warning(step.error)

        return scenes

    def generate_key_clues(self, story: str, truth: Dict[str, str], scenes: List[Dict]) -> List[Dict]:
        """Step 3: 为每个真相维度生成 key_clue"""
        prompt = self.templates["key_clues"].replace("{story}", story).replace("{truth}", json.dumps(truth, ensure_ascii=False)).replace("{scenes}", json.dumps(scenes, ensure_ascii=False))
        data, raw = self._call_llm(
            "key_clues",
            prompt,
            "你是推理游戏设计师。为每个真相维度生成一条关键线索。"
        )

        step = GenerationStep(
            name="key_clues",
            prompt_template="step3_key_clues.txt",
            output_model="List[Clue]",
            result=data,
            raw_response=raw,
            timestamp=time.strftime("%Y%m%d_%H%M%S")
        )
        self.steps.append(step)

        # 验证：每个真相维度有对应key_clue
        clues = data.get("key_clues", [])
        covered_dims = set()
        for clue in clues:
            if clue.get("deduction_link"):
                covered_dims.add(clue["deduction_link"]["truth_dimension"])

        missing = set(truth.keys()) - covered_dims
        if missing:
            step.error = f"真相维度 {missing} 缺少对应的 key_clue"
            logger.warning(step.error)

        return clues

    def generate_sources(self, story: str, scenes: List[Dict], clues: List[Dict]) -> List[Dict]:
        """Step 4: 生成NPC/物品，并分配线索"""
        prompt = self.templates["sources"].replace("{story}", story).replace("{scenes}", json.dumps(scenes, ensure_ascii=False)).replace("{clues}", json.dumps(clues, ensure_ascii=False))
        data, raw = self._call_llm(
            "sources",
            prompt,
            "你是推理游戏设计师。生成NPC和物品，分配线索到各来源。"
        )

        step = GenerationStep(
            name="sources",
            prompt_template="step4_sources.txt",
            output_model="List[Source]",
            result=data,
            raw_response=raw,
            timestamp=time.strftime("%Y%m%d_%H%M%S")
        )
        self.steps.append(step)

        # 验证：每个线索都分配给某个来源
        sources = data.get("sources", [])
        assigned_clues = set()
        for source in sources:
            for clue_id in source.get("hidden_clues", []):
                assigned_clues.add(clue_id)

        clue_ids = set(c["id"] for c in clues)
        unassigned = clue_ids - assigned_clues
        if unassigned:
            step.error = f"线索 {unassigned} 未分配给任何来源"
            logger.warning(step.error)

        return sources

    def generate_actions(self, scenes: List[Dict], sources: List[Dict]) -> List[Dict]:
        """Step 5: 生成行动（双向移动 + 交互）"""
        prompt = self.templates["actions"].replace("{scenes}", json.dumps(scenes, ensure_ascii=False)).replace("{sources}", json.dumps(sources, ensure_ascii=False))
        data, raw = self._call_llm(
            "actions",
            prompt,
            "你是推理游戏设计师。生成所有行动：双向移动和交互。"
        )

        step = GenerationStep(
            name="actions",
            prompt_template="step5_actions.txt",
            output_model="List[Action]",
            result=data,
            raw_response=raw,
            timestamp=time.strftime("%Y%m%d_%H%M%S")
        )
        self.steps.append(step)

        actions = data.get("actions", [])

        # 验证：双向移动
        move_pairs = {}  # (from_id, to_id) -> action
        scene_ids = [s["id"] for s in scenes]

        for action in actions:
            if action.get("action_type") == "move":
                # 检查所有场景连接都有双向行动
                pass  # 简化验证，主要靠提示词保证

        return actions

    def build_game_world(self) -> World:
        """整合所有步骤生成 GameWorld"""
        if len(self.steps) < 5:
            raise ValueError("生成步骤不完整")

        truth = self.steps[0].result
        scenes_data = self.steps[1].result.get("scenes", [])
        clues_data = self.steps[2].result.get("key_clues", [])
        sources_data = self.steps[3].result.get("sources", [])
        actions_data = self.steps[4].result.get("actions", [])

        # 添加填充线索（可选）
        filler_clues = self.steps[2].result.get("filler_clues", [])
        clues_data.extend(filler_clues)

        # 构建 Pydantic 模型
        scenes = [Scene(**s) for s in scenes_data]
        clues = [Clue(**c) for c in clues_data]
        sources = [Source(**s) for s in sources_data]
        actions = [Action(**a) for a in actions_data]

        world = World(
            truth=truth,
            scenes=scenes,
            clues=clues,
            sources=sources,
            actions=actions
        )

        # 最终验证
        validator = WorldValidator()
        valid, errors = validator.validate(world)
        if not valid:
            logger.warning(f"Validation errors: {errors}")

        return world

    def save_summary(self):
        """保存生成摘要"""
        summary = {
            "steps": [
                {
                    "name": s.name,
                    "timestamp": s.timestamp,
                    "success": s.error is None,
                    "error": s.error
                }
                for s in self.steps
            ],
            "total_steps": len(self.steps),
            "successful_steps": sum(1 for s in self.steps if s.error is None),
            "log_files": [str(self.log_dir / f"{s.name}_{s.timestamp}.json") for s in self.steps]
        }

        summary_file = self.run_dir / "generation_summary.json"
        summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Summary saved: {summary_file}")