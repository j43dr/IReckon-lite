# IReckon 3.0 Lite

[English](./README_LITE.md) | [中文](./README_ZH.md)

## 简介

IReckon 3.0 精简版 - 不包含 AI 模型权重的轻量版本。**不包含游戏功能**。

### 与完整版的区别

| 功能 | 完整版 | 精简版 |
|------|--------|--------|
| AI 模型权重 (~69MB) | ✅ | ❌ |
| 规则推理 | ✅ | ✅ |
| 量化支持 | ✅ | ✅ |
| 跨平台工具 (20+) | ✅ | ✅ |
| 游戏适配器 | ✅ | ❌ |
| Agent 系统 | ✅ | ✅ |

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动

```bash
# 后端 API
python main.py

# Web 界面 (新终端)
streamlit run ui/app.py
```

### 访问

- API 文档: http://localhost:8000/docs
- Web 界面: http://localhost:8501

### 一键启动 (Windows)

直接双击 `run.bat`

## 功能特性

### 🛠️ 跨平台工具系统
- 剪贴板、通知、音量、电池
- 网络、存储、进程
- 命令行执行、文件读写
- 截图、传感器

### 🤖 Agent 系统
- 学习者 (从错误学习)
- 执行者 (任务执行)
- 审查者 (效率/正确性)
- 内容过滤
- 创意生成

### 🌐 网络学习循环
- 白名单过滤
- 沙箱验证
- 冲突检测

### 🧠 世界模型
- 规则推理 (内置)
- 量化支持 (INT8/INT4/FP16)

## 配置

### 基本配置
编辑 `config/config.yaml`:

```yaml
system:
  name: IReckon
  version: 3.0
  language: zh-CN

server:
  host: 0.0.0.0
  port: 8000
```

### 添加 AI 实例
通过 API:
```bash
curl -X POST http://localhost:8000/api/ai-instances \
  -H "Content-Type: application/json" \
  -d '{"id": "openai","name": "GPT-4","endpoint": "https://api.openai.com/v1","model": "gpt-4"}'
```

## 添加权重（可选）

如需使用神经网络模型：
1. 从完整版获取 `lewm_full.pt`
2. 放置到 `app/world_model/weights/lewm_full.pt`
3. 重启应用

或设置环境变量:
```bash
# Windows
set LEWM_WEIGHTS_PATH=C:\path\to\weights.pt

# Linux/macOS
export LEWM_WEIGHTS_PATH=/path/to/weights
```

## 开发

```bash
# 运行测试
python test_all.py

# 启动 UI
streamlit run ui/app.py --server.port 8501

# 后台运行
python main.py > output.log 2>&1 &
```

## 项目结构

```
IReckon-3.0-lite/
├── app/                 # 核心代码
│   ├── core/           # 核心模块
│   ├── agents/         # Agent系统
│   ├── llm/           # LLM集成
│   ├── tools/          # 工具系统
│   ├── web/           # Web API
│   └── world_model/    # 世界模型
├── ui/                 # Streamlit界面
│   ├── components/     # 组件
│   └── utils/          # 工具函数
├── config/             # 配置文件
│   ├── config.yaml
│   ├── prompts/        # 提示词模板
│   └── themes/         # 主题
├── main.py             # 入口
├── run.bat             # 启动脚本
├── requirements.txt    # 依赖
└── README_LITE.md    # 本文档
```

## 故障排除

### 端口占用
```bash
# 查找占用进程
netstat -ano | findstr "8000"

# 结束进程
taskkill /PID <进程ID> /F
```

### 权限问题
以管理员身份运行终端

### 模块导入错误
```bash
pip install -r requirements.txt
```

## 技术栈

- **后端**: FastAPI, uvicorn
- **前端**: Streamlit
- **数据库**: SQLite (aiosqlite)
- **LLM集成**: LangGraph, LiteLLM
- **工具**: psutil, aiofiles, cryptography

## 许可证

MIT License - 详见 [LICENSE](./LICENSE) 文件

## 问题反馈

如有问题，请提交 Issue: https://github.com/your-repo/IReckon/issues