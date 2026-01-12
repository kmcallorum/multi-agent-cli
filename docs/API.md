# API Reference

## Core Classes

### AgentExecutor

Execute individual agent actions.

```python
from multi_agent_cli.executor import AgentExecutor

executor = AgentExecutor(
    agent_bridge=bridge,
    metrics=metrics_recorder,
    default_timeout=60
)

# Async execution
result = await executor.execute(
    agent="pm",
    action="track_tasks",
    params={"path": "./src"},
    timeout=120
)

# Sync execution
result = executor.execute_sync(
    agent="pm",
    action="track_tasks",
    params={"path": "./src"}
)
```

### AgentCoordinator

Coordinate multiple agent executions.

```python
from multi_agent_cli.coordinator import AgentCoordinator

coordinator = AgentCoordinator(
    executor=executor,
    max_workers=3,
    metrics=metrics_recorder
)

# Parallel execution
tasks = [
    ("pm", "track_tasks", {"path": "./src"}),
    ("research", "analyze", {"path": "./README.md"}),
]
results = await coordinator.execute_parallel(tasks)

# Workflow execution
result = await coordinator.execute_workflow(workflow, strict=True)
```

## Models

### AgentConfig

```python
from multi_agent_cli.models.agent import AgentConfig

config = AgentConfig(
    name="pm",
    enabled=True,
    path="./pm/dist/index.js",
    timeout=60,
    env={"DEBUG": "true"}
)
```

### Workflow

```python
from multi_agent_cli.models.workflow import Workflow, WorkflowStep

workflow = Workflow(
    name="Quality Check",
    description="Code quality analysis",
    steps=[
        WorkflowStep(
            name="Track Tasks",
            agent="pm",
            action="track_tasks",
            params={"path": "./src"},
            on_error="continue"
        )
    ],
    quality_gates=QualityGates(max_fixmes=5)
)
```

### AgentResult

```python
from multi_agent_cli.models.results import AgentResult

# Success result
result = AgentResult.success(
    agent="pm",
    action="track_tasks",
    data={"count": 5},
    duration_seconds=1.5
)

# Failure result
result = AgentResult.failure(
    agent="pm",
    action="track_tasks",
    error="Timeout",
    duration_seconds=60.0
)
```

## Factory Pattern

### Creating Agent Bridges

```python
from multi_agent_cli.factory import (
    get_default_factory,
    set_default_factory,
    MockAgentBridgeFactory
)

# Use default factory
factory = get_default_factory()
bridge = factory.create(config)

# Use mock factory for testing
mock_factory = MockAgentBridgeFactory({
    "pm.track_tasks": {"status": "success", "data": {}}
})
set_default_factory(mock_factory)
```

## Configuration

### Loading Configuration

```python
from multi_agent_cli.config import (
    load_config,
    load_workflow,
    create_default_config,
    save_config
)

# Load from file
config = load_config("agents.yaml")

# Create default
config = create_default_config()

# Save configuration
save_config(config, "output.yaml")

# Load workflow
workflow = load_workflow("workflow.yaml")
```

## Reporters

### Using Reporters

```python
from multi_agent_cli.reporters import (
    RichReporter,
    JSONReporter,
    TableReporter,
    get_reporter
)

# Get reporter by type
reporter = get_reporter("rich", verbose=True)

# Display results
reporter.display_result(agent_result)
reporter.display_workflow_result(workflow_result)
reporter.display_results([result1, result2])
```

## Metrics

### Recording Metrics

```python
from multi_agent_cli.metrics import (
    MetricsRecorder,
    get_metrics,
    start_metrics_server
)

# Get global metrics instance
metrics = get_metrics()

# Record metrics
metrics.record_agent_invocation("pm", "track_tasks")
metrics.record_agent_success("pm", "track_tasks", 1.5)
metrics.record_workflow_complete("quality_check", True, 10.0, 0)

# Start metrics server
start_metrics_server(port=9090)
```
