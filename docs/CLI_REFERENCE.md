# CLI Reference

## Global Options

```bash
multi-agent-cli [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --config PATH      Path to config file (default: agents.yaml)
  -v, --verbose          Verbose output
  -q, --quiet            Quiet output (errors only)
  -f, --format FORMAT    Output format: rich, json, table
  --version              Show version and exit
  --help                 Show help and exit
```

## Commands

### run

Execute a single agent action.

```bash
multi-agent-cli run AGENT ACTION [OPTIONS]

Arguments:
  AGENT   Agent name (pm, research, index)
  ACTION  Action to perform

Options:
  -p, --path PATH       Project path (default: .)
  --params JSON         Additional parameters as JSON
  -o, --output FILE     Save results to file
  -t, --timeout SECS    Execution timeout (default: 60)
```

**Examples:**

```bash
multi-agent-cli run pm track_tasks --path ./src
multi-agent-cli run research analyze_document --path README.md
multi-agent-cli run pm track_tasks --params '{"include_done": true}'
multi-agent-cli run pm track_tasks --output results.json
```

### parallel

Run multiple agents in parallel.

```bash
multi-agent-cli parallel [OPTIONS]

Options:
  -a, --agents LIST     Comma-separated agent names
  -w, --workflow FILE   Workflow definition file
  -n, --max-workers N   Maximum parallel workers (default: 3)
  -p, --path PATH       Project path for all agents
  -o, --output FILE     Save results to file
  --aggregate           Combine results into single report
```

**Examples:**

```bash
multi-agent-cli parallel --agents pm,research,index --path ./src
multi-agent-cli parallel --agents pm,research --max-workers 2
multi-agent-cli parallel --agents pm,research --output results.json
```

### workflow

Execute a sequential workflow.

```bash
multi-agent-cli workflow FILE [OPTIONS]

Arguments:
  FILE  Workflow YAML file

Options:
  --strict              Fail on first error
  --continue-on-error   Continue even if steps fail
  -o, --output FILE     Save workflow results to file
```

**Examples:**

```bash
multi-agent-cli workflow code-review.yaml
multi-agent-cli workflow compliance-check.yaml --strict
multi-agent-cli workflow analysis.yaml --output results.json
```

### list

List available agents.

```bash
multi-agent-cli list [OPTIONS]

Options:
  -v, --verbose   Show agent capabilities
```

### config

Configuration management.

```bash
multi-agent-cli config COMMAND

Commands:
  show       Show current configuration
  validate   Validate configuration file
  init       Create example configuration
```

**Examples:**

```bash
multi-agent-cli config show
multi-agent-cli config validate agents.yaml
multi-agent-cli config init --output my-config.yaml
multi-agent-cli config init --example-workflows
```

### metrics

Start Prometheus metrics server.

```bash
multi-agent-cli metrics [OPTIONS]

Options:
  -p, --port PORT   Prometheus metrics port (default: 9090)
  -h, --host HOST   Host to bind to (default: 0.0.0.0)
```

### init

Initialize project with default configuration.

```bash
multi-agent-cli init [OPTIONS]

Options:
  --example-workflows   Include example workflows
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | Agent/workflow error |
| 2    | Unexpected error |
