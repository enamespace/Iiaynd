import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv
from zai import ZhipuAiClient

# 加载 .env 文件
load_dotenv()


class ZhipuLLMClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "glm-4.6v"):
        self.api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPUAI_API_KEY is not set. Please set it in .env file or as an environment variable.")

        self.client = ZhipuAiClient(api_key=self.api_key)
        self.model = model
        self.logger = logging.getLogger("ZhipuLLMClient")

    def call(self, prompt: str, system_prompt: str = "你是一个有用的助手。") -> str:
        """普通文本调用"""
        self.logger.info(f"--- LLM REQUEST ---\nSystem: {system_prompt}\nUser: {prompt[:500]}...\n-------------------------------")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            content = response.choices[0].message.content
            self.logger.info(f"--- LLM RESPONSE ---\n{content[:500]}...\n--------------------")
            return content
        except Exception as e:
            self.logger.error(f"Error calling ZhipuAI: {e}")
            raise