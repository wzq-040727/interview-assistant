"""
AI API 客户端模块
兼容 OpenAI API 协议
"""

import requests
import json
from typing import Optional, List, Dict, Generator
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
        self.system_prompt = """技术面试助手。直接回答，不废话。

格式：
答案：（精炼解答）
关键点：
• 要点
代码示例：
```代码```"""

    def generate_answer(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """
        生成答案（非流式）

        Args:
            question: 问题
            context: 上下文（可选）

        Returns:
            生成的答案，如果失败返回 None
        """
        try:
            messages = self._build_messages(question, context)
            response = self._call_api(messages)

            if response:
                self.conversation_history.append(Message(role="user", content=question))
                self.conversation_history.append(Message(role="assistant", content=response))

            return response

        except Exception as e:
            print(f"生成答案失败：{e}")
            return None

    def generate_answer_stream(self, question: str, context: Optional[str] = None) -> Generator[str, None, None]:
        """
        流式生成答案

        Args:
            question: 问题
            context: 上下文（可选）

        Yields:
            生成的文本片段
        """
        try:
            messages = self._build_messages(question, context)
            full_response = ""

            for chunk in self._call_api_stream(messages):
                full_response += chunk
                yield chunk

            if full_response:
                self.conversation_history.append(Message(role="user", content=question))
                self.conversation_history.append(Message(role="assistant", content=full_response))

        except Exception as e:
            print(f"流式生成答案失败：{e}")
            yield f"生成失败：{e}"

    def _build_messages(self, question: str, context: Optional[str] = None) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = []

        # 系统提示
        messages.append({"role": "system", "content": self.system_prompt})

        # 添加当前问题
        messages.append({"role": "user", "content": question})

        return messages

    def _call_api(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """调用 AI API（非流式）"""
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
            response = requests.post(url, headers=headers, json=data, timeout=60)

            if response.status_code == 200:
                result = response.json()
                choices = result.get('choices', [])
                if choices:
                    content = choices[0].get('message', {}).get('content', '')
                    return content.strip() if content else None
                return None
            else:
                print(f"API 错误：{response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print("API 请求超时")
            return None
        except requests.exceptions.RequestException as e:
            print(f"API 请求失败：{e}")
            return None

    def _call_api_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """调用 AI API（流式）"""
        url = f"{self.base_url}/chat/completions"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60, stream=True)

            if response.status_code != 200:
                print(f"API 错误：{response.status_code}")
                return

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                        if line.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(line)
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.Timeout:
            print("API 请求超时")
        except requests.exceptions.RequestException as e:
            print(f"API 请求失败：{e}")

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()

    def get_history(self) -> List[Message]:
        """获取对话历史"""
        return self.conversation_history.copy()


class AIClientFactory:
    """AI 客户端工厂"""

    @staticmethod
    def create(config: dict) -> AIClient:
        """根据配置创建 AI 客户端"""
        return AIClient(
            base_url=config.get('base_url', ''),
            api_key=config.get('api_key', ''),
            model=config.get('model', 'gpt-4'),
            max_tokens=config.get('max_tokens', 2000),
            temperature=config.get('temperature', 0.7)
        )
