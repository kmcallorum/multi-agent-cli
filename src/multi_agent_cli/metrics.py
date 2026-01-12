"""Prometheus metrics recording."""

from __future__ import annotations

from typing import Protocol

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    start_http_server,
)


class MetricsProtocol(Protocol):
    """Protocol for metrics recording."""

    def record_agent_invocation(self, agent: str, action: str) -> None:
        """Record an agent invocation."""
        ...

    def record_agent_success(self, agent: str, action: str, duration: float) -> None:
        """Record successful agent execution."""
        ...

    def record_agent_error(self, agent: str, action: str) -> None:
        """Record failed agent execution."""
        ...

    def record_workflow_start(self, workflow_name: str, total_steps: int) -> None:
        """Record workflow start."""
        ...

    def record_workflow_complete(
        self,
        workflow_name: str,
        success: bool,
        duration: float,
        failed_steps: int,
    ) -> None:
        """Record workflow completion."""
        ...

    def record_parallel_execution(self, max_workers: int, duration: float) -> None:
        """Record parallel execution."""
        ...

    def record_cli_command(self, command: str) -> None:
        """Record CLI command execution."""
        ...

    def record_cli_error(self, command: str) -> None:
        """Record CLI command error."""
        ...


class NullMetricsRecorder:
    """Null metrics recorder for testing that doesn't use Prometheus."""

    def record_agent_invocation(self, agent: str, action: str) -> None:
        """Record an agent invocation (no-op)."""
        pass

    def record_agent_success(self, agent: str, action: str, duration: float) -> None:
        """Record successful agent execution (no-op)."""
        pass

    def record_agent_error(self, agent: str, action: str) -> None:
        """Record failed agent execution (no-op)."""
        pass

    def record_workflow_start(self, workflow_name: str, total_steps: int) -> None:
        """Record workflow start (no-op)."""
        pass

    def record_workflow_complete(
        self,
        workflow_name: str,
        success: bool,
        duration: float,
        failed_steps: int,
    ) -> None:
        """Record workflow completion (no-op)."""
        pass

    def record_parallel_execution(self, max_workers: int, duration: float) -> None:
        """Record parallel execution (no-op)."""
        pass

    def record_cli_command(self, command: str) -> None:
        """Record CLI command execution (no-op)."""
        pass

    def record_cli_error(self, command: str) -> None:
        """Record CLI command error (no-op)."""
        pass


class MetricsRecorder:
    """Record Prometheus metrics for agent execution."""

    _instance: MetricsRecorder | None = None
    _initialized: bool = False

    def __new__(cls) -> MetricsRecorder:
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize metrics (only once)."""
        if MetricsRecorder._initialized:
            return

        MetricsRecorder._initialized = True

        # Agent execution metrics
        self.agent_invocations = Counter(
            "agent_invocations_total",
            "Total agent invocations",
            ["agent", "action"],
        )
        self.agent_invocations_success = Counter(
            "agent_invocations_success_total",
            "Successful agent invocations",
            ["agent", "action"],
        )
        self.agent_invocations_error = Counter(
            "agent_invocations_error_total",
            "Failed agent invocations",
            ["agent", "action"],
        )
        self.agent_duration = Histogram(
            "agent_duration_seconds",
            "Agent execution duration",
            ["agent", "action"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
        )

        # Workflow metrics
        self.workflows_executed = Counter(
            "workflows_executed_total",
            "Total workflows executed",
            ["workflow_name"],
        )
        self.workflows_success = Counter(
            "workflows_success_total",
            "Successful workflow executions",
            ["workflow_name"],
        )
        self.workflows_failed = Counter(
            "workflows_failed_total",
            "Failed workflow executions",
            ["workflow_name"],
        )
        self.workflow_duration = Histogram(
            "workflow_duration_seconds",
            "Workflow execution duration",
            ["workflow_name"],
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
        )
        self.workflow_steps_total = Gauge(
            "workflow_steps_total",
            "Total steps in workflow",
            ["workflow_name"],
        )
        self.workflow_steps_failed = Gauge(
            "workflow_steps_failed",
            "Failed steps in workflow",
            ["workflow_name"],
        )

        # Parallel execution metrics
        self.parallel_executions = Counter(
            "parallel_executions_total",
            "Total parallel executions",
        )
        self.parallel_max_workers = Gauge(
            "parallel_max_workers",
            "Maximum parallel workers configured",
        )
        self.parallel_duration = Histogram(
            "parallel_duration_seconds",
            "Parallel execution duration",
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
        )

        # CLI metrics
        self.cli_commands = Counter(
            "cli_commands_total",
            "Total CLI commands executed",
            ["command"],
        )
        self.cli_errors = Counter(
            "cli_errors_total",
            "CLI command errors",
            ["command"],
        )

    def record_agent_invocation(self, agent: str, action: str) -> None:
        """Record an agent invocation.

        Args:
            agent: Agent name.
            action: Action performed.
        """
        self.agent_invocations.labels(agent=agent, action=action).inc()

    def record_agent_success(self, agent: str, action: str, duration: float) -> None:
        """Record successful agent execution.

        Args:
            agent: Agent name.
            action: Action performed.
            duration: Execution duration in seconds.
        """
        self.agent_invocations_success.labels(agent=agent, action=action).inc()
        self.agent_duration.labels(agent=agent, action=action).observe(duration)

    def record_agent_error(self, agent: str, action: str) -> None:
        """Record failed agent execution.

        Args:
            agent: Agent name.
            action: Action performed.
        """
        self.agent_invocations_error.labels(agent=agent, action=action).inc()

    def record_workflow_start(self, workflow_name: str, total_steps: int) -> None:
        """Record workflow start.

        Args:
            workflow_name: Workflow name.
            total_steps: Total number of steps.
        """
        self.workflows_executed.labels(workflow_name=workflow_name).inc()
        self.workflow_steps_total.labels(workflow_name=workflow_name).set(total_steps)

    def record_workflow_complete(
        self,
        workflow_name: str,
        success: bool,
        duration: float,
        failed_steps: int,
    ) -> None:
        """Record workflow completion.

        Args:
            workflow_name: Workflow name.
            success: Whether workflow succeeded.
            duration: Total duration in seconds.
            failed_steps: Number of failed steps.
        """
        if success:
            self.workflows_success.labels(workflow_name=workflow_name).inc()
        else:
            self.workflows_failed.labels(workflow_name=workflow_name).inc()

        self.workflow_duration.labels(workflow_name=workflow_name).observe(duration)
        self.workflow_steps_failed.labels(workflow_name=workflow_name).set(failed_steps)

    def record_parallel_execution(self, max_workers: int, duration: float) -> None:
        """Record parallel execution.

        Args:
            max_workers: Maximum workers used.
            duration: Execution duration in seconds.
        """
        self.parallel_executions.inc()
        self.parallel_max_workers.set(max_workers)
        self.parallel_duration.observe(duration)

    def record_cli_command(self, command: str) -> None:
        """Record CLI command execution.

        Args:
            command: Command name.
        """
        self.cli_commands.labels(command=command).inc()

    def record_cli_error(self, command: str) -> None:
        """Record CLI command error.

        Args:
            command: Command name.
        """
        self.cli_errors.labels(command=command).inc()


def start_metrics_server(  # pragma: no cover
    port: int = 9090, host: str = "0.0.0.0"
) -> None:
    """Start Prometheus metrics HTTP server.

    Args:
        port: Port to listen on.
        host: Host to bind to.
    """
    start_http_server(port, host)


# Global metrics instance
_metrics: MetricsRecorder | NullMetricsRecorder | None = None


def get_metrics() -> MetricsRecorder | NullMetricsRecorder:
    """Get global metrics instance.

    Returns:
        MetricsRecorder instance.
    """
    global _metrics
    if _metrics is None:
        _metrics = MetricsRecorder()
    return _metrics


def set_metrics(metrics: MetricsRecorder | NullMetricsRecorder | None) -> None:
    """Set global metrics instance (for testing).

    Args:
        metrics: Metrics recorder or None to reset.
    """
    global _metrics
    _metrics = metrics
