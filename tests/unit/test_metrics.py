"""Tests for metrics module."""

from __future__ import annotations

import pytest

from multi_agent_cli.metrics import (
    MetricsRecorder,
    NullMetricsRecorder,
    get_metrics,
    set_metrics,
)


@pytest.mark.unit
class TestMetricsRecorder:
    """Tests for MetricsRecorder."""

    def test_record_agent_invocation(self) -> None:
        """Test recording agent invocation."""
        metrics = MetricsRecorder()
        # Get current value before incrementing
        before = metrics.agent_invocations.labels(
            agent="pm_inv", action="track_tasks"
        )._value.get()
        metrics.record_agent_invocation("pm_inv", "track_tasks")
        after = metrics.agent_invocations.labels(
            agent="pm_inv", action="track_tasks"
        )._value.get()
        assert after - before == 1.0

    def test_record_agent_success(self) -> None:
        """Test recording successful agent execution."""
        metrics = MetricsRecorder()
        before = metrics.agent_invocations_success.labels(
            agent="pm_succ", action="track_tasks"
        )._value.get()
        metrics.record_agent_success("pm_succ", "track_tasks", 1.5)
        after = metrics.agent_invocations_success.labels(
            agent="pm_succ", action="track_tasks"
        )._value.get()
        assert after - before == 1.0

    def test_record_agent_error(self) -> None:
        """Test recording failed agent execution."""
        metrics = MetricsRecorder()
        before = metrics.agent_invocations_error.labels(
            agent="pm_err", action="track_tasks"
        )._value.get()
        metrics.record_agent_error("pm_err", "track_tasks")
        after = metrics.agent_invocations_error.labels(
            agent="pm_err", action="track_tasks"
        )._value.get()
        assert after - before == 1.0

    def test_record_workflow_start(self) -> None:
        """Test recording workflow start."""
        metrics = MetricsRecorder()
        before = metrics.workflows_executed.labels(
            workflow_name="test_workflow_start"
        )._value.get()
        metrics.record_workflow_start("test_workflow_start", 5)
        after = metrics.workflows_executed.labels(
            workflow_name="test_workflow_start"
        )._value.get()
        assert after - before == 1.0

        steps = metrics.workflow_steps_total.labels(
            workflow_name="test_workflow_start"
        )._value.get()
        assert steps == 5.0

    def test_record_workflow_complete_success(self) -> None:
        """Test recording successful workflow completion."""
        metrics = MetricsRecorder()
        before = metrics.workflows_success.labels(
            workflow_name="test_workflow_success"
        )._value.get()
        metrics.record_workflow_complete("test_workflow_success", True, 10.5, 0)
        after = metrics.workflows_success.labels(
            workflow_name="test_workflow_success"
        )._value.get()
        assert after - before == 1.0

    def test_record_workflow_complete_failure(self) -> None:
        """Test recording failed workflow completion."""
        metrics = MetricsRecorder()
        before = metrics.workflows_failed.labels(
            workflow_name="test_workflow_fail"
        )._value.get()
        metrics.record_workflow_complete("test_workflow_fail", False, 5.0, 2)
        after = metrics.workflows_failed.labels(
            workflow_name="test_workflow_fail"
        )._value.get()
        assert after - before == 1.0

        failed_steps = metrics.workflow_steps_failed.labels(
            workflow_name="test_workflow_fail"
        )._value.get()
        assert failed_steps == 2.0

    def test_record_parallel_execution(self) -> None:
        """Test recording parallel execution."""
        metrics = MetricsRecorder()
        before = metrics.parallel_executions._value.get()
        metrics.record_parallel_execution(3, 5.0)
        after = metrics.parallel_executions._value.get()
        assert after - before == 1.0

        workers = metrics.parallel_max_workers._value.get()
        assert workers == 3.0

    def test_record_cli_command(self) -> None:
        """Test recording CLI command."""
        metrics = MetricsRecorder()
        before = metrics.cli_commands.labels(command="run_test")._value.get()
        metrics.record_cli_command("run_test")
        after = metrics.cli_commands.labels(command="run_test")._value.get()
        assert after - before == 1.0

    def test_record_cli_error(self) -> None:
        """Test recording CLI error."""
        metrics = MetricsRecorder()
        before = metrics.cli_errors.labels(command="run_test_err")._value.get()
        metrics.record_cli_error("run_test_err")
        after = metrics.cli_errors.labels(command="run_test_err")._value.get()
        assert after - before == 1.0


@pytest.mark.unit
class TestNullMetricsRecorder:
    """Tests for NullMetricsRecorder."""

    def test_all_methods_are_noops(self) -> None:
        """Test that all NullMetricsRecorder methods are no-ops."""
        metrics = NullMetricsRecorder()
        # These should not raise any errors
        metrics.record_agent_invocation("agent", "action")
        metrics.record_agent_success("agent", "action", 1.0)
        metrics.record_agent_error("agent", "action")
        metrics.record_workflow_start("workflow", 5)
        metrics.record_workflow_complete("workflow", True, 10.0, 0)
        metrics.record_parallel_execution(3, 5.0)
        metrics.record_cli_command("run")
        metrics.record_cli_error("run")


@pytest.mark.unit
class TestMetricsFunctions:
    """Tests for metrics module functions."""

    def test_get_metrics(self) -> None:
        """Test getting global metrics instance."""
        set_metrics(None)  # Reset
        metrics = get_metrics()
        assert metrics is not None
        assert isinstance(metrics, MetricsRecorder)

    def test_set_metrics(self) -> None:
        """Test setting global metrics instance."""
        custom_metrics = NullMetricsRecorder()
        set_metrics(custom_metrics)

        metrics = get_metrics()
        assert metrics is custom_metrics

        # Clean up
        set_metrics(None)

    def test_set_metrics_to_none(self) -> None:
        """Test resetting metrics to None."""
        set_metrics(NullMetricsRecorder())
        set_metrics(None)

        # Should create new MetricsRecorder
        metrics = get_metrics()
        assert isinstance(metrics, MetricsRecorder)
