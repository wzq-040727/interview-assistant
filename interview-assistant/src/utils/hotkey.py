"""
快捷键控制模块
监听全局快捷键，控制悬浮窗显示/隐藏
"""

from pynput import keyboard
from typing import Callable, Optional
import threading


class HotkeyManager:
    """快捷键管理器"""

    def __init__(self, toggle_callback: Callable[[], None], hotkey: str = "ctrl+b"):
        """
        初始化快捷键管理器

        Args:
            toggle_callback: 切换回调函数
            hotkey: 快捷键组合（如 "ctrl+b"）
        """
        self.toggle_callback = toggle_callback
        self.hotkey = hotkey.lower()

        # 解析快捷键
        self.modifiers, self.key = self._parse_hotkey(hotkey)

        # 状态
        self.pressed_keys = set()
        self.listener: Optional[keyboard.Listener] = None
        self.is_running = False

    def _parse_hotkey(self, hotkey: str) -> tuple:
        """
        解析快捷键字符串

        Args:
            hotkey: 快捷键字符串（如 "ctrl+b"）

        Returns:
            (modifiers, key) 元组
        """
        parts = hotkey.lower().split('+')
        modifiers = set()
        key = None

        for part in parts:
            part = part.strip()
            if part in ('ctrl', 'control'):
                modifiers.add('ctrl')
            elif part in ('alt',):
                modifiers.add('alt')
            elif part in ('shift',):
                modifiers.add('shift')
            elif part in ('win', 'super', 'cmd'):
                modifiers.add('win')
            else:
                key = part

        return modifiers, key

    def _get_key_name(self, key) -> Optional[str]:
        """
        获取按键名称

        Args:
            key: 按键对象

        Returns:
            按键名称
        """
        try:
            if hasattr(key, 'char'):
                return key.char.lower() if key.char else None
            elif hasattr(key, 'name'):
                return key.name.lower()
            else:
                return str(key).lower().replace('key.', '')
        except Exception:
            return None

    def _is_modifier(self, key_name: str) -> bool:
        """
        判断是否是修饰键

        Args:
            key_name: 按键名称

        Returns:
            是否是修饰键
        """
        return key_name in ('ctrl', 'alt', 'shift', 'win', 'control')

    def _check_hotkey(self) -> bool:
        """
        检查当前按下的键是否匹配快捷键

        Returns:
            是否匹配
        """
        # 检查修饰键
        for modifier in self.modifiers:
            if modifier not in self.pressed_keys:
                return False

        # 检查主键
        if self.key and self.key not in self.pressed_keys:
            return False

        return True

    def _on_press(self, key):
        """
        按键按下事件

        Args:
            key: 按键对象
        """
        key_name = self._get_key_name(key)
        if key_name:
            self.pressed_keys.add(key_name)

            # 检查快捷键
            if self._check_hotkey():
                # 清除按键状态，避免重复触发
                self.pressed_keys.clear()
                # 调用回调
                if self.toggle_callback:
                    threading.Thread(target=self.toggle_callback, daemon=True).start()

    def _on_release(self, key):
        """
        按键释放事件

        Args:
            key: 按键对象
        """
        key_name = self._get_key_name(key)
        if key_name:
            self.pressed_keys.discard(key_name)

    def start(self) -> bool:
        """
        启动快捷键监听

        Returns:
            是否成功启动
        """
        if self.is_running:
            return True

        try:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.start()
            self.is_running = True
            print(f"快捷键监听已启动（{self.hotkey}）")
            return True

        except Exception as e:
            print(f"启动快捷键监听失败：{e}")
            return False

    def stop(self):
        """停止快捷键监听"""
        self.is_running = False

        if self.listener:
            try:
                self.listener.stop()
                self.listener.join(timeout=1)
            except Exception:
                pass
            self.listener = None

        self.pressed_keys.clear()
        print("快捷键监听已停止")

    def update_hotkey(self, new_hotkey: str):
        """
        更新快捷键

        Args:
            new_hotkey: 新的快捷键组合
        """
        self.hotkey = new_hotkey.lower()
        self.modifiers, self.key = self._parse_hotkey(new_hotkey)
        print(f"快捷键已更新为：{new_hotkey}")

    def __del__(self):
        """析构函数"""
        self.stop()


class HotkeyManagerFactory:
    """快捷键管理器工厂"""

    @staticmethod
    def create(config: dict, toggle_callback: Callable[[], None]) -> HotkeyManager:
        """
        根据配置创建快捷键管理器

        Args:
            config: 配置字典
            toggle_callback: 切换回调函数

        Returns:
            HotkeyManager 实例
        """
        hotkey = config.get('hotkey', 'ctrl+b')
        return HotkeyManager(toggle_callback, hotkey)
