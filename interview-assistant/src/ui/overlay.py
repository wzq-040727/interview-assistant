"""
透明悬浮窗模块
显示答案的透明悬浮窗
"""

import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QApplication, QSystemTrayIcon, QMenu, QAction,
    QSplitter, QScrollBar
)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPainter, QBrush
from typing import Optional


class OverlayWindow(QWidget):
    """透明悬浮窗"""

    # 信号
    closed = pyqtSignal()

    def __init__(self, config: dict):
        """
        初始化悬浮窗

        Args:
            config: 配置字典
        """
        super().__init__()

        self.config = config
        self.opacity = config.get('opacity', 0.9)
        self.font_size = config.get('font_size', 14)
        self.font_family = config.get('font_family', 'Microsoft YaHei')
        self.position = config.get('position', 'top-right')
        self.width = config.get('width', 800)
        self.max_height = config.get('max_height', 1000)

        # 拖动相关
        self.drag_position = QPoint()
        self.is_dragging = False

        # 当前答案
        self.current_question = ""
        self.current_answer = ""

        self._init_ui()
        self._setup_window()

    def _init_ui(self):
        """初始化界面 - 两列布局"""
        # 主布局
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)

        # ===== 顶部：问题区域 =====
        self.question_label = QLabel("[问题]")
        self.question_label.setFont(QFont(self.font_family, self.font_size - 2, QFont.Bold))
        self.question_label.setStyleSheet("color: #FFD700;")
        self.main_layout.addWidget(self.question_label)

        self.question_text = QLabel("")
        self.question_text.setFont(QFont(self.font_family, self.font_size))
        self.question_text.setStyleSheet("color: #FFFFFF;")
        self.question_text.setWordWrap(True)
        self.main_layout.addWidget(self.question_text)

        # 分隔线
        separator = QLabel()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #555555;")
        self.main_layout.addWidget(separator)

        # ===== 两列区域 =====
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(15)

        # ----- 左列：关键点 + 代码示例 -----
        left_column = QVBoxLayout()
        left_column.setSpacing(10)

        # 关键点
        self.key_points_label = QLabel("[关键点]")
        self.key_points_label.setFont(QFont(self.font_family, self.font_size - 2, QFont.Bold))
        self.key_points_label.setStyleSheet("color: #90EE90;")
        left_column.addWidget(self.key_points_label)

        self.key_points_text = QTextEdit()
        self.key_points_text.setFont(QFont(self.font_family, self.font_size - 1))
        self.key_points_text.setStyleSheet("""
            QTextEdit {
                color: #FFFFFF;
                background-color: rgba(0, 0, 0, 150);
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        self.key_points_text.setReadOnly(True)
        self.key_points_text.setMinimumHeight(150)
        left_column.addWidget(self.key_points_text)

        # 代码示例
        self.code_label = QLabel("[代码示例]")
        self.code_label.setFont(QFont(self.font_family, self.font_size - 2, QFont.Bold))
        self.code_label.setStyleSheet("color: #FFB6C1;")
        left_column.addWidget(self.code_label)

        self.code_text = QTextEdit()
        self.code_text.setFont(QFont("Consolas", self.font_size - 1))
        self.code_text.setStyleSheet("""
            QTextEdit {
                color: #00FF00;
                background-color: rgba(0, 0, 0, 200);
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
                font-family: Consolas, monospace;
            }
        """)
        self.code_text.setReadOnly(True)
        left_column.addWidget(self.code_text)

        # 左列容器
        left_widget = QWidget()
        left_widget.setLayout(left_column)
        left_widget.setFixedWidth(300)  # 左列固定宽度

        # ----- 右列：完整答案 -----
        right_column = QVBoxLayout()
        right_column.setSpacing(10)

        self.answer_label = QLabel("[完整答案]")
        self.answer_label.setFont(QFont(self.font_family, self.font_size - 2, QFont.Bold))
        self.answer_label.setStyleSheet("color: #00BFFF;")
        right_column.addWidget(self.answer_label)

        self.answer_text = QTextEdit()
        self.answer_text.setFont(QFont(self.font_family, self.font_size))
        self.answer_text.setStyleSheet("""
            QTextEdit {
                color: #FFFFFF;
                background-color: rgba(0, 0, 0, 150);
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.answer_text.setReadOnly(True)
        right_column.addWidget(self.answer_text)

        # 右列容器
        right_widget = QWidget()
        right_widget.setLayout(right_column)

        # 添加到两列布局
        columns_layout.addWidget(left_widget)
        columns_layout.addWidget(right_widget, 1)  # 右列拉伸

        self.main_layout.addLayout(columns_layout, 1)  # 两列区域拉伸

        self.setLayout(self.main_layout)

    def _setup_window(self):
        """设置窗口属性"""
        # 窗口标志
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool  # 不在任务栏显示
        )

        # 透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 设置透明度
        self.setWindowOpacity(self.opacity)

        # 设置大小
        self.resize(self.width, self.max_height)

        # 设置位置
        self._set_position()

    def _set_position(self):
        """设置窗口位置"""
        screen = QApplication.primaryScreen().geometry()
        x, y = 0, 0

        if self.position == "top-right":
            x = screen.width() - self.width - 20
            y = 20
        elif self.position == "top-left":
            x = 20
            y = 20
        elif self.position == "bottom-right":
            x = screen.width() - self.width - 20
            y = screen.height() - self.max_height - 20
        elif self.position == "bottom-left":
            x = 20
            y = screen.height() - self.max_height - 20

        self.move(x, y)

    def paintEvent(self, event):
        """绘制事件，绘制半透明背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制半透明背景
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

    def mousePressEvent(self, event):
        """鼠标按下事件，用于拖动"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.is_dragging = True
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件，用于拖动"""
        if event.buttons() == Qt.LeftButton and self.is_dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.is_dragging = False
        event.accept()

    def show_streaming(self, question: str, text: str):
        """
        流式显示文本

        Args:
            question: 问题
            text: 当前已生成的文本
        """
        # 更新问题
        if not self.isVisible():
            self.current_question = question
            self.question_text.setText(question)
            self.show()
            self.activateWindow()

        # 实时显示原始文本
        self.answer_text.setText(text)
        # 滚动到底部
        self.answer_text.verticalScrollBar().setValue(
            self.answer_text.verticalScrollBar().maximum()
        )

    def show_answer(self, question: str, answer_data):
        """
        显示最终格式化答案

        Args:
            question: 问题
            answer_data: 答案数据（FormattedAnswer 或 dict）
        """
        # 更新问题
        self.current_question = question
        self.question_text.setText(question)

        # 更新答案
        if hasattr(answer_data, 'answer'):
            # FormattedAnswer 对象
            self.answer_text.setText(answer_data.answer)

            # 更新关键点
            if answer_data.key_points:
                key_points_str = "\n".join([f"• {point}" for point in answer_data.key_points])
                self.key_points_text.setText(key_points_str)
            else:
                self.key_points_text.setText("无关键点")

            # 更新代码示例
            if answer_data.code_example:
                self.code_text.setText(answer_data.code_example)
                self.code_label.show()
                self.code_text.show()
            else:
                self.code_label.hide()
                self.code_text.hide()

        elif isinstance(answer_data, dict):
            # 字典格式
            self.answer_text.setText(answer_data.get('answer', ''))

            key_points = answer_data.get('key_points', [])
            if key_points:
                key_points_str = "\n".join([f"• {point}" for point in key_points])
                self.key_points_text.setText(key_points_str)
            else:
                self.key_points_text.setText("无关键点")

            code = answer_data.get('code_example')
            if code:
                self.code_text.setText(code)
                self.code_label.show()
                self.code_text.show()
            else:
                self.code_label.hide()
                self.code_text.hide()
        else:
            # 字符串格式
            self.answer_text.setText(str(answer_data))

        # 显示窗口
        self.show()
        self.activateWindow()

    def toggle(self):
        """切换显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()

    def clear(self):
        """清空内容"""
        self.question_text.setText("")
        self.answer_text.setText("")
        self.key_points_text.setText("")
        self.code_text.setText("")
        self.code_label.hide()
        self.code_text.hide()

    def closeEvent(self, event):
        """关闭事件"""
        self.closed.emit()
        event.accept()
