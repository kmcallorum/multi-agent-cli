# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-12

### Added

- Initial release
- Single agent execution with `run` command
- Parallel agent execution with `parallel` command
- Sequential workflow execution with `workflow` command
- Configuration management with `config` commands
- Project initialization with `init` command
- Prometheus metrics server with `metrics` command
- Rich terminal output with progress bars and tables
- JSON and table output formats
- Pydantic-based data validation
- Dependency injection with factory pattern
- 100% test coverage
- Docker support
- GitHub Actions CI/CD workflows
- Comprehensive documentation

### Features

- **CLI Commands**
  - `run` - Execute single agent actions
  - `parallel` - Run multiple agents simultaneously
  - `workflow` - Execute sequential workflows
  - `list` - List available agents
  - `config show/validate/init` - Configuration management
  - `metrics` - Prometheus metrics server
  - `init` - Initialize project configuration

- **Output Formats**
  - Rich (default) - Beautiful terminal output
  - JSON - Machine-readable output
  - Table - Structured table format

- **Metrics**
  - Agent invocation counters
  - Execution duration histograms
  - Workflow success/failure tracking
  - Parallel execution monitoring

- **Quality Gates**
  - Maximum FIXME count
  - Minimum documentation score
  - Maximum dead code percentage
