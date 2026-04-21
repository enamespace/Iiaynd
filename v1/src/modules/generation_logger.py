"""生成日志记录器

统一管理生成过程的日志记录，包括：
- 单一日志文件 generation_log.json
- 统一的时间戳（ISO 8601 格式）
- 耗时统计（每步 + 总计）
- Token 使用统计
- 验证结果记录
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("generation_logger")


@dataclass
class TokenUsage:
    """Token 使用统计"""
    prompt: int = 0
    completion: int = 0
    total: int = 0

    def add(self, other: 'TokenUsage') -> None:
        """累加另一个 TokenUsage"""
        self.prompt += other.prompt
        self.completion += other.completion
        self.total += other.total

    def to_dict(self) -> Dict[str, int]:
        return {
            "prompt": self.prompt,
            "completion": self.completion,
            "total": self.total
        }


@dataclass
class LLMResponseLog:
    """LLM 响应日志"""
    raw: str  # 原始响应
    cleaned: str  # 清洗后的 JSON 文本
    model: str  # 模型名称
    duration_seconds: float  # 耗时
    tokens: TokenUsage  # token 使用

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw": self.raw,
            "cleaned": self.cleaned,
            "model": self.model,
            "duration_seconds": self.duration_seconds,
            "tokens": self.tokens.to_dict()
        }


@dataclass
class StepValidation:
    """步骤验证结果"""
    passed: bool
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": self.errors
        }


@dataclass
class GenerationStepLog:
    """单个生成步骤的日志"""
    name: str
    sequence: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    input: Dict[str, Any] = field(default_factory=dict)
    prompt_template: str = ""
    prompt: str = ""
    system_prompt: str = ""
    llm_response: Optional[LLMResponseLog] = None
    parsed_data: Dict[str, Any] = field(default_factory=dict)
    validation: Optional[StepValidation] = None
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "sequence": self.sequence,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": round(self.duration_seconds, 3),
            "input": self.input,
            "prompt_template": self.prompt_template,
            "prompt": self.prompt,
            "system_prompt": self.system_prompt,
            "parsed_data": self.parsed_data,
            "success": self.success
        }
        if self.llm_response:
            result["llm_response"] = self.llm_response.to_dict()
        if self.validation:
            result["validation"] = self.validation.to_dict()
        return result


class GenerationLogger:
    """生成日志记录器"""

    def __init__(self, run_id: str, story_name: str, run_dir: Path, model: str):
        self.run_id = run_id
        self.story_name = story_name
        self.run_dir = run_dir
        self.model = model

        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.steps: List[GenerationStepLog] = []
        self.total_tokens = TokenUsage()
        self.current_step: Optional[GenerationStepLog] = None

        # 确保目录存在
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def start_step(self, name: str, input_data: Dict[str, Any]) -> GenerationStepLog:
        """开始一个新步骤"""
        step = GenerationStepLog(
            name=name,
            sequence=len(self.steps) + 1,
            started_at=datetime.now(),
            input=input_data
        )
        self.current_step = step
        self.steps.append(step)
        logger.info(f"Step [{name}] started")
        return step

    def record_llm_call(
        self,
        prompt_template: str,
        prompt: str,
        system_prompt: str,
        raw_response: str,
        cleaned_response: str,
        model: str,
        duration_seconds: float,
        tokens: TokenUsage
    ) -> None:
        """记录 LLM 调用详情"""
        if not self.current_step:
            logger.warning("No current step to record LLM call")
            return

        self.current_step.prompt_template = prompt_template
        self.current_step.prompt = prompt
        self.current_step.system_prompt = system_prompt
        self.current_step.llm_response = LLMResponseLog(
            raw=raw_response,
            cleaned=cleaned_response,
            model=model,
            duration_seconds=duration_seconds,
            tokens=tokens
        )

        # 累加 token
        self.total_tokens.add(tokens)

    def record_parsed_data(self, parsed_data: Dict[str, Any]) -> None:
        """记录解析后的数据"""
        if not self.current_step:
            logger.warning("No current step to record parsed data")
            return
        self.current_step.parsed_data = parsed_data

    def record_validation(self, passed: bool, errors: List[str] = None) -> None:
        """记录验证结果"""
        if not self.current_step:
            logger.warning("No current step to record validation")
            return
        self.current_step.validation = StepValidation(
            passed=passed,
            errors=errors or []
        )
        self.current_step.success = passed

    def complete_step(self) -> None:
        """完成当前步骤"""
        if not self.current_step:
            logger.warning("No current step to complete")
            return

        self.current_step.completed_at = datetime.now()
        if self.current_step.started_at:
            duration = (self.current_step.completed_at - self.current_step.started_at).total_seconds()
            self.current_step.duration_seconds = duration

        logger.info(f"Step [{self.current_step.name}] completed in {self.current_step.duration_seconds:.2f}s")
        self.current_step = None

    def finalize(self, final_validation_passed: bool, final_validation_errors: List[str] = None, output_file: str = None) -> Path:
        """完成日志记录，保存到文件"""
        self.completed_at = datetime.now()
        total_duration = (self.completed_at - self.started_at).total_seconds()

        log_data = {
            "run_id": self.run_id,
            "story_name": self.story_name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "total_duration_seconds": round(total_duration, 3),
            "total_tokens": self.total_tokens.to_dict(),
            "model": self.model,
            "steps": [step.to_dict() for step in self.steps],
            "final_validation": {
                "passed": final_validation_passed,
                "errors": final_validation_errors or []
            },
            "output_file": output_file
        }

        log_file = self.run_dir / "generation_log.json"
        log_file.write_text(json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Generation log saved: {log_file}")

        return log_file

    def get_step_result(self, step_name: str) -> Optional[Dict[str, Any]]:
        """获取指定步骤的解析结果"""
        for step in self.steps:
            if step.name == step_name:
                return step.parsed_data
        return None