# Architecture

## Overview

multi-agent-cli follows a clean, layered architecture with dependency injection for testability.

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                        (cli.py)                              │
│  Commands: run, parallel, workflow, list, config, metrics   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Coordination Layer                       │
│  ┌─────────────────┐     ┌────────────────────────────┐    │
│  │    Executor     │     │      Coordinator           │    │
│  │ (executor.py)   │     │   (coordinator.py)         │    │
│  │                 │     │                            │    │
│  │ Single agent    │◄────│  Parallel execution        │    │
│  │ execution       │     │  Workflow orchestration    │    │
│  └─────────────────┘     └────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Factory Layer                            │
│                     (factory.py)                             │
│  ┌──────────────────────┐  ┌─────────────────────────┐     │
│  │ DefaultAgentBridge   │  │  MockAgentBridge        │     │
│  │ (pytest-agents)      │  │  (testing)              │     │
│  └──────────────────────┘  └─────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     External Layer                           │
│                   (pytest-agents)                            │
└─────────────────────────────────────────────────────────────┘
```

## Components

### CLI Layer (`cli.py`)

- Click-based command definitions
- Global options (config, verbose, format)
- Rich output formatting
- Error handling and exit codes

### Executor (`executor.py`)

- Single agent execution
- Timeout handling
- Metrics recording
- Async/sync execution

### Coordinator (`coordinator.py`)

- Parallel execution with rate limiting
- Workflow execution with dependencies
- Quality gate checking

### Factory (`factory.py`)

- Dependency injection for agent bridges
- Mock bridge for testing
- Global factory configuration

### Models (`models/`)

- Pydantic models for configuration
- Result types
- Workflow definitions

### Reporters (`reporters.py`)

- Rich terminal output
- JSON output
- Table output

### Metrics (`metrics.py`)

- Prometheus metrics recording
- HTTP metrics server

## Design Principles

1. **Dependency Injection**: All major classes accept dependencies via constructor
2. **Protocol-based Interfaces**: Use Python protocols for loose coupling
3. **Async-first**: Core operations are async with sync wrappers
4. **Testability**: MockAgentBridgeFactory enables testing without real agents
5. **Configuration-driven**: YAML-based configuration for flexibility
