"""
面试练习助手 - 主程序入口
集成所有模块，实现完整功能
"""

import sys
import os
import signal
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio.capture import AudioCapture
from src.audio.processor import AudioProcessor
from src.recognition.whisper_engine import SpeechRecognizer
from src.recognition.question_detector import QuestionDetector
from src.ai.client import AIClient
from src.ai.answer_generator import AnswerGenerator
from src.ui.overlay import OverlayWindow
from src.utils.config import Config
from src.utils.hotkey import HotkeyManager


class InterviewAssistant:
    """面试练习助手主类"""

    def __init__(self):
        """初始化面试练习助手"""
        # 加载配置
        self.config = Config()

        # 初始化模块
        self.audio_capture = None
        self.audio_processor = None
        self.speech_recognizer = None
        self.question_detector = None
        self.ai_client = None
        self.answer_generator = None
        self.overlay = None
        self.hotkey_manager = None
        self.tray_icon = None

        # 应用程序
        self.app = None

        # 状态
        self.is_running = False

    def initialize(self) -> bool:
        """
        初始化所有模块

        Returns:
            是否成功初始化
        """
        try:
            # 创建 QApplication
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)

            # 初始化音频处理器
            audio_config = self.config.get_section('audio')
            self.audio_processor = AudioProcessor(
                sample_rate=audio_config.get('sample_rate', 16000),
                channels=audio_config.get('channels', 1)
            )

            # 初始化语音识别器
            recognition_config = self.config.get_section('recognition')
            self.speech_recognizer = SpeechRecognizer(
                api_url=recognition_config.get('api_url', ''),
                api_key=recognition_config.get('api_key', ''),
                language=recognition_config.get('language', 'zh'),
                model=recognition_config.get('model', 'whisper-1')
            )

            # 初始化问题检测器
            filter_config = self.config.get_section('filter')
            self.question_detector = QuestionDetector(
                min_length=filter_config.get('min_question_length', 10),
                max_length=filter_config.get('max_question_length', 500),
                ignore_patterns=filter_config.get('ignore_patterns'),
                question_keywords=filter_config.get('question_keywords')
            )

            # 初始化 AI 客户端
            ai_config = self.config.get_section('ai')
            self.ai_client = AIClient(
                base_url=ai_config.get('base_url', ''),
                api_key=ai_config.get('api_key', ''),
                model=ai_config.get('model', 'gpt-4'),
                max_tokens=ai_config.get('max_tokens', 2000),
                temperature=ai_config.get('temperature', 0.7)
            )

            # 初始化答案生成器
            self.answer_generator = AnswerGenerator(self.ai_client)

            # 初始化悬浮窗
            ui_config = self.config.get_section('ui')
            self.overlay = OverlayWindow(ui_config)

            # 初始化快捷键管理器
            self.hotkey_manager = HotkeyManager(
                toggle_callback=self.overlay.toggle,
                hotkey=ui_config.get('hotkey', 'ctrl+b')
            )

            # 初始化音频捕获器
            self.audio_capture = AudioCapture(
                sample_rate=audio_config.get('sample_rate', 16000),
                channels=audio_config.get('channels', 1),
                chunk_size=audio_config.get('chunk_size', 1024)
            )

            # 初始化系统托盘
            self._init_tray_icon()

            print("所有模块初始化完成")
            return True

        except Exception as e:
            print(f"初始化失败：{e}")
            return False

    def _init_tray_icon(self):
        """初始化系统托盘图标"""
        self.tray_icon = QSystemTrayIcon()

        # 创建简单的图标（白色圆形）
        from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(0, 191, 255)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()

        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip("面试练习助手")

        # 创建菜单
        menu = QMenu()

        show_action = QAction("显示/隐藏", menu)
        show_action.triggered.connect(self.overlay.toggle)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.connect(self.quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

        # 点击托盘图标切换显示
        self.tray_icon.activated.connect(self._on_tray_activated)

        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        """
        托盘图标激活事件

        Args:
            reason: 激活原因
        """
        if reason == QSystemTrayIcon.Trigger:
            self.overlay.toggle()

    def start(self):
        """启动面试练习助手"""
        if self.is_running:
            return

        # 启动快捷键监听
        if not self.hotkey_manager.start():
            print("快捷键监听启动失败")
            return

        # 启动音频捕获
        if not self.audio_capture.start(self._on_audio_frame):
            print("音频捕获启动失败")
            return

        self.is_running = True
        print("面试练习助手已启动")
        print(f"按 {self.config.get('ui.hotkey', 'ctrl+b')} 显示/隐藏悬浮窗")

    def _on_audio_frame(self, audio_data: bytes):
        """
        音频帧回调

        Args:
            audio_data: 音频数据
        """
        # 处理音频帧
        is_segment_end, segment_data = self.audio_processor.process_frame(audio_data)

        # 如果检测到语音段结束
        if is_segment_end and segment_data:
            # 语音识别
            text = self.speech_recognizer.recognize(
                segment_data,
                sample_rate=self.config.get('audio.sample_rate', 16000),
                channels=self.config.get('audio.channels', 1)
            )

            if text:
                print(f"识别到语音：{text}")

                # 检测是否是问题
                result = self.question_detector.detect(text)

                if result.is_question:
                    print(f"检测到问题（置信度：{result.confidence:.2f}）：{text}")

                    # 生成答案
                    answer = self.answer_generator.generate(text)

                    if answer:
                        # 显示答案
                        self.overlay.show_answer(text, answer)
                        print("答案已显示")

    def stop(self):
        """停止面试练习助手"""
        if not self.is_running:
            return

        # 停止音频捕获
        if self.audio_capture:
            self.audio_capture.stop()

        # 停止快捷键监听
        if self.hotkey_manager:
            self.hotkey_manager.stop()

        self.is_running = False
        print("面试练习助手已停止")

    def quit(self):
        """退出程序"""
        self.stop()

        # 隐藏托盘图标
        if self.tray_icon:
            self.tray_icon.hide()

        # 退出应用
        if self.app:
            self.app.quit()

    def run(self):
        """运行程序"""
        if not self.initialize():
            print("初始化失败，程序退出")
            sys.exit(1)

        self.start()

        # 运行主循环
        sys.exit(self.app.exec_())


def main():
    """主函数"""
    assistant = InterviewAssistant()
    assistant.run()


if __name__ == '__main__':
    main()
