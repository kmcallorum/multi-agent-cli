"""Result formatting and reporting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from multi_agent_cli.models.results import AgentResult, WorkflowResult


class Reporter(Protocol):
    """Protocol for result reporters."""

    def display_result(self, result: AgentResult) -> None:
        """Display single agent result.

        Args:
            result: Agent result to display.
        """
        ...

    def display_workflow_result(self, result: WorkflowResult) -> None:
        """Display workflow result.

        Args:
            result: Workflow result to display.
        """
        ...

    def display_results(self, results: list[AgentResult]) -> None:
        """Display multiple agent results.

        Args:
            results: List of agent results.
        """
        ...


class RichReporter:
    """Format results with Rich library for beautiful terminal output."""

    def __init__(self, console: Console | None = None, verbose: bool = False) -> None:
        """Initialize reporter.

        Args:
            console: Optional Rich console instance.
            verbose: Enable verbose output.
        """
        self.console = console or Console()
        self.verbose = verbose

    def display_result(self, result: AgentResult) -> None:
        """Display single agent result.

        Args:
            result: Agent result to display.
        """
        if result.status == "success":
            self.console.print(
                f"[green]✓[/green] {result.agent}.{result.action} "
                f"[dim]({result.duration_seconds:.2f}s)[/dim]"
            )
        else:
            self.console.print(
                f"[red]✗[/red] {result.agent}.{result.action} "
                f"[dim]({result.duration_seconds:.2f}s)[/dim]"
            )
            if result.error:  # pragma: no branch
                self.console.print(f"  [red]Error:[/red] {result.error}")

        # Show data in verbose mode or if there's data to show
        if self.verbose and result.data:
            self._display_data_table(result)

    def _display_data_table(self, result: AgentResult) -> None:
        """Display result data as a table.

        Args:
            result: Agent result with data.
        """
        table = Table(title=f"{result.agent} Results", show_header=True)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        for key, value in result.data.items():
            table.add_row(str(key), str(value))

        self.console.print(table)

    def display_workflow_result(self, result: WorkflowResult) -> None:
        """Display workflow result.

        Args:
            result: Workflow result to display.
        """
        status_color = "green" if result.quality_gates_passed else "red"
        status_icon = "✓" if result.quality_gates_passed else "✗"

        panel = Panel(
            f"[bold]{result.workflow_name}[/bold]\n"
            f"Steps: {result.steps_completed} completed, "
            f"{result.steps_failed} failed\n"
            f"Duration: {result.total_duration:.2f}s\n"
            f"Quality Gates: [{status_color}]{status_icon}[/{status_color}]",
            title="Workflow Summary",
            border_style=status_color,
        )
        self.console.print(panel)

        # Show individual results
        for step_result in result.results:
            self.display_result(step_result)

    def display_results(self, results: list[AgentResult]) -> None:
        """Display multiple agent results.

        Args:
            results: List of agent results.
        """
        success_count = sum(1 for r in results if r.status == "success")
        total = len(results)
        total_duration = sum(r.duration_seconds for r in results)

        self.console.print(
            f"\n[bold]Results:[/bold] {success_count}/{total} succeeded "
            f"[dim]({total_duration:.2f}s total)[/dim]\n"
        )

        for result in results:
            self.display_result(result)

    def display_agents_list(
        self,
        agents: list[tuple[str, bool, str]],
    ) -> None:
        """Display list of available agents.

        Args:
            agents: List of (name, enabled, description) tuples.
        """
        self.console.print("\n[bold]Available agents:[/bold]\n")

        for name, enabled, description in agents:
            icon = "[green]✓[/green]" if enabled else "[red]✗[/red]"
            status = "" if enabled else " [dim](disabled)[/dim]"
            self.console.print(f"  {icon} [cyan]{name}[/cyan] - {description}{status}")

        self.console.print()

    def display_config(self, config: dict[str, Any]) -> None:
        """Display configuration.

        Args:
            config: Configuration dictionary.
        """
        self.console.print("\n[bold]Current Configuration:[/bold]\n")
        self.console.print_json(json.dumps(config, indent=2))

    def display_error(self, message: str, details: str | None = None) -> None:
        """Display error message.

        Args:
            message: Error message.
            details: Optional error details.
        """
        self.console.print(f"[red]Error:[/red] {message}")
        if details and self.verbose:
            self.console.print(f"[dim]{details}[/dim]")

    def display_success(self, message: str) -> None:
        """Display success message.

        Args:
            message: Success message.
        """
        self.console.print(f"[green]✓[/green] {message}")

    def display_info(self, message: str) -> None:
        """Display info message.

        Args:
            message: Info message.
        """
        self.console.print(f"[blue]i[/blue] {message}")


class JSONReporter:
    """Output results as JSON."""

    def __init__(self, console: Console | None = None, indent: int = 2) -> None:
        """Initialize reporter.

        Args:
            console: Optional Rich console instance.
            indent: JSON indentation level.
        """
        self.console = console or Console()
        self.indent = indent

    def display_result(self, result: AgentResult) -> None:
        """Display result as JSON.

        Args:
            result: Agent result to display.
        """
        self.console.print(result.model_dump_json(indent=self.indent))

    def display_workflow_result(self, result: WorkflowResult) -> None:
        """Display workflow result as JSON.

        Args:
            result: Workflow result to display.
        """
        self.console.print(result.model_dump_json(indent=self.indent))

    def display_results(self, results: list[AgentResult]) -> None:
        """Display multiple results as JSON array.

        Args:
            results: List of agent results.
        """
        data = [r.model_dump() for r in results]
        self.console.print(json.dumps(data, indent=self.indent))

    def display_error(self, message: str, details: str | None = None) -> None:
        """Display error message as JSON.

        Args:
            message: Error message.
            details: Optional error details.
        """
        data = {"error": message}
        if details:
            data["details"] = details
        self.console.print(json.dumps(data, indent=self.indent))

    def display_success(self, message: str) -> None:
        """Display success message as JSON.

        Args:
            message: Success message.
        """
        self.console.print(json.dumps({"success": message}, indent=self.indent))


class TableReporter:
    """Output results as formatted tables."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize reporter.

        Args:
            console: Optional Rich console instance.
        """
        self.console = console or Console()

    def display_result(self, result: AgentResult) -> None:
        """Display result as table row.

        Args:
            result: Agent result to display.
        """
        table = Table(show_header=True)
        table.add_column("Agent", style="cyan")
        table.add_column("Action", style="cyan")
        table.add_column("Status")
        table.add_column("Duration")
        table.add_column("Error")

        status_style = "green" if result.status == "success" else "red"
        table.add_row(
            result.agent,
            result.action,
            f"[{status_style}]{result.status}[/{status_style}]",
            f"{result.duration_seconds:.2f}s",
            result.error or "",
        )
        self.console.print(table)

    def display_workflow_result(self, result: WorkflowResult) -> None:
        """Display workflow result as table.

        Args:
            result: Workflow result to display.
        """
        # Summary table
        summary = Table(title=f"Workflow: {result.workflow_name}")
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value")

        summary.add_row("Steps Completed", str(result.steps_completed))
        summary.add_row("Steps Failed", str(result.steps_failed))
        summary.add_row("Total Duration", f"{result.total_duration:.2f}s")
        gates_status = (
            "[green]Passed[/green]"
            if result.quality_gates_passed
            else "[red]Failed[/red]"
        )
        summary.add_row("Quality Gates", gates_status)
        self.console.print(summary)

        # Steps table
        self.display_results(result.results)

    def display_results(self, results: list[AgentResult]) -> None:
        """Display results as table.

        Args:
            results: List of agent results.
        """
        table = Table(title="Results", show_header=True)
        table.add_column("Agent", style="cyan")
        table.add_column("Action", style="cyan")
        table.add_column("Status")
        table.add_column("Duration")
        table.add_column("Error")

        for result in results:
            status_style = "green" if result.status == "success" else "red"
            table.add_row(
                result.agent,
                result.action,
                f"[{status_style}]{result.status}[/{status_style}]",
                f"{result.duration_seconds:.2f}s",
                result.error or "",
            )

        self.console.print(table)

    def display_error(self, message: str, details: str | None = None) -> None:
        """Display error message.

        Args:
            message: Error message.
            details: Optional error details.
        """
        self.console.print(f"[red]Error:[/red] {message}")
        if details:
            self.console.print(f"[dim]{details}[/dim]")

    def display_success(self, message: str) -> None:
        """Display success message.

        Args:
            message: Success message.
        """
        self.console.print(f"[green]Success:[/green] {message}")


def get_reporter(
    format_type: str,
    console: Console | None = None,
    verbose: bool = False,
) -> RichReporter | JSONReporter | TableReporter:
    """Get reporter instance by format type.

    Args:
        format_type: Output format (rich, json, table).
        console: Optional Rich console instance.
        verbose: Enable verbose output.

    Returns:
        Reporter instance.
    """
    if format_type == "json":
        return JSONReporter(console)
    elif format_type == "table":
        return TableReporter(console)
    else:
        return RichReporter(console, verbose)


def save_result_to_file(
    result: AgentResult | WorkflowResult,
    path: str | Path,
) -> None:
    """Save result to JSON file.

    Args:
        result: Result to save.
        path: File path.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))


def save_results_to_file(
    results: list[AgentResult],
    path: str | Path,
) -> None:
    """Save multiple results to JSON file.

    Args:
        results: Results to save.
        path: File path.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = [r.model_dump() for r in results]
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
