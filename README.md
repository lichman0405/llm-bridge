# LLM Bridge: Universal API Adapter

[中文](./README-cn.md)

LLM Bridge is a powerful, self-hosted API translation layer that allows clients designed for a specific Large Language Model (LLM) API, such as the claude-code CLI, to seamlessly connect to and utilize a wide variety of other LLM backends like DeepSeek, GPT-4o, and local models via Ollama.

It acts as a "universal adapter," receiving requests in one format (e.g., Anthropic's), translating them into a standardized internal format, and then forwarding them to any configured backend model. This provides ultimate flexibility without needing to change your favorite client-side tools.

---

## ✨ Features

- **Universal Compatibility**: Enables clients built for the Anthropic API (like claude-code) to use any OpenAI-compatible model.

- **Configuration-Driven**: No hardcoding. Add, remove, or modify supported models by simply editing the `models.yml` and `.env` files.

- **Centralized API Key Management**: Securely store all your LLM API keys in a single `.env` file on your server, never exposing them on the client side.

- **Default Model Override**: Set a global default model for all requests, simplifying usage by eliminating the need for command-line flags.

- **Extensible Architecture**: Easily add support for new LLMs or even new API formats (e.g., Gemini native) by creating new adapters.

- **Containerized & Portable**: Runs anywhere with Docker, ensuring a consistent and isolated environment.

---

## 🚀 Quick Start

Follow these steps to get your LLM Bridge service running in minutes.

### Prerequisites

- Docker and Docker Compose
- The client tool you wish to use (e.g., claude-code CLI)
- API keys for the LLM services you want to connect to (e.g., DeepSeek, OpenAI)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd llm-bridge
```

### 2. Configure Models (`models.yml`)

Open the `models.yml` file. This file acts as a routing table. Define all the models you want to make available. The key is the model name you will use in your client, and the values point to the required configuration variables.

**Example models.yml:**

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

### 3. Configure Secrets (`.env`)

Create a `.env` file in the project root by copying the provided example. This file will store all your secret API keys and base URLs. **This file should never be committed to version control.**

**Example .env:**

```bash
# .env
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
OPENAI_BASE_URL="https://api.openai.com/v1"

DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"

OLLAMA_API_KEY="ollama"
OLLAMA_BASE_URL="http://localhost:11434/v1"
```

### 4. Build and Run the Service

Use Docker Compose to build the container and run the service in the background.

```bash
docker-compose up --build -d
```

Your bridge service is now running! By default, it's accessible at `http://localhost:8000` (or the port you configured in `docker-compose.yml`).

---

## 🛠️ Usage

### For the claude-code CLI

This is the primary use case. Configure your client-side terminal environment to redirect claude-code's requests to your bridge service.

1. Open a new terminal window.
2. Set the required environment variables:

```bash
# Point the API endpoint to your bridge service
export ANTHROPIC_BASE_URL="http://<your-server-ip>:<port>/anthropic"

# Use a dummy API key to trigger the correct login mode
export ANTHROPIC_API_KEY="sk-this-is-a-bridge"
```

Replace `<your-server-ip>:<port>` with your bridge's actual address (e.g., `localhost:8000`).

3. Start using claude:

- With a default model set on the server:

```bash
claude "Hello, what can you do?"
```

- To specify a different model from `models.yml`:

```bash
claude -m "gpt-4o" "Explain the theory of relativity."
```

### For Other OpenAI-Compatible Clients

The bridge also exposes a standard OpenAI-compatible endpoint. For any client that supports custom OpenAI endpoints, use the following settings:

- **API Base URL**: `http://<your-server-ip>:<port>/v1`
- **API Key**: Any of the API keys you have configured in your `.env` file (e.g., your DeepSeek key).
- **Model Name**: Any of the model names defined in your `models.yml`.

---

