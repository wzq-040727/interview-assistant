"""
主题样式模块
定义 UI 主题和样式
"""

from PyQt5.QtGui import QColor, QFont
from typing import Dict


class Theme:
    """主题类"""

    # 颜色定义
    COLORS = {
        'background': QColor(0, 0, 0, 180),
        'text': QColor(255, 255, 255),
        'question': QColor(255, 215, 0),  # 金色
        'answer': QColor(0, 191, 255),  # 深蓝色
        'key_point': QColor(144, 238, 144),  # 浅绿色
        'code': QColor(0, 255, 0),  # 绿色
        'separator': QColor(85, 85, 85),
        'border': QColor(85, 85, 85),
    }

    # 字体定义
    FONTS = {
        'title': QFont('Microsoft YaHei', 12, QFont.Bold),
        'content': QFont('Microsoft YaHei', 14),
        'code': QFont('Consolas', 13),
    }

    @classmethod
    def get_stylesheet(cls) -> str:
        """
        获取全局样式表

        Returns:
            CSS 样式字符串
        """
        return """
            QWidget {
                background-color: transparent;
            }

            QLabel {
                color: #FFFFFF;
            }

            QTextEdit {
                color: #FFFFFF;
                background-color: rgba(0, 0, 0, 150);
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }

            QTextEdit:focus {
                border: 1px solid #00BFFF;
            }
        """

    @classmethod
    def get_question_style(cls) -> str:
        """获取问题区域样式"""
        return "color: #FFD700; font-weight: bold;"

    @classmethod
    def get_answer_style(cls) -> str:
        """获取答案区域样式"""
        return "color: #FFFFFF;"

    @classmethod
    def get_key_point_style(cls) -> str:
        """获取关键点样式"""
        return "color: #90EE90;"

    @classmethod
    def get_code_style(cls) -> str:
        """获取代码样式"""
        return "color: #00FF00; background-color: rgba(0, 0, 0, 200); font-family: Consolas, monospace;"


class ThemeManager:
    """主题管理器"""

    def __init__(self):
        """初始化主题管理器"""
        self.current_theme = Theme
        self.custom_colors: Dict[str, QColor] = {}

    def set_color(self, name: str, color: QColor):
        """
        设置自定义颜色

        Args:
            name: 颜色名称
            color: 颜色值
        """
        self.custom_colors[name] = color

    def get_color(self, name: str) -> QColor:
        """
        获取颜色

        Args:
            name: 颜色名称

        Returns:
            颜色值
        """
        if name in self.custom_colors:
            return self.custom_colors[name]
        return self.current_theme.COLORS.get(name, QColor(255, 255, 255))

    def get_font(self, name: str) -> QFont:
        """
        获取字体

        Args:
            name: 字体名称

        Returns:
            字体对象
        """
        return self.current_theme.FONTS.get(name, QFont('Microsoft YaHei', 14))
