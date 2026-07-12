# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

面试练习助手：通过麦克风/系统音频实时捕获面试官问题，调用 AI 生成结构化答案（完整答案 + 关键点 + 代码示例），以透明悬浮窗显示。Windows 平台专用。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动程序
python src/main.py

# 无测试、无 lint 配置
```

## 架构

数据流管道：`音频捕获 → 音频处理(静音检测) → 语音识别 → 问题检测 → AI答案生成 → 悬浮窗显示`

### 线程模型

- **主线程**：Qt 事件循环 + UI 渲染
- **音频捕获线程**：`AudioCapture._capture_loop` 持续读取音频帧
- **AI 生成线程**：每次检测到问题时临时创建，通过 `AnswerSignal`（`pyqtSignal`）将结果安全传回主线程更新 UI

关键：UI 更新必须在主线程，跨线程通信使用 PyQt 信号机制（`answer_signal.answer_ready` / `stream_update`），不要直接在子线程操作 Qt 控件。

### 模块职责

| 模块 | 核心类 | 职责 |
|------|--------|------|
| `src/audio/capture.py` | `AudioCapture` | PyAudio 音频捕获，支持 WASAPI 环回（系统音频）和麦克风两种模式 |
| `src/audio/processor.py` | `AudioProcessor`, `AudioConverter` | 静音检测、语音段切分、WAV 格式转换 |
| `src/recognition/whisper_engine.py` | `SpeechRecognizer` | 基于 `SpeechRecognition` 库的语音转文字（Google/Sphinx 引擎） |
| `src/recognition/question_detector.py` | `QuestionDetector` | 基于关键词+正则模式的问题检测，过滤无关语音 |
| `src/ai/client.py` | `AIClient` | OpenAI 兼容 API 客户端，支持流式/非流式调用 |
| `src/ai/answer_generator.py` | `AnswerGenerator`, `AnswerFormatter` | 调用 AI 生成答案并提取关键点、代码块 |
| `src/ui/overlay.py` | `OverlayWindow` | PyQt5 透明悬浮窗，两列布局（左：关键点+代码，右：完整答案） |
| `src/utils/config.py` | `Config` | YAML 配置加载，支持点号分隔的 key 访问（如 `ai.base_url`） |
| `src/utils/hotkey.py` | `HotkeyManager` | pynput 全局快捷键监听 |
| `src/main.py` | `InterviewAssistant` | 主类，初始化所有模块并编排管道 |

### 配置

配置文件：`config/settings.yaml`。`Config` 类将 YAML 内容与 `DEFAULT_CONFIG` 深度合并。配置项按 section（`audio`/`recognition`/`ai`/`ui`/`filter`）组织。

## 开发注意事项

- 项目仅支持 Windows（依赖 `pyaudiowpatch`、WASAPI 环回、系统托盘）
- AI API 使用 OpenAI 兼容协议（`/chat/completions`），endpoint 和 key 在 `config/settings.yaml` 的 `ai` section
- `AnswerFormatter` 用正则从 AI 响应中提取结构化数据，格式依赖 `AIClient.system_prompt` 中定义的输出模板
- 悬浮窗使用 `Qt.Tool` 标志，屏幕共享时不可见（设计意图）
- 代码风格：中文注释和 print 输出，类型注解使用 `typing` 模块
