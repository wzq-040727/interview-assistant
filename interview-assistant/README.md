# 面试练习助手

一款面试练习工具，用于技术面试准备。通过 API 语音识别实时捕捉面试官问题，调用 AI 生成答案，以透明悬浮窗形式显示。

## 功能特性

- ✅ 实时语音识别（API 模式）
- ✅ 智能过滤无关内容
- ✅ AI 答案生成（完整答案 + 关键点 + 代码示例）
- ✅ 透明悬浮窗（屏幕共享时不可见）
- ✅ 快捷键控制（Ctrl + B）
- ✅ 配置文件管理

## 系统要求

- Windows 10/11
- Python 3.9+
- 网络连接（API 调用）

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/wzq-040727/interview-assistant.git
cd interview-assistant
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置 API：
编辑 `config/settings.yaml`，填入你的 API Key。

## 使用方法

1. 启动程序：
```bash
python src/main.py
```

2. 打开腾讯会议

3. 按 `Ctrl + B` 显示/隐藏悬浮窗

4. 面试官提问时，系统自动识别并显示答案

## 配置说明

配置文件位置：`config/settings.yaml`

```yaml
# API 配置
ai:
  base_url: "https://token-plan-cn.xiaomimimo.com/v1"
  api_key: "your-api-key"
  model: "gpt-4"

# 快捷键配置
ui:
  hotkey: "ctrl+b"
```

## 目录结构

```
interview-assistant/
├── src/
│   ├── main.py              # 主程序入口
│   ├── audio/               # 音频捕获模块
│   ├── recognition/         # 语音识别模块
│   ├── ai/                  # AI 答案生成模块
│   ├── ui/                  # 界面显示模块
│   └── utils/               # 工具模块
├── tests/                   # 测试文件
├── config/                  # 配置文件
├── requirements.txt         # 依赖列表
└── README.md                # 项目说明
```

## 许可证

MIT License
