import os
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Type, TypeVar, Callable, List
from dotenv import load_dotenv
from pydantic import BaseModel
from zai import ZhipuAiClient

# 加载 .env 文件
load_dotenv()

logger = logging.getLogger("llm_retry")

T = TypeVar("T", bound=BaseModel)


def clean_json_response(content: str) -> str:
    """清洗 LLM 返回的 JSON 内容，移除 Markdown 代码块标记"""
    cleaned = content.strip()
    # 移除开头的代码块标记
    for prefix in ["```json\n", "```JSON\n", "```json", "```JSON", "```\n", "```"]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    # 移除结尾的代码块标记
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


class ZhipuLLMClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "glm-4.6v", log_dir: Optional[Path] = None):
        self.api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPUAI_API_KEY is not set. Please set it in .env file or as an environment variable.")

        self.client = ZhipuAiClient(api_key=self.api_key)
        self.model = model
        self.log_dir = log_dir
        self.logger = logging.getLogger("ZhipuLLMClient")

    def set_log_dir(self, log_dir: Optional[Path]) -> None:
        """Set or change the log directory for persisting LLM outputs."""
        self.log_dir = log_dir

    def call(self, prompt: str, system_prompt: str = "你是一个有用的助手。") -> str:
        """普通文本调用"""
        self.logger.info(f"--- LLM REQUEST ---\nSystem: {system_prompt}\nUser: {prompt[:1000]}...\n-------------------------------")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "system_prompt": system_prompt,
            "user_prompt": prompt,
            "response": None,
            "response_length": 0,
            "success": False,
            "error": None
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            self.logger.info(f"--- LLM RESPONSE ---\n{content[:1000]}...\n--------------------")

            # Update log entry with success
            log_entry["response"] = content
            log_entry["response_length"] = len(content)
            log_entry["success"] = True

            return content
        except Exception as e:
            self.logger.error(f"Error calling ZhipuAI: {e}")
            log_entry["error"] = str(e)
            raise
        finally:
            # Persist log if log_dir is set
            if self.log_dir:
                self._save_log(log_entry, timestamp)

    def call_conversation(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """多轮对话调用，传入完整消息历史

        Args:
            messages: 消息历史列表，每条消息包含 role 和 content
                     [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
            system_prompt: 可选的系统提示词，如果提供会作为第一条 system 消息

        Returns:
            LLM 返回的内容
        """
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        self.logger.info(f"--- LLM CONVERSATION ---\nMessages: {len(full_messages)}\n-------------------------------")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "mode": "conversation",
            "messages": full_messages,
            "response": None,
            "response_length": 0,
            "success": False,
            "error": None
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages
            )
            content = response.choices[0].message.content
            self.logger.info(f"--- LLM RESPONSE ---\n{content[:1000]}...\n--------------------")

            log_entry["response"] = content
            log_entry["response_length"] = len(content)
            log_entry["success"] = True

            return content
        except Exception as e:
            self.logger.error(f"Error in conversation call: {e}")
            log_entry["error"] = str(e)
            raise
        finally:
            if self.log_dir:
                self._save_log(log_entry, timestamp)

    def _save_log(self, log_entry: dict, timestamp: str) -> None:
        """Save LLM call log to file."""
        if not self.log_dir:
            return
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / f"llm_call_{timestamp}.json"
        try:
            log_file.write_text(json.dumps(log_entry, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            self.logger.warning(f"Failed to save LLM log: {e}")


def llm_call_with_retry_single(
    llm: ZhipuLLMClient,
    prompt: str,
    system_prompt: str,
    model_class: Type[T],
    max_retries: int = 3,
    error_context: str = "LLM生成"
) -> T:
    """单次调用模式 Retry（备选方案）

    每次独立调用，prompt 包含上次输出和错误信息。

    Args:
        llm: LLM 客户端
        prompt: 用户提示词
        system_prompt: 系统提示词
        model_class: 目标 Pydantic 模型类
        max_retries: 最大重试次数
        error_context: 错误上下文描述（用于日志）

    Returns:
        验证通过的模型实例

    Raises:
        ValueError: 达到最大重试次数仍未成功
    """
    errors_feedback: List[str] = []
    last_output: Optional[str] = None

    for attempt in range(1, max_retries + 1):
        logger.info(f"{error_context} attempt {attempt}/{max_retries} (single mode)")

        # 构造当前 prompt
        current_prompt = prompt
        current_system = system_prompt

        if errors_feedback and last_output:
            current_prompt += f"\n\n【上次输出】\n{last_output}\n\n【错误】\n" + "\n".join(f"- {e}" for e in errors_feedback) + "\n请修正并输出完整JSON。"
            current_system = system_prompt + " 你正在修正上次的输出。"
            logger.info(f"Retrying with {len(errors_feedback)} error feedbacks (last output included)")

        try:
            content = llm.call(prompt=current_prompt, system_prompt=current_system)
            last_output = content
            cleaned = clean_json_response(content)

            # JSON 解析
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as e:
                error_msg = f"JSON解析失败: {e}"
                logger.warning(error_msg)
                errors_feedback = [error_msg]
                continue

            # Pydantic 验证
            try:
                result = model_class(**data)
                logger.info(f"{error_context} succeeded on attempt {attempt}")
                return result
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Pydantic验证失败: {error_msg}")
                errors_feedback = [error_msg]
                continue

        except Exception as e:
            logger.warning(f"LLM调用失败: {e}")
            errors_feedback = [f"LLM调用失败: {e}"]
            continue

    raise ValueError(
        f"{error_context}失败，达到最大重试次数 {max_retries}。\n"
        f"最终错误:\n" + "\n".join(f"- {e}" for e in errors_feedback)
    )


def llm_call_with_retry_conversation(
    llm: ZhipuLLMClient,
    prompt: str,
    system_prompt: str,
    model_class: Type[T],
    max_retries: int = 3,
    error_context: str = "LLM生成"
) -> T:
    """多轮对话模式 Retry（优先方案）

    使用 messages 数组保持对话历史，LLM 理解这是在修正之前的回答。

    Args:
        llm: LLM 客户端
        prompt: 用户提示词
        system_prompt: 系统提示词
        model_class: 目标 Pydantic 模型类
        max_retries: 最大重试次数
        error_context: 错误上下文描述（用于日志）

    Returns:
        验证通过的模型实例

    Raises:
        ValueError: 达到最大重试次数仍未成功
    """
    messages: List[dict] = [{"role": "user", "content": prompt}]
    current_system = system_prompt
    last_content: Optional[str] = None

    for attempt in range(1, max_retries + 1):
        logger.info(f"{error_context} attempt {attempt}/{max_retries} (conversation mode)")

        try:
            content = llm.call_conversation(messages, system_prompt=current_system)
            last_content = content
            cleaned = clean_json_response(content)

            # JSON 解析
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as e:
                error_msg = f"JSON解析失败: {e}"
                logger.warning(error_msg)
                # 添加 assistant + user (错误反馈)
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"JSON解析失败: {e}\n请修正并输出完整JSON。"})
                current_system = system_prompt + " 你正在修正 JSON 格式问题。"
                continue

            # Pydantic 验证
            try:
                result = model_class(**data)
                logger.info(f"{error_context} succeeded on attempt {attempt}")
                return result
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Pydantic验证失败: {error_msg}")
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"验证失败: {error_msg}\n请修正并输出完整JSON。"})
                current_system = system_prompt + " 你正在修正数据验证问题。"
                continue

        except Exception as e:
            logger.warning(f"LLM调用失败: {e}")
            messages.append({"role": "user", "content": f"调用失败: {e}，请重试。"})
            continue

    raise ValueError(
        f"{error_context}失败，达到最大重试次数 {max_retries}。\n"
        f"对话历史:\n" + "\n".join(f"  {m['role']}: {m['content'][:100]}..." for m in messages[-4:])
    )


def llm_call_with_retry(
    llm: ZhipuLLMClient,
    prompt: str,
    system_prompt: str,
    model_class: Type[T],
    max_retries: int = 3,
    error_context: str = "LLM生成",
    mode: str = "conversation"
) -> T:
    """通用 LLM 调用重试机制，支持双模式

    处理 JSON 解析失败和 Pydantic 验证失败的自动重试。

    Args:
        llm: LLM 客户端
        prompt: 用户提示词
        system_prompt: 系统提示词
        model_class: 目标 Pydantic 模型类
        max_retries: 最大重试次数
        error_context: 错误上下文描述（用于日志）
        mode: 重试模式 - "conversation"（多轮对话，优先）或 "single"（单次调用，备选）

    Returns:
        验证通过的模型实例

    Raises:
        ValueError: 达到最大重试次数仍未成功
    """
    if mode == "conversation":
        return llm_call_with_retry_conversation(
            llm, prompt, system_prompt, model_class, max_retries, error_context
        )
    else:
        return llm_call_with_retry_single(
            llm, prompt, system_prompt, model_class, max_retries, error_context
        )