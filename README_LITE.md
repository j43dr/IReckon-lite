# IReckon 3.0 Lite

[English](./README_LITE.md) | [中文](./README_ZH.md)

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0Lite-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-orange" alt="license">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Android-brightgreen" alt="platform">
</p>

## 🎯 简介

IReckon 3.0 精简版 - 轻量级 AI Agent 系统，不包含 AI 模型权重。

### 核心特性

| 功能 | 说明 |
|------|------|
| 🤖 Agent系统 | 学习者、执行者、审查者等专业化 Agent |
| 🛠️ 工具系统 | 20+ 跨平台工具（剪贴板、通知、音量、电池、网络等）|
| 🎮 游戏适配器 | 从网络教程学习任意游戏 |
| 🌐 网络学习 | 带安全检查的持续学习循环 |
| 🧠 世界模型 | 规则推理（可选神经网络）|
| 📱 跨平台 | Windows / Linux / macOS / Android |

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动

```bash
python main.py
```

### 访问

- **API文档**: http://localhost:8000/docs
- **Web界面**: http://localhost:8501 (需另外启动 `streamlit run ui/app.py`)

## 📖 功能特性

### 1. Agent 系统

```
┌─────────────────┐
│   学习者 Agent   │ ← 从经验学习
└────────┬────────┘
         ↓
┌─────────────────┐
│   执行者 Agent   │ ← 执行任务
└────────┬────────┘
         ↓
┌─────────────────┐
│   审查者 Agent   │ ← 审查结果
└────────┬────────┘
         ↓
    └─→ 自我改进 ←┘
```

### 2. 工具系统

- 📋 剪贴板
- 🔔 通知
- 🔊 音量
- 🔋 电池
- 🌐 网络
- 💾 存储
- 📷 相机
- ⌨️ 键盘/鼠标
- 🖥️ Shell命令
- 🌐 网页搜索/抓取

### 3. 游戏适配器

从网络教程自动学习游戏：
```python
from app.games.universal_adapter import learn_from_scratch

# 学习新游戏
adapter = await learn_from_scratch("My Game", "https://example.com/tutorial")
```

### 4. 世界模型

支持规则推理和量化：

```python
from app.world_model import predict_action, quantize

# 推理
result = await predict_action(state, action)

# 量化 (INT4/INT8/FP16)
model = await quantize(model, bits=8)
```

## 🔧 配置

编辑 `config/config.yaml`：

```yaml
system:
  name: "IReckon"
  version: "3.0"

server:
  host: "0.0.0.0"
  port: 8000
```

## 📦 项目结构

```
IReckon-lite/
├── app/
│   ├── agents/         # Agent实现
│   ├── core/          # 核心模块
│   ├── engine/        # 任务引擎
│   ├── games/         # 游戏适配器
│   ├── llm/           # LLM集成
│   ├── tools/         # 工具系统
│   ├── vision/        # 视觉系统
│   ├── web/           # Web API
│   └── world_model/   # 世界模型
├── ui/                 # Streamlit界面
├── config/             # 配置文件
├── main.py             # 入口
├── run.bat             # 一键启动(Windows)
└── requirements.txt    # 依赖
```

## 🐛 问题排查

### 端口被占用

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### 依赖安装失��

```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 📄 许可证

MIT License

---

<p align="center">Made with ❤️ by IReckon Team</p>