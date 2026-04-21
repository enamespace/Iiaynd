import os
import json
import logging
import time
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from zai import ZhipuAiClient

# 加载 .env 文件
load_dotenv()


@dataclass
class LLMResponse:
    """LLM 调用响应"""
    content: str  # 响应内容
    model: str  # 使用的模型
    prompt_tokens: int = 0  # 输入 token 数
    completion_tokens: int = 0  # 输出 token 数
    total_tokens: int = 0  # 总 token 数
    duration_seconds: float = 0.0  # 调用耗时（秒）


class ZhipuLLMClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "glm-4.6v"):
        self.api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPUAI_API_KEY is not set. Please set it in .env file or as an environment variable.")

        self.client = ZhipuAiClient(api_key=self.api_key)
        self.model = model
        self.logger = logging.getLogger("ZhipuLLMClient")

    def call(self, prompt: str, system_prompt: str = "你是一个有用的助手。") -> LLMResponse:
        """调用 LLM 并返回响应（含 token 使用信息）"""
        self.logger.info(f"--- LLM REQUEST ---\nSystem: {system_prompt}\nUser: {prompt[:500]}...\n-------------------------------")

        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            duration = time.time() - start_time

            content = response.choices[0].message.content
            self.logger.info(f"--- LLM RESPONSE ---\n{content[:500]}...\n--------------------")

            # 提取 token 使用信息
            usage = getattr(response, 'usage', None)
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            return LLMResponse(
                content=content,
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                duration_seconds=round(duration, 3)
            )
        except Exception as e:
            self.logger.error(f"Error calling ZhipuAI: {e}")
            raise