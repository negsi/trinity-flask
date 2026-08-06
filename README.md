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

However, we recommend using our Angular frontend, which is coming soon.

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
- [Using the API](#using-the-api)
  - [Agent Endpoints](#agent)
  - [Agent Datasources](#agent-datasources)
  - [Chat & Execution Endpoints](#chat--execution-endpoints-apiv1chat)
- [Examples](#examples)

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

In `.env`, specify your AI provider, your preferred large language model, and the API token. If you want to use a MySQL-Server as storage backend, then add the necessary parameters there as well.

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

### Task Execution Workflow

- **Internal Knowledge / Datasources:** For queries answerable directly via model knowledge or uploaded files (Knowledge Base), the agent responds immediately without triggering external tools.
- **External Web Processing:** For complex requests requiring web data (e.g., *"Read this web article and summarize the key findings"*), Trinity builds a structured JSON Task Chain executing a `fetch` $\rightarrow$ `process` pipeline.
- **Tool Fallback Handling:** If a user request demands capabilities beyond the available toolset, the agent explicitly informs the user about unexecutable requirements.

### Using the API

The backend exposes a RESTful JSON API under the base path `/api/v1`. Below is the detailed endpoint documentation for managing agents, datasources, and chat interactions.

### Agent

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
  "system_prompt": "You are a helpful researcher. Extract useful facts from the given content."
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | `string` | **Yes** | Agent name (1 - 100 characters) |
| `description` | `string` | No | Short description (max 500 characters) |
| `system_prompt` | `string` | No | Custom system instruction prompt for the LLM |

**Responses:**

- **`201 Created`**
  ```json
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "name": "Research Assistant",
    "description": "An agent specialized in Web Search and Data Extraction",
    "system_prompt": "You are a helpful researcher. Extract useful facts from the given content.",
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
  "sender_id": "usr-001",
  "sender_type": "user",
  "sender_name": "Alice",
  "text": "Can you summarize the attached manual?",
  "recipient_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab"
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `conversation_id` | `string` | No | ID of existing conversation (new one created if null) |
| `sender_id` | `string` | **Yes** | ID of the message author |
| `sender_type` | `string` | **Yes** | Enum: `"user"`, `"agent"`, or `"system"` |
| `sender_name` | `string` | **Yes** | Display name of the sender |
| `text` | `string` | **Yes** | Message payload text |
| `recipient_id` | `string` | No | Target recipient ID (e.g., Agent ID) |

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
Retrieves chronological message history for a specific conversation ID.

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
      "text": "Hello Agent!",
      "recipient_id": "agent-123",
      "timestamp": "2025-02-23T14:28:00+00:00"
    },
    {
      "id": "msg-002",
      "conversation_id": "conv-1234-5678",
      "sender_id": "agent-123",
      "sender_type": "agent",
      "sender_name": "Trinity Assistant",
      "text": "Hello Alice! How can I help you today?",
      "recipient_id": "usr-001",
      "timestamp": "2025-02-23T14:28:02+00:00"
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

### Examples

<details>
<summary>Creating a standard AI Agent</summary>

<br>

**cURL:**  
```bash
curl -X POST http://localhost:5000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cypher",
    "description": "Cypher, ein Agent zur Ingestion von Daten.",
    "system_prompt": "Du bist Cypher, ein Agent zur Ingestion von Daten."
  }'
```

**Response:**

```json
{
  "datasources": [],
  "description": "Cypher, ein Agent zur Ingestion von Daten.",
  "id": "92a5a280-9c4e-4103-afe4-c47e2ed9207e",
  "name": "Cypher",
  "system_prompt": "Du bist Cypher, ein Agent zur Ingestion von Daten."
}

```

</details>

<details>
<summary>Assign a data source to an agent</summary>

<br>

**cURL:**  
```bash
curl -X POST http://localhost:5000/api/v1/agents/AGENT_ID/datasources \
  -F "file=@./docs/berlin.open-meteo.link.txt" \
  -F "name=Open-Meteo Berlin Docs"
```

**Response:**

```json
{
  "agent_id": "e9acc6d1-f8e5-4b4f-a47d-6a2bc9e988fd",
  "file_size": 264,
  "filename": "248f0946-3ac4-4eaa-a9d5-82c857a11914_berlin.open-meteo.link.txt",
  "id": "969c5b97-a5ca-483c-a8a6-f34de567afdc",
  "mime_type": "text/plain",
  "name": "Open-Meteo Berlin Docs"
}

```

</details>

<details>
<summary>Write a chat message and save it in the conversations table</summary>

<br>

**cURL:**  
```bash
curl -X POST http://localhost:5000/api/v1/chat/messages \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id": "e9acc6d1-f8e5-4b4f-a47d-6a2bc9e988fd",
    "text": "Hi, wer bist du und was kannst du?"
  }'
```

**Response:**

```json
{
  "conversation_id": "c4d11c66-fd56-4da0-8621-d0bb84871666",
  "id": "c69dbe0c-f363-4913-85d4-06b12cb4bd75",
  "recipient_id": "e9acc6d1-f8e5-4b4f-a47d-6a2bc9e988fd",
  "sender_id": "[CURRENT_ACTOR.ID]",
  "sender_name": "[CURRENT_ACTOR.NAME]",
  "sender_type": "[CURRENT_ACTOR.ACTOR_TYPE]",
  "text": "Hi, wer bist du und was kannst du?",
  "timestamp": "2026-08-04T08:56:43.589930"
}


```
</details>

<details>
<summary>Sends a chat message to a LLM. Stores the response in the conversations table</summary>

<br>

**cURL:**  
```bash
curl -N -X POST http://localhost:5000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "[CONVERSATION_ID]",
    "agent_id": "[AGENT_ID]",
    "message": "Hi, wer bist du und was kannst du?"
  }'
```

**Response:**

Hallo! Ich bin Cypher, dein spezialisierter Agent für die Datenaufnahme und -verarbeitung.

Meine Hauptaufgabe besteht darin, Informationen effizient aus externen Webquellen zu beschaffen und diese für dich aufzubereiten. Hier ist ein Überblick darüber, was ich für dich tun kann:

*   **Datenabruf:** Ich kann Inhalte von spezifischen Webseiten oder URLs abrufen (`fetch_url`), um sie für eine weitere Analyse zugänglich zu machen.
*   **Datenanalyse & Transformation:** Mit Hilfe des `message_llm`-Werkzeugs kann ich die von mir abgerufenen Daten auswerten, zusammenfassen, strukturieren oder in andere Formate umwandeln.
*   **Verknüpfung von Informationen:** Ich kann komplexe Arbeitsabläufe in sogenannten „Task Chains“ planen, um Aufgaben in logischen Schritten abzuarbeiten (z. B. zuerst eine Seite laden, dann den Inhalt analysieren).
*   **Nutzung von Kontext:** Ich habe Zugriff auf Informationen, die du mir in Form von Dateien (Knowledge Base) zur Verfügung stellst, und kann diese direkt mit neuen Online-Daten kombinieren.

<br>

**cURL:**  
```bash
curl -N -X POST http://localhost:5000/api/v1/chat/stream -H "Content-Type: application/json" -d '{
    "conversation_id": "[CONVERSATION_ID]",
    "agent_id": "[AGENT_ID]",
    "message": "Wie werden die Strahlungswerte heute in Berlin?"
  }'
```

**Response:**

Die Wetterdaten für den 4. August 2026 in Berlin zeigen einen Tag mit wechselhafter Bewölkung und spezifischen Strahlungsverläufen. Hier ist die Zusammenfassung der kurzwelligen Strahlung (`shortwave_radiation`):

**Zusammenfassung der Strahlungswerte:**
*   **Tagesverlauf:** Die Strahlung beginnt mit dem Sonnenaufgang kurz nach 06:00 Uhr (4,3 W/m²). Die Werte steigen stetig an und erreichen ihren Höhepunkt am Nachmittag.
*   **Maximum:** Der höchste Wert wird um **16:00 Uhr mit 575,5 W/m²** gemessen, gefolgt von einer weiteren starken Phase um 15:00 Uhr (464,8 W/m²) und 17:00 Uhr (459,5 W/m²).
*   **Vormittagsphase:** Zwischen 08:00 und 13:00 Uhr schwanken die Werte aufgrund der starken Bewölkung (meist 100 %) zwischen etwa 69 W/m² und 226 W/m².
*   **Tagesende:** Nach 20:00 Uhr (121,3 W/m²) fällt die Strahlung rasch ab, bis sie ab 22:00 Uhr bei 0,0 W/m² liegt.

**Zusammenfassende Einschätzung:**
Trotz der phasenweise vollständigen Bewölkung (insbesondere am Vormittag und frühen Mittag) erreicht die kurzwellige Einstrahlung am Nachmittag, bei gleichzeitig abnehmender Wolkendecke, signifikante Werte von über 500 W/m². Dies deutet auf einen recht warmen Sommertag mit einer Höchsttemperatur von 28,9 °C am Abend hin.Die Strahlungswerte in Berlin erreichen heute einen interessanten Verlauf, der stark von der Bewölkung beeinflusst wird.

Hier ist die Zusammenfassung für den heutigen Tag:

*   **Tagesverlauf:** Die Strahlung nimmt mit dem Sonnenaufgang kurz nach 06:00 Uhr ihren Anfang (4,3 W/m²). Während der Vormittagsstunden (08:00 bis 13:00 Uhr) bleibt die kurzwellige Strahlung aufgrund der dichten Bewölkung (meist 100 %) moderat und schwankt zwischen ca. 69 W/m² und 226 W/m².
*   **Maximum:** Die intensivste Einstrahlung wird am Nachmittag erreicht. Den Höchstwert verzeichnen wir um **16:00 Uhr mit 575,5 W/m²**. Auch die Stunden davor (15:00 Uhr: 464,8 W/m²) und danach (17:00 Uhr: 459,5 W/m²) bieten eine deutliche Zunahme der Strahlungsintensität, was mit einer auflockernden Wolkendecke zusammenfällt.
*   **Abendstunden:** Nach 20:00 Uhr (121,3 W/m²) sinken die Werte rapide ab, bis die Strahlung ab 22:00 Uhr vollständig auf 0,0 W/m² zurückgeht.

</details>
