"""
配置管理模块
管理用户配置文件
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """配置管理类"""

    # 默认配置
    DEFAULT_CONFIG = {
        'audio': {
            'source': 'system',
            'sample_rate': 16000,
            'channels': 1,
            'chunk_size': 1024
        },
        'recognition': {
            'api_url': 'https://token-plan-cn.xiaomimimo.com/v1/audio/transcriptions',
            'api_key': 'your-api-key',
            'language': 'zh',
            'model': 'whisper-1'
        },
        'ai': {
            'base_url': 'https://token-plan-cn.xiaomimimo.com/v1',
            'api_key': 'your-api-key',
            'model': 'gpt-4',
            'max_tokens': 2000,
            'temperature': 0.7
        },
        'ui': {
            'hotkey': 'ctrl+b',
            'opacity': 0.9,
            'font_size': 14,
            'font_family': 'Microsoft YaHei',
            'position': 'top-right',
            'width': 400,
            'max_height': 600
        },
        'filter': {
            'min_question_length': 10,
            'max_question_length': 500,
            'ignore_patterns': [
                '你好', '稍等', '下一个', '开始', '结束',
                '可以了', '好的', '嗯', '哦', '对'
            ],
            'question_keywords': [
                '什么', '如何', '为什么', '请解释', '请描述',
                '请实现', '请设计', '请编写', '请写', '怎么做',
                '原理', '区别', '优缺点'
            ]
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        if config_path is None:
            # 默认路径：项目根目录下的 config/settings.yaml
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / 'config' / 'settings.yaml'

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self):
        """加载配置文件"""
        # 从默认配置开始
        self.config = self._deep_copy(self.DEFAULT_CONFIG)

        # 如果配置文件存在，加载并合并
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self.config = self._merge_config(self.config, user_config)
                print(f"配置已加载：{self.config_path}")
            except Exception as e:
                print(f"加载配置文件失败：{e}")
        else:
            # 如果配置文件不存在，创建默认配置
            self.save()
            print(f"已创建默认配置文件：{self.config_path}")

    def save(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            print(f"配置已保存：{self.config_path}")
        except Exception as e:
            print(f"保存配置文件失败：{e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔，如 'ai.base_url'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键（支持点号分隔）
            value: 配置值
        """
        keys = key.split('.')
        config = self.config

        # 导航到最后一级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置段

        Args:
            section: 段名称

        Returns:
            配置字典
        """
        return self.config.get(section, {})

    def _deep_copy(self, obj: Any) -> Any:
        """
        深拷贝对象

        Args:
            obj: 源对象

        Returns:
            拷贝后的对象
        """
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """
        合并配置

        Args:
            base: 基础配置
            override: 覆盖配置

        Returns:
            合并后的配置
        """
        result = self._deep_copy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = self._deep_copy(value)

        return result

    def reload(self):
        """重新加载配置"""
        self.load()

    def __str__(self) -> str:
        """字符串表示"""
        return yaml.dump(self.config, allow_unicode=True, default_flow_style=False)


class ConfigFactory:
    """配置工厂"""

    @staticmethod
    def create(config_path: Optional[str] = None) -> Config:
        """
        创建配置实例

        Args:
            config_path: 配置文件路径

        Returns:
            Config 实例
        """
        return Config(config_path)
