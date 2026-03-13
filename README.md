# IntelliKnow KMS - AI 驱动的知识管理系统（核心服务）

## 📋 项目简介
本项目是 IntelliKnow KMS 的**核心服务**，提供文档解析、向量检索、意图分类等 AI 能力，并通过 API 对外提供服务。

## 📋 项目概述
本项目是一个基于 AI 的知识管理系统，**分为两个独立的部分**：
1. **IntelliKnow-KMS** - 核心服务（包含飞书机器人）
2. **teams_bot** - Teams 机器人（独立项目）

两者通过 API 通信，可以独立部署和运行。

## ✨ 核心功能
- 📄 **文档驱动知识库**：支持 PDF/DOCX/TXT 上传，自动解析并存入向量库
- 🎯 **意图分类**：使用 Qwen 模型将用户问题分类为 HR/Legal/Finance/General
- 🔍 **语义搜索**：基于 ChromaDB 的向量检索，准确找到相关信息
- 📊 **管理后台**：Streamlit 提供的可视化界面，支持文档管理、查询分析
- 🔌 **API 接口**：为前端机器人（Teams/飞书）提供统一的查询接口

## 🛠️ 技术栈
- **后端框架**：FastAPI
- **管理后台**：Streamlit
- **向量数据库**：ChromaDB
- **大语言模型**：通义千问 (Qwen)
- **前端机器人**：独立项目（见下方说明）

## 📁 项目结构

├── IntelliKnow-KMS/ # 核心服务（本仓库）
│ ├── README.md # 核心服务说明
│ ├── AI_USAGE.md # AI 使用反思
│ ├── api.py # KMS 主服务 (端口8000)
│ ├── app.py # Streamlit 后台 (端口8501)
│ ├── feishu_ws.py # 飞书机器人
│ ├── kb/ # 知识库模块
│ ├── orchestrator/ # 意图分类模块
│ └── test_data/ # 测试文档
│
└── teams_bot/ # Teams 机器人（需单独克隆）
├── README.md # Teams 机器人说明
├── src/ # 源代码
│ ├── app.py
│ └── config.py
└── .env # 环境配置

## 🚀 快速开始

## 第一部分：IntelliKnow-KMS（核心服务）+ 飞书机器人

### 环境要求
- Python 3.10+
- Conda（推荐）或 venv

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/ZenengSun/IntelliKnow-KMS.git
   cd IntelliKnow-KMS

2. **创建并激活环境**
    `conda create -n intelliknow python=3.10 -y`
    `conda activate intelliknow`

3. **安装依赖**
    `pip install -r requirements.txt`

4. **配置环境变量**
    `cp .env.local .env`
    编辑 .env 文件：
    ```python
    # 通义千问配置
    QWEN_API_KEY=你的阿里云API密钥
    QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
    # 飞书配置
    FEISHU_APP_ID=你的飞书应用App ID
    FEISHU_APP_SECRET=你的飞书应用App Secret
    ```

5. **创建测试数据**
    `python create_test_data.py`

### 运行服务

1. **启动 KMS 主服务**
    `uvicorn api:app --reload --host 0.0.0.0 --port 8000`

2. **启动 Streamlit 管理后台**
    `streamlit run app.py `
    访问 http://localhost:8501

3. **启动飞书机器人**
    `python feishu_ws.py`

## 第二部分：teams_bot（Teams 机器人）

- **仓库地址**：[teams-bot](https://github.com/ZenengSun/teams-bot)
- https://github.com/ZenengSun/teams-bot.git

### ✨ 功能
- 🤖 在 Microsoft Teams 中接收用户消息
- 🔌 调用 IntelliKnow-KMS 的 API
- 📤 返回意图分类和知识库回答


### 🛠️ 技术栈
- 框架：Microsoft 365 Agents SDK
- 语言：Python
- 依赖：aiohttp, microsoft-teams-api

### 🚀 核心服务启动步骤
**前置条件**
- ✅ IntelliKnow-KMS 核心服务必须已启动（端口8000）
- ✅ Azure 账号（已创建 Bot 资源）
- ✅ Teams 开发者账号

1. **进入项目目录**
    `cd teams_bot`

2. **创建并激活环境（独立环境）**
    # 使用 venv（推荐）
    `python -m venv venv`
    `venv\Scripts\activate`

    # 或使用 conda（与核心服务环境隔离）
    `conda create -n teams_bot python=3.10 -y`
    `conda activate teams_bot`

3. **安装依赖**
    `pip install aiohttp python-dotenv microsoft-teams-api`

4. **配置环境变量**
    编辑 .env 文件：
    CLIENT_ID=你的Azure Bot应用ID
    CLIENT_SECRET=你的Azure Bot密码

5. **修改 KMS API 地址**
    打开 src/app.py，找到并修改：
    KMS_API_URL = "http://你的KMS服务IP:8000/query"
    # 例如：KMS_API_URL = "http://192.168.1.100:8000/query"

6. **启动 Teams 机器人**
    `cd src`
    `python app.py`
`
7. **在 VS Code 中调试**
    - 按 F5
    - 选择 Debug in Playground
    - 在 Playground 中发送消息测试

## 🔌 API 接口说明（核心服务）
1. **健康检查**
    `GET http://localhost:8000/health`

2. **文档上传**
    `POST http://localhost:8000/upload`
    Content-Type: multipart/form-data
    file: (PDF/DOCX/TXT文件)

3. **查询接口（供机器人调用）**
    `POST http://localhost:8000/query`
    ```json
    Content-Type: application/json
    {
        "query": "年假有多少天？",
        "platform": "feishu"  # 或 "teams"
    }
    ```
4. **返回示例**
    ```json
    {
    "query": "年假有多少天？",
    "intent": {
        "intent": "HR",
        "confidence": 0.95,
        "reason": "问题涉及年假，属于人力资源范畴"
    },
    "response": "根据员工手册：\n- 入职满1年：5天带薪年假\n- 入职满3年：10天带薪年假",
    "sources": [
        {
        "filename": "hr_policy.txt",
        "score": 0.89
        }
    ]
    }
    ```
    

## 🧪 测试用例

1. **HR 问题**
- "年假有多少天？"
- "病假需要什么证明？"

2. **财务问题**
- "出差住宿标准是多少？"
- "报销流程是什么？"

3. **法务问题**
- "合同有效期多久？"
- "保密协议违约金多少？"

## 📜 许可证
MIT

