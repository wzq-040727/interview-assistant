"""
AI API 客户端模块
兼容 OpenAI API 协议
"""

import requests
import json
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class Message:
    """消息类"""
    role: str  # system, user, assistant
    content: str


class AIClient:
    """AI API 客户端"""

    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4",
                 max_tokens: int = 2000, temperature: float = 0.7):
        """
        初始化 AI 客户端

        Args:
            base_url: API 基础地址
            api_key: API 密钥
            model: 模型名称
            max_tokens: 最大 token 数
            temperature: 温度参数
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # 对话历史
        self.conversation_history: List[Message] = []

        # 系统提示
        self.system_prompt = """你是一个技术面试助手。请根据面试官的问题，提供完整的答案。

回答格式要求：
1. 问题复述：简要复述问题
2. 完整答案：详细解答
3. 关键点：列出 3-5 个关键点
4. 代码示例：如果适用，提供代码示例

注意：
- 答案要准确、专业
- 代码示例要简洁、可运行
- 关键点要突出重点
- 使用中文回答"""

    def generate_answer(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """
        生成答案

        Args:
            question: 问题
            context: 上下文（可选）

        Returns:
            生成的答案，如果失败返回 None
        """
        try:
            # 构建消息
            messages = self._build_messages(question, context)

            # 调用 API
            response = self._call_api(messages)

            if response:
                # 保存到对话历史
                self.conversation_history.append(Message(role="user", content=question))
                self.conversation_history.append(Message(role="assistant", content=response))

            return response

        except Exception as e:
            print(f"生成答案失败：{e}")
            return None

    def _build_messages(self, question: str, context: Optional[str] = None) -> List[Dict[str, str]]:
        """
        构建消息列表

        Args:
            question: 问题
            context: 上下文

        Returns:
            消息列表
        """
        messages = []

        # 系统提示
        messages.append({"role": "system", "content": self.system_prompt})

        # 添加对话历史（保留最近 5 轮）
        recent_history = self.conversation_history[-10:] if self.conversation_history else []
        for msg in recent_history:
            messages.append({"role": msg.role, "content": msg.content})

        # 添加上下文
        if context:
            messages.append({
                "role": "system",
                "content": f"上下文信息：\n{context}"
            })

        # 添加当前问题
        messages.append({"role": "user", "content": question})

        return messages

    def _call_api(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        调用 AI API

        Args:
            messages: 消息列表

        Returns:
            生成的文本
        """
        url = f"{self.base_url}/chat/completions"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        try:
            print(f"调用 API：{url}")
            print(f"模型：{self.model}")

            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=60  # 增加超时时间到 60 秒
            )

            if response.status_code == 200:
                result = response.json()
                choices = result.get('choices', [])
                if choices:
                    content = choices[0].get('message', {}).get('content', '')
                    return content.strip() if content else None
                return None
            else:
                print(f"API 错误：{response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("API 请求超时")
            return None
        except requests.exceptions.RequestException as e:
            print(f"API 请求失败：{e}")
            return None
        except json.JSONDecodeError:
            print("API 响应格式错误")
            return None

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()

    def get_history(self) -> List[Message]:
        """
        获取对话历史

        Returns:
            消息列表
        """
        return self.conversation_history.copy()


class AIClientFactory:
    """AI 客户端工厂"""

    @staticmethod
    def create(config: dict) -> AIClient:
        """
        根据配置创建 AI 客户端

        Args:
            config: 配置字典

        Returns:
            AIClient 实例
        """
        return AIClient(
            base_url=config.get('base_url', ''),
            api_key=config.get('api_key', ''),
            model=config.get('model', 'gpt-4'),
            max_tokens=config.get('max_tokens', 2000),
            temperature=config.get('temperature', 0.7)
        )
