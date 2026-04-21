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
from pathlib import Path
from typing import Dict, Any, List

from src.llm_client import ZhipuLLMClient, LLMResponse
from src.models import (
    GameWorld, Scene, Source, Clue, GameAction
)
from src.modules.world_validator import WorldValidator
from src.modules.generation_logger import GenerationLogger, TokenUsage

logger = logging.getLogger("progressive_generator")


class ProgressiveGenerator:
    """渐进式游戏世界生成器"""

    def __init__(self, llm: ZhipuLLMClient, run_id: str, story_name: str, run_dir: Path):
        self.llm = llm
        self.run_dir = run_dir
        self.story_name = story_name

        # 使用新的 GenerationLogger
        self.logger_manager = GenerationLogger(
            run_id=run_id,
            story_name=story_name,
            run_dir=run_dir,
            model=llm.model
        )

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

    def _call_llm(
        self,
        step_name: str,
        prompt: str,
        system_prompt: str,
        prompt_template: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用 LLM 并记录日志"""
        # 开始步骤
        self.logger_manager.start_step(step_name, input_data)

        # 调用 LLM
        response: LLMResponse = self.llm.call(prompt=prompt, system_prompt=system_prompt)
        raw_response = response.content

        # 清洗 JSON
        cleaned = raw_response.strip()
        for prefix in ["```json\n", "```JSON\n", "```json", "```"]:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # 解析 JSON
        try:
            parsed_data = json.loads(cleaned)
            parse_error = None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in step {step_name}: {e}")
            parse_error = str(e)
            parsed_data = {"parse_error": parse_error, "raw_content": cleaned}

        # 记录 LLM 调用详情
        tokens = TokenUsage(
            prompt=response.prompt_tokens,
            completion=response.completion_tokens,
            total=response.total_tokens
        )
        self.logger_manager.record_llm_call(
            prompt_template=prompt_template,
            prompt=prompt,
            system_prompt=system_prompt,
            raw_response=raw_response,
            cleaned_response=cleaned,
            model=response.model,
            duration_seconds=response.duration_seconds,
            tokens=tokens
        )

        # 记录解析数据
        self.logger_manager.record_parsed_data(parsed_data)

        # 如果解析失败，记录验证失败
        if parse_error:
            self.logger_manager.record_validation(passed=False, errors=[parse_error])
        else:
            # 先标记为通过，后续具体验证会更新
            self.logger_manager.record_validation(passed=True, errors=[])

        # 完成步骤
        self.logger_manager.complete_step()

        return parsed_data

    def generate_truth(self, story: str) -> Dict[str, str]:
        """Step 1: 生成真相"""
        prompt = self.templates["truth"].replace("{story}", story)
        data = self._call_llm(
            "truth",
            prompt,
            "你是推理游戏设计师。根据故事内容，确定唯一的真相。",
            "step1_truth.txt",
            {"story": story[:500] + "..." if len(story) > 500 else story}  # 简化输入记录
        )

        # 验证：必须有2-3个维度
        validation_errors = []
        if "parse_error" not in data and len(data) < 2:
            validation_errors.append("真相维度太少，至少需要2个")
            logger.warning(validation_errors[0])

        # 更新验证结果
        if validation_errors:
            self.logger_manager.steps[-1].validation.passed = False
            self.logger_manager.steps[-1].validation.errors = validation_errors
            self.logger_manager.steps[-1].success = False

        return data

    def generate_scenes(self, story: str, truth: Dict[str, str]) -> List[Dict]:
        """Step 2: 生成场景"""
        prompt = self.templates["scenes"].replace("{story}", story).replace("{truth}", json.dumps(truth, ensure_ascii=False))
        data = self._call_llm(
            "scenes",
            prompt,
            "你是推理游戏设计师。根据故事和真相，生成场景列表。",
            "step2_scenes.txt",
            {"truth": truth}  # 记录真相作为输入
        )

        scenes = data.get("scenes", [])
        validation_errors = []

        # 验证：至少2个场景
        if len(scenes) < 2:
            validation_errors.append("场景太少，至少需要2个")
            logger.warning(validation_errors[0])

        # 检查双向连接
        scene_map = {s["id"]: s for s in scenes}
        for scene in scenes:
            for conn_id in scene.get("connected_scenes", []):
                conn_scene = scene_map.get(conn_id)
                if conn_scene and scene["id"] not in conn_scene.get("connected_scenes", []):
                    error_msg = f"场景 {scene['name']} 连接到 {conn_scene['name']}，但后者没有返回连接"
                    validation_errors.append(error_msg)
                    logger.warning(error_msg)

        # 更新验证结果
        if validation_errors:
            self.logger_manager.steps[-1].validation.passed = False
            self.logger_manager.steps[-1].validation.errors = validation_errors
            self.logger_manager.steps[-1].success = False

        return scenes

    def generate_key_clues(self, story: str, truth: Dict[str, str], scenes: List[Dict]) -> List[Dict]:
        """Step 3: 为每个真相维度生成 key_clue"""
        prompt = self.templates["key_clues"].replace("{story}", story).replace("{truth}", json.dumps(truth, ensure_ascii=False)).replace("{scenes}", json.dumps(scenes, ensure_ascii=False))
        data = self._call_llm(
            "key_clues",
            prompt,
            "你是推理游戏设计师。为每个真相维度生成一条关键线索。",
            "step3_key_clues.txt",
            {"truth": truth, "scenes_count": len(scenes)}  # 简化输入记录
        )

        clues = data.get("key_clues", [])
        validation_errors = []

        # 验证：每个真相维度有对应 key_clue
        covered_dims = set()
        for clue in clues:
            if clue.get("deduction_link"):
                covered_dims.add(clue["deduction_link"]["truth_dimension"])

        missing = set(truth.keys()) - covered_dims
        if missing:
            error_msg = f"真相维度 {missing} 缺少对应的 key_clue"
            validation_errors.append(error_msg)
            logger.warning(error_msg)

        # 更新验证结果
        if validation_errors:
            self.logger_manager.steps[-1].validation.passed = False
            self.logger_manager.steps[-1].validation.errors = validation_errors
            self.logger_manager.steps[-1].success = False

        return clues

    def generate_sources(self, story: str, scenes: List[Dict], clues: List[Dict]) -> List[Dict]:
        """Step 4: 生成NPC/物品，并分配线索"""
        prompt = self.templates["sources"].replace("{story}", story).replace("{scenes}", json.dumps(scenes, ensure_ascii=False)).replace("{clues}", json.dumps(clues, ensure_ascii=False))
        data = self._call_llm(
            "sources",
            prompt,
            "你是推理游戏设计师。生成NPC和物品，分配线索到各来源。",
            "step4_sources.txt",
            {"scenes_count": len(scenes), "clues_count": len(clues)}  # 简化输入记录
        )

        sources = data.get("sources", [])
        validation_errors = []

        # 验证：每个线索都分配给某个来源
        assigned_clues = set()
        for source in sources:
            for clue_id in source.get("hidden_clues", []):
                assigned_clues.add(clue_id)

        clue_ids = set(c["id"] for c in clues)
        unassigned = clue_ids - assigned_clues
        if unassigned:
            error_msg = f"线索 {unassigned} 未分配给任何来源"
            validation_errors.append(error_msg)
            logger.warning(error_msg)

        # 更新验证结果
        if validation_errors:
            self.logger_manager.steps[-1].validation.passed = False
            self.logger_manager.steps[-1].validation.errors = validation_errors
            self.logger_manager.steps[-1].success = False

        return sources

    def generate_actions(self, scenes: List[Dict], sources: List[Dict]) -> List[Dict]:
        """Step 5: 生成行动（双向移动 + 交互）"""
        prompt = self.templates["actions"].replace("{scenes}", json.dumps(scenes, ensure_ascii=False)).replace("{sources}", json.dumps(sources, ensure_ascii=False))
        data = self._call_llm(
            "actions",
            prompt,
            "你是推理游戏设计师。生成所有行动：双向移动和交互。",
            "step5_actions.txt",
            {"scenes_count": len(scenes), "sources_count": len(sources)}  # 简化输入记录
        )

        actions = data.get("actions", [])

        # 此步骤暂时不做严格验证，主要靠提示词保证
        return actions

    def build_game_world(self) -> GameWorld:
        """整合所有步骤生成 GameWorld"""
        if len(self.logger_manager.steps) < 5:
            raise ValueError("生成步骤不完整")

        truth = self.logger_manager.get_step_result("truth")
        scenes_data = self.logger_manager.get_step_result("scenes").get("scenes", [])
        clues_data = self.logger_manager.get_step_result("key_clues").get("key_clues", [])
        sources_data = self.logger_manager.get_step_result("sources").get("sources", [])
        actions_data = self.logger_manager.get_step_result("actions").get("actions", [])

        # 添加填充线索（可选）
        key_clues_result = self.logger_manager.get_step_result("key_clues")
        filler_clues = key_clues_result.get("filler_clues", [])
        clues_data.extend(filler_clues)

        # 构建 Pydantic 模型
        scenes = [Scene(**s) for s in scenes_data]
        clues = [Clue(**c) for c in clues_data]
        sources = [Source(**s) for s in sources_data]
        actions = [GameAction(**a) for a in actions_data]

        world = GameWorld(
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

        return world, valid, errors

    def finalize_log(self, output_file: str, final_validation_passed: bool, final_validation_errors: List[str] = None) -> Path:
        """完成日志记录"""
        return self.logger_manager.finalize(
            final_validation_passed=final_validation_passed,
            final_validation_errors=final_validation_errors,
            output_file=output_file
        )