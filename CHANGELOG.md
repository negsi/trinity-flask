# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/negsi/trinity-flask/compare/v0.0.6...develop
[0.0.6]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.6
[0.0.5]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.5
[0.0.4]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.4
[0.0.3]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.3
[0.0.2]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.2
[0.0.1]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.1