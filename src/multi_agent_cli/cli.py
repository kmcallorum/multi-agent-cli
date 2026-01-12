"""Click-based CLI commands for multi-agent-cli."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from multi_agent_cli.config import (
    create_default_config,
    load_config,
    load_workflow,
    save_config,
    validate_agent_name,
)
from multi_agent_cli.coordinator import AgentCoordinator
from multi_agent_cli.exceptions import (
    ConfigError,
    MultiAgentCLIError,
    ValidationError,
    WorkflowError,
)
from multi_agent_cli.executor import AgentExecutor
from multi_agent_cli.factory import get_default_factory
from multi_agent_cli.metrics import get_metrics, start_metrics_server
from multi_agent_cli.models.agent import AgentsConfig
from multi_agent_cli.reporters import (
    JSONReporter,
    RichReporter,
    TableReporter,
    get_reporter,
    save_result_to_file,
    save_results_to_file,
)

console = Console()


class CLIContext:
    """Context object for CLI commands."""

    def __init__(
        self,
        config: AgentsConfig | None = None,
        verbose: bool = False,
        quiet: bool = False,
        output_format: str = "rich",
    ) -> None:
        """Initialize CLI context.

        Args:
            config: Agents configuration.
            verbose: Verbose output flag.
            quiet: Quiet output flag.
            output_format: Output format (rich, json, table).
        """
        self.config = config
        self.verbose = verbose
        self.quiet = quiet
        self.output_format = output_format
        self._reporter: RichReporter | JSONReporter | TableReporter | None = None

    @property
    def reporter(self) -> RichReporter | JSONReporter | TableReporter:
        """Get reporter instance."""
        if self._reporter is None:
            self._reporter = get_reporter(
                self.output_format,
                console,
                self.verbose,
            )
        return self._reporter


pass_context = click.make_pass_decorator(CLIContext)


@click.group()
@click.option(
    "--config",
    "-c",
    "config_path",
    default="agents.yaml",
    help="Path to config file (default: agents.yaml)",
    type=click.Path(),
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet output (errors only)")
@click.option(
    "--format",
    "-f",
    "output_format",
    default="rich",
    type=click.Choice(["rich", "json", "table"]),
    help="Output format",
)
@click.version_option(package_name="multi-agent-cli")
@click.pass_context
def cli(
    ctx: click.Context,
    config_path: str,
    verbose: bool,
    quiet: bool,
    output_format: str,
) -> None:
    """Multi-agent orchestration CLI.

    Run AI agents in parallel or sequence with full observability.
    """
    # Try to load config, but don't fail if it doesn't exist
    config: AgentsConfig | None = None
    if Path(config_path).exists():
        try:
            config = load_config(config_path)
        except ConfigError as e:
            if verbose:
                console.print(f"[yellow]Warning:[/yellow] {e}")

    ctx.obj = CLIContext(
        config=config,
        verbose=verbose,
        quiet=quiet,
        output_format=output_format,
    )

    # Record CLI command metric
    metrics = get_metrics()
    metrics.record_cli_command(ctx.invoked_subcommand or "unknown")


@cli.command()
@click.argument("agent")
@click.argument("action")
@click.option("--path", "-p", default=".", help="Project path")
@click.option("--params", help="Additional parameters as JSON")
@click.option("--output", "-o", help="Save results to file")
@click.option("--timeout", "-t", default=60, help="Execution timeout in seconds")
@pass_context
def run(
    ctx: CLIContext,
    agent: str,
    action: str,
    path: str,
    params: str | None,
    output: str | None,
    timeout: int,
) -> None:
    """Run a single agent.

    AGENT is the agent name (pm, research, index).
    ACTION is the action to perform.

    Examples:
        multi-agent-cli run pm track_tasks --path ./src
        multi-agent-cli run research analyze_document --path README.md
    """
    try:
        # Validate agent name
        valid_agents = {"pm", "research", "index"}
        if ctx.config:
            valid_agents = set(ctx.config.agents.keys())
        validate_agent_name(agent, valid_agents)

        # Parse params
        action_params: dict[str, Any] = {"path": path}
        if params:
            try:
                action_params.update(json.loads(params))
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON params: {e}") from e

        # Create executor
        config = ctx.config or create_default_config()
        factory = get_default_factory()
        bridge = factory.create(config)
        executor = AgentExecutor(bridge, get_metrics(), timeout)

        # Execute with progress
        if not ctx.quiet:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(f"Running {agent}.{action}...", total=None)
                result = executor.execute_sync(agent, action, action_params, timeout)
        else:
            result = executor.execute_sync(agent, action, action_params, timeout)

        # Display result
        ctx.reporter.display_result(result)

        # Save if requested
        if output:
            save_result_to_file(result, output)
            if not ctx.quiet:
                console.print(f"[dim]Results saved to {output}[/dim]")

        # Exit with error code if failed
        if result.status == "error":
            sys.exit(1)

    except MultiAgentCLIError as e:  # pragma: no cover
        ctx.reporter.display_error(str(e))
        get_metrics().record_cli_error("run")
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        ctx.reporter.display_error(f"Unexpected error: {e}")
        get_metrics().record_cli_error("run")
        sys.exit(2)


@cli.command()
@click.option(
    "--agents",
    "-a",
    help="Comma-separated agent names",
)
@click.option("--workflow", "-w", "workflow_path", help="Workflow definition file")
@click.option("--max-workers", "-n", default=3, help="Maximum parallel workers")
@click.option("--path", "-p", default=".", help="Project path for all agents")
@click.option("--output", "-o", help="Save results to file")
@click.option("--aggregate", is_flag=True, help="Combine results into single report")
@pass_context
def parallel(
    ctx: CLIContext,
    agents: str | None,
    workflow_path: str | None,
    max_workers: int,
    path: str,
    output: str | None,
    aggregate: bool,
) -> None:
    """Run multiple agents in parallel.

    Examples:
        multi-agent-cli parallel --agents pm,research,index --path ./src
        multi-agent-cli parallel --workflow analysis.yaml
    """
    try:
        if not agents and not workflow_path:
            raise ValidationError("Either --agents or --workflow must be specified")

        config = ctx.config or create_default_config()
        factory = get_default_factory()
        bridge = factory.create(config)
        executor = AgentExecutor(bridge, get_metrics())
        coordinator = AgentCoordinator(executor, max_workers, get_metrics())

        # Build tasks
        tasks: list[tuple[str, str, dict[str, Any]]] = []

        if agents:  # pragma: no branch
            agent_list = [a.strip() for a in agents.split(",")]
            for agent_name in agent_list:
                # Default action based on agent
                default_actions = {
                    "pm": "track_tasks",
                    "research": "analyze_document",
                    "index": "index_repository",
                }
                action = default_actions.get(agent_name, "run")
                tasks.append((agent_name, action, {"path": path}))

        # Execute
        if not ctx.quiet:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(
                    f"Running {len(tasks)} agents in parallel...", total=None
                )
                results = coordinator.execute_parallel_sync(tasks)
        else:
            results = coordinator.execute_parallel_sync(tasks)

        # Display results
        ctx.reporter.display_results(results)

        # Save if requested
        if output:
            save_results_to_file(results, output)
            if not ctx.quiet:
                console.print(f"[dim]Results saved to {output}[/dim]")

        # Exit with error code if any failed
        if any(r.status == "error" for r in results):  # pragma: no cover
            sys.exit(1)

    except MultiAgentCLIError as e:  # pragma: no cover
        ctx.reporter.display_error(str(e))
        get_metrics().record_cli_error("parallel")
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        ctx.reporter.display_error(f"Unexpected error: {e}")
        get_metrics().record_cli_error("parallel")
        sys.exit(2)


@cli.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Fail on first error")
@click.option("--continue-on-error", is_flag=True, help="Continue even if steps fail")
@click.option("--output", "-o", help="Save workflow results to file")
@pass_context
def workflow(
    ctx: CLIContext,
    workflow_file: str,
    strict: bool,
    continue_on_error: bool,
    output: str | None,
) -> None:
    """Run sequential workflow.

    WORKFLOW_FILE is the path to the workflow YAML file.

    Examples:
        multi-agent-cli workflow code-review.yaml
        multi-agent-cli workflow compliance-check.yaml --strict
    """
    try:
        # Load workflow
        wf = load_workflow(workflow_file)

        config = ctx.config or create_default_config()
        factory = get_default_factory()
        bridge = factory.create(config)
        executor = AgentExecutor(bridge, get_metrics())
        coordinator = AgentCoordinator(executor, metrics=get_metrics())

        # Determine strict mode
        use_strict = strict and not continue_on_error

        # Execute
        if not ctx.quiet:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(f"Running workflow '{wf.name}'...", total=None)
                result = coordinator.execute_workflow_sync(wf, use_strict)
        else:
            result = coordinator.execute_workflow_sync(wf, use_strict)

        # Display results
        ctx.reporter.display_workflow_result(result)

        # Save if requested
        if output:
            save_result_to_file(result, output)
            if not ctx.quiet:  # pragma: no branch
                console.print(f"[dim]Results saved to {output}[/dim]")

        # Exit with error code if failed
        if result.steps_failed > 0 or not result.quality_gates_passed:
            sys.exit(1)

    except WorkflowError as e:  # pragma: no cover
        ctx.reporter.display_error(str(e))
        get_metrics().record_cli_error("workflow")
        sys.exit(1)
    except MultiAgentCLIError as e:  # pragma: no cover
        ctx.reporter.display_error(str(e))
        get_metrics().record_cli_error("workflow")
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        ctx.reporter.display_error(f"Unexpected error: {e}")
        get_metrics().record_cli_error("workflow")
        sys.exit(2)


@cli.command("list")
@click.option("--verbose", "-v", is_flag=True, help="Show agent capabilities")
@pass_context
def list_agents(ctx: CLIContext, verbose: bool) -> None:
    """List available agents.

    Examples:
        multi-agent-cli list
        multi-agent-cli list --verbose
    """
    config = ctx.config or create_default_config()

    # Agent descriptions
    descriptions = {
        "pm": "Project management agent (track tasks, milestones)",
        "research": "Research agent (analyze docs, extract info)",
        "index": "Index agent (code search, dependency analysis)",
    }

    agents: list[tuple[str, bool, str]] = []
    for name, agent_config in config.agents.items():
        desc = descriptions.get(name, "Custom agent")
        agents.append((name, agent_config.enabled, desc))

    if isinstance(ctx.reporter, RichReporter):
        ctx.reporter.display_agents_list(agents)
    else:
        # JSON or table format
        data = [
            {"name": name, "enabled": enabled, "description": desc}
            for name, enabled, desc in agents
        ]
        console.print(json.dumps(data, indent=2))


@cli.group()
def config() -> None:
    """Manage configuration."""
    pass


@config.command("show")
@pass_context
def config_show(ctx: CLIContext) -> None:
    """Show current configuration."""
    if ctx.config is None:
        ctx.reporter.display_error("No configuration loaded")
        sys.exit(1)

    if isinstance(ctx.reporter, RichReporter):
        ctx.reporter.display_config(ctx.config.to_dict())
    else:
        console.print(json.dumps(ctx.config.to_dict(), indent=2))


@config.command("validate")
@click.argument("file", type=click.Path(exists=True))
@pass_context
def config_validate(ctx: CLIContext, file: str) -> None:
    """Validate configuration file."""
    try:
        load_config(file)
        ctx.reporter.display_success(f"Configuration '{file}' is valid")
    except ConfigError as e:
        ctx.reporter.display_error(f"Invalid configuration: {e}")
        sys.exit(1)


@config.command("init")
@click.option("--output", "-o", default="agents.yaml", help="Output file path")
@click.option("--example-workflows", is_flag=True, help="Include example workflows")
@pass_context
def config_init(
    ctx: CLIContext,
    output: str,
    example_workflows: bool,
) -> None:
    """Create example configuration.

    Examples:
        multi-agent-cli config init
        multi-agent-cli config init --output my-config.yaml
    """
    if Path(output).exists():
        ctx.reporter.display_error(f"File already exists: {output}")
        sys.exit(1)

    config = create_default_config()
    save_config(config, output)
    ctx.reporter.display_success(f"Created configuration: {output}")

    if example_workflows:
        # Create workflows directory and example
        workflows_dir = Path("workflows")
        workflows_dir.mkdir(exist_ok=True)

        example_workflow = {
            "name": "Code Quality Analysis",
            "description": "Comprehensive code quality check",
            "steps": [
                {
                    "name": "Track Technical Debt",
                    "agent": "pm",
                    "action": "track_tasks",
                    "params": {"path": "./src"},
                    "on_error": "continue",
                },
                {
                    "name": "Analyze Documentation",
                    "agent": "research",
                    "action": "analyze_document",
                    "params": {"path": "./README.md"},
                    "on_error": "fail",
                },
            ],
            "quality_gates": {
                "max_fixmes": 10,
                "min_documentation_score": 0.7,
            },
        }

        import yaml

        workflow_path = workflows_dir / "example.yaml"
        with workflow_path.open("w") as f:
            yaml.dump(example_workflow, f, default_flow_style=False)

        ctx.reporter.display_success(f"Created example workflow: {workflow_path}")


@cli.command()
@click.option("--port", "-p", default=9090, help="Prometheus metrics port")
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind to")
@pass_context
def metrics(ctx: CLIContext, port: int, host: str) -> None:
    """Start Prometheus metrics server.

    Examples:
        multi-agent-cli metrics
        multi-agent-cli metrics --port 9091 --host 127.0.0.1
    """
    if not ctx.quiet:  # pragma: no cover
        console.print(f"Starting metrics server at http://{host}:{port}/metrics")
        console.print("Press Ctrl+C to stop")

    try:  # pragma: no cover
        start_metrics_server(port, host)
        # Keep running
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:  # pragma: no cover
        if not ctx.quiet:
            console.print("\nMetrics server stopped")


@cli.command()
@click.option("--example-workflows", is_flag=True, help="Include example workflows")
@pass_context
def init(ctx: CLIContext, example_workflows: bool) -> None:
    """Initialize project with default configuration.

    Creates agents.yaml and optional workflow examples.

    Examples:
        multi-agent-cli init
        multi-agent-cli init --example-workflows
    """
    # Delegate to config init
    ctx_obj = click.get_current_context()
    ctx_obj.invoke(
        config_init, output="agents.yaml", example_workflows=example_workflows
    )


if __name__ == "__main__":  # pragma: no cover
    cli()
