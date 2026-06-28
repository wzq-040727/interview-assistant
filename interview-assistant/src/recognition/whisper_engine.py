"""
语音识别模块
支持本地 Whisper 模型和 API 两种模式
"""

import whisper
import numpy as np
import tempfile
import os
from typing import Optional
from ..audio.processor import AudioConverter


class SpeechRecognizer:
    """语音识别器，支持本地 Whisper 和 API 两种模式"""

    def __init__(self, mode: str = "local", api_url: str = "", api_key: str = "",
                 language: str = "zh", model: str = "base"):
        """
        初始化语音识别器

        Args:
            mode: 识别模式 "local" 或 "api"
            api_url: API 地址（API 模式）
            api_key: API 密钥（API 模式）
            language: 语言代码
            model: 模型名称（本地模式：tiny/base/small/medium/large）
        """
        self.mode = mode
        self.api_url = api_url
        self.api_key = api_key
        self.language = language
        self.model_name = model
        self.converter = AudioConverter()

        # 本地 Whisper 模型
        self.whisper_model = None

        if mode == "local":
            self._load_local_model()

    def _load_local_model(self):
        """加载本地 Whisper 模型"""
        try:
            print(f"正在加载 Whisper 模型：{self.model_name}...")
            self.whisper_model = whisper.load_model(self.model_name)
            print("Whisper 模型加载完成")
        except Exception as e:
            print(f"加载 Whisper 模型失败：{e}")
            self.whisper_model = None

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
            if self.mode == "local":
                return self._recognize_local(audio_data, sample_rate, channels)
            else:
                return self._recognize_api(audio_data, sample_rate, channels)

        except Exception as e:
            print(f"语音识别失败：{e}")
            return None

    def _recognize_local(self, audio_data: bytes, sample_rate: int,
                         channels: int) -> Optional[str]:
        """
        使用本地 Whisper 模型识别

        Args:
            audio_data: 原始音频数据
            sample_rate: 采样率
            channels: 声道数

        Returns:
            识别出的文字
        """
        if self.whisper_model is None:
            print("Whisper 模型未加载")
            return None

        try:
            # 转换为 numpy 数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # 转换为 float32 并归一化
            audio_float = audio_array.astype(np.float32) / 32768.0

            # 如果是立体声，转换为单声道
            if channels == 2:
                audio_float = audio_float.reshape(-1, 2).mean(axis=1)

            # 重采样到 16kHz（Whisper 要求）
            if sample_rate != 16000:
                # 简单的重采样
                target_length = int(len(audio_float) * 16000 / sample_rate)
                indices = np.linspace(0, len(audio_float) - 1, target_length)
                audio_float = np.interp(indices, np.arange(len(audio_float)), audio_float)

            # 使用 Whisper 识别
            result = self.whisper_model.transcribe(
                audio_float,
                language=self.language,
                fp16=False  # Windows 上使用 CPU 模式
            )

            text = result.get('text', '').strip()
            return text if text else None

        except Exception as e:
            print(f"本地识别失败：{e}")
            return None

    def _recognize_api(self, audio_data: bytes, sample_rate: int,
                       channels: int) -> Optional[str]:
        """
        使用 API 识别

        Args:
            audio_data: 原始音频数据
            sample_rate: 采样率
            channels: 声道数

        Returns:
            识别出的文字
        """
        import requests
        import json

        try:
            # 转换为 WAV 格式
            wav_data = self.converter.convert_to_wav(
                audio_data,
                sample_rate=sample_rate,
                channels=channels
            )

            # 调用 API
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }

            files = {
                'file': ('audio.wav', wav_data, 'audio/wav')
            }

            data = {
                'model': 'whisper-1',
                'language': self.language
            }

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
                print(f"API 错误：{response.status_code}")
                return None

        except Exception as e:
            print(f"API 识别失败：{e}")
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
        # 检查是否使用本地模式
        use_local = config.get('use_local', True)

        if use_local:
            return SpeechRecognizer(
                mode="local",
                language=config.get('language', 'zh'),
                model=config.get('model', 'base')
            )
        else:
            return SpeechRecognizer(
                mode="api",
                api_url=config.get('api_url', ''),
                api_key=config.get('api_key', ''),
                language=config.get('language', 'zh')
            )
