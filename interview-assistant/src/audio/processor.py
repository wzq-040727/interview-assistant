"""
音频处理模块
处理音频数据，包括格式转换、静音检测等
"""

import numpy as np
from typing import Optional, Tuple
from collections import deque
import time


class AudioProcessor:
    """音频处理器，用于处理音频数据"""

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 silence_threshold: float = 0.01, silence_duration: float = 1.0):
        """
        初始化音频处理器

        Args:
            sample_rate: 采样率
            channels: 声道数
            silence_threshold: 静音阈值（0.0 - 1.0）
            silence_duration: 静音持续时间（秒），用于检测说话结束
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration

        # 音频缓冲区
        self.buffer = deque(maxlen=int(sample_rate * 10 / 1024))  # 10秒缓冲
        self.is_speaking = False
        self.last_sound_time = time.time()

        # 当前语音段
        self.current_segment = []
        self.segment_start_time = None

    def process_frame(self, audio_data: bytes) -> Tuple[bool, Optional[bytes]]:
        """
        处理音频帧

        Args:
            audio_data: 原始音频数据（bytes）

        Returns:
            Tuple[bool, Optional[bytes]]:
                - bool: 是否检测到语音段结束
                - Optional[bytes]: 完整的语音段数据（如果检测到结束）
        """
        # 转换为 numpy 数组
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # 计算音量级别
        level = self._calculate_level(audio_array)

        current_time = time.time()

        # 检测是否有声音
        if level > self.silence_threshold:
            # 有声音
            if not self.is_speaking:
                self.is_speaking = True
                self.segment_start_time = current_time
                self.current_segment = []

            self.last_sound_time = current_time
            self.current_segment.append(audio_data)

        else:
            # 静音
            if self.is_speaking:
                self.current_segment.append(audio_data)

                # 检查静音持续时间
                if current_time - self.last_sound_time > self.silence_duration:
                    # 语音段结束
                    self.is_speaking = False
                    segment_data = self._merge_segments(self.current_segment)
                    self.current_segment = []
                    self.segment_start_time = None
                    return True, segment_data

        return False, None

    def _calculate_level(self, audio_array: np.ndarray) -> float:
        """
        计算音频音量级别

        Args:
            audio_array: 音频数据数组

        Returns:
            音量级别（0.0 - 1.0）
        """
        if len(audio_array) == 0:
            return 0.0

        rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
        level = min(rms / 32768.0, 1.0)
        return level

    def _merge_segments(self, segments: list) -> bytes:
        """
        合并音频段

        Args:
            segments: 音频段列表

        Returns:
            合并后的音频数据
        """
        return b''.join(segments)

    def get_current_level(self) -> float:
        """
        获取当前音量级别

        Returns:
            音量级别（0.0 - 1.0）
        """
        if not self.current_segment:
            return 0.0

        last_frame = self.current_segment[-1]
        audio_array = np.frombuffer(last_frame, dtype=np.int16)
        return self._calculate_level(audio_array)

    def reset(self):
        """重置处理器状态"""
        self.buffer.clear()
        self.is_speaking = False
        self.last_sound_time = time.time()
        self.current_segment = []
        self.segment_start_time = None

    def get_segment_duration(self) -> float:
        """
        获取当前语音段持续时间

        Returns:
            持续时间（秒）
        """
        if not self.segment_start_time:
            return 0.0
        return time.time() - self.segment_start_time


class AudioConverter:
    """音频格式转换器"""

    @staticmethod
    def convert_to_wav(audio_data: bytes, sample_rate: int = 16000,
                       channels: int = 1, sample_width: int = 2) -> bytes:
        """
        将原始音频数据转换为 WAV 格式

        Args:
            audio_data: 原始音频数据
            sample_rate: 采样率
            channels: 声道数
            sample_width: 采样宽度（字节）

        Returns:
            WAV 格式的音频数据
        """
        import io
        import wave

        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)

        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def resample(audio_data: bytes, orig_rate: int, target_rate: int,
                 channels: int = 1) -> bytes:
        """
        重采样音频数据

        Args:
            audio_data: 原始音频数据
            orig_rate: 原始采样率
            target_rate: 目标采样率
            channels: 声道数

        Returns:
            重采样后的音频数据
        """
        if orig_rate == target_rate:
            return audio_data

        # 转换为 numpy 数组
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # 计算重采样后的长度
        target_length = int(len(audio_array) * target_rate / orig_rate)

        # 使用线性插值重采样
        indices = np.linspace(0, len(audio_array) - 1, target_length)
        resampled = np.interp(indices, np.arange(len(audio_array)), audio_array.astype(np.float32))

        return resampled.astype(np.int16).tobytes()
