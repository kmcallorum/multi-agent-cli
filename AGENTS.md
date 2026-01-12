# multi-agent-cli - AGENTS.md

## Project Vision

A production-grade command-line tool for orchestrating multiple AI agents in parallel or sequence. Think "kubectl for AI agents" - a single CLI that coordinates pytest-agents' PM, Research, and Index agents to perform complex multi-agent workflows from the terminal.

**Target Users:**
- Developers using pytest-agents who want CLI access
- DevOps engineers automating code quality checks
- CI/CD pipelines needing agent-based validation
- Teams running automated code analysis

**Core Value Proposition:**
> "Run sophisticated multi-agent workflows from a single command, with full observability, parallel execution, and production-ready architecture."

## EXECUTION MODE: AUTONOMOUS

Claude should make ALL changes without asking for approval unless a critical architectural decision arises.
Quality gates at the end determine success. If all tests pass, linting succeeds, and coverage hits 100%, the implementation is acceptable.

---

## What It Does

### Core Functionality
1. **Single Agent Execution**: Run one agent with specific action and parameters
2. **Parallel Agent Orchestration**: Run multiple agents simultaneously with rate limiting
3. **Sequential Workflows**: Chain agent operations with data flow between steps
4. **Configuration Management**: Load agent configs from YAML files or environment
5. **Rich Output**: Beautiful terminal output with progress bars, tables, and status
6. **Metrics Export**: Prometheus metrics for production monitoring
7. **Result Aggregation**: Combine results from multiple agents into unified reports

### What It Does NOT Do
- ❌ NO web UI (CLI only, maybe HTML reports)
- ❌ NO agent training or model fine-tuning (just orchestration)
- ❌ NO database (file-based configuration and results)
- ❌ NO authentication/authorization (local tool)
- ❌ NO distributed execution across machines (single-host only)
- ❌ NO agent development (uses existing pytest-agents)

---

## Project Structure

```
multi-agent-cli/
├── src/
│   └── multi_agent_cli/
│       ├── __init__.py
│       ├── cli.py                  # Click-based CLI commands
│       ├── coordinator.py          # Multi-agent coordination logic
│       ├── config.py               # Configuration loading and validation
│       ├── executor.py             # Agent execution engine
│       ├── reporters.py            # Result formatting and reporting
│       ├── metrics.py              # Prometheus metrics
│       ├── factory.py              # DI factory for agent clients
│       └── models/
│           ├── __init__.py
│           ├── agent.py            # Agent configuration models
│           ├── workflow.py         # Workflow definition models
│           └── results.py          # Result aggregation models
├── tests/
│   ├── unit/
│   │   ├── test_cli.py
│   │   ├── test_coordinator.py
│   │   ├── test_config.py
│   │   ├── test_executor.py
│   │   ├── test_factory.py
│   │   ├── test_reporters.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── test_single_agent.py
│   │   ├── test_parallel_execution.py
│   │   └── test_workflows.py
│   ├── fixtures/
│   │   ├── sample_configs/
│   │   └── mock_agents/
│   └── conftest.py
├── examples/
│   ├── basic_pm_run.py
│   ├── parallel_analysis.py
│   ├── sequential_workflow.py
│   └── custom_reporter.py
├── configs/
│   ├── agents.yaml.example
│   └── workflows.yaml.example
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CLI_REFERENCE.md
│   ├── CONFIGURATION.md
│   └── API.md
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── release.yml
│       ├── security.yml
│       └── coverage.yml
├── pyproject.toml
├── README.md
├── AGENTS.md                        # This file
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── LICENSE
├── Dockerfile
├── docker-compose.yml
└── .gitignore
```

---

## Technical Stack

### Core Dependencies (MUST USE)
```toml
[project.dependencies]
click = ">=8.1.0"                  # CLI framework
rich = ">=13.0.0"                  # Beautiful terminal output
pydantic = ">=2.0.0"               # Data validation
pytest-agents = ">=1.0.0"          # Agent orchestration (your package!)
pyyaml = ">=6.0.0"                 # Config file parsing
prometheus-client = ">=0.19.0"     # Metrics
typing-extensions = ">=4.9.0"      # Type hints
```

### Dev Dependencies
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "types-PyYAML>=6.0.0",
]
```

### DO NOT ADD
- ❌ No FastAPI/Flask (not building an API)
- ❌ No SQLAlchemy (no database)
- ❌ No Celery/Redis (no distributed tasks)
- ❌ No complex ORMs
- ❌ No web frameworks

---

## Architecture Constraints

### DO: Simple and Testable
```python
# GOOD: Simple, testable, injectable
class AgentExecutor:
    def __init__(
        self, 
        agent_bridge: AgentBridge,
        metrics: MetricsRecorder | None = None
    ):
        self.bridge = agent_bridge
        self.metrics = metrics
    
    async def execute(
        self, 
        agent: str, 
        action: str, 
        params: dict
    ) -> AgentResult:
        result = self.bridge.invoke_agent(agent, action, params)
        return AgentResult.from_dict(result)

# BAD: Over-engineered
class AbstractAgentExecutionStrategy(ABC):
    @abstractmethod
    def execute(self) -> ExecutionResult:
        pass

class FactoryStrategyExecutor(AbstractAgentExecutionStrategy):
    # ... 500 lines of complexity
```

### DO: Dependency Injection Everywhere
```python
# All major classes should support DI
class MultiAgentCLI:
    def __init__(
        self,
        executor: AgentExecutor,
        reporter: ResultReporter,
        metrics: MetricsRecorder,
    ):
        self.executor = executor
        self.reporter = reporter
        self.metrics = metrics
```

### DO: Factory Pattern for Agent Creation
```python
class AgentClientFactory:
    """Create agent bridge instances."""
    
    def create_bridge(
        self, 
        config: AgentConfig
    ) -> AgentBridge:
        """Create configured agent bridge."""
        pass
    
    def create_mock_bridge(
        self, 
        mock_responses: dict
    ) -> AgentBridge:
        """Create mock bridge for testing."""
        pass
```

### DON'T: Over-Abstract
- No "ExecutorRegistry" singletons
- No "StrategyPattern" unless absolutely necessary
- Prefer composition over inheritance
- Keep it flat and obvious

---

## CLI Design

### Command Structure
```bash
# Main command
multi-agent-cli [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]

# Global options (apply to all commands)
--config PATH       # Path to config file (default: agents.yaml)
--verbose/-v        # Verbose output
--quiet/-q          # Quiet output (errors only)
--format FORMAT     # Output format: rich, json, table
--metrics-port PORT # Prometheus metrics port (default: 9090)
```

### Core Commands

#### 1. **run** - Execute Single Agent
```bash
multi-agent-cli run AGENT ACTION [OPTIONS]

# Examples
multi-agent-cli run pm track_tasks --path ./src
multi-agent-cli run research analyze_document --path README.md
multi-agent-cli run index index_repository --path ./src

# Options
--path PATH           # Project path
--params JSON         # Additional parameters as JSON
--output FILE         # Save results to file
--timeout SECONDS     # Execution timeout (default: 60)
```

#### 2. **parallel** - Run Multiple Agents in Parallel
```bash
multi-agent-cli parallel [OPTIONS]

# Examples
multi-agent-cli parallel --agents pm,research,index --path ./src
multi-agent-cli parallel --workflow analysis.yaml

# Options
--agents LIST         # Comma-separated agent names
--workflow FILE       # Workflow definition file
--max-workers N       # Maximum parallel workers (default: 3)
--path PATH           # Project path for all agents
--aggregate           # Combine results into single report
```

#### 3. **workflow** - Run Sequential Workflow
```bash
multi-agent-cli workflow FILE [OPTIONS]

# Examples
multi-agent-cli workflow code-review.yaml
multi-agent-cli workflow compliance-check.yaml --strict

# Options
--strict              # Fail on first error
--continue-on-error   # Continue even if steps fail
--output FILE         # Save workflow results
```

#### 4. **list** - List Available Agents
```bash
multi-agent-cli list [OPTIONS]

# Examples
multi-agent-cli list
multi-agent-cli list --verbose  # Show agent capabilities

# Output
Available agents:
  ✓ pm        - Project management agent (track tasks, milestones)
  ✓ research  - Research agent (analyze docs, extract info)
  ✓ index     - Index agent (code search, dependency analysis)
```

#### 5. **config** - Manage Configuration
```bash
multi-agent-cli config SUBCOMMAND

# Subcommands
multi-agent-cli config show           # Show current config
multi-agent-cli config validate FILE  # Validate config file
multi-agent-cli config init           # Create example config
```

#### 6. **metrics** - Start Metrics Server
```bash
multi-agent-cli metrics [OPTIONS]

# Examples
multi-agent-cli metrics --port 9090
multi-agent-cli metrics --host 0.0.0.0

# Starts HTTP server at http://localhost:9090/metrics
```

#### 7. **init** - Initialize Project
```bash
multi-agent-cli init [OPTIONS]

# Examples
multi-agent-cli init                    # Create default config
multi-agent-cli init --example-workflows # Include example workflows

# Creates:
#   agents.yaml
#   workflows/
#   .multi-agent-cli/
```

---

## Configuration Files

### agents.yaml
```yaml
# Agent configuration
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

# Global settings
settings:
  max_parallel_workers: 3
  default_timeout: 60
  metrics_enabled: true
  metrics_port: 9090
  
# Output preferences
output:
  format: "rich"  # rich, json, table
  verbose: false
  save_results: true
  results_dir: "./results"
```

### workflow.yaml
```yaml
# Sequential workflow definition
name: "Code Quality Analysis"
description: "Comprehensive code quality check using multiple agents"

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

# Quality gates
quality_gates:
  max_fixmes: 5
  min_documentation_score: 0.8
  max_dead_code_percent: 5
```

---

## Core Data Models

### Agent Configuration (Pydantic)
```python
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    """Agent configuration model."""
    
    name: str = Field(..., description="Agent name (pm, research, index)")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    path: str = Field(..., description="Path to agent's index.js")
    timeout: int = Field(default=60, description="Execution timeout in seconds")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    
class AgentsConfig(BaseModel):
    """Complete agents configuration."""
    
    agents: dict[str, AgentConfig]
    settings: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
```

### Workflow Definition
```python
class WorkflowStep(BaseModel):
    """Single workflow step."""
    
    name: str
    agent: str
    action: str
    params: dict[str, Any] = Field(default_factory=dict)
    on_error: Literal["fail", "continue"] = "fail"
    depends_on: list[str] = Field(default_factory=list)
    timeout: int | None = None

class Workflow(BaseModel):
    """Complete workflow definition."""
    
    name: str
    description: str
    steps: list[WorkflowStep]
    quality_gates: dict[str, Any] = Field(default_factory=dict)
```

### Results
```python
class AgentResult(BaseModel):
    """Result from single agent execution."""
    
    agent: str
    action: str
    status: Literal["success", "error"]
    data: dict[str, Any]
    duration_seconds: float
    timestamp: str
    error: str | None = None

class WorkflowResult(BaseModel):
    """Result from workflow execution."""
    
    workflow_name: str
    steps_completed: int
    steps_failed: int
    total_duration: float
    results: list[AgentResult]
    quality_gates_passed: bool
    summary: dict[str, Any]
```

---

## Implementation Guidelines

### 1. CLI Implementation (cli.py)

**Use Click with Rich integration:**
```python
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

@click.group()
@click.option('--config', default='agents.yaml', help='Config file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """Multi-agent orchestration CLI."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config(config)
    ctx.obj['verbose'] = verbose

@cli.command()
@click.argument('agent')
@click.argument('action')
@click.option('--path', default='.', help='Project path')
@click.option('--output', help='Output file')
@click.pass_context
def run(ctx, agent, action, path, output):
    """Run a single agent."""
    executor = create_executor(ctx.obj['config'])
    
    with Progress() as progress:
        task = progress.add_task(f"Running {agent}.{action}...", total=100)
        result = executor.execute(agent, action, {'path': path})
        progress.update(task, completed=100)
    
    display_result(result)
    
    if output:
        save_result(result, output)
```

### 2. Agent Coordinator (coordinator.py)

**Parallel execution with rate limiting:**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AgentCoordinator:
    """Coordinate multiple agent executions."""
    
    def __init__(
        self,
        executor: AgentExecutor,
        max_workers: int = 3,
        metrics: MetricsRecorder | None = None
    ):
        self.executor = executor
        self.max_workers = max_workers
        self.metrics = metrics
    
    async def execute_parallel(
        self,
        tasks: list[tuple[str, str, dict]]
    ) -> list[AgentResult]:
        """Execute multiple agents in parallel with rate limiting."""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def rate_limited_execute(agent, action, params):
            async with semaphore:
                return await self.executor.execute(agent, action, params)
        
        results = await asyncio.gather(*[
            rate_limited_execute(agent, action, params)
            for agent, action, params in tasks
        ])
        
        return results
    
    async def execute_workflow(
        self,
        workflow: Workflow
    ) -> WorkflowResult:
        """Execute workflow steps in order, respecting dependencies."""
        completed_steps = {}
        results = []
        
        for step in workflow.steps:
            # Wait for dependencies
            for dep in step.depends_on:
                if dep not in completed_steps:
                    raise WorkflowError(f"Dependency {dep} not completed")
            
            # Execute step
            try:
                result = await self.executor.execute(
                    step.agent,
                    step.action,
                    step.params
                )
                results.append(result)
                completed_steps[step.name] = result
            except Exception as e:
                if step.on_error == "fail":
                    raise
                # Continue on error
                results.append(AgentResult(
                    agent=step.agent,
                    action=step.action,
                    status="error",
                    error=str(e),
                    data={},
                    duration_seconds=0,
                    timestamp=datetime.now().isoformat()
                ))
        
        return WorkflowResult.from_results(workflow, results)
```

### 3. Executor (executor.py)

**Agent execution with metrics:**
```python
import time
from datetime import datetime

class AgentExecutor:
    """Execute individual agent actions."""
    
    def __init__(
        self,
        agent_bridge: AgentBridge,
        metrics: MetricsRecorder | None = None
    ):
        self.bridge = agent_bridge
        self.metrics = metrics
    
    async def execute(
        self,
        agent: str,
        action: str,
        params: dict[str, Any]
    ) -> AgentResult:
        """Execute single agent action."""
        start = time.time()
        
        # Track invocation
        if self.metrics:
            self.metrics.increment_counter(
                'agent_invocations_total',
                {'agent': agent, 'action': action}
            )
        
        try:
            # Invoke agent via pytest-agents bridge
            result = self.bridge.invoke_agent(agent, action, params)
            
            duration = time.time() - start
            
            # Track success
            if self.metrics:
                self.metrics.increment_counter(
                    'agent_invocations_success_total',
                    {'agent': agent, 'action': action}
                )
                self.metrics.observe_histogram(
                    'agent_duration_seconds',
                    duration,
                    {'agent': agent, 'action': action}
                )
            
            return AgentResult(
                agent=agent,
                action=action,
                status=result.get('status', 'success'),
                data=result.get('data', {}),
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
                error=result.get('data', {}).get('error')
            )
        
        except Exception as e:
            duration = time.time() - start
            
            # Track error
            if self.metrics:
                self.metrics.increment_counter(
                    'agent_invocations_error_total',
                    {'agent': agent, 'action': action}
                )
            
            return AgentResult(
                agent=agent,
                action=action,
                status="error",
                data={},
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
```

### 4. Factory Pattern (factory.py)

**DI for agent bridge creation:**
```python
from typing import Protocol

class AgentBridgeFactory(Protocol):
    """Protocol for agent bridge factories."""
    
    def create(self, config: AgentsConfig) -> AgentBridge:
        """Create agent bridge from config."""
        ...

class DefaultAgentBridgeFactory:
    """Default factory using pytest-agents."""
    
    def create(self, config: AgentsConfig) -> AgentBridge:
        """Create real agent bridge."""
        from pytest_agents import AgentBridge, PytestAgentsConfig
        
        pytest_config = PytestAgentsConfig(
            agent_pm_enabled=config.agents.get('pm', {}).enabled,
            agent_pm_path=config.agents.get('pm', {}).path,
            # ... configure other agents
        )
        
        return AgentBridge(pytest_config)

class MockAgentBridgeFactory:
    """Factory for testing with mock responses."""
    
    def __init__(self, mock_responses: dict[str, dict]):
        """Initialize with mock responses.
        
        Args:
            mock_responses: {
                'pm.track_tasks': {'status': 'success', 'data': {...}},
                'research.analyze_document': {...}
            }
        """
        self.mock_responses = mock_responses
        self.invocations = []
    
    def create(self, config: AgentsConfig) -> AgentBridge:
        """Create mock agent bridge."""
        return MockAgentBridge(self.mock_responses, self.invocations)

# Global factory
_default_factory: AgentBridgeFactory | None = None

def get_default_factory() -> AgentBridgeFactory:
    """Get default factory instance."""
    global _default_factory
    if _default_factory is None:
        _default_factory = DefaultAgentBridgeFactory()
    return _default_factory

def set_default_factory(factory: AgentBridgeFactory | None) -> None:
    """Set default factory (for testing)."""
    global _default_factory
    _default_factory = factory
```

### 5. Rich Output (reporters.py)

**Beautiful terminal output:**
```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

class RichReporter:
    """Format results with Rich library."""
    
    def __init__(self):
        self.console = Console()
    
    def display_result(self, result: AgentResult):
        """Display single agent result."""
        if result.status == "success":
            self.console.print(f"✓ {result.agent}.{result.action}", style="green")
        else:
            self.console.print(f"✗ {result.agent}.{result.action}", style="red")
            if result.error:
                self.console.print(f"  Error: {result.error}", style="red")
        
        # Show data in formatted table
        if result.data:
            table = Table(title=f"{result.agent} Results")
            for key, value in result.data.items():
                table.add_row(str(key), str(value))
            self.console.print(table)
    
    def display_workflow_result(self, result: WorkflowResult):
        """Display workflow results."""
        panel = Panel(
            f"[bold]{result.workflow_name}[/bold]\n"
            f"Steps: {result.steps_completed} completed, {result.steps_failed} failed\n"
            f"Duration: {result.total_duration:.2f}s",
            title="Workflow Summary",
            border_style="green" if result.quality_gates_passed else "red"
        )
        self.console.print(panel)
        
        # Show individual results
        for step_result in result.results:
            self.display_result(step_result)

class JSONReporter:
    """Output results as JSON."""
    
    def display_result(self, result: AgentResult):
        """Display as JSON."""
        print(result.model_dump_json(indent=2))
```

---

## Testing Strategy

### 100% Coverage Target

**Every function must be tested. No exceptions.**

### Mock Strategy

**Use MockAgentBridgeFactory for all tests:**
```python
# conftest.py
import pytest
from multi_agent_cli.factory import MockAgentBridgeFactory, set_default_factory

@pytest.fixture
def mock_agent_responses():
    """Standard mock responses for testing."""
    return {
        'pm.track_tasks': {
            'status': 'success',
            'data': {
                'tasks': [
                    {'id': '1', 'type': 'todo', 'description': 'Test task'}
                ],
                'count': 1
            }
        },
        'research.analyze_document': {
            'status': 'success',
            'data': {
                'summary': 'Test document',
                'completeness': 0.9
            }
        }
    }

@pytest.fixture
def mock_factory(mock_agent_responses):
    """Mock factory for testing."""
    factory = MockAgentBridgeFactory(mock_agent_responses)
    set_default_factory(factory)
    yield factory
    set_default_factory(None)  # Reset after test
```

### Unit Test Structure

**Test every class in isolation:**
```python
# tests/unit/test_executor.py
import pytest
from multi_agent_cli.executor import AgentExecutor

@pytest.mark.unit
class TestAgentExecutor:
    """Tests for AgentExecutor."""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_factory):
        """Test successful agent execution."""
        bridge = mock_factory.create(AgentsConfig(...))
        executor = AgentExecutor(bridge)
        
        result = await executor.execute('pm', 'track_tasks', {'path': './src'})
        
        assert result.status == "success"
        assert result.agent == "pm"
        assert result.action == "track_tasks"
        assert result.duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_execute_error(self, mock_factory):
        """Test error handling."""
        mock_factory.mock_responses['pm.track_tasks'] = {
            'status': 'error',
            'data': {'error': 'Test error'}
        }
        
        bridge = mock_factory.create(AgentsConfig(...))
        executor = AgentExecutor(bridge)
        
        result = await executor.execute('pm', 'track_tasks', {})
        
        assert result.status == "error"
        assert result.error == "Test error"
```

### Integration Test Strategy

**Test real agent bridge (optional, marked separately):**
```python
# tests/integration/test_single_agent.py
import pytest

@pytest.mark.integration
@pytest.mark.requires_agents  # Only run if agents are available
class TestSingleAgentIntegration:
    """Integration tests with real agents."""
    
    def test_pm_agent_track_tasks(self):
        """Test PM agent actually works."""
        # Use real AgentBridge, not mock
        pass
```

### Coverage Requirements

**pyproject.toml:**
```toml
[tool.coverage.run]
source = ["src/multi_agent_cli"]
branch = true
omit = []  # No omissions - 100% coverage

[tool.coverage.report]
fail_under = 100  # Fail CI if below 100%
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "\\.\\.\\.",
    "pass",
]
```

---

## Prometheus Metrics

### Metrics to Track

```python
# Agent execution metrics
agent_invocations_total              # Counter by agent/action
agent_invocations_success_total      # Counter by agent/action
agent_invocations_error_total        # Counter by agent/action
agent_duration_seconds               # Histogram by agent/action

# Coordinator metrics
workflows_executed_total             # Counter by workflow_name
workflows_success_total              # Counter by workflow_name
workflows_failed_total               # Counter by workflow_name
workflow_duration_seconds            # Histogram by workflow_name
workflow_steps_total                 # Gauge by workflow_name
workflow_steps_failed                # Gauge by workflow_name

# Parallel execution metrics
parallel_executions_total            # Counter
parallel_max_workers                 # Gauge
parallel_duration_seconds            # Histogram

# CLI metrics
cli_commands_total                   # Counter by command
cli_errors_total                     # Counter by command
```

### Metrics Server

```python
# metrics.py
from prometheus_client import start_http_server, Counter, Histogram, Gauge

class MetricsRecorder:
    """Record Prometheus metrics."""
    
    def __init__(self):
        self.agent_invocations = Counter(
            'agent_invocations_total',
            'Total agent invocations',
            ['agent', 'action']
        )
        self.agent_duration = Histogram(
            'agent_duration_seconds',
            'Agent execution duration',
            ['agent', 'action']
        )
        # ... more metrics
    
    def increment_counter(self, name: str, labels: dict):
        """Increment a counter."""
        getattr(self, name.replace('_total', '')).labels(**labels).inc()
    
    def observe_histogram(self, name: str, value: float, labels: dict):
        """Observe histogram value."""
        getattr(self, name.replace('_seconds', '')).labels(**labels).observe(value)

def start_metrics_server(port: int = 9090, host: str = "0.0.0.0"):
    """Start Prometheus metrics HTTP server."""
    start_http_server(port, host)
```

---

## Error Handling

### Custom Exceptions

```python
# exceptions.py
class MultiAgentCLIError(Exception):
    """Base exception for multi-agent-cli."""
    pass

class ConfigError(MultiAgentCLIError):
    """Configuration error."""
    pass

class AgentError(MultiAgentCLIError):
    """Agent execution error."""
    pass

class WorkflowError(MultiAgentCLIError):
    """Workflow execution error."""
    pass

class ValidationError(MultiAgentCLIError):
    """Validation error."""
    pass
```

### Error Handling Strategy

```python
# Proper error context
try:
    result = executor.execute(agent, action, params)
except AgentError as e:
    console.print(f"[red]Agent error:[/red] {e}")
    console.print(f"[yellow]Agent:[/yellow] {agent}")
    console.print(f"[yellow]Action:[/yellow] {action}")
    sys.exit(1)
except Exception as e:
    console.print(f"[red]Unexpected error:[/red] {e}")
    if verbose:
        console.print_exception()
    sys.exit(2)
```

---

## Security Requirements

### Input Validation

**Validate ALL user inputs:**
```python
def validate_agent_name(name: str) -> str:
    """Validate agent name."""
    if not name.isalnum():
        raise ValidationError(f"Invalid agent name: {name}")
    if name not in ['pm', 'research', 'index']:
        raise ValidationError(f"Unknown agent: {name}")
    return name

def validate_path(path: str, project_root: str) -> Path:
    """Validate path is within project root."""
    resolved = Path(path).resolve()
    root = Path(project_root).resolve()
    
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValidationError(f"Path outside project: {path}")
    
    return resolved
```

### No Code Injection

**Never use eval() or exec():**
```python
# NEVER do this
params = eval(user_input)  # DANGEROUS

# DO this instead
import json
params = json.loads(user_input)  # Safe
```

### Secure Logging

**Never log sensitive data:**
```python
# GOOD: Log sanitized data
logger.info(f"Executing {agent}.{action} with {len(params)} params")

# BAD: Log raw params (might contain secrets)
logger.info(f"Params: {params}")
```

---

## CI/CD Configuration

### GitHub Actions Workflows

#### ci.yml - Main CI Pipeline
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run ruff
        run: ruff check src tests
      
      - name: Run mypy
        run: mypy src
      
      - name: Run tests with coverage
        run: pytest --cov=src/multi_agent_cli --cov-report=xml --cov-report=term
      
      - name: Check 100% coverage
        run: |
          coverage report --fail-under=100
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage.xml
          fail_ci_if_error: true
```

#### security.yml - Security Scanning
```yaml
name: Security

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  codeql:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: python
      
      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
  
  snyk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Snyk
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high
```

#### release.yml - Automated PyPI Publishing
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install build tools
        run: pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

### dependabot.yml
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## Documentation Requirements

### README.md Structure

```markdown
# multi-agent-cli

[![PyPI](https://img.shields.io/pypi/v/multi-agent-cli.svg)](https://pypi.org/project/multi-agent-cli/)
[![CI](https://github.com/kmcallorum/multi-agent-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/kmcallorum/multi-agent-cli/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kmcallorum/multi-agent-cli/graph/badge.svg)](https://codecov.io/gh/kmcallorum/multi-agent-cli)
[![Snyk Security](https://snyk.io/test/github/kmcallorum/multi-agent-cli/badge.svg)](https://snyk.io/test/github/kmcallorum/multi-agent-cli)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Command-line tool for orchestrating multiple AI agents in parallel or sequence. Think "kubectl for AI agents."

## Features

- **Single Agent Execution**: Run one agent with specific action
- **Parallel Orchestration**: Run multiple agents simultaneously
- **Sequential Workflows**: Chain agent operations with dependencies
- **Rich Terminal Output**: Beautiful progress bars and tables
- **Prometheus Metrics**: Production-ready observability
- **100% Test Coverage**: Thoroughly tested and reliable

## Quick Start

```bash
# Install
pip install multi-agent-cli

# Run single agent
multi-agent-cli run pm track_tasks --path ./src

# Run parallel analysis
multi-agent-cli parallel --agents pm,research,index --path ./src

# Execute workflow
multi-agent-cli workflow code-review.yaml
```

## Installation
## Usage Examples
## Configuration
## Workflows
## Metrics
## Development
## Contributing
## License
```

### CONTRIBUTING.md

Standard contribution guidelines with:
- How to set up development environment
- Running tests (must maintain 100% coverage)
- Code style (ruff, mypy strict)
- Commit message format (conventional commits)
- PR process

### SECURITY.md

Security policy with:
- Supported versions
- How to report vulnerabilities
- Security best practices for users

---

## Docker Support

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source
COPY src/ src/

# CLI entrypoint
ENTRYPOINT ["multi-agent-cli"]
CMD ["--help"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  multi-agent-cli:
    build: .
    volumes:
      - ./configs:/app/configs
      - ./results:/app/results
      - ./src:/workspace/src:ro
    environment:
      - PYTEST_AGENTS_CONFIG=/app/configs/agents.yaml
    command: run pm track_tasks --path /workspace/src
  
  metrics:
    build: .
    command: metrics --port 9090 --host 0.0.0.0
    ports:
      - "9090:9090"
```

---

## Quality Gates (Must Pass)

### Automated Checks
```bash
# All must pass for approval
ruff check src tests         # Linting passes
ruff format --check src tests # Formatting correct
mypy src                     # Type checking passes
pytest --cov=src/multi_agent_cli --cov-report=term --cov-fail-under=100
                             # 100% coverage achieved
docker build .               # Docker builds successfully
```

### Code Quality Standards
- ✅ Type hints on ALL functions (no `Any` unless necessary)
- ✅ Docstrings on ALL public APIs
- ✅ No `# type: ignore` unless absolutely necessary
- ✅ No security vulnerabilities (Snyk + CodeQL)
- ✅ Max line length: 88 (Black standard)
- ✅ No unused imports
- ✅ No dead code

---

## Repository Configuration

### GitHub Repository Settings

**Description:**
> "Command-line tool for orchestrating multiple AI agents. Run pytest-agents PM, Research, and Index agents in parallel or sequence with full observability."

**Topics:**
```
ai, agents, cli, orchestration, pytest-agents, automation, 
devops, code-quality, multi-agent, python, testing, 
prometheus, metrics, parallel-execution, workflow
```

**Features to Enable:**
- ✅ Issues
- ✅ Discussions (optional)
- ✅ Projects (optional)
- ✅ Wiki (disabled - use docs/)
- ✅ Sponsorship (optional)

**Branch Protection (main):**
- ✅ Require pull request reviews
- ✅ Require status checks to pass
  - CI / test (Python 3.11)
  - CI / test (Python 3.12)
  - Security / codeql
  - Security / snyk
- ✅ Require branches to be up to date
- ✅ Require conversation resolution

**Secrets to Configure:**
- `PYPI_API_TOKEN` - For automated releases
- `CODECOV_TOKEN` - For coverage reporting
- `SNYK_TOKEN` - For security scanning

---

## Anti-Patterns to Avoid

### ❌ DON'T: Over-engineer the CLI
```python
# BAD: Too many abstraction layers
class AbstractCommandExecutor(ABC):
    @abstractmethod
    def execute(self) -> CommandResult:
        pass

class FactoryCommandExecutor(AbstractCommandExecutor):
    # ... layers upon layers
```

### ✅ DO: Keep it simple
```python
# GOOD: Direct and clear
@cli.command()
def run(agent, action, path):
    executor = AgentExecutor(create_bridge())
    result = executor.execute(agent, action, {'path': path})
    console.print(result)
```

### ❌ DON'T: Create unnecessary abstractions
```python
# BAD: Registry pattern where it's not needed
class CommandRegistry:
    _commands = {}
    
    @classmethod
    def register(cls, name, handler):
        cls._commands[name] = handler
```

### ✅ DO: Use Click's built-in patterns
```python
# GOOD: Click handles command registration
@cli.command()
def my_command():
    pass
```

### ❌ DON'T: Pollute logs with sensitive data
```python
# BAD: Logging full params
logger.info(f"Running with params: {params}")
```

### ✅ DO: Sanitize logs
```python
# GOOD: Log safely
logger.info(f"Running {agent}.{action} with {len(params)} params")
```

---

## Performance Considerations

### Async Everything
```python
# Agent calls are I/O bound - use async
async def execute_parallel(tasks):
    return await asyncio.gather(*[
        execute_task(task) for task in tasks
    ])
```

### Rate Limiting
```python
# Respect system resources
semaphore = asyncio.Semaphore(max_workers)

async def rate_limited_execute(agent, action, params):
    async with semaphore:
        return await executor.execute(agent, action, params)
```

### Progress Feedback
```python
# Always show progress for long operations
with Progress() as progress:
    task = progress.add_task("Running agents...", total=len(tasks))
    for result in results:
        progress.update(task, advance=1)
```

---

## Success Criteria

The project is complete when:

1. ✅ CLI works: `multi-agent-cli run pm track_tasks --path ./src`
2. ✅ Parallel execution works: `multi-agent-cli parallel --agents pm,research,index`
3. ✅ Workflows execute: `multi-agent-cli workflow example.yaml`
4. ✅ All tests pass: `pytest`
5. ✅ 100% coverage: `pytest --cov --cov-fail-under=100`
6. ✅ Type checking passes: `mypy src`
7. ✅ Linting passes: `ruff check src tests`
8. ✅ Docker builds: `docker build .`
9. ✅ README has clear examples
10. ✅ Can be installed: `pip install multi-agent-cli`
11. ✅ All badges working (CI, coverage, security)
12. ✅ GitHub repository configured with secrets

---

## Timeline Expectation

With this detailed AGENTS.md, Claude should be able to build this in:
- **Target: 4-6 hours** (more complex than prompt-optimizer)
- **Max acceptable: 8 hours**

If it takes longer, the AGENTS.md needs more detail or the scope is too large.

---

## Notes for Claude

- Prefer simplicity over cleverness
- Write testable code with dependency injection
- Use type hints religiously
- Keep functions small and focused
- 100% coverage is NON-NEGOTIABLE
- Rich output should be beautiful but not complex
- If unsure about a design decision, pick the simpler option
- The goal is a reliable CLI tool that orchestrates agents, not a framework

When complete, the tool should be immediately usable by developers who want to run pytest-agents from the command line without writing Python code.

---

## Example Usage Scenarios

### Scenario 1: Code Quality Check in CI
```bash
# .github/workflows/quality.yml
- name: Run multi-agent quality check
  run: |
    multi-agent-cli parallel \
      --agents pm,research,index \
      --path ./src \
      --format json \
      --output quality-report.json
    
    multi-agent-cli workflow compliance-check.yaml --strict
```

### Scenario 2: Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
multi-agent-cli run pm track_tasks --path ./src

if [ $? -ne 0 ]; then
  echo "Quality check failed. Fix issues before committing."
  exit 1
fi
```

### Scenario 3: Interactive Development
```bash
# Check code quality
multi-agent-cli run pm track_tasks --path ./src

# Analyze documentation
multi-agent-cli run research analyze_document --path README.md

# Find dead code
multi-agent-cli run index find_unused --path ./src
```

---

## Final Checklist

Before considering the project complete:

### Code Quality
- [ ] All functions have type hints
- [ ] All public APIs have docstrings
- [ ] No `# type: ignore` (or justified with comments)
- [ ] No unused imports
- [ ] No dead code
- [ ] Ruff passes with zero warnings
- [ ] Mypy strict mode passes

### Testing
- [ ] 100% code coverage
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Mock factory works correctly
- [ ] Error cases tested
- [ ] Edge cases covered

### Documentation
- [ ] README complete with examples
- [ ] CONTRIBUTING.md present
- [ ] SECURITY.md present
- [ ] CHANGELOG.md created
- [ ] API docs generated
- [ ] Examples directory populated

### CI/CD
- [ ] All workflows configured
- [ ] Secrets set in GitHub
- [ ] Badges added to README
- [ ] Branch protection enabled
- [ ] Automated releases working

### Security
- [ ] CodeQL configured and passing
- [ ] Snyk configured and passing
- [ ] Dependabot configured
- [ ] No security vulnerabilities
- [ ] Input validation complete

### Docker
- [ ] Dockerfile builds successfully
- [ ] docker-compose works
- [ ] Image size reasonable (<500MB)
- [ ] Entrypoint works correctly

### Package
- [ ] PyPI name available
- [ ] pyproject.toml complete
- [ ] LICENSE file present
- [ ] Version number set
- [ ] Can install with `pip install multi-agent-cli`
- [ ] CLI command works after install

---

**This is the most comprehensive AGENTS.md yet. Use it to build multi-agent-cli with confidence.**
