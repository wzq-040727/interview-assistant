"""
答案生成模块
格式化和优化 AI 生成的答案
"""

import re
from typing import Optional, Dict, Generator
from dataclasses import dataclass


@dataclass
class FormattedAnswer:
    """格式化的答案"""
    question: str  # 问题复述
    answer: str  # 完整答案
    key_points: list  # 关键点
    code_example: Optional[str]  # 代码示例
    raw_text: str  # 原始文本


class AnswerFormatter:
    """答案格式化器"""

    def __init__(self):
        """初始化答案格式化器"""
        # 各部分的标题模式
        self.section_patterns = {
            'question': [
                r'(?:问题复述|问题|题目)[：:]\s*(.*?)(?=\n(?:完整答案|答案|解答)|\Z)',
            ],
            'answer': [
                r'(?:答案|完整答案|解答)[：:]\s*(.*?)(?=\n关键点[：:]|\Z)',
            ],
            'key_points': [
                r'(?:关键点|要点|重点)[：:]\s*(.*?)(?=\n代码示例[：:]|\Z)',
            ],
            'code': [
                r'(?:代码示例|代码)[：:]\s*(.*?)(?=\Z)',
            ]
        }

    def format(self, question: str, raw_answer: str) -> FormattedAnswer:
        """格式化答案"""
        extracted_question = self._extract_section(raw_answer, 'question') or question
        extracted_answer = self._extract_section(raw_answer, 'answer') or raw_answer
        extracted_key_points = self._extract_key_points(raw_answer)
        extracted_code = self._extract_code(raw_answer)

        return FormattedAnswer(
            question=extracted_question.strip(),
            answer=extracted_answer.strip(),
            key_points=extracted_key_points,
            code_example=extracted_code,
            raw_text=raw_answer
        )

    def _extract_section(self, text: str, section: str) -> Optional[str]:
        """提取指定部分"""
        patterns = self.section_patterns.get(section, [])
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_key_points(self, text: str) -> list:
        """提取关键点"""
        key_points = []

        # 尝试提取带编号的关键点
        patterns = [
            r'[•·]\s*(.*?)(?=\n[•·]|\n\n|\Z)',
            r'[-*]\s*(.*?)(?=\n[-*]|\n\n|\Z)',
            r'\d+[.、]\s*(.*?)(?=\n\d+[.、]|\n\n|\Z)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                key_points.extend([m.strip() for m in matches if m.strip()])
                break

        # 如果没有找到，尝试按行提取
        if not key_points:
            key_points_section = self._extract_section(text, 'key_points')
            if key_points_section:
                lines = key_points_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 5:
                        line = re.sub(r'^[•·\-*\d.、]+\s*', '', line)
                        if line:
                            key_points.append(line)

        return key_points[:5]

    def _extract_code(self, text: str) -> Optional[str]:
        """提取代码示例"""
        # 尝试提取代码块
        code_block_pattern = r'```[\w]*\n(.*?)```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 尝试提取代码部分
        code_section = self._extract_section(text, 'code')
        if code_section:
            code_lines = []
            for line in code_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    code_lines.append(line)
            if code_lines:
                return '\n'.join(code_lines)

        return None


class AnswerGenerator:
    """答案生成器"""

    def __init__(self, ai_client, formatter: Optional[AnswerFormatter] = None):
        """初始化答案生成器"""
        self.ai_client = ai_client
        self.formatter = formatter or AnswerFormatter()

    def generate(self, question: str, context: Optional[str] = None) -> Optional[FormattedAnswer]:
        """生成答案（非流式）"""
        raw_answer = self.ai_client.generate_answer(question, context)

        if not raw_answer:
            return None

        formatted_answer = self.formatter.format(question, raw_answer)
        return formatted_answer

    def generate_stream(self, question: str, context: Optional[str] = None) -> Generator[str, None, FormattedAnswer]:
        """
        流式生成答案

        Args:
            question: 问题
            context: 上下文

        Yields:
            文本片段

        Returns:
            格式化的答案（通过 StopIteration.value）
        """
        full_text = ""
        for chunk in self.ai_client.generate_answer_stream(question, context):
            full_text += chunk
            yield chunk

        # 返回格式化的答案
        return self.formatter.format(question, full_text)

    def clear_context(self):
        """清空上下文"""
        self.ai_client.clear_history()


class AnswerGeneratorFactory:
    """答案生成器工厂"""

    @staticmethod
    def create(ai_client) -> AnswerGenerator:
        """创建答案生成器"""
        return AnswerGenerator(ai_client)
