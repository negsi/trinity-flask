<p align="center">
  <img src="./docs/readme.md_banner.svg" alt="Trinity Agent Designer Banner" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/github/v/tag/negsi/trinity-flask?style=flat-square&label=Version&color=blue" alt="Latest Version">
  <img src="https://img.shields.io/badge/AI-Google%20Gemini-8E75B2?style=flat-square&logo=googlegemini&logoColor=white" alt="Gemini">
</p>

<p align="center"><strong>Highly Configurable Multi-Agent Orchestration Framework</strong><br>
Customizable Agent Builder & Workflow Engine
</p>

<p align="center">
  <a href="#installation"><strong>Quickstart</strong></a> · 
  <a href="docs/documentation"><strong>Documentation</strong></a> · 
  <a href="docs/documentation/en/06.trinity-api.md"><strong>Trinity API</strong></a>
</p>

<p align="center">
  This is the python flask backend for Trinity, an AI agent designer. The goal of this project is the simple and convenient creation of AI agents that are capable of solving complex tasks and understanding complicated situations. All agents possess capabilities that can be executed as tools on your system. Trinity can create and process task sequences. You can use an API to control the system. 
</p>

![Trinity Application View](docs/readme.appview.jpg)

<p align="center">
  However, we recommend using our <a href="https://github.com/negsi/trinity-angular"><strong>Angular Frontend</strong></a>.
</p>

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

7. **`call_api`**
  - **Purpose:** Executes structured HTTP API requests (GET, POST, PUT, PATCH, DELETE) against local or remote REST endpoints.
  - **Rules & Syntax:**
    - **`url`** (string, required): Full target URL including scheme and host (e.g., `http://127.0.0.1:5000/api/v1/customers`).
    - **`method`** (string, optional): HTTP request method. Supported values: `"GET"` (default), `"POST"`, `"PUT"`, `"PATCH"`, `"DELETE"`.
    - **`params`** (object, optional): Key-value pairs for query string parameters. Supports step reference placeholders (e.g., `[STEP_1]`).
    - **`json_data`** (object, optional): JSON payload body for write operations (`POST`, `PUT`, `PATCH`). Supports step reference placeholders.
    - **`headers`** (object, optional): Custom HTTP request headers (e.g., `{"Authorization": "Bearer ..."}`).
    - **`timeout`** (integer, optional): Request timeout duration in seconds. Defaults to `30`.
  - **Usage Context:** Designed specifically for structured endpoints and REST APIs. For unstructured web pages, documents, or RSS feeds, use `fetch_url` instead.

8. **`read_file`**
  - **Purpose:** Reads and retrieves the raw text content of an existing file from the active conversation workspace.
  - **Rules & Syntax:**
    - **`file_path`** (string, required): Relative path or filename of the target file (e.g., `README.md` or `exports/data.json`).
    - **`encoding`** (string, optional): Text encoding used to read the file (defaults to `"utf-8"`).
    - File paths are automatically isolated and resolved inside the active conversation directory.
    - Ideal for context hydration, parsing local repository artifacts, or retrieving outputs generated in prior execution steps before passing them to downstream tools like `message_llm`.

9. **`message_agent`**
  - **Purpose:** Delegates a sub-task or question to another specialized agent in the system and waits for its execution output.
  - **Rules & Syntax:**
    - **`target_agent_id`** (string, required): The unique UUID of the target agent to invoke. Must be a valid ID listed in the system prompt. Self-invocation is strictly prohibited.
    - **`message`** (string, required): The prompt, instruction, or task payload passed to the target agent. Supports step reference placeholders (e.g., `[STEP_1]`).
  - **Rules & Behavior:**
    - Supports real-time streaming of sub-agent task events, text output, and execution steps via generator delegation.
    - Automatically enforces nested execution depth safety limits (up to `MAX_SUBAGENT_CALL_DEPTH = 3`) to prevent infinite recursive agent loops.
    - Results returned by `message_agent` are treated as final for that sub-task; parent agents are instructed to consume the returned payload directly without executing redundant fallback steps.
  - **Feature Toggle:** Can be globally disabled via environment configuration by setting `TRINITY_TOOLS_MESSAGE_AGENT_ENABLED=false` in `.env`. When disabled, the tool description and system agent list are stripped from the prompt context.

10. **`manage_odf`**
  - **Purpose:** Creates, reads, appends to, or updates OpenDocument Format files (`.odt` text documents, `.ods` spreadsheets, `.odp` presentations) using `odfdo`.
  - **Rules & Syntax:**
    - **`action`** (string, required): Operation to perform. Supported values: `"create"`, `"read"`, `"append"`, `"update"`.
    - **`doc_type`** (string, optional): OpenDocument format type. Supported values: `"odt"` (default), `"ods"`, `"odp"`.
    - **`filename`** (string, optional): Target output filename (e.g., `report.odt`, `grades.ods`, `presentation.odp`).
    - **`title`** (string, optional): Document header or first spreadsheet table name.
    - **`content`** (any, optional): Content payload to insert or append. Supports 2D arrays, lists of dictionaries, CSV strings, or step reference placeholders (e.g., `[STEP_2]`).
  - **Rules & Behavior:**
    - Automatically isolates and saves generated ODF files inside the active conversation workspace.

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

## Agent Examples

Looking for inspiration or a starting point to build your own agents? Check out the [`docs/examples`](docs/examples) directory! 

There you'll find ready-to-use configurations, prompt setups, and example chats for various Trinity agents.

