"""
语音识别模块
使用 SpeechRecognition 库进行语音识别
"""

import speech_recognition as sr
import numpy as np
from typing import Optional
from ..audio.processor import AudioConverter


class SpeechRecognizer:
    """语音识别器，使用 SpeechRecognition 库"""

    def __init__(self, language: str = "zh-CN", engine: str = "google"):
        """
        初始化语音识别器

        Args:
            language: 语言代码
            engine: 识别引擎 "google"（免费）或 "sphinx"（离线）
        """
        self.language = language
        self.engine = engine
        self.recognizer = sr.Recognizer()
        self.converter = AudioConverter()

        # 调整识别器参数
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

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

            # 创建 AudioData 对象
            audio = sr.AudioData(wav_data, sample_rate, 2)  # 2 bytes per sample

            # 使用指定引擎识别
            if self.engine == "google":
                text = self.recognizer.recognize_google(audio, language=self.language)
            elif self.engine == "sphinx":
                text = self.recognizer.recognize_sphinx(audio, language=self.language)
            else:
                text = self.recognizer.recognize_google(audio, language=self.language)

            return text.strip() if text else None

        except sr.UnknownValueError:
            # 语音无法识别
            return None
        except sr.RequestError as e:
            # API 请求失败
            print(f"语音识别 API 错误：{e}")
            return None
        except Exception as e:
            print(f"语音识别失败：{e}")
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
            language=config.get('language', 'zh-CN'),
            engine=config.get('engine', 'google')
        )
