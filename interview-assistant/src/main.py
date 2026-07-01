"""
面试练习助手 - 主程序入口
集成所有模块，实现完整功能
"""

import sys
import os
import signal
import threading
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QIcon


class AnswerSignal(QObject):
    """答案信号，用于线程间通信"""
    answer_ready = pyqtSignal(str, object)  # 完整答案
    stream_update = pyqtSignal(str, str)  # 问题, 当前文本


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

        # 信号（用于线程间通信）
        self.answer_signal = AnswerSignal()

    def initialize(self) -> bool:
        """初始化所有模块"""
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
                language=recognition_config.get('language', 'zh-CN'),
                engine=recognition_config.get('engine', 'google')
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
                chunk_size=audio_config.get('chunk_size', 1024),
                source=audio_config.get('source', 'microphone')
            )

            # 初始化系统托盘
            self._init_tray_icon()

            # 连接信号（用于线程间通信）
            self.answer_signal.answer_ready.connect(self._show_answer_in_main_thread)
            self.answer_signal.stream_update.connect(self._update_stream_in_main_thread)

            print("所有模块初始化完成")
            return True

        except Exception as e:
            print(f"初始化失败：{e}")
            return False

    def _init_tray_icon(self):
        """初始化系统托盘图标"""
        self.tray_icon = QSystemTrayIcon()

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

        menu = QMenu()

        show_action = QAction("显示/隐藏", menu)
        show_action.triggered.connect(self.overlay.toggle)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.overlay.toggle()

    def start(self):
        """启动面试练习助手"""
        if self.is_running:
            return

        if not self.hotkey_manager.start():
            print("快捷键监听启动失败")
            return

        if not self.audio_capture.start(self._on_audio_frame):
            print("音频捕获启动失败")
            return

        self.is_running = True
        print("面试练习助手已启动")
        print(f"按 {self.config.get('ui.hotkey', 'ctrl+b')} 显示/隐藏悬浮窗")

    def _on_audio_frame(self, audio_data: bytes):
        """音频帧回调"""
        is_segment_end, segment_data = self.audio_processor.process_frame(audio_data)

        if is_segment_end and segment_data:
            text = self.speech_recognizer.recognize(
                segment_data,
                sample_rate=self.config.get('audio.sample_rate', 16000),
                channels=self.config.get('audio.channels', 1)
            )

            if text:
                print(f"识别到语音：{text}")

                result = self.question_detector.detect(text)

                if result.is_question:
                    print(f"检测到问题（置信度：{result.confidence:.2f}）：{text}")

                    # 使用流式生成
                    self._generate_stream(text)

    def _generate_stream(self, question: str):
        """流式生成答案（在子线程中）"""
        def stream_worker():
            try:
                full_text = ""
                for chunk in self.answer_generator.generate_stream(question):
                    full_text += chunk
                    # 每收到一块就更新 UI
                    self.answer_signal.stream_update.emit(question, full_text)

                # 生成完成，格式化最终答案
                from src.ai.answer_generator import AnswerFormatter
                formatter = AnswerFormatter()
                formatted = formatter.format(question, full_text)
                self.answer_signal.answer_ready.emit(question, formatted)

            except Exception as e:
                print(f"流式生成失败：{e}")

        thread = threading.Thread(target=stream_worker, daemon=True)
        thread.start()

    def _update_stream_in_main_thread(self, question: str, text: str):
        """主线程中更新流式文本"""
        self.overlay.show_streaming(question, text)

    def _show_answer_in_main_thread(self, question: str, answer):
        """主线程中显示最终答案"""
        self.overlay.show_answer(question, answer)
        print("答案已显示")

    def stop(self):
        """停止面试练习助手"""
        if not self.is_running:
            return

        if self.audio_capture:
            self.audio_capture.stop()

        if self.hotkey_manager:
            self.hotkey_manager.stop()

        self.is_running = False
        print("面试练习助手已停止")

    def quit(self):
        """退出程序"""
        self.stop()

        if self.tray_icon:
            self.tray_icon.hide()

        if self.app:
            self.app.quit()

    def run(self):
        """运行程序"""
        if not self.initialize():
            print("初始化失败，程序退出")
            sys.exit(1)

        self.start()
        sys.exit(self.app.exec_())


def main():
    """主函数"""
    assistant = InterviewAssistant()

    def signal_handler(sig, frame):
        print("\n正在退出...")
        assistant.quit()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    assistant.run()


if __name__ == '__main__':
    main()
