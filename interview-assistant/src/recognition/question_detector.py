"""
问题检测模块
识别面试官的问题，过滤无关内容
"""

import re
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """检测结果"""
    is_question: bool
    question_text: str
    confidence: float
    reason: str


class QuestionDetector:
    """问题检测器"""

    def __init__(self, min_length: int = 10, max_length: int = 500,
                 ignore_patterns: Optional[List[str]] = None,
                 question_keywords: Optional[List[str]] = None):
        """
        初始化问题检测器

        Args:
            min_length: 最小问题长度
            max_length: 最大问题长度
            ignore_patterns: 忽略的模式列表
            question_keywords: 问题关键词列表
        """
        self.min_length = min_length
        self.max_length = max_length

        # 默认忽略模式
        self.ignore_patterns = ignore_patterns or [
            "你好", "稍等", "下一个", "开始", "结束",
            "可以了", "好的", "嗯", "哦", "对"
        ]

        # 默认问题关键词
        self.question_keywords = question_keywords or [
            "什么", "如何", "为什么", "请解释", "请描述",
            "请实现", "请设计", "请编写", "请写", "怎么做",
            "原理", "区别", "优缺点", "实现", "设计",
            "解释", "描述", "说明", "分析", "比较"
        ]

        # 疑问词模式
        self.question_patterns = [
            r'什么\w{0,4}是',  # 什么是...
            r'如何\w{0,4}实现',  # 如何实现...
            r'为什么\w{0,4}会',  # 为什么会...
            r'怎么\w{0,4}做',  # 怎么做...
            r'请\w{0,2}解释',  # 请解释...
            r'请\w{0,2}描述',  # 请描述...
            r'请\w{0,2}设计',  # 请设计...
            r'请\w{0,2}实现',  # 请实现...
            r'请\w{0,2}编写',  # 请编写...
            r'请\w{0,2}写',  # 请写...
        ]

    def detect(self, text: str) -> DetectionResult:
        """
        检测文本是否是问题

        Args:
            text: 待检测的文本

        Returns:
            DetectionResult 检测结果
        """
        if not text:
            return DetectionResult(
                is_question=False,
                question_text="",
                confidence=0.0,
                reason="空文本"
            )

        text = text.strip()

        # 检查长度
        if len(text) < self.min_length:
            return DetectionResult(
                is_question=False,
                question_text=text,
                confidence=0.0,
                reason=f"文本过短（{len(text)} < {self.min_length}）"
            )

        if len(text) > self.max_length:
            return DetectionResult(
                is_question=False,
                question_text=text,
                confidence=0.0,
                reason=f"文本过长（{len(text)} > {self.max_length}）"
            )

        # 检查是否匹配忽略模式
        for pattern in self.ignore_patterns:
            if pattern in text:
                # 如果文本只包含忽略模式，则过滤
                if len(text) <= len(pattern) + 5:
                    return DetectionResult(
                        is_question=False,
                        question_text=text,
                        confidence=0.0,
                        reason=f"匹配忽略模式：{pattern}"
                    )

        # 检查是否包含问题关键词
        keyword_score = self._check_keywords(text)
        pattern_score = self._check_patterns(text)

        # 综合评分
        total_score = max(keyword_score, pattern_score)

        if total_score > 0.3:
            return DetectionResult(
                is_question=True,
                question_text=text,
                confidence=total_score,
                reason="检测到问题特征"
            )

        # 默认认为是问题（面试场景中，大部分语音都是问题）
        return DetectionResult(
            is_question=True,
            question_text=text,
            confidence=0.5,
            reason="默认识别为问题"
        )

    def _check_keywords(self, text: str) -> float:
        """
        检查问题关键词

        Args:
            text: 文本

        Returns:
            匹配分数（0.0 - 1.0）
        """
        matched_keywords = []
        for keyword in self.question_keywords:
            if keyword in text:
                matched_keywords.append(keyword)

        if not matched_keywords:
            return 0.0

        # 匹配的关键词越多，分数越高
        score = min(len(matched_keywords) * 0.3, 1.0)
        return score

    def _check_patterns(self, text: str) -> float:
        """
        检查问题模式

        Args:
            text: 文本

        Returns:
            匹配分数（0.0 - 1.0）
        """
        for pattern in self.question_patterns:
            if re.search(pattern, text):
                return 0.8

        return 0.0

    def add_ignore_pattern(self, pattern: str):
        """
        添加忽略模式

        Args:
            pattern: 忽略模式
        """
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)

    def add_question_keyword(self, keyword: str):
        """
        添加问题关键词

        Args:
            keyword: 问题关键词
        """
        if keyword not in self.question_keywords:
            self.question_keywords.append(keyword)


class QuestionDetectorFactory:
    """问题检测器工厂"""

    @staticmethod
    def create(config: dict) -> QuestionDetector:
        """
        根据配置创建问题检测器

        Args:
            config: 配置字典

        Returns:
            QuestionDetector 实例
        """
        return QuestionDetector(
            min_length=config.get('min_question_length', 10),
            max_length=config.get('max_question_length', 500),
            ignore_patterns=config.get('ignore_patterns'),
            question_keywords=config.get('question_keywords')
        )
