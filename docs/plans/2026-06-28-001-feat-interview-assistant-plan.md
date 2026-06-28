# 面试练习助手 - 技术实现计划

**日期：** 2026-06-28
**状态：** 已完成
**类型：** feat
**来源：** `docs/brainstorms/2026-06-28-interview-assistant-requirements.md`

---

## 摘要

构建一个面试练习助手，用于技术面试准备。通过 API 语音识别实时捕捉面试官问题，调用 AI 生成答案，以透明悬浮窗形式显示。支持快捷键控制、智能过滤无关内容。

---

## 问题框架

**目标用户：** 准备技术面试的开发者
**核心问题：** 面试时需要快速理解问题并组织答案
**解决方案：** 实时语音识别 + AI 答案生成 + 透明悬浮窗

---

## 需求追溯

| 需求 ID | 描述 | 实现单元 |
|---------|------|----------|
| R1 | 实时语音识别 | U1, U2 |
| R2 | 智能过滤无关内容 | U3 |
| R3 | AI 答案生成 | U4 |
| R4 | 透明悬浮窗显示 | U5 |
| R5 | 快捷键控制 | U6 |
| R6 | 配置管理 | U7 |

---

## 关键技术决策

### KTD1: 语音识别方案
**决策：** 使用 API 语音识别（OpenAI 兼容）
**理由：**
- 不需要本地运行大型模型
- 识别准确率高
- 支持中文
- 依赖用户的专属 API 服务

**替代方案：**
- 本地 Whisper：需要下载模型，占用磁盘空间，CPU/GPU 要求高

### KTD2: 音频捕获方案
**决策：** 使用 pyaudio + Windows WASAPI 环回捕获
**理由：**
- 可以捕获系统音频输出
- 区分系统音频和麦克风输入
- 实时处理，不保存录音

**替代方案：**
- 虚拟音频设备：需要额外安装，配置复杂

### KTD3: 界面框架
**决策：** 使用 PyQt5/6
**理由：**
- 支持透明窗口
- 跨平台（虽然目前只支持 Windows）
- 社区成熟，文档完善

**替代方案：**
- Tkinter：透明支持有限
- Electron：资源占用大

### KTD4: 问题检测方案
**决策：** 规则引擎 + 关键词匹配
**理由：**
- 实现简单，响应快
- 可配置，易于调整
- 不需要额外的 ML 模型

**替代方案：**
- NLP 模型：增加复杂度，响应慢

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    面试练习助手                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  音频捕获   │  │  语音识别   │  │  问题检测   │     │
│  │  (pyaudio)  │→│  (API)      │→│  (规则引擎) │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                      ↓  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  界面显示   │←│  答案格式   │←│  AI 答案    │     │
│  │  (PyQt)     │  │  (模板)     │  │  (API)      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 实现单元

### U1. 项目结构搭建

**目标：** 创建项目目录结构和基础文件

**依赖：** 无

**文件：**
- `interview-assistant/` - 项目根目录
- `interview-assistant/requirements.txt` - 依赖列表
- `interview-assistant/README.md` - 项目说明
- `interview-assistant/config/settings.yaml` - 配置文件

**方法：**
- 创建标准 Python 项目结构
- 编写 requirements.txt（pyaudio, PyQt5, pynput, requests, pyyaml）
- 创建基础配置文件模板

**测试场景：**
- 项目结构完整
- 依赖可正确安装
- 配置文件可正确加载

**验证：** 项目结构创建成功，依赖安装无报错

---

### U2. 音频捕获模块

**目标：** 实时捕获系统音频输出

**依赖：** U1

**文件：**
- `interview-assistant/src/audio/capture.py` - 音频捕获类
- `interview-assistant/src/audio/processor.py` - 音频处理
- `interview-assistant/tests/test_audio.py` - 测试文件

**方法：**
- 使用 pyaudio 打开 WASAPI 环回流
- 实时读取音频数据
- 转换为 16kHz, 16bit, mono 格式
- 提供音频帧回调接口

**技术设计：**
```python
class AudioCapture:
    def __init__(self, sample_rate=16000, channels=1):
        self.pa = pyaudio.PyAudio()
        self.stream = None

    def start(self, callback):
        # 打开 WASAPI 环回流
        # 实时调用 callback(audio_frame)
        pass

    def stop(self):
        # 停止捕获，释放资源
        pass
```

**测试场景：**
- 成功打开系统音频流
- 正确捕获音频数据
- 音频格式转换正确
- 资源释放无泄漏

**验证：** 能够捕获系统音频并输出到回调函数

---

### U3. 语音识别与问题检测模块

**目标：** 将音频转换为文本，识别面试官问题，过滤无关内容

**依赖：** U2

**文件：**
- `interview-assistant/src/recognition/whisper_engine.py` - API 语音识别
- `interview-assistant/src/recognition/question_detector.py` - 问题检测
- `interview-assistant/tests/test_recognition.py` - 测试文件

**方法：**
- 调用 API 语音识别接口
- 实现问题检测规则引擎
- 过滤短句、寒暄、指令性语言
- 识别疑问句和技术关键词

**问题检测规则：**
```python
class QuestionDetector:
    def __init__(self):
        self.ignore_patterns = ["你好", "稍等", "下一个"]
        self.question_keywords = ["什么", "如何", "为什么", "请解释", "请描述"]

    def is_question(self, text):
        # 过滤短句
        if len(text) < 10:
            return False
        # 过滤寒暄
        for pattern in self.ignore_patterns:
            if pattern in text:
                return False
        # 检查是否是问题
        for keyword in self.question_keywords:
            if keyword in text:
                return True
        return False
```

**测试场景：**
- 正确识别中文语音
- 过滤短句（< 10字）
- 过滤寒暄（"你好"、"稍等"）
- 识别疑问句（包含"什么"、"如何"等）
- 识别技术关键词

**验证：** 能够正确识别面试官问题，过滤无关内容

---

### U4. AI 答案生成模块

**目标：** 根据问题生成完整答案

**依赖：** U3

**文件：**
- `interview-assistant/src/ai/client.py` - API 客户端
- `interview-assistant/src/ai/answer_generator.py` - 答案生成
- `interview-assistant/tests/test_ai.py` - 测试文件

**方法：**
- 实现 OpenAI 兼容 API 客户端
- 设计 prompt 模板，生成结构化答案
- 支持多轮对话上下文
- 格式化答案（问题复述、答案、关键点、代码示例）

**API 调用：**
```python
class AIClient:
    def __init__(self, base_url, api_key, model):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    def generate_answer(self, question, context=None):
        # 调用 API 生成答案
        # 返回格式化答案
        pass
```

**Prompt 模板：**
```
你是一个技术面试助手。请根据面试官的问题，提供完整的答案。

问题：{question}

请按以下格式回答：
1. 问题复述：简要复述问题
2. 完整答案：详细解答
3. 关键点：列出 3-5 个关键点
4. 代码示例：如果适用，提供代码示例
```

**测试场景：**
- 成功调用 API
- 答案格式正确（包含问题复述、答案、关键点、代码）
- 支持多轮对话
- 响应时间 < 3 秒

**验证：** 能够根据问题生成高质量、格式化的答案

---

### U5. 透明悬浮窗模块

**目标：** 创建透明悬浮窗显示答案

**依赖：** U1

**文件：**
- `interview-assistant/src/ui/overlay.py` - 悬浮窗类
- `interview-assistant/src/ui/theme.py` - 主题样式
- `interview-assistant/tests/test_ui.py` - 测试文件

**方法：**
- 使用 PyQt5 创建透明窗口
- 设置窗口属性：无边框、置顶、透明
- 实现内容显示区域
- 支持窗口拖动

**窗口属性：**
```python
class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool  # 不在任务栏显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
```

**显示布局：**
```
┌─────────────────────────────────────┐
│  [问题] 面试官的问题                │
├─────────────────────────────────────┤
│  [答案]                             │
│  完整的答案内容...                  │
│                                     │
│  [关键点]                           │
│  • 要点 1                           │
│  • 要点 2                           │
│                                     │
│  [代码示例]                         │
│  def example():                     │
│      pass                           │
└─────────────────────────────────────┘
```

**测试场景：**
- 窗口成功创建
- 窗口透明、无边框、置顶
- 内容正确显示
- 窗口可拖动
- 屏幕共享时不可见

**验证：** 悬浮窗正常显示，屏幕共享时不可见

---

### U6. 快捷键控制模块

**目标：** 实现 `Ctrl + B` 快捷键控制悬浮窗显示/隐藏

**依赖：** U5

**文件：**
- `interview-assistant/src/utils/hotkey.py` - 快捷键处理
- `interview-assistant/tests/test_hotkey.py` - 测试文件

**方法：**
- 使用 pynput 监听全局快捷键
- `Ctrl + B` 切换悬浮窗显示/隐藏
- 支持自定义快捷键配置

**快捷键监听：**
```python
from pynput import keyboard

class HotkeyManager:
    def __init__(self, toggle_callback):
        self.toggle_callback = toggle_callback
        self.listener = keyboard.Listener(
            on_press=self.on_press
        )

    def on_press(self, key):
        # 检测 Ctrl + B
        if key == keyboard.Key.ctrl_l:
            self.ctrl_pressed = True
        elif key == keyboard.KeyCode.from_char('b') and self.ctrl_pressed:
            self.toggle_callback()

    def start(self):
        self.listener.start()
```

**测试场景：**
- 快捷键正确监听
- `Ctrl + B` 触发显示/隐藏
- 不影响其他快捷键
- 资源正确释放

**验证：** 快捷键控制正常工作

---

### U7. 配置管理模块

**目标：** 管理用户配置

**依赖：** U1

**文件：**
- `interview-assistant/src/utils/config.py` - 配置管理
- `interview-assistant/tests/test_config.py` - 测试文件

**方法：**
- 使用 YAML 格式配置文件
- 支持默认配置和用户自定义配置
- 配置项验证

**配置结构：**
```yaml
audio:
  source: "system"
  sample_rate: 16000
  channels: 1

recognition:
  api_url: "https://token-plan-cn.xiaomimimo.com/v1"
  api_key: "your-api-key"
  language: "zh"

ai:
  base_url: "https://token-plan-cn.xiaomimimo.com/v1"
  api_key: "your-api-key"
  model: "gpt-4"
  max_tokens: 2000

ui:
  hotkey: "ctrl+b"
  opacity: 0.9
  font_size: 14
  position: "top-right"

filter:
  min_question_length: 10
  ignore_patterns:
    - "你好"
    - "稍等"
    - "下一个"
```

**测试场景：**
- 配置文件正确加载
- 默认值正确填充
- 配置验证正确
- 支持热更新

**验证：** 配置管理正常工作

---

### U8. 主程序集成

**目标：** 集成所有模块，实现完整功能

**依赖：** U2, U3, U4, U5, U6, U7

**文件：**
- `interview-assistant/src/main.py` - 主程序入口
- `interview-assistant/tests/test_integration.py` - 集成测试

**方法：**
- 初始化所有模块
- 实现音频捕获 → 语音识别 → 问题检测 → 答案生成 → 界面显示流程
- 添加系统托盘图标
- 实现优雅退出

**主程序流程：**
```python
def main():
    # 加载配置
    config = load_config()

    # 初始化模块
    audio = AudioCapture(config.audio)
    recognizer = SpeechRecognizer(config.recognition)
    detector = QuestionDetector(config.filter)
    ai = AIClient(config.ai)
    overlay = OverlayWindow(config.ui)
    hotkey = HotkeyManager(overlay.toggle)

    # 启动音频捕获
    audio.start(on_audio_frame)

    # 启动快捷键监听
    hotkey.start()

    # 显示系统托盘
    show_tray_icon()

    # 运行主循环
    app.exec_()

def on_audio_frame(frame):
    # 语音识别
    text = recognizer.recognize(frame)

    # 问题检测
    if detector.is_question(text):
        # 生成答案
        answer = ai.generate_answer(text)

        # 显示答案
        overlay.show_answer(text, answer)
```

**测试场景：**
- 所有模块正确初始化
- 完整流程正常运行
- 系统托盘图标显示
- 优雅退出无报错

**验证：** 完整功能正常工作

---

## 输出结构

```
interview-assistant/
├── src/
│   ├── main.py
│   ├── audio/
│   │   ├── capture.py
│   │   └── processor.py
│   ├── recognition/
│   │   ├── whisper_engine.py
│   │   └── question_detector.py
│   ├── ai/
│   │   ├── client.py
│   │   └── answer_generator.py
│   ├── ui/
│   │   ├── overlay.py
│   │   └── theme.py
│   └── utils/
│       ├── config.py
│       └── hotkey.py
├── tests/
│   ├── test_audio.py
│   ├── test_recognition.py
│   ├── test_ai.py
│   ├── test_ui.py
│   ├── test_hotkey.py
│   ├── test_config.py
│   └── test_integration.py
├── config/
│   └── settings.yaml
├── requirements.txt
└── README.md
```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| API 不可用 | 高 | 提供离线模式（本地模型） |
| 音频捕获失败 | 高 | 提供详细权限设置指南 |
| 识别准确率低 | 中 | 优化 prompt，支持手动修正 |
| 界面显示异常 | 中 | 提供多种窗口模式选择 |

---

## 测试场景

### 单元测试
- 音频捕获模块测试
- 语音识别模块测试
- 问题检测模块测试
- AI 答案生成模块测试
- 界面显示模块测试
- 快捷键控制模块测试
- 配置管理模块测试

### 集成测试
- 完整流程测试
- 多模块协作测试
- 异常处理测试

### 用户验收测试
- 腾讯会议实际测试
- 屏幕共享不可见测试
- 性能测试（CPU、内存占用）

---

## 里程碑

### Phase 1：基础框架（1周）
- [ ] U1: 项目结构搭建
- [ ] U2: 音频捕获模块
- [ ] U5: 透明悬浮窗基础

### Phase 2：核心功能（1周）
- [ ] U3: 语音识别与问题检测
- [ ] U4: AI 答案生成
- [ ] U6: 快捷键控制

### Phase 3：完善优化（1周）
- [ ] U7: 配置管理
- [ ] U8: 主程序集成
- [ ] 测试与优化

### Phase 4：测试发布（1周）
- [ ] 功能测试
- [ ] 性能优化
- [ ] 文档编写

---

## 延迟到后续工作

- 支持更多面试平台（Zoom、Teams）
- 支持离线模式（本地 Whisper 模型）
- 答案评分功能
- 学习进度分析
- 录音保存功能

---

## 来源与研究

- 需求文档：`docs/brainstorms/2026-06-28-interview-assistant-requirements.md`
- 参考产品：Cuemate
- Whisper 文档：https://github.com/openai/whisper
- PyQt 文档：https://www.riverbankcomputing.com/static/Docs/PyQt5/

---

**下一步：** 使用 `/ce-work` 开始实现此计划。
