# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/negsi/trinity-flask/compare/v0.0.2...develop
[0.0.2]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.2
[0.0.1]: https://github.com/negsi/trinity-flask/releases/tag/v0.0.1