<p align="center">
  <img src="./docs/readme.md_banner.svg" alt="Trinity Agent Designer Banner" width="100%">
</p>

<p align="right">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License">
  </a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white" alt="Flask">
</p>

<p align="right">
  <img src="https://img.shields.io/badge/AI-Google%20Gemini-8E75B2?style=flat-square&logo=googlegemini&logoColor=white" alt="Gemini">
</p>

This is the python flask backend for Trinity, an AI agent designer. The goal of this project is the simple and convenient creation of AI agents that are capable of solving complex tasks and understanding complicated situations. All agents possess capabilities that can be executed as tools on your system. Trinity can create and process task sequences. You can use an API to control the system. 

However, we recommend using our [Angular frontend](https://github.com/negsi/trinity-angular).

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
  - [1. Clone or download repository](#1-clone-or-download-repository)
  - [2. Create a virtual environment (optional, but recommended)](#2-create-a-virtual-environment-optional-but-recommended)
  - [3. Install dependencies](#3-install-dependencies)
  - [4. Use MySQL-Server (Optional)](#4-use-mysql-server-optional)
  - [5. Install AI LLM dependencies](#5-install-ai-llm-dependencies)
  - [6. Create .env](#6-create-env)
  - [7. Install Database schema](#7-install-database-schema)
- [Running the Application](#running-the-application)
- [Agent Tools & Task Chains](#agent-tools--task-chains)
  - [Built-in Agent Tools](#built-in-agent-tools)
  - [Task Execution Workflow](#task-execution-workflow)
- [Agent Memory](#agent-memory)
  - [Configuration Options](#configuration-options)
- [Using the API](#using-the-api)
  - [Agent Endpoints](#agent)
  - [Agent Datasources](#agent-datasources)
  - [Chat & Execution Endpoints](#chat--execution-endpoints-apiv1chat)
- [Agent Examples](#agent-examples)

---

## Requirements

- Python 3.10 or newer  
- pip (Python Package Installer)  
- Optional: a virtual environment (recommended)

---

## Installation

### 1. Clone or download repository

```bash
git clone https://github.com/negsi/trinity-flask.git
cd trinity-flask
```

### 2. Create a virtual environment (optional, but recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Use MySQL-Server (Optional)

We currently persist data primarily to an `sqlite` database, but we also offer the option to use a MySQL server and provide a corresponding `docker-compose` configuration file for this purpose. If you prefer to use MySQL, then don't forget to install `pymsql`.

```bash
pip install pymysql
```

### 5. Install AI LLM dependencies

We currently work and test exclusively with Google Gemini, but we also implement OpenAI as LLM provider. The possibility of using other LLM providers and also support for locally working LLMs is planned. 

Depending on the provider, you may need to install a corresponding Python dependency.

```bash
pip install google-genai # for Gemini
pip install openai # for OpenAI
```

### 6. Create .env

```bash
cp .env.template .env
```

In `.env`, specify your AI provider, your preferred large language model, and the API token. If you plan to use image generation capabilities, configure the `IMAGE_GENERATOR_PROVIDER` (`gemini` or `openai`) and optionally specify `IMAGE_GENERATOR_MODEL`. If you want to use a MySQL-Server as storage backend, then add the necessary parameters there as well.

Optionally, configure your mail setup depending on your environment:

`Local Development (e.g., Mailpit):` Set `SMTP_SERVER=localhost` and `SMTP_PORT=1025`. Leave `SMTP_USER` and `SMTP_PASSWORD` empty.

`External Mail Provider:` Enter your SMTP credentials (`SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM`) to send emails via an authenticated server using TLS.

For enhanced web search capabilities, you can optionally configure Tavily:

**Web Search Provider:** Set `TAVILY_API_KEY` to your Tavily API token to enable deep, LLM-optimized web search results. If left unset, the web_search tool will automatically fall back to `DuckDuckGo` with zero configuration required.

### 7. Install Database schema

```bash
flask db upgrade
```

---

## Running the Application
Start serving the app via 
```bash
python run_app.py
```
If you want to use our MySQL Docker Compose configuration, then run the following command for starting the container.
```bash
docker compose -f docker-compose.mysql.yml up -d
```

If you want to recreate the database you can delete `instances/app.db` or run 
```bash
docker exec -it trinity_mysql \
  mysql -utrinity -ptrinity \
  -e "DROP DATABASE trinity; CREATE DATABASE trinity;"
```

---

## Agent Tools & Task Chains

Trinity agents execute complex web gathering, data processing, and analysis tasks by orchestrating specialized tools into multi-step execution plans (**Task Chains**).

### Built-in Agent Tools

1. **`fetch_url`**
   - **Purpose:** Fetches the raw text content of a specified web page or online document.
   - **Rules & Behavior:**
     - Processes exactly **one URL per execution step**.
     - Requires separate sequential steps when dealing with multiple URLs.
     - Does not invent placeholder URLs. To discover links on a page, the agent must first visit the target URL in step 1 to extract valid links.

2. **`message_llm`**
   - **Purpose:** Processes, summarizes, evaluates, translates, or structurally transforms retrieved data.
   - **Rules & Syntax:**
     - Uses step references to chain inputs from prior steps (e.g., using `[STEP_1]` as input for processing results obtained during step 1).
     - Strict placeholder syntax enforcement ensures reliable data flow between task steps.

3. **`write_file`**
   - **Purpose:** Writes or appends text content to a specified file within the active conversation workspace.
   - **Rules & Syntax:**
     - **`file_path`** (string, required): Relative path or filename (e.g., `summary.md` or `exports/data.json`).
     - **`content`** (string, required): The text payload to write. Supports step reference placeholders (e.g., `[STEP_2]`).
     - **`mode`** (string, optional): File write mode. Use `"w"` to overwrite or create a new file (default), or `"a"` to append to an existing file.
     - Files are automatically isolated and saved inside the active conversation directory.

4. **`send_email`**
   - **Purpose:** Sends an email message via local mail transfer agents (e.g., Postfix/Sendmail) or remote SMTP servers.
   - **Rules & Syntax:**
     - **`to_email`** (string, required): Target recipient email address.
     - **`subject`** (string, required): Subject line of the email.
     - **`body`** (string, required): The text or HTML body content. Supports step reference placeholders (e.g., `[STEP_3]`).
     - **`is_html`** (boolean, optional): Set to `true` if the body contains HTML markup. Defaults to `false`.
     - Automatically routes through local unauthenticated delivery or configured SMTP credentials via the application's `EmailService`.

5. **`generate_image`**
   - **Purpose:** Generates an image based on a detailed text prompt and saves it as a file inside the active conversation workspace.
   - **Rules & Syntax:**
     - **`prompt`** (string, required): A detailed and descriptive image prompt (preferably in English for optimal image generation quality).
     - **`filename`** (string, optional): Target filename (e.g., `scene.png` or `illustration.jpg`).
     - **`aspect_ratio`** (string, optional): Aspect ratio of the generated image. Supported values: `"1:1"` (default), `"16:9"`, `"9:16"`.

6. **`web_search`**
   - **Purpose:** Executes live web search queries to discover current information, links, and real-time market or news updates.
   - **Rules & Behavior:**
     - **`query`** (string, required): The search terms or research prompt to execute.
     - **Hybrid Provider Resolution:** Automatically selects the search backend based on environmental configuration:
       - **Tavily Search API:** Utilized when `TAVILY_API_KEY` is configured in `.env`. Provides LLM-optimized, structured search results and deep factual content.
       - **DuckDuckGo Search:** Functions as a zero-config, privacy-focused fallback provider when no API key is present.
     - Designed for initial discovery phases in multi-step task chains, providing actionable target URLs for subsequent `fetch_url` analysis.

### Task Execution Workflow

- **Internal Knowledge / Datasources:** For queries answerable directly via model knowledge or uploaded files (Knowledge Base), the agent responds immediately without triggering external tools.
- **External Web Processing:** For complex requests requiring web data (e.g., *"Read this web article and summarize the key findings"*), Trinity builds a structured JSON Task Chain executing a `fetch` $\rightarrow$ `process` pipeline.
- **Tool Fallback Handling:** If a user request demands capabilities beyond the available toolset, the agent explicitly informs the user about unexecutable requirements.

## Agent Memory

Trinity agents support configurable conversation memory, allowing you to tailor how past context is supplied to the LLM during chat sessions. Memory handling can be controlled globally via a master toggle or fine-tuned using filtering and truncation modes.

### Configuration Options

- **`memory_enabled`** (`boolean`, default: `true`)  
  Master switch for agent context retention. When set to `false`, the agent receives no past conversation history and treats every prompt as stateless.

- **`memory_mode`** (`string`, default: `"user_only"`)  
  Controls which messages are included in the historical context:
  - `"user_only"`: Filters out assistant responses, forwarding only past user prompts to optimize token usage while maintaining topic context.
  - `"all"`: Includes the full dialogue (both user prompts and assistant responses).

- **`memory_limit_type`** (`string`, default: `"all"`)  
  Determines how the chat history is truncated:
  - `"all"`: Keeps the complete conversation history without message-count capping.
  - `"message_count"`: Caps context retention to the most recent $N$ messages.

- **`memory_message_count`** (`integer`, default: `null`)  
  Defines the maximum number of recent messages retained when `memory_limit_type` is set to `"message_count"`.

---

### Example Memory Strategy

For lightweight execution or strict token budgets, set `memory_mode` to `"user_only"` combined with a restricted `memory_message_count`:

```json
{
  "memory_enabled": true,
  "memory_mode": "user_only",
  "memory_limit_type": "message_count",
  "memory_message_count": 10
}
``` 

### Using the API

The backend exposes a RESTful JSON API under the base path `/api/v1`. Below is the detailed endpoint documentation for managing agents, datasources, and chat interactions.

### Agents

<details>
<summary><code>POST</code> <strong>/api/v1/agents</strong> — Create a new agent</summary>

<br>

**Description:**  
Creates a new AI agent instance in the system.

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "name": "Research Assistant",
  "description": "An agent specialized in Web Search and Data Extraction",
  "system_prompt": "You are a helpful researcher. Extract useful facts from the given content.",
  "memory_enabled": true,
  "memory_mode": "user_only",
  "memory_limit_type": "message_count",
  "memory_message_count": 10
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | `string` | **Yes** | Agent name (1 - 100 characters) |
| `description` | `string` | No | Short description (max 500 characters) |
| `system_prompt` | `string` | No | Custom system instruction prompt for the LLM |
| `memory_enabled` | `boolean` | No | Master toggle to enable or disable agent conversation memory (Default: true) |
| `memory_mode` | `string` | No | Chat history filter: "user_only" or "all" (Default: "user_only") |
| `memory_limit_type` | `string` | No | History limiting mode: "all" or "message_count" (Default: "all") |
| `memory_message_count` | `string` | No | Maximum number of recent messages to retain (Required if memory_limit_type is "message_count") |

**Responses:**

- **`201 Created`**
  ```json
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "name": "Research Assistant",
    "description": "An agent specialized in Web Search and Data Extraction",
    "system_prompt": "You are a helpful researcher. Extract useful facts from the given content.",
    "memory_enabled": true,
    "memory_mode": "user_only",
    "memory_limit_type": "message_count",
    "memory_message_count": 10,
    "datasources": []
  }
  ```

- **`400 Bad Request`** (Validation error)
  ```json
  {
    "validation_errors": [
      {
        "field": "name",
        "message": "Field required"
      }
    ]
  }
  ```

</details>

<details>
<summary><code>GET</code> <strong>/api/v1/agents</strong> — List all agents</summary>

<br>

**Description:**  
Retrieves a list of all registered agents, ordered by their latest chat message timestamp descending.

**Responses:**

- **`200 OK`**
  ```json
  [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "name": "Research Assistant",
      "description": "An agent specialized in Web Search and Data Extraction",
      "system_prompt": "You are a helpful researcher.",
      "datasources": [
        {
          "id": "ds-12345",
          "name": "Manual.pdf",
          "filename": "uuid_Manual.pdf",
          "mime_type": "application/pdf",
          "file_size": 204800,
          "agent_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab"
        }
      ]
    }
  ]
  ```

</details>


<details>
<summary><code>PUT</code> <strong>/api/v1/agents/{agent_id}</strong> — Update an agent</summary>

<br>

**Description:**  
Updates metadata and settings for an existing agent.

**Path Parameters:**
- `agent_id` (`string`): Unique ID of the agent to update.

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "name": "Updated Research Assistant",
  "description": "Updated description",
  "system_prompt": "You are an updated system prompt."
}
```

**Responses:**

- **`200 OK`**
  ```json
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "name": "Updated Research Assistant",
    "description": "Updated description",
    "system_prompt": "You are an updated system prompt.",
    "datasources": []
  }
  ```

- **`404 Not Found`**
  ```json
  {
    "error": "NOT_FOUND",
    "message": "Agent mit der ID 'a1b2c3d4-e5f6-7890-abcd-1234567890ab' wurde nicht gefunden."
  }
  ```

</details>

<details>
<summary><code>DELETE</code> <strong>/api/v1/agents/{agent_id}</strong> — Delete an agent</summary>

<br>

**Description:**  
Permanently deletes an agent and all linked data sources from the backend.

**Path Parameters:**
- `agent_id` (`string`): Unique ID of the agent to delete.

**Responses:**

- **`204 No Content`** *(Empty body)*

- **`404 Not Found`**
  ```json
  {
    "error": "NOT_FOUND",
    "message": "Agent mit der ID 'a1b2c3d4-e5f6-7890-abcd-1234567890ab' wurde nicht gefunden."
  }
  ```

</details>

### Agent Datasources

<details>
<summary><code>POST</code> <strong>/api/v1/agents/{agent_id}/datasources</strong> — Upload a datasource</summary>

<br>

**Description:**  
Uploads a document (PDF, Text, JSON, etc.) via `multipart/form-data` and links it as knowledge base to the specified agent.

**Path Parameters:**
- `agent_id` (`string`): Target Agent ID.

**Headers:**
- `Content-Type: multipart/form-data`

**Form Parameters:**
- `file` (File Blob, **Required**): The file to upload.
- `name` (string, Optional): Custom display name for the document in the UI.

**Responses:**

- **`201 Created`**
  ```json
  {
    "id": "ds-7890-abcd",
    "name": "Company Knowledge Base",
    "filename": "f83a12cd-89ab-4c3d_handbook.pdf",
    "mime_type": "application/pdf",
    "file_size": 1048576,
    "agent_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab"
  }
  ```

- **`400 Bad Request`**
  ```json
  {
    "error": "NO_FILE_PART"
  }
  ```

- **`404 Not Found`** (Agent does not exist)

</details>

<details>
<summary><code>DELETE</code> <strong>/api/v1/agents/{agent_id}/datasources/{datasource_id}</strong> — Delete a datasource</summary>

<br>

**Description:**  
Deletes a specific data source from an agent and removes the physical file from storage.

**Path Parameters:**
- `agent_id` (`string`): Agent ID.
- `datasource_id` (`string`): Datasource ID to remove.

**Responses:**

- **`200 OK`**
  ```json
  {
    "message": "Datasource successfully deleted",
    "id": "ds-7890-abcd"
  }
  ```

- **`404 Not Found`**

</details>

### Chat & Execution Endpoints (`/api/v1/chat`)

<details>
<summary><code>POST</code> <strong>/api/v1/chat/messages</strong> — Send a chat message</summary>

<br>

**Description:**  
Persists a message in a conversation. If `conversation_id` is omitted or `null`, a new conversation instance is created automatically.

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "conversation_id": "conv-1234-5678",
  "text": "Can you summarize the attached manual?",
  "recipient_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab"
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `conversation_id` | `string` | No | ID of existing conversation (new one created if null) |
| `text` | `string` | **Yes** | Message payload text |
| `recipient_id` | `string` | No | Target recipient ID (e.g., Agent ID) |
| `files` | `file` (array) | No | Optional file attachments |

**Responses:**

- **`201 Created`**
  ```json
  {
    "id": "msg-99887766",
    "conversation_id": "conv-1234-5678",
    "sender_id": "usr-001",
    "sender_type": "user",
    "sender_name": "Alice",
    "text": "Can you summarize the attached manual?",
    "recipient_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "attachments": [
      {
        "id": "att-10293847",
        "name": "manual.pdf",
        "filename": "f83a12cd-89ab-4c3d_manual.pdf",
        "file_path": "uploads/f83a12cd-89ab-4c3d_manual.pdf",
        "mime_type": "application/pdf",
        "file_size": 1048576,
        "message_id": "msg-99887766"
      }
    ],
    "timestamp": "2025-02-23T14:30:00.000000+00:00"
  }
  ```

- **`400 Bad Request`**
  ```json
  {
    "error": "INVALID_SENDER_TYPE"
  }
  ```

</details>

<details>
<summary><code>GET</code> <strong>/api/v1/chat/conversations/{conversation_id}/messages</strong> — Get conversation history</summary>

<br>

**Description:**  
Retrieves chronological message history for a specific conversation ID, including associated file attachments.

**Path Parameters:**
- `conversation_id` (`string`): The conversation ID.

**Responses:**

- **`200 OK`**
  ```json
  [
    {
      "id": "msg-001",
      "conversation_id": "conv-1234-5678",
      "sender_id": "usr-001",
      "sender_type": "user",
      "sender_name": "Alice",
      "text": "Hello Agent, here is the document.",
      "recipient_id": "agent-123",
      "attachments": [
        {
          "id": "att-10293847",
          "name": "document.pdf",
          "filename": "uuid_document.pdf",
          "file_path": "uploads/uuid_document.pdf",
          "mime_type": "application/pdf",
          "file_size": 512000,
          "message_id": "msg-001"
        }
      ],
      "timestamp": "2026-08-07T14:28:00+00:00"
    },
    {
      "id": "msg-002",
      "conversation_id": "conv-1234-5678",
      "sender_id": "agent-123",
      "sender_type": "agent",
      "sender_name": "Trinity Assistant",
      "text": "Hello Alice! I have analyzed your document. How can I help you with it?",
      "recipient_id": "usr-001",
      "attachments": [],
      "timestamp": "2026-08-07T14:28:02+00:00"
    }
  ]
  ```

</details>

<details>
<summary><code>POST</code> <strong>/api/v1/chat/stream</strong> — Stream agent response (SSE)</summary>

<br>

**Description:**  
Streams response tokens in real-time from the agent back to the caller using Server-Sent Events (SSE) / Event Streams. Handles multi-turn ReAct loops and task-chain tool executions automatically.

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "message": "Fetch the RSS feed from https://news.ycombinator.com/rss and summarize the top 3 stories.",
  "conversation_id": "conv-1234-5678",
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "agent_name": "Research Assistant",
  "user_id": "usr-001"
}
```

| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | `string` | No | `"Hallo!"` | User prompt / message |
| `conversation_id` | `string` | No | `null` | Associated conversation ID |
| `agent_id` | `string` | No | `conversation_id` | ID of executing agent |
| `agent_name` | `string` | No | `"Agent"` | Name of executing agent |
| `user_id` | `string` | No | `"user-default"` | Author user ID |

**Responses:**

- **`200 OK`**
  - **Content-Type:** `text/event-stream`
  - **Body Stream Example:**
    ```text
    I am retrieving the RSS feed for you...
    • Story 1: Launches New Features
    • Story 2: AI Breakthrough announced
    ```

</details>

### Conversations

<details>
<summary><code>GET</code> <strong>/api/v1/agents/{agent_id}/conversations</strong> — List conversations for an agent</summary>

<br>

**Description:**  
Retrieves a list of all conversations/sessions associated with a specific agent, ordered by creation date descending.

**URL Parameters:**
- `agent_id` (string, required): The ID of the agent.

**Responses:**

- **`200 OK`**
  ```json
  [
    {
      "id": "f2bfa604-f84d-47e7-bed6-90213aa08919",
      "agent_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "title": "Chat gestartet von Christian",
      "created_at": "2026-08-12T16:17:39.111251"
    }
  ]
  ```
</details>


<details>
<summary><code>GET</code> <strong>/api/v1/agents/{agent_id}/conversations/{conversation_id}/history</strong> — Fetch conversation message history</summary>

<br>

**Description:**  
Retrieves the message history for a specific conversation session of an agent.

**URL Parameters:**
- `agent_id` (string, required): The ID of the agent.
- `conversation_id` (string, required): The ID of the conversation.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of messages to return (default: `50`).

**Responses:**

- **`200 OK`**
  ```json
  [
    {
      "id": "c7d08d0e-d13d-42ca-973d-f5dde5cadff9",
      "conversation_id": "f2bfa604-f84d-47e7-bed6-90213aa08919",
      "sender_id": "user-christian",
      "sender_name": "Christian",
      "sender_type": "user",
      "recipient_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "text": "test",
      "attachments": [],
      "timestamp": "2026-08-12T16:17:39.111251"
    },
    {
      "id": "2797dbe1-f438-4109-87e3-ab77fb1be3cf",
      "conversation_id": "f2bfa604-f84d-47e7-bed6-90213aa08919",
      "sender_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "sender_name": "Research Assistant",
      "sender_type": "agent",
      "recipient_id": "user-christian",
      "text": "Hallo! Wie kann ich dir heute behilflich sein?",
      "attachments": [],
      "timestamp": "2026-08-12T16:17:40.275248"
    }
  ]

- **`404 Not Found`**
  ```json
  {
    "error": "Agent or conversation not found"
  }
  ```
</details>

<details>
<summary><code>DELETE</code> <strong>/api/v1/agents/{agent_id}/conversations/{conversation_id}</strong> — Delete a conversation</summary>

<br>

**Description:**  
Permanently deletes a specific conversation session and its associated messages and attachments for an agent.

**URL Parameters:**
- `agent_id` (string, required): The ID of the agent.
- `conversation_id` (string, required): The ID of the conversation to delete.

**Responses:**

- **`204 No Content`**
  *(Empty response body)*

- **`404 Not Found`**
  ```json
  {
    "error": "Agent or conversation not found"
  }
  ``` 
</details>

## Agent Examples

Looking for inspiration or a starting point to build your own agents? Check out the [`docs/examples`](docs/examples) directory! 

There you'll find ready-to-use configurations, prompt setups, and example chats for various Trinity agents.

