# multi-agent-cli

[![PyPI](https://img.shields.io/pypi/v/multi-agent-cli.svg)](https://pypi.org/project/multi-agent-cli/)
[![CI](https://github.com/kmcallorum/multi-agent-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/kmcallorum/multi-agent-cli/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kmcallorum/multi-agent-cli/graph/badge.svg)](https://codecov.io/gh/kmcallorum/multi-agent-cli)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Command-line tool for orchestrating multiple AI agents in parallel or sequence. Think "kubectl for AI agents."

## Features

- **Single Agent Execution**: Run one agent with specific action and parameters
- **Parallel Orchestration**: Run multiple agents simultaneously with rate limiting
- **Sequential Workflows**: Chain agent operations with data flow between steps
- **Rich Terminal Output**: Beautiful progress bars, tables, and status indicators
- **Prometheus Metrics**: Production-ready observability and monitoring
- **100% Test Coverage**: Thoroughly tested and reliable

## Quick Start

```bash
# Install
pip install multi-agent-cli

# Initialize configuration
multi-agent-cli init

# Run single agent
multi-agent-cli run pm track_tasks --path ./src

# Run parallel analysis
multi-agent-cli parallel --agents pm,research,index --path ./src

# Execute workflow
multi-agent-cli workflow code-review.yaml
```

## Installation

```bash
# From PyPI
pip install multi-agent-cli

# From source
git clone https://github.com/kmcallorum/multi-agent-cli.git
cd multi-agent-cli
pip install -e ".[dev]"
```

### Requirements

- Python 3.11+
- pytest-agents 1.0.0+

## Usage

### Running a Single Agent

```bash
# Basic usage
multi-agent-cli run AGENT ACTION [OPTIONS]

# Examples
multi-agent-cli run pm track_tasks --path ./src
multi-agent-cli run research analyze_document --path README.md
multi-agent-cli run index index_repository --path ./src

# With JSON parameters
multi-agent-cli run pm track_tasks --params '{"include_done": true}'

# Save output to file
multi-agent-cli run pm track_tasks --output results.json
```

### Parallel Execution

```bash
# Run multiple agents in parallel
multi-agent-cli parallel --agents pm,research,index --path ./src

# Limit parallel workers
multi-agent-cli parallel --agents pm,research,index --max-workers 2

# Save aggregated results
multi-agent-cli parallel --agents pm,research --output parallel_results.json
```

### Workflow Execution

```bash
# Run a workflow file
multi-agent-cli workflow code-review.yaml

# Strict mode (fail on first error)
multi-agent-cli workflow compliance-check.yaml --strict

# Continue on errors
multi-agent-cli workflow analysis.yaml --continue-on-error
```

### Configuration Management

```bash
# Show current configuration
multi-agent-cli config show

# Validate configuration file
multi-agent-cli config validate agents.yaml

# Initialize with example workflows
multi-agent-cli config init --example-workflows
```

### Metrics Server

```bash
# Start Prometheus metrics server
multi-agent-cli metrics --port 9090

# Access metrics at http://localhost:9090/metrics
```

## Configuration

### agents.yaml

```yaml
agents:
  pm:
    enabled: true
    path: "./pm/dist/index.js"
    timeout: 60

  research:
    enabled: true
    path: "./research/dist/index.js"
    timeout: 90

  index:
    enabled: true
    path: "./index/dist/index.js"
    timeout: 120

settings:
  max_parallel_workers: 3
  default_timeout: 60
  metrics_enabled: true
  metrics_port: 9090

output:
  format: "rich"
  verbose: false
  save_results: true
  results_dir: "./results"
```

### Workflow Definition

```yaml
name: "Code Quality Analysis"
description: "Comprehensive code quality check"

steps:
  - name: "Track Technical Debt"
    agent: pm
    action: track_tasks
    params:
      path: "./src"
    on_error: continue

  - name: "Analyze Documentation"
    agent: research
    action: analyze_document
    params:
      path: "./README.md"
    on_error: fail

  - name: "Index Codebase"
    agent: index
    action: index_repository
    params:
      path: "./src"
    depends_on:
      - "Track Technical Debt"

quality_gates:
  max_fixmes: 5
  min_documentation_score: 0.8
  max_dead_code_percent: 5
```

## Output Formats

```bash
# Rich terminal output (default)
multi-agent-cli run pm track_tasks

# JSON output
multi-agent-cli --format json run pm track_tasks

# Table output
multi-agent-cli --format table run pm track_tasks
```

## Docker

```bash
# Build image
docker build -t multi-agent-cli .

# Run single agent
docker run -v $(pwd)/src:/workspace/src multi-agent-cli run pm track_tasks

# Run with docker-compose
docker-compose up multi-agent-cli
```

## Development

```bash
# Clone repository
git clone https://github.com/kmcallorum/multi-agent-cli.git
cd multi-agent-cli

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/multi_agent_cli --cov-report=term-missing

# Lint
ruff check src tests
ruff format src tests

# Type check
mypy src
```

## Metrics

The CLI exposes Prometheus metrics when using the `metrics` command:

- `agent_invocations_total` - Total agent invocations by agent/action
- `agent_invocations_success_total` - Successful invocations
- `agent_invocations_error_total` - Failed invocations
- `agent_duration_seconds` - Execution duration histogram
- `workflows_executed_total` - Total workflows executed
- `workflows_success_total` - Successful workflows
- `parallel_executions_total` - Total parallel executions
- `cli_commands_total` - CLI commands executed

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security policy and reporting vulnerabilities.

## License

MIT License - see [LICENSE](LICENSE) for details.
