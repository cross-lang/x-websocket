# x-websocket

基于 WebSocket 协议的 LLM 实时交互应用，采用 FastAPI 构建，提供全双工低延迟的流式对话能力，支持 OpenAI / Kimi / DeepSeek 等多模型提供商。

## 核心特征

- **WebSocket 全双工通信** — 基于 RFC 6455 标准，单一 TCP 连接支持长时间会话，毫秒级实时交互
- **JWT 认证** — 安全的用户认证与授权机制，保障连接安全
- **多模型支持** — OpenAI、Kimi、DeepSeek、Mock、Local LLM，可扩展接入新提供商
- **流式响应** — 异步生成器实时推送 LLM 生成内容，避免阻塞等待
- **房间广播** — 支持房间消息广播、个人消息和连接状态管理
- **CLI 工具** — 内置 `x-websocket` 命令行工具，提供服务启动、令牌生成、健康检查等管理命令
- **配置驱动** — 基于 Pydantic Settings 的 `.env` 配置管理，类型安全，开箱即用

## 项目结构

```
x-websocket/
├── src/                        # 源码根目录
│   ├── __init__.py             # 包元数据与版本信息
│   ├── __main__.py             # CLI 入口（Click 命令组）
│   ├── server.py               # FastAPI 应用，WebSocket 端点与消息路由
│   ├── auth/                   # 认证模块
│   │   ├── __init__.py
│   │   └── jwt_auth.py         # JWT 令牌生成与验证
│   ├── connection/             # 连接管理
│   │   ├── __init__.py
│   │   └── manager.py          # WebSocket 连接管理器（注册/注销/广播）
│   ├── core/                   # 核心基础设施
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings 配置类
│   │   └── logger.py           # 日志配置
│   ├── handlers/               # 消息处理器
│   │   ├── __init__.py
│   │   ├── base.py             # 处理器抽象基类
│   │   ├── chat.py             # 聊天消息处理器
│   │   ├── status.py           # 状态查询处理器
│   │   └── stream.py           # 流式消息处理器
│   ├── llm/                    # LLM 提供商接口
│   │   ├── __init__.py
│   │   ├── base.py             # LLM 抽象基类与工厂模式
│   │   ├── openai.py           # OpenAI 客户端
│   │   ├── kimi.py             # Kimi（月之暗面）客户端
│   │   ├── deepseek.py         # DeepSeek 客户端
│   │   ├── mock.py             # Mock LLM（开发测试用）
│   │   └── local.py            # 本地 LLM 支持（transformers）
│   └── models/                 # 数据模型
│       ├── __init__.py
│       └── message.py          # Pydantic 消息模型（Chat / Stream / Status）
├── examples/                   # 示例代码
│   └── basic_client.py         # 基础 WebSocket 客户端示例
├── tests/                      # 测试目录
├── pyproject.toml              # 项目配置与依赖声明
├── uv.lock                     # 依赖锁定文件
├── .env.example                # 环境变量示例
├── LICENSE                     # MIT 许可证
└── README.md
```

## 系统架构

### 系统分层架构

```
┌─────────────────────────────────────────────────────┐
│                    客户端层 (Client)                  │
│         WebSocket Client / CLI / 浏览器               │
└──────────────────────┬──────────────────────────────┘
                       │ ws:// / wss://
                       ▼
┌─────────────────────────────────────────────────────┐
│                   接入层 (Gateway)                    │
│              FastAPI + CORS Middleware                │
│              WebSocket Endpoint (/ws)                │
└──────────┬───────────┬───────────────┬──────────────┘
           │           │               │
           ▼           ▼               ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│   认证模块    │ │ 消息路由  │ │  连接管理器   │
│  JWT Auth    │ │ Dispatch  │ │  Connection   │
└──────┬───────┘ └─────┬────┘ │  Manager      │
       │               │      └──────────────┘
       │    ┌──────────┼──────────┐
       │    ▼          ▼          ▼
       │ ┌──────┐ ┌────────┐ ┌───────┐
       │ │ Chat │ │ Stream │ │Status │    业务处理器层
       │ │Handler│ │Handler │ │Handler│
       │ └──┬───┘ └───┬────┘ └───┬───┘
       │    │         │          │
       │    ▼         ▼          ▼
       │ ┌──────────────────────────┐
       │ │      LLM 工厂模式        │     模型服务层
       │ │      (LLM Factory)       │
       │ └─┬────┬─────┬─────┬────┬─┘
       │   ▼    ▼     ▼     ▼    ▼
       │ ┌────┐┌────┐┌─────┐┌───┐┌─────┐
       │ │OAI││Kimi││DS   ││Mck││Local│
       │ └───┘└────┘└─────┘└───┘└─────┘
       │
┌──────┴──────────────────────────────────────────────┐
│                  基础设施层 (Infra)                    │
│     Config (Pydantic Settings)  │  Logger  │  CLI    │
└─────────────────────────────────────────────────────┘
```

### 核心功能业务流程

```
                              客户端
                                │
                    ┌───────────┼───────────┐
                    │   1. WebSocket 握手    │
                    │   (HTTP Upgrade)       │
                    └───────────┬───────────┘
                                │
                    ┌───────────┼───────────┐
                    │   2. 发送 JWT Token     │
                    │   {"token": "xxx"}     │
                    └───────────┬───────────┘
                                │
                     ┌──────────▼──────────┐
                     │   3. 服务器验证令牌   │
                     │   JWT Auth Service   │
                     └──────────┬──────────┘
                          验证通过?
                       ╱          ╲
                     是             否
                     │              │
              ┌──────▼──────┐  ┌───▼────┐
              │ 4. 连接确认  │  │ 关闭连接│
              │ 注册到管理器 │  │ 返回错误│
              └──────┬──────┘  └────────┘
                     │
          ┌──────────┼──────────┐
          │   5. 双向消息通信     │
          └──────────┼──────────┘
                     │
        ┌────────┬───┴───┬────────┐
        ▼        ▼       ▼        ▼
   ┌────────┐┌────────┐┌──────┐┌─────┐
   │  chat  ││ stream ││status││ ping│
   │ 聊天   ││ 流式   ││ 状态 ││心跳 │
   └───┬────┘└───┬────┘└──┬───┘└──┬──┘
       │         │        │       │
       ▼         ▼        ▼       ▼
   ┌─────────────────────────────────┐
   │      LLM Factory → Provider     │
   │   (OpenAI / Kimi / DeepSeek /…) │
   └───────────────┬─────────────────┘
                   │ 流式/非流式响应
                   ▼
              返回客户端
```

### 模块依赖关系

```
server.py ──► auth/jwt_auth.py
         ──► connection/manager.py
         ──► models/message.py
         ──► handlers/chat.py ──► llm/base.py (LLMFactory)
         ──► handlers/stream.py ──► llm/base.py
         ──► handlers/status.py ──► llm/base.py
                                ──► llm/openai.py
                                ──► llm/kimi.py
                                ──► llm/deepseek.py
                                ──► llm/mock.py
                                ──► llm/local.py
core/config.py ──► (Pydantic Settings, .env)
core/logger.py ──► (Python logging)
__main__.py ──► server.py, core/config.py (CLI 入口)
```

## 快速开始

### 环境要求


| 项目     | 要求                                        |
| ------ | ----------------------------------------- |
| Python | >= 3.11                                   |
| 包管理器   | [uv](https://docs.astral.sh/uv/)（推荐）或 pip |
| 操作系统   | Windows / Linux / macOS                   |


### 1. 克隆项目

```bash
git clone https://gitee.com/yeyushilai/x-websocket.git
cd x-websocket
```

### 2. 安装依赖

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
# Linux / macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装项目依赖
uv pip install -e .

# 安装开发依赖（可选，用于测试和代码检查）
uv pip install -e ".[dev]"
```

### 3. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env
```

编辑 `.env` 文件，至少需要配置以下项：


| 变量                 | 说明                                          | 是否必须           |
| ------------------ | ------------------------------------------- | -------------- |
| `JWT_SECRET`       | JWT 签名密钥                                    | **必须**         |
| `LLM_PROVIDER`     | 默认 LLM 提供商（openai / kimi / deepseek / mock） | 可选，默认 `openai` |
| `OPENAI_API_KEY`   | OpenAI API 密钥                               | 按需配置           |
| `KIMI_API_KEY`     | Kimi API 密钥                                 | 按需配置           |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥                             | 按需配置           |


完整配置项参见 [.env.example](.env.example)。

### 4. 生成 JWT 令牌

```bash
x-websocket token test_user_001
```

### 5. 启动服务

```bash
# 默认启动（0.0.0.0:8765）
x-websocket serve

# 自定义主机和端口
x-websocket serve --host 127.0.0.1 --port 8000

# 开发模式（热重载）
x-websocket serve --reload
```

### 6. 运行示例客户端

```bash
# 确保服务器已启动
python examples/basic_client.py
```

### 常用命令


| 命令                            | 说明               |
| ----------------------------- | ---------------- |
| `x-websocket serve`           | 启动 WebSocket 服务器 |
| `x-websocket config`          | 查看当前配置           |
| `x-websocket health`          | 健康检查             |
| `x-websocket token <user_id>` | 为指定用户生成 JWT 令牌   |
| `pytest tests/`               | 运行测试             |
| `ruff check src/`             | 代码检查             |
| `black src/`                  | 代码格式化            |


## 技术栈


| 分类            | 技术                                                                                                                                     |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Web 框架**    | [FastAPI](https://fastapi.tiangolo.com/) — 高性能异步 Web 框架                                                                                |
| **ASGI 服务器**  | [Uvicorn](https://www.uvicorn.org/) — 基于 uvloop 的 ASGI 服务器                                                                             |
| **WebSocket** | [websockets](https://websockets.readthedocs.io/) — Python WebSocket 库                                                                  |
| **数据校验**      | [Pydantic](https://docs.pydantic.dev/) / [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — 数据模型与配置管理 |
| **LLM SDK**   | [OpenAI Python SDK](https://github.com/openai/openai-python) — 多模型提供商统一调用                                                              |
| **认证**        | [PyJWT](https://pyjwt.readthedocs.io/) + [cryptography](https://cryptography.io/) — JWT 令牌生成与验证                                        |
| **HTTP 客户端**  | [httpx](https://www.python-httpx.org/) — 异步 HTTP 客户端                                                                                   |
| **CLI 工具**    | [Click](https://click.palletsprojects.com/) — 命令行界面构建                                                                                  |
| **终端输出**      | [Rich](https://rich.readthedocs.io/) — 终端富文本格式化                                                                                        |
| **包管理**       | [uv](https://docs.astral.sh/uv/) — 高性能 Python 包管理器                                                                                     |
| **代码质量**      | [Ruff](https://docs.astral.sh/ruff/) / [Black](https://black.readthedocs.io/) / [mypy](https://mypy.readthedocs.io/)                   |


## WebSocket 连接与通信流程

**连接建立流程：**

```
客户端                                     服务器
   |                                          |
   |---- WebSocket 握手请求 (HTTP Upgrade) --->|
   |                                          |
   |<-- WebSocket 握手响应 (101 Switching) ----|
   |                                          |
   |---- 认证消息 (JWT Token) ---------------->|
   |                                          |
   |<-- 连接确认消息 --------------------------|
   |                                          |
   |==== 全双工消息通信 =======================|
```

**详细步骤：**

1. **建立连接**：客户端通过 WebSocket 协议连接到 `ws://localhost:8765/ws` 端点
2. **发送认证消息**：连接成功后立即发送包含 JWT 令牌的认证消息
  ```json
   {"token": "your_jwt_token_here"}
  ```
3. **接收连接确认**：服务器验证令牌后返回连接成功消息
4. **双向通信**：支持三种消息类型的实时交互：
  - `chat` — 聊天消息（支持房间广播）
  - `stream` — 流式生成请求（实时返回 LLM 生成内容）
  - `status` — 状态查询（任务状态跟踪）

### 消息格式示例

**流式请求：**

```json
{
  "type": "stream",
  "prompt": "请介绍一下WebSocket协议",
  "model": "openai"
}
```

**聊天消息：**

```json
{
  "type": "chat",
  "content": "你好，这是一个测试消息",
  "room_id": "room_001"
}
```

**状态查询：**

```json
{
  "type": "status",
  "task_id": "task_123456",
  "action": "query"
}
```

### 支持的 LLM 提供商


| 提供商      | 标识         | 说明                            |
| -------- | ---------- | ----------------------------- |
| OpenAI   | `openai`   | OpenAI 兼容 API（含 Azure OpenAI） |
| Kimi     | `kimi`     | 月之暗面 Moonshot API             |
| DeepSeek | `deepseek` | DeepSeek API                  |
| Mock     | `mock`     | 模拟 LLM，用于开发测试                 |
| Local    | `local`    | 本地部署 LLM（需安装 transformers）    |


## API 文档

启动服务器后，访问以下地址：


| 文档类型            | 地址                                                                       |
| --------------- | ------------------------------------------------------------------------ |
| Swagger UI（交互式） | [http://localhost:8765/docs](http://localhost:8765/docs)                 |
| ReDoc（只读）       | [http://localhost:8765/redoc](http://localhost:8765/redoc)               |
| OpenAPI JSON    | [http://localhost:8765/openapi.json](http://localhost:8765/openapi.json) |


## 配置说明

完整配置参见 [.env.example](.env.example)，核心配置项：


| 变量名                    | 说明         | 默认值                    |
| ---------------------- | ---------- | ---------------------- |
| `HOST`                 | 服务器主机      | `0.0.0.0`              |
| `PORT`                 | 服务器端口      | `8765`                 |
| `DEBUG`                | 调试模式       | `true`                 |
| `JWT_SECRET`           | JWT 密钥     | **必须设置**               |
| `JWT_ALGORITHM`        | JWT 算法     | `HS256`                |
| `TOKEN_EXPIRE_MINUTES` | 令牌过期时间（分钟） | `60`                   |
| `LLM_PROVIDER`         | 默认 LLM 提供商 | `openai`               |
| `LOG_LEVEL`            | 日志级别       | `INFO`                 |
| `LOG_FILE`             | 日志文件路径     | `logs/x_websocket.log` |


## 开发指南

### 添加新的 LLM 提供商

1. 在 `src/llm/` 目录下创建新文件，实现继承 `BaseLLM` 的客户端类
2. 实现 `generate_stream()`、`chat()` 和 `get_status()` 方法
3. 在 `LLMFactory` 中注册新提供商
4. 在 `src/core/config.py` 的 `Settings` 类中添加对应配置字段

### 运行测试

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行全部测试
pytest tests/

# 带覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

## 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

## 参考资料

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [WebSocket 协议 (RFC 6455)](https://datatracker.ietf.org/doc/html/rfc6455)
- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [uv 官方文档](https://docs.astral.sh/uv/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Uvicorn 官方文档](https://www.uvicorn.org/)

## 联系方式

- **作者**：John Young
- **邮箱**：[john.young@foxmail.com](mailto:john.young@foxmail.com)
- **Gitee**：[https://gitee.com/yeyushilai](https://gitee.com/yeyushilai)
- **GitHub**：[https://github.com/yeyushilai](https://github.com/yeyushilai)

