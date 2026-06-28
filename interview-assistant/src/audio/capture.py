"""
音频捕获模块
使用 pyaudio 捕获系统音频输出（WASAPI 环回模式）
"""

import pyaudio
import wave
import threading
import numpy as np
from typing import Callable, Optional


class AudioCapture:
    """音频捕获类，用于捕获系统音频输出"""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_size: int = 1024):
        """
        初始化音频捕获

        Args:
            sample_rate: 采样率
            channels: 声道数
            chunk_size: 每次读取的帧数
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size

        self.pa: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.is_running = False
        self.callback: Optional[Callable] = None
        self.thread: Optional[threading.Thread] = None

    def _find_wasapi_loopback(self) -> Optional[int]:
        """
        查找 WASAPI 环回设备

        Returns:
            设备索引，如果未找到返回 None
        """
        if self.pa is None:
            return None

        for i in range(self.pa.get_device_count()):
            device_info = self.pa.get_device_info_by_index(i)
            # 查找 WASAPI 环回设备（通常是扬声器的环回）
            if device_info.get('maxInputChannels', 0) > 0:
                host_api_info = self.pa.get_host_api_info_by_index(device_info.get('hostApi', 0))
                if host_api_info and 'WASAPI' in host_api_info.get('name', ''):
                    return i

        # 如果没有找到 WASAPI 设备，尝试使用默认输入设备
        try:
            default_input = self.pa.get_default_input_device_info()
            return default_input.get('index')
        except Exception:
            return None

    def _get_supported_sample_rate(self, device_index: int) -> int:
        """
        获取设备支持的采样率

        Args:
            device_index: 设备索引

        Returns:
            支持的采样率
        """
        if self.pa is None:
            return self.sample_rate

        device_info = self.pa.get_device_info_by_index(device_index)
        default_sample_rate = int(device_info.get('defaultSampleRate', 44100))

        # 尝试常见的采样率
        common_rates = [16000, 44100, 48000, 22050, 11025]
        for rate in common_rates:
            try:
                # 检查是否支持该采样率
                supported = self.pa.is_format_supported(
                    rate,
                    input_device=device_index,
                    input_channels=self.channels,
                    input_format=pyaudio.paInt16
                )
                if supported:
                    return rate
            except Exception:
                continue

        # 如果都不支持，返回设备默认采样率
        return default_sample_rate

    def start(self, callback: Callable[[bytes], None]) -> bool:
        """
        开始捕获音频

        Args:
            callback: 音频数据回调函数，接收 bytes 类型的音频数据

        Returns:
            是否成功启动
        """
        if self.is_running:
            return True

        try:
            self.pa = pyaudio.PyAudio()

            # 查找环回设备
            device_index = self._find_wasapi_loopback()
            if device_index is None:
                print("错误：未找到音频输入设备")
                return False

            # 获取设备支持的采样率
            actual_sample_rate = self._get_supported_sample_rate(device_index)
            print(f"使用采样率：{actual_sample_rate} Hz")

            # 打开音频流
            self.stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=actual_sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )

            # 更新实际采样率
            self.sample_rate = actual_sample_rate

            self.callback = callback
            self.is_running = True

            # 启动捕获线程
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()

            print(f"音频捕获已启动（设备索引：{device_index}）")
            return True

        except Exception as e:
            print(f"启动音频捕获失败：{e}")
            self.stop()
            return False

    def _capture_loop(self):
        """音频捕获循环"""
        while self.is_running and self.stream:
            try:
                # 读取音频数据
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)

                # 调用回调函数
                if self.callback:
                    self.callback(data)

            except Exception as e:
                if self.is_running:
                    print(f"音频捕获错误：{e}")
                break

    def stop(self):
        """停止捕获音频"""
        self.is_running = False

        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        if self.pa:
            try:
                self.pa.terminate()
            except Exception:
                pass
            self.pa = None

        self.callback = None
        print("音频捕获已停止")

    def get_audio_level(self, data: bytes) -> float:
        """
        计算音频音量级别

        Args:
            data: 音频数据

        Returns:
            音量级别（0.0 - 1.0）
        """
        try:
            audio_data = np.frombuffer(data, dtype=np.int16)
            if len(audio_data) == 0:
                return 0.0
            rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            # 归一化到 0-1
            level = min(rms / 32768.0, 1.0)
            return level
        except Exception:
            return 0.0

    def __del__(self):
        """析构函数，确保资源释放"""
        self.stop()
