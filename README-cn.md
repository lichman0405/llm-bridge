# LLM Bridge: 通用大模型API桥接工具

[英文](./README.md)

LLM Bridge 是一个强大的、可自托管的API翻译层。它允许为特定大模型API（如 claude-code CLI）设计的客户端，无缝连接并使用其他各种大模型后端，例如 DeepSeek、GPT-4o，或通过Ollama运行的本地模型。

它扮演着一个“万能转换插头”的角色，能接收一种格式的请求（例如Anthropic格式），将其翻译成统一的内部标准格式，然后再转发给任何已配置的后端模型。这为您提供了极致的灵活性，而无需更换您最喜欢的客户端工具。

---

## ✨ 功能特性

- **通用兼容性**: 让为Anthropic API构建的客户端（如 claude-code）能够使用任何兼容OpenAI的模型。

- **配置驱动**: 零硬编码。通过简单地编辑 `models.yml` 和 `.env` 文件，即可添加、删除或修改支持的模型。

- **集中管理API密钥**: 将您所有大模型的API密钥安全地存储在服务器端的单个 `.env` 文件中，绝不暴露在客户端。

- **默认模型覆盖**: 可为所有请求设置一个全局默认模型，无需在命令行中反复指定，简化日常使用。

- **可扩展架构**: 通过创建新的适配器，可以轻松地为新的大模型甚至新的API格式（如原生的Gemini）添加支持。

- **容器化与可移植性**: 借助Docker，可在任何地方运行，确保了环境的一致性和隔离性。

---

## 🚀 快速开始

按照以下步骤，在几分钟内启动并运行您的LLM Bridge服务。

### 环境准备

- Docker 和 Docker Compose
- 您希望使用的客户端工具（例如 claude-code CLI）
- 您希望连接的大模型服务的API密钥（例如 DeepSeek, OpenAI）

### 1. 克隆仓库

```bash
git clone <your-repository-url>
cd llm-bridge
```

### 2. 配置模型 (`models.yml`)

打开 `models.yml` 文件。此文件扮演着路由表的角色。在这里定义所有您希望使用的模型。键（key）是您将在客户端中使用的模型名称，而值（value）则指向所需的配置变量。

**models.yml 示例:**

```yaml
# models.yml
gpt-4o:
  adapter: OpenAICompatibleAdapter
  api_key_name: OPENAI_API_KEY
  base_url_name: OPENAI_BASE_URL

deepseek-chat:
  adapter: OpenAICompatibleAdapter
  api_key_name: DEEPSEEK_API_KEY
  base_url_name: DEEPSEEK_BASE_URL

llama3:
  adapter: OpenAICompatibleAdapter
  api_key_name: OLLAMA_API_KEY
  base_url_name: OLLAMA_BASE_URL
```

### 3. 配置密钥 (`.env`)

在项目根目录下，通过复制示例来创建一个 `.env` 文件。此文件将存储您所有的机密API密钥和基础URL。**请绝对不要将此文件提交到任何版本控制系统。**

**.env 示例:**

```bash
# .env
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
OPENAI_BASE_URL="https://api.openai.com/v1"

DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"

OLLAMA_API_KEY="ollama"
OLLAMA_BASE_URL="http://localhost:11434/v1"
```

### 4. 构建并运行服务

使用 Docker Compose 来构建容器镜像，并在后台运行服务。

```bash
docker-compose up --build -d
```

您的桥接服务现已成功运行！默认情况下，您可以通过 `http://localhost:8000` 访问它（或您在 `docker-compose.yml` 中配置的端口）。

---

## 🛠️ 使用方法

### 针对 claude-code CLI

这是最主要的使用场景。配置您的客户端终端环境，将 claude-code 的请求重定向到您的桥接服务。

1. 打开一个新的终端窗口。
2. 设置所需的环境变量：

```bash
# 将API端点指向您的桥接服务
export ANTHROPIC_BASE_URL="http://<your-server-ip>:<port>/anthropic"

# 使用一个“伪造”的API密钥来触发正确的登录模式
export ANTHROPIC_API_KEY="sk-this-is-a-bridge"
```

请将 `<your-server-ip>:<port>` 替换为您桥接服务的实际地址（例如 `localhost:8000`）。

3. 开始使用 claude：

- 使用服务器上配置的默认模型：

```bash
claude "你好，你都会做什么？"
```

- 临时指定 `models.yml` 中的其他模型：

```bash
claude -m "gpt-4o" "请解释一下相对论。"
```

### 针对其他兼容OpenAI的客户端

本桥接工具也提供了一个标准的、兼容OpenAI的端点。对于任何支持自定义OpenAI端点的客户端，请使用以下设置：

- **API Base URL**: `http://<your-server-ip>:<port>/v1`
- **API Key**: 您在 `.env` 文件中配置的任何一个API密钥（例如您的DeepSeek密钥）。
- **Model Name**: 您在 `models.yml` 中定义的任何一个模型名称。

---

