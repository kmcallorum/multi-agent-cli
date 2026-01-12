# Configuration

## Configuration File

By default, multi-agent-cli looks for `agents.yaml` in the current directory.

### agents.yaml

```yaml
agents:
  pm:
    enabled: true
    path: "./pm/dist/index.js"
    timeout: 60
    env:
      DEBUG: "true"

  research:
    enabled: true
    path: "./research/dist/index.js"
    timeout: 90
    env: {}

  index:
    enabled: true
    path: "./index/dist/index.js"
    timeout: 120
    env: {}

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

### Agent Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | Yes | - | Agent identifier |
| enabled | boolean | No | true | Whether agent is enabled |
| path | string | Yes | - | Path to agent's index.js |
| timeout | integer | No | 60 | Execution timeout in seconds |
| env | object | No | {} | Environment variables |

### Settings Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| max_parallel_workers | integer | 3 | Maximum concurrent agents |
| default_timeout | integer | 60 | Default timeout in seconds |
| metrics_enabled | boolean | true | Enable Prometheus metrics |
| metrics_port | integer | 9090 | Metrics server port |

### Output Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| format | string | "rich" | Output format (rich, json, table) |
| verbose | boolean | false | Enable verbose output |
| save_results | boolean | true | Save results to files |
| results_dir | string | "./results" | Results directory |

## Workflow Files

### workflow.yaml

```yaml
name: "Workflow Name"
description: "Description of workflow"

steps:
  - name: "Step Name"
    agent: agent_name
    action: action_name
    params:
      key: value
    on_error: continue  # or "fail"
    depends_on:
      - "Previous Step Name"
    timeout: 120  # optional override

quality_gates:
  max_fixmes: 5
  min_documentation_score: 0.8
  max_dead_code_percent: 5
```

### Step Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | Yes | - | Step identifier |
| agent | string | Yes | - | Agent to use |
| action | string | Yes | - | Action to perform |
| params | object | No | {} | Action parameters |
| on_error | string | No | "fail" | "fail" or "continue" |
| depends_on | array | No | [] | Dependency step names |
| timeout | integer | No | - | Step-specific timeout |

### Quality Gates

| Field | Type | Description |
|-------|------|-------------|
| max_fixmes | integer | Maximum allowed FIXME count |
| min_documentation_score | float | Minimum documentation score (0-1) |
| max_dead_code_percent | float | Maximum dead code percentage |

## Environment Variables

| Variable | Description |
|----------|-------------|
| PYTEST_AGENTS_CONFIG | Override config file path |
| MULTI_AGENT_CLI_VERBOSE | Enable verbose output |
| MULTI_AGENT_CLI_FORMAT | Set output format |
