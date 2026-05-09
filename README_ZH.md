# IReckon 3.0 Lite

[English](./README_LITE.md) | 中文

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0Lite-blue" alt="版本">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-orange" alt="许可证">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Android-brightgreen" alt="平台">
</p>

## 🎯 简介

IReckon 3.0 精简版 - 轻量级 AI Agent 系统，不包含 AI 模型权重。

### 与完整版的区别

| 功能 | 完整版 | 精简版 |
|------|--------|--------|
| AI模型权重 | ✅ (69MB) | ❌ |
| 规则推理 | ✅ | ✅ |
| 量化支持 | ✅ | ✅ |
| 核心功能 | ✅ | ✅ |

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

### 2. 工具系统 (20+)

| 工具 | 功能 |
|------|------|
| 📋 剪贴板 | 读写系统剪贴板 |
| 🔔 通知 | 发送系统通知 |
| 🔊 音量 | 控制音量 |
| 🔋 电池 | 获取电池状态 |
| 🌐 网络 | 网络诊断 |
| 💾 存储 | 磁盘空间 |
| 📷 相机 | 拍照 |
| ⌨️ 键盘/鼠标 | 模拟输入 |
| 🖥️ Shell | 执行命令 |
| 🌐 网页 | 搜索/抓取 |

### 3. 游戏适配器

自动从网络教程学习游戏：
```python
from app.games.universal_adapter import learn_from_scratch

# 学习新游戏
adapter = await learn_from_scratch("游戏名", "https://教程链接")
```

### 4. 世界模型

支持规则推理：
```python
from app.world_model import predict_action

# 推理
result = await predict_action(state, action)
```

量化支持 (INT4/INT8/FP16):
```python
from app.world_model import quantize
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

## 🐛 常见问题

### 1. 端口被占用

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill <PID>
```

### 2. 依赖安装失败

```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 权限问题

```bash
# 以管理员身份运行
```

## 📄 许可证

MIT License

---

<p align="center">由 IReckon Team ❤️ 用心打造</p>