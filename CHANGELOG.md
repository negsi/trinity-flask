# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Modular tool package architecture under `app/services/tools/` to split domain-specific system tools:
  - `file_tools.py`: Contains sandboxed file operation `write_file` and path resolution helpers (`locate_file`, `get_latest_image_in_dir`).
  - `media_tools.py`: Contains `generate_image` execution logic and payload handling.
  - `communication_tools.py`: Houses `send_email` and LLM delegation helper `message_llm`.
  - `api_tools.py`: Encapsulates HTTP request utilities (`call_api`, `fetch_url`).
  - `search_tools.py`: Implements web search aggregators (`web_search`).

### Changed

- Refactored monolithic `app/services/tools.py` into a structured, modular `app/services/tools/` package.
- Refactored `ToolRegistry` in `registry.py` to act as a lightweight dependency injection binding layer, delegating execution logic to individual tool modules.
- Updated infrastructure service imports across tool modules (`file_tools.py`, `media_tools.py`, `communication_tools.py`, `registry.py`) to reference `app.services.infrastructure`[cite: 6].
- Refactored `send_email` in `communication_tools.py` to remove the unrequested latest-image fallback, preventing unexpected attachments in text-only dispatches[cite: 6].
- Safely stripped `email_service` from `kwargs` in `ToolRegistry.send_email` to prevent `TypeError` duplicate keyword argument conflicts when invoked via runner/agent context[cite: 6].
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

[Unreleased]: https://github.com/negsi/trinity-flask/compare/v0.1.4...develop
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