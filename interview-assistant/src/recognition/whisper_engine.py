"""
语音识别模块
使用 API 进行语音识别（兼容 OpenAI Whisper API）
"""

import requests
import io
import json
from typing import Optional
from ..audio.processor import AudioConverter


class SpeechRecognizer:
    """语音识别器，使用 API 进行语音转文字"""

    def __init__(self, api_url: str, api_key: str, language: str = "zh",
                 model: str = "whisper-1"):
        """
        初始化语音识别器

        Args:
            api_url: API 地址
            api_key: API 密钥
            language: 语言代码
            model: 模型名称
        """
        self.api_url = api_url
        self.api_key = api_key
        self.language = language
        self.model = model
        self.converter = AudioConverter()

    def recognize(self, audio_data: bytes, sample_rate: int = 16000,
                  channels: int = 1) -> Optional[str]:
        """
        识别音频数据

        Args:
            audio_data: 原始音频数据（bytes）
            sample_rate: 采样率
            channels: 声道数

        Returns:
            识别出的文字，如果识别失败返回 None
        """
        try:
            # 转换为 WAV 格式
            wav_data = self.converter.convert_to_wav(
                audio_data,
                sample_rate=sample_rate,
                channels=channels
            )

            # 调用 API
            text = self._call_api(wav_data)
            return text

        except Exception as e:
            print(f"语音识别失败：{e}")
            return None

    def _call_api(self, wav_data: bytes) -> Optional[str]:
        """
        调用语音识别 API

        Args:
            wav_data: WAV 格式的音频数据

        Returns:
            识别出的文字
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }

        files = {
            'file': ('audio.wav', wav_data, 'audio/wav')
        }

        data = {
            'model': self.model,
            'language': self.language
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                files=files,
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '').strip()
                return text if text else None
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

    def recognize_stream(self, audio_chunks: list, sample_rate: int = 16000,
                         channels: int = 1) -> Optional[str]:
        """
        识别音频流（多个音频块）

        Args:
            audio_chunks: 音频块列表
            sample_rate: 采样率
            channels: 声道数

        Returns:
            识别出的文字
        """
        # 合并音频块
        audio_data = b''.join(audio_chunks)
        return self.recognize(audio_data, sample_rate, channels)


class SpeechRecognizerFactory:
    """语音识别器工厂"""

    @staticmethod
    def create(config: dict) -> SpeechRecognizer:
        """
        根据配置创建语音识别器

        Args:
            config: 配置字典

        Returns:
            SpeechRecognizer 实例
        """
        return SpeechRecognizer(
            api_url=config.get('api_url', ''),
            api_key=config.get('api_key', ''),
            language=config.get('language', 'zh'),
            model=config.get('model', 'whisper-1')
        )
