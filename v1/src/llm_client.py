import os
import json
import logging
from typing import Dict, Any, Optional
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

    def call_with_json(self, prompt: str, system_prompt: str = "你是一个有用的助手。") -> Dict[str, Any]:
        """调用 LLM 并期望返回 JSON 格式的数据"""
        content = ""
        # 打印请求体
        self.logger.info(f"--- LLM REQUEST (JSON Mode) ---\nSystem: {system_prompt}\nUser: {prompt}\n-------------------------------")
        try:
            # 备注：zai-sdk 0.2.2+ 支持 response_format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            content = response.choices[0].message.content
            # 打印返回体
            self.logger.info(f"--- LLM RESPONSE ---\n{content}\n--------------------")
            
            # 尝试清洗可能存在的 Markdown 代码块标记
            cleaned_content = content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            return json.loads(cleaned_content)
        except json.JSONDecodeError as je:
            self.logger.error(f"JSON Decode Error: {je}. Raw content: {content}")
            raise ValueError(f"Failed to parse LLM response as JSON. Raw content: {content}")
        except Exception as e:
            self.logger.error(f"Error calling ZhipuAI (zai-sdk): {e}")
            raise

    def call(self, prompt: str, system_prompt: str = "你是一个有用的助手。") -> str:
        """普通文本调用"""
        self.logger.info(f"--- LLM REQUEST (Text Mode) ---\nSystem: {system_prompt}\nUser: {prompt}\n-------------------------------")
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
            self.logger.info(f"--- LLM RESPONSE ---\n{content}\n--------------------")
            return content
        except Exception as e:
            self.logger.error(f"Error calling ZhipuAI (zai-sdk): {e}")
            raise
