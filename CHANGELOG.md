# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## Added

## Changed

## [0.1.12] - 2026-08-26

## Added

- New `_has_llm_step_in_chain` helper method in `ReActLoopRunner` to check for `message_llm` execution steps in task chains.

## Changed

- Refactored `base_agent.prompt.md` system prompt for better readability, token efficiency, and clearer tool execution rules. (!)
- Increased `MAX_SUBAGENT_CALL_DEPTH` to `7` in AgentOrchestrator.
- **Task Execution Pipeline (`TaskExecutor`):** Extended `task_step_update` protocol payloads to include execution results.
  - Updated step completion SSE events to attach `result` fetched dynamically from the execution context (`context.get(f'step_{step_num}')`).
  - Formatted protocol payload emission for improved readability during streaming execution.

## [0.1.11] - 2026-08-24

## Added

- Add `message_agent` tool enabling inter-agent delegation, prompt passing, and real-time generator event streaming.
- Implement recursion safety limits (`MAX_SUBAGENT_CALL_DEPTH = 3`) within `AgentOrchestrator` to prevent sub-agent call loops.
- Pass caller context (`agent_id`, `call_depth`, `conversation_id`) across ReAct execution steps and sub-task generators.
- Add instructions and strict interaction guidelines for `message_agent` in `base_agent.prompt.md`.

## Changed

- Move developer utility scripts (`code_tree.py`, `concat_code.py`) into dedicated `scripts/` directory.
- Update `ToolRegistry` and dependency injection containers to support dynamic `AgentOrchestrator` binding.
- Enforce file retention in primary conversation directories during sub-task execution.
- Refactor `ReActLoopRunner` to suppress intermediate LLM step yields during nested execution chains.

## [0.1.10] - 2026-08-23

## Added

- Introduced signature inspection via `inspect.signature` in `TaskExecutor` to verify whether candidate context parameters (`conversation_id`, `base_dir`, `email_service`) or `**kwargs` are accepted before injecting them into standard tool executions.
- Added optional `conversations_folder` dependency injection parameter to `TaskExecutor` and `ReActLoopRunner` constructors to decouple file path resolution from global configuration.

## Changed

- Updated `AgentContextBuilder` to lazily evaluate and populate the `{available_agents_list}` system prompt template placeholder only when explicitly present in the prompt string.
- Replaced hardcoded file extension checks (`.png`, `.jpg`, etc.) in `AgentOrchestrator` with dynamic MIME type detection using `mimetypes.guess_type`.
- Refactored `AgentContextBuilder` message history filtering to rely strictly on `ActorType.USER` enum comparisons instead of string conversion fallbacks.
- Updated file path construction in `TaskExecutor._collect_created_files` to utilize the injected `conversations_folder` base path instead of referencing global `BaseConfig`.

## Fixed

- Added exception handling wrappers around `FileStorageService.extract_text_content` calls in both message attachment and datasource contexts to prevent failed text extractions from disrupting prompt generation.

## [0.1.9] - 2026-08-23

### Added

- Added context inspection for `flask.g.actor` in `SecurityContextService.get_current_actor()` to support explicitly set execution contexts.
- Added JSON request payload parsing in `SecurityContextService` to dynamically resolve agent identity (`sender_id`, `sender_type`, `sender_name`) for incoming agent-to-agent HTTP communication.
- Introduced `FileUrlResolver` callable type and `default_file_url_resolver` in `agent_orchestrator` to decouple file URL generation.
- Added structured system prompt placeholder rendering via `_render_system_prompt_placeholders()` in `AgentContextBuilder`.

### Changed

- Refactored `SecurityContextService.get_current_actor()` fallback logic to return the static user identity (`user-christian`) only when no explicit context or agent payload is present.
- Refactored model interactions in `AgentContextBuilder`, `ReActLoopRunner`, and `TaskExecutor` to use direct attribute access and strong typing instead of dynamic `getattr` fallbacks.
- Applied `@dataclass(slots=True)` optimization to `ReActTurnState`, `ReActExecutionSummary`, and `ChainExecutionResult` for improved memory usage and attribute lookup speed.
- Marked agent lifecycle constants (`PROTOCOL_TASK_CHAIN`, `PROTOCOL_ATTACHMENTS`) as `Final`.
- Updated file attachment handling and URL resolution in `AgentOrchestrator` to utilize the injected `FileUrlResolver`.

## [0.1.8] - 2026-08-22

### Added

- Introduced `POST /api/v1/agents/<agent_id>/stream` endpoint to consolidate user message persistence (including file uploads via `multipart/form-data`) and real-time LLM execution streaming into a single SSE request.
- Added an initial metadata event (`{"type": "meta", ...}`) at the start of the SSE stream to immediately send the assigned `conversation_id` and `user_message_id` back to the client.

### Changed

- Refactored the SSE chat streaming workflow from `/api/v1/chat/stream` to the agent-centric endpoint `/api/v1/agents/<agent_id>/stream`.
- Updated frontend chat services (`ApiChatService` and `ChatWorkspaceComponent`) to stream messages and file attachments directly without executing a prior separate REST persistence call.

### Removed

- Deprecated and removed obsolete `POST /api/v1/chat/messages` and `POST /api/v1/chat/stream` endpoints.

## [0.1.7] - 2026-08-22

### Added

- Added `read_sandboxed_file` method to `FileStorageService` for secure, sandboxed file reading with directory traversal guards.
- Introduced `read_file` tool to allow agents to read sandboxed text files within the active conversation directory.
- Exposed `read_file` in `file_tools.py`, `ToolRegistry`, and package exports (`app.services.tools`).
- Added documentation for `read_file` to system agent prompt (`base_agent.prompt.md`) and global `README.md`.
- Support for dynamic placeholder replacements (`{conversation.id}` and `{conversation.directory}`) in `AgentContextBuilder`.
- Injected `conversations_folder` configuration into `AgentContextBuilder` via the DI container (`Container`).
- Introduced system identity properties (`{conversation.id}`, `{conversation.directory}`) and updated layout sections in `base_agent.prompt.md`.

### Changed

- Updated `ReActLoopRunner` to pass `conversation_id` down through all turn execution layers to `AgentContextBuilder`.
- Streamlined and restructured the base agent system prompt (`base_agent.prompt.md`) to improve instructions for tools, task chains, and conversation context.

## [0.1.6] - 2026-08-22

### Added
* **Dynamic Agent Awareness Context:** Injected full system agent directory (IDs and names) into system prompts to establish foundations for Agent-to-Agent (A2A) orchestration.
* **Internal API & Network Settings Configuration:** Added `API_BASE_URL` and `LOG_LEVEL` configuration options to `.env.template` and `BaseConfig`.

### Changed
* **Base Prompt Configuration Header:** Updated system prompt templates to expose current `agent.id` alongside dynamic agent network availability.
* **Agent Context Builder Extensions:** Enhanced `AgentContextBuilder` to resolve available system agents at prompt composition time.
* **Development Environment Logging:** Refactored `DevelopmentConfig` in `app/config.py` to dynamically configure system-wide `logging.basicConfig` and application logger based on `LOG_LEVEL`.

## [0.1.5] - 2026-08-20

### Added

- Modular tool package architecture under `app/services/tools/` to split domain-specific system tools:
  - `file_tools.py`: Contains sandboxed file operation `write_file` and path resolution helpers (`locate_file`, `get_latest_image_in_dir`).
  - `media_tools.py`: Contains `generate_image` execution logic and payload handling.
  - `communication_tools.py`: Houses `send_email` and LLM delegation helper `message_llm`.
  - `api_tools.py`: Encapsulates HTTP request utilities (`call_api`, `fetch_url`).
  - `search_tools.py`: Implements web search aggregators (`web_search`).

### Changed

- Reorganized core application services into domain-specific package structures:
  - `app/services/agent/`: Houses `AgentService`, `AgentOrchestrator`, `AgentContextBuilder`, and `ReActLoopRunner`.
  - `app/services/messaging/`: Houses `MessagingService` and `MessageAttachmentService`.
  - `app/services/knowledge/`: Houses `DatasourceService`.
  - `app/services/infrastructure/`: Houses `EmailService`, `FileStorageService`, `LLMService`, and `SecurityContextService`.
- Refactored monolithic `app/services/tools.py` into a structured, modular `app/services/tools/` package.
- Refactored `ToolRegistry` in `app/services/tools/registry.py` to act as a lightweight dependency injection binding layer, delegating execution logic to individual tool modules.
- Updated Dependency Injection container bindings (`app/containers.py`) and API route blueprints (`app/routes/agents.py`, `app/routes/chat.py`) to align with the new modular service namespaces.
- Updated infrastructure service imports across tool modules (`file_tools.py`, `media_tools.py`, `communication_tools.py`, `registry.py`) to reference `app.services.infrastructure`.
- Refactored `send_email` in `communication_tools.py` to remove the unrequested latest-image fallback, preventing unexpected attachments in text-only dispatches.
- Safely stripped `email_service` from `kwargs` in `ToolRegistry.send_email` to prevent `TypeError` duplicate keyword argument conflicts when invoked via runner/agent context.
- Modernized type hints across tool modules using standard Python 3.10+ annotations (`dict[str, Any]`, `Path | None`).
- Standardized file path resolution using `pathlib.Path` across sandbox operations.

## [0.1.4] - 2026-08-20

### Added
- New built-in agent tool `call_api` for executing structured HTTP API requests (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) with query params, JSON payloads, and custom headers.
- Multimodal attachment support for image uploads (`image/jpeg`, `image/png`, `image/webp`) in `AgentContextBuilder`.
- `ActorIdentity` `TypedDict` structure in `SecurityContextService` for strongly typed caller identity metadata.
- Centralized protocol stream constants (`PROTOCOL_ATTACHMENTS`, `PROTOCOL_TASK_CHAIN`) across `AgentOrchestrator`, `ReActLoopRunner`, and `TaskExecutor`.
- Public module re-exports in `app.services.llm.__init__` via `__all__` for provider, registry, and stream parser classes.

### Changed
- `call_api` signature: Added `**kwargs` catch-all parameter to gracefully absorb framework-injected execution context (such as `conversation_id`).
- `LLMMessage` domain model: Expanded `content` field to accept structured lists/parts for multimodal payloads alongside strings.
- `GeminiProvider`: Added dynamic conversion of provider-agnostic image dictionaries (`type: image`, `bytes`, `mime_type`) into `google.genai.types.Part.from_bytes`.
- `AgentContextBuilder`: Decoupled text document parsing (PDF/TXT) from binary image MIME type handling for clean provider-neutral payload assembly.
- Modernized type annotations across all service modules to standard Python 3.10+ syntax (`list`, `dict`, `tuple`, `X | Y` union types).
- Refactored file and path operations across `FileStorageService`, `EmailService`, `MessageAttachmentService`, `DatasourceService`, and `AgentOrchestrator` from `os.path` functions to `pathlib.Path`.
- `MessageAttachmentService`: Decoupled path resolution from Flask runtime `current_app` context by adding an explicit `conversations_folder` constructor parameter.
- `AgentOrchestrator`: Extracted final turn persistence, markdown image formatting, and attachment protocol markers into a dedicated `_finalize_agent_turn` helper method.
- `FileStorageService`: Modularized document parsing logic into separate `_extract_pdf_text` and `_extract_plain_text` helper methods.
- `EmailService`: Refactored message delivery into dedicated `_attach_files` and `_dispatch_smtp` helper routines.
- `GeminiImagenProvider`: Enforced explicit inheritance from `ImageGeneratorProvider`.
- `OpenAIDalleProvider`: Replaced conditional aspect ratio logic with a dictionary lookup table (`size_map`).

### Fixed
- Resolved `TypeError` in `call_api` tool execution caused by unexpected keyword arguments injected by `TaskExecutor`.

## [0.1.3] - 2026-08-18

### Added

- `TAVILY_API_KEY` placeholder to `.env.template`.

## [0.1.2] - 2026-08-18

### Added

- Added `web_search` tool implementation supporting hybrid web searches using Tavily with automatic fallback to DuckDuckGo (`ddgs`).
- Added `ddgs` and `tavily-python` dependencies to `requirements.txt`. (`pip install -r requirements.txt`)
- Added `web_search` documentation to `README.md` under built-in agent tools and `.env` setup guide.
- Added `web_search` tool prompt instructions and usage guidelines in `base_agent.prompt.md`.

### Changed

- Registered `web_search` tool in `ToolRegistry` to expose web search capabilities to agents.

## [0.1.1] - 2026-08-18

### Added
- **Task Chain Execution Streaming:** Real-time execution status signals (`task_chain_init`, `task_step_update`) emitted via SSE stream for visual progress indicators in the frontend UI.
- **Robust Email Attachment Resolution:** Added multi-tier attachment resolution (`locate_file`) in `ToolRegistry.send_email` using recursive directory walking and a fallback mechanism to automatically attach the most recently generated image if omitted by LLM tool arguments. (pip install -r requirements.txt)

### Changed
- **TaskExecutor:** Integrated task chain cycle event dispatching before and after step execution cycles (`pending`, `running`, `completed`).
- **ReActLoopRunner:** Bypassed task chain control markers (`__TASK_CHAIN__:`) from message memory accumulation to preserve clean database chat history.
- **Email Delivery Service & Tools:** Refactored `EmailService` and `send_email` tool to dispatch generated images as standard file attachments (`Content-Disposition: attachment`) instead of inline MIME (`cid:`) structures, including automatic stripping of leftover Markdown and HTML image tags from email bodies.

## [0.1.0] - 2026-08-17

### Added
- **`generate_image` Built-in Tool:**
  - Integrated a new built-in agent tool for image generation supporting configurable aspect ratios (`1:1`, `16:9`, `9:16`) and automated file persistence.
  - Multi-provider support featuring implementations for **Google Gemini / Imagen** (`GeminiImagenProvider`) and **OpenAI DALL-E 3** (`OpenAIDalleProvider`).
  - Support for custom image models via environment configuration (`IMAGE_GENERATOR_PROVIDER`, `IMAGE_GENERATOR_MODEL`).
- **Binary Content Storage:**
  - Extended `FileStorageService.write_sandboxed_file` to natively handle both text and raw binary (`bytes`) payloads (e.g., JPEG/PNG images) with automated mode detection (`wb`/`ab`).
- **Automatic Attachment Handling for Task Chains:**
  - Added tracking and context extraction for dynamically generated files during `generate_image` tool execution in `TaskExecutor`.
  - Implemented automatic image link/attachment detection in `AgentOrchestrator` to prevent duplicate rendering when images are already linked in LLM responses.

### Changed
- **Dependency Injection Container:**
  - Registered image generation providers and injected `image_generator_provider` into `ToolRegistry` via `dependency-injector`.
- **ReAct Loop Execution:**
  - Extended `ReActLoopRunner` generator return signature to return a tuple `(last_result, created_files)` for downstream pipeline tracking.
  - Added robust `getattr` fallbacks across execution result parsing.
- **System Prompts & Documentation:**
  - Updated `base_agent.prompt.md` and `README.md` with tool specs for `generate_image`.
- **Configuration & Environment:**
  - Updated `.env.template` and `app/config.py` with default settings for image generation providers.

## [0.0.9] - 2026-08-15

### Added
- **SSE Stream Attachment Notification**: Added inline attachment payload event (`__ATTACHMENTS__`) to the Server-Sent Events stream after ReAct loop execution to notify clients of newly created files in real time.

### Changed
- **Conversation File Endpoint**: Replaced simple `<filename>` route parameter with path-converter (`<path:filename>`) in `get_conversation_file` endpoint to support nested files and relative filepaths.
- **Message Attachment Storage Location**: Updated `MessageAttachmentService` and `MessagingService` to save user-uploaded message attachments directly into the target conversation sandbox directory (`instance/conversations/<conversation_id>/`), keeping all uploaded and generated files unified in the same folder hierarchy.

## [0.0.8] - 2026-08-14

### Added

- Introduced trinity `examples` directory
- Added `LLMExecutionRepository` domain protocol for decoupled LLM execution persistence.
- Added `get_conversations_by_agent` method to `MessagingService` to support multi-conversation history.
- **Domain Enums & Type Safety**:
  - Introduced strongly typed string enums (`ActorType`, `ResponseType`, `MemoryMode`, `MemoryLimitType`, `ExecutionStepStatus`) in `domain/enums.py`.
- **Domain Exceptions**:
  - Added `LLMExecutionNotFoundError` and `ToolNotFoundError` in `domain/errors.py`.

### Changed

- **Clean Architecture & DDD Refactoring**:
  - **Domain Models**: Refactored all domain dataclasses to use `slots=True`, explicit Python 3.10+ type hints, automatic ID/timestamp default factories (UTC), and invariant validations in `__post_init__` (e.g., entity validation, enum mapping).
  - **Domain Interfaces**: Updated repository protocols with explicit typing, boolean return flags for deletions, and extended queries (e.g., `DatasourceRepository.get_by_agent_id`).
  - Extracted ReAct agent loop logic into `ReActLoopRunner`.
  - Refactored `FileStorageService` to centralize I/O, path validation, and text extraction.
  - Replaced `flask.current_app` dependencies in `tools.py` with `ToolRegistry` injection.
  - Standardized domain-specific exception handling across services.
- **Persistence & SQLAlchemy Layer**: (flask db upgrade)
  - Updated SQLAlchemy repositories with explicit `try...except SQLAlchemyError` handling, automatic session rollbacks, and domain `StorageError` wraps.
  - Upgraded database base to SQLAlchemy 2.0 `DeclarativeBase` and optimized ORM relationships (cascade deletes, `selectin` loading to prevent N+1 queries).
  - Improved relation mapping synchronization for domain aggregates (e.g., `Agent` datasources, `Message` attachments).
- **Messaging & Persistence**:
  - Updated `MessagingService` to manage conversation lifecycles and attachment links directly.
  - Enhanced `SQLAlchemyConversationRepository` with fallback UUID generation to guarantee primary key constraints.

## [0.0.7] - 2026-08-13

### Added
- Dynamic Conversation Memory: Native support for flexible memory modes (`user_only`, `message_count`) within `agent_context_builder.py`. (flask db upgrade)
- System Prompt Enhancements: Expanded base instructions covering chat history, memory retention, and structured tool execution.
- Agent Templates: Optimized system prompts for specialized agent roles (including CBT therapy with cognitive restructuring frameworks and interactive ASCII chess).

### Changed
- Refactored `_build_agent_context_history` to filter chat histories more robustly and map them seamlessly into structured `LLMMessage` objects.
- Streamlined system prompt hierarchy: Consolidated all guidelines regarding Knowledge Base, tool usage, and output formatting at the end of the prompt for improved attention weights.

## [0.0.6] - 2026-08-13

### Added

- REST API endpoint for deleting agent conversations

### Changed

- fixed new conversation generation

## [0.0.5] - 2026-08-12

### Added

- REST API endpoints to fetch agent conversations and message history.
- Automatic creation and assignment of conversations to agents in `MessagingService`.
- `agent_id` field to `conversations` database schema. (flask db upgrade)

## [0.0.4] - 2026-08-11 

### Added

- Code refactoring
- Agent configuration to base system prompt (name, date and time for now)

## [0.0.3] - 2026-08-10

### Added

- implemented proper SSE streaming and event formatting
- user messages now can hold file attachments (flask db upgrade)
- implemented write file tool (needs testing)
- implemented send mail tool

## [0.0.2] - 2026-08-06

### Added

- Security Context Service for implementing user management later
- More documentation

### Changed

- You no longer need to send sender_id, sender_type and sender_name when posting to messages and to the llm stream

## [0.0.1] - 2026-08-03

### Added

- base application structure
- main menu
- filesystem storage for uploaded files
- persistence layer for relational data
- corresponding services
- application configuration
- application api routes
- error handling and debug utils
- llm service layer vor gemini

[Unreleased]: https://github.com/negsi/trinity-flask/compare/v0.1.12...develop
[0.1.12]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.12
[0.1.11]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.11
[0.1.10]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.10
[0.1.9]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.9
[0.1.8]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.8
[0.1.7]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.7
[0.1.6]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.6
[0.1.5]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.5
[0.1.4]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.4
[0.1.3]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.3
[0.1.2]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.2
[0.1.1]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.1
[0.1.0]: https://github.com/negsi/trinity-flask/releases/tag/v0.1.0
[0.0.9]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.9
[0.0.8]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.8
[0.0.7]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.7
[0.0.6]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.6
[0.0.5]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.5
[0.0.4]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.4
[0.0.3]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.3
[0.0.2]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.2
[0.0.1]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.1