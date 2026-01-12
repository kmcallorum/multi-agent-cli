"""Tests for reporters module."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from multi_agent_cli.models.results import (
    AgentResult,
    DryRunResult,
    DryRunStep,
    WorkflowResult,
)
from multi_agent_cli.reporters import (
    JSONReporter,
    RichReporter,
    TableReporter,
    get_reporter,
    save_result_to_file,
    save_results_to_file,
)


@pytest.fixture
def string_console() -> Console:
    """Create console that outputs to string."""
    return Console(file=StringIO(), force_terminal=False)


@pytest.fixture
def success_result() -> AgentResult:
    """Create success result."""
    return AgentResult.success(
        agent="pm",
        action="track_tasks",
        data={"count": 5, "items": ["a", "b"]},
        duration_seconds=1.5,
    )


@pytest.fixture
def error_result() -> AgentResult:
    """Create error result."""
    return AgentResult.failure(
        agent="pm",
        action="track_tasks",
        error="Something went wrong",
        duration_seconds=0.5,
    )


@pytest.fixture
def workflow_result(
    success_result: AgentResult, error_result: AgentResult
) -> WorkflowResult:
    """Create workflow result."""
    return WorkflowResult.from_results(
        workflow_name="Test Workflow",
        results=[success_result, error_result],
        quality_gates_passed=False,
    )


@pytest.fixture
def valid_dry_run_result() -> DryRunResult:
    """Create valid dry-run result."""
    return DryRunResult(
        workflow_name="Test Workflow",
        workflow_description="A test workflow",
        total_steps=2,
        steps=[
            DryRunStep(
                order=1,
                name="Step 1",
                agent="pm",
                action="track_tasks",
                params={"path": "./src"},
                depends_on=[],
                timeout=60,
                on_error="fail",
            ),
            DryRunStep(
                order=2,
                name="Step 2",
                agent="research",
                action="analyze_document",
                params={"path": "./README.md"},
                depends_on=["Step 1"],
                timeout=None,
                on_error="continue",
            ),
        ],
        validation_errors=[],
        quality_gates={
            "max_fixmes": 10,
            "min_documentation_score": 0.7,
            "max_dead_code_percent": None,
        },
        is_valid=True,
    )


@pytest.fixture
def invalid_dry_run_result() -> DryRunResult:
    """Create invalid dry-run result with validation errors."""
    return DryRunResult(
        workflow_name="Invalid Workflow",
        workflow_description="",
        total_steps=1,
        steps=[
            DryRunStep(
                order=1,
                name="Step 1",
                agent="pm",
                action="track_tasks",
                params={},
                depends_on=["NonexistentStep"],
                timeout=None,
                on_error="fail",
            ),
        ],
        validation_errors=[
            "Step 'Step 1' depends on non-existent step 'NonexistentStep'"
        ],
        quality_gates={},
        is_valid=False,
    )


@pytest.mark.unit
class TestRichReporter:
    """Tests for RichReporter."""

    def test_display_success_result(
        self,
        string_console: Console,
        success_result: AgentResult,
    ) -> None:
        """Test displaying success result."""
        reporter = RichReporter(string_console)
        reporter.display_result(success_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "pm.track_tasks" in output
        assert "1.50s" in output

    def test_display_error_result(
        self,
        string_console: Console,
        error_result: AgentResult,
    ) -> None:
        """Test displaying error result."""
        reporter = RichReporter(string_console)
        reporter.display_result(error_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "pm.track_tasks" in output
        assert "Something went wrong" in output

    def test_display_result_verbose(
        self,
        string_console: Console,
        success_result: AgentResult,
    ) -> None:
        """Test displaying result with verbose mode."""
        reporter = RichReporter(string_console, verbose=True)
        reporter.display_result(success_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "count" in output

    def test_display_workflow_result(
        self,
        string_console: Console,
        workflow_result: WorkflowResult,
    ) -> None:
        """Test displaying workflow result."""
        reporter = RichReporter(string_console)
        reporter.display_workflow_result(workflow_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "Test Workflow" in output
        assert "1 completed" in output
        assert "1 failed" in output

    def test_display_results(
        self,
        string_console: Console,
        success_result: AgentResult,
        error_result: AgentResult,
    ) -> None:
        """Test displaying multiple results."""
        reporter = RichReporter(string_console)
        reporter.display_results([success_result, error_result])

        output = string_console.file.getvalue()  # type: ignore
        assert "1/2 succeeded" in output

    def test_display_agents_list(self, string_console: Console) -> None:
        """Test displaying agents list."""
        reporter = RichReporter(string_console)
        agents = [
            ("pm", True, "Project management"),
            ("research", False, "Research agent"),
        ]
        reporter.display_agents_list(agents)

        output = string_console.file.getvalue()  # type: ignore
        assert "pm" in output
        assert "disabled" in output

    def test_display_config(self, string_console: Console) -> None:
        """Test displaying configuration."""
        reporter = RichReporter(string_console)
        config = {"key": "value", "nested": {"inner": 123}}
        reporter.display_config(config)

        output = string_console.file.getvalue()  # type: ignore
        assert "key" in output
        assert "value" in output

    def test_display_error(self, string_console: Console) -> None:
        """Test displaying error message."""
        reporter = RichReporter(string_console)
        reporter.display_error("Test error")

        output = string_console.file.getvalue()  # type: ignore
        assert "Error" in output
        assert "Test error" in output

    def test_display_error_with_details_verbose(self, string_console: Console) -> None:
        """Test displaying error with details in verbose mode."""
        reporter = RichReporter(string_console, verbose=True)
        reporter.display_error("Test error", "Details here")

        output = string_console.file.getvalue()  # type: ignore
        assert "Details here" in output

    def test_display_error_with_details_not_verbose(
        self, string_console: Console
    ) -> None:
        """Test displaying error without details when not verbose."""
        reporter = RichReporter(string_console, verbose=False)
        reporter.display_error("Test error", "Details here")

        output = string_console.file.getvalue()  # type: ignore
        assert "Details here" not in output

    def test_display_success(self, string_console: Console) -> None:
        """Test displaying success message."""
        reporter = RichReporter(string_console)
        reporter.display_success("Success message")

        output = string_console.file.getvalue()  # type: ignore
        assert "Success message" in output

    def test_display_info(self, string_console: Console) -> None:
        """Test displaying info message."""
        reporter = RichReporter(string_console)
        reporter.display_info("Info message")

        output = string_console.file.getvalue()  # type: ignore
        assert "Info message" in output

    def test_display_dry_run_valid(
        self,
        string_console: Console,
        valid_dry_run_result: DryRunResult,
    ) -> None:
        """Test displaying valid dry-run result."""
        reporter = RichReporter(string_console)
        reporter.display_dry_run_result(valid_dry_run_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "DRY RUN" in output
        assert "VALID" in output
        assert "Test Workflow" in output
        assert "Execution Plan" in output
        assert "Step 1" in output
        assert "Step 2" in output
        assert "pm" in output
        assert "research" in output

    def test_display_dry_run_invalid(
        self,
        string_console: Console,
        invalid_dry_run_result: DryRunResult,
    ) -> None:
        """Test displaying invalid dry-run result."""
        reporter = RichReporter(string_console)
        reporter.display_dry_run_result(invalid_dry_run_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "DRY RUN" in output
        assert "INVALID" in output
        assert "Validation Errors" in output
        assert "NonexistentStep" in output

    def test_display_dry_run_with_quality_gates(
        self,
        string_console: Console,
        valid_dry_run_result: DryRunResult,
    ) -> None:
        """Test displaying dry-run result with quality gates."""
        reporter = RichReporter(string_console)
        reporter.display_dry_run_result(valid_dry_run_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "Quality Gates" in output
        assert "max_fixmes" in output
        assert "10" in output


@pytest.mark.unit
class TestJSONReporter:
    """Tests for JSONReporter."""

    def test_display_result(
        self,
        string_console: Console,
        success_result: AgentResult,
    ) -> None:
        """Test displaying result as JSON."""
        reporter = JSONReporter(string_console)
        reporter.display_result(success_result)

        output = string_console.file.getvalue()  # type: ignore
        # Should be valid JSON
        data = json.loads(output)
        assert data["agent"] == "pm"

    def test_display_workflow_result(
        self,
        string_console: Console,
        workflow_result: WorkflowResult,
    ) -> None:
        """Test displaying workflow result as JSON."""
        reporter = JSONReporter(string_console)
        reporter.display_workflow_result(workflow_result)

        output = string_console.file.getvalue()  # type: ignore
        data = json.loads(output)
        assert data["workflow_name"] == "Test Workflow"

    def test_display_results(
        self,
        string_console: Console,
        success_result: AgentResult,
        error_result: AgentResult,
    ) -> None:
        """Test displaying multiple results as JSON."""
        reporter = JSONReporter(string_console)
        reporter.display_results([success_result, error_result])

        output = string_console.file.getvalue()  # type: ignore
        data = json.loads(output)
        assert len(data) == 2

    def test_display_error(self, string_console: Console) -> None:
        """Test displaying error as JSON."""
        reporter = JSONReporter(string_console)
        reporter.display_error("Test error")

        output = string_console.file.getvalue()  # type: ignore
        data = json.loads(output)
        assert data["error"] == "Test error"

    def test_display_error_with_details(self, string_console: Console) -> None:
        """Test displaying error with details as JSON."""
        reporter = JSONReporter(string_console)
        reporter.display_error("Test error", "Error details")

        output = string_console.file.getvalue()  # type: ignore
        data = json.loads(output)
        assert data["error"] == "Test error"
        assert data["details"] == "Error details"

    def test_display_success(self, string_console: Console) -> None:
        """Test displaying success as JSON."""
        reporter = JSONReporter(string_console)
        reporter.display_success("Success message")

        output = string_console.file.getvalue()  # type: ignore
        data = json.loads(output)
        assert data["success"] == "Success message"

    def test_display_dry_run_result(
        self,
        string_console: Console,
        valid_dry_run_result: DryRunResult,
    ) -> None:
        """Test displaying dry-run result as JSON."""
        reporter = JSONReporter(string_console)
        reporter.display_dry_run_result(valid_dry_run_result)

        output = string_console.file.getvalue()  # type: ignore
        data = json.loads(output)
        assert data["workflow_name"] == "Test Workflow"
        assert data["is_valid"] is True
        assert len(data["steps"]) == 2


@pytest.mark.unit
class TestTableReporter:
    """Tests for TableReporter."""

    def test_display_result(
        self,
        string_console: Console,
        success_result: AgentResult,
    ) -> None:
        """Test displaying result as table."""
        reporter = TableReporter(string_console)
        reporter.display_result(success_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "pm" in output
        assert "track_tasks" in output

    def test_display_workflow_result(
        self,
        string_console: Console,
        workflow_result: WorkflowResult,
    ) -> None:
        """Test displaying workflow result as table."""
        reporter = TableReporter(string_console)
        reporter.display_workflow_result(workflow_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "Test Workflow" in output

    def test_display_results(
        self,
        string_console: Console,
        success_result: AgentResult,
        error_result: AgentResult,
    ) -> None:
        """Test displaying multiple results as table."""
        reporter = TableReporter(string_console)
        reporter.display_results([success_result, error_result])

        output = string_console.file.getvalue()  # type: ignore
        assert "Results" in output

    def test_display_error(self, string_console: Console) -> None:
        """Test displaying error message."""
        reporter = TableReporter(string_console)
        reporter.display_error("Test error")

        output = string_console.file.getvalue()  # type: ignore
        assert "Error" in output
        assert "Test error" in output

    def test_display_error_with_details(self, string_console: Console) -> None:
        """Test displaying error with details."""
        reporter = TableReporter(string_console)
        reporter.display_error("Test error", "Error details")

        output = string_console.file.getvalue()  # type: ignore
        assert "Test error" in output
        assert "Error details" in output

    def test_display_success(self, string_console: Console) -> None:
        """Test displaying success message."""
        reporter = TableReporter(string_console)
        reporter.display_success("Success message")

        output = string_console.file.getvalue()  # type: ignore
        assert "Success" in output
        assert "Success message" in output

    def test_display_dry_run_valid(
        self,
        string_console: Console,
        valid_dry_run_result: DryRunResult,
    ) -> None:
        """Test displaying valid dry-run result as table."""
        reporter = TableReporter(string_console)
        reporter.display_dry_run_result(valid_dry_run_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "DRY RUN" in output
        assert "VALID" in output
        assert "Execution Plan" in output

    def test_display_dry_run_invalid(
        self,
        string_console: Console,
        invalid_dry_run_result: DryRunResult,
    ) -> None:
        """Test displaying invalid dry-run result as table."""
        reporter = TableReporter(string_console)
        reporter.display_dry_run_result(invalid_dry_run_result)

        output = string_console.file.getvalue()  # type: ignore
        assert "DRY RUN" in output
        assert "INVALID" in output
        assert "Validation Errors" in output


@pytest.mark.unit
class TestGetReporter:
    """Tests for get_reporter function."""

    def test_get_rich_reporter(self) -> None:
        """Test getting Rich reporter."""
        reporter = get_reporter("rich")
        assert isinstance(reporter, RichReporter)

    def test_get_json_reporter(self) -> None:
        """Test getting JSON reporter."""
        reporter = get_reporter("json")
        assert isinstance(reporter, JSONReporter)

    def test_get_table_reporter(self) -> None:
        """Test getting table reporter."""
        reporter = get_reporter("table")
        assert isinstance(reporter, TableReporter)

    def test_default_is_rich(self) -> None:
        """Test default reporter is Rich."""
        reporter = get_reporter("unknown")
        assert isinstance(reporter, RichReporter)


@pytest.mark.unit
class TestSaveResultToFile:
    """Tests for save_result_to_file function."""

    def test_save_agent_result(
        self,
        tmp_path: Path,
        success_result: AgentResult,
    ) -> None:
        """Test saving agent result to file."""
        output_path = tmp_path / "result.json"
        save_result_to_file(success_result, output_path)

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert data["agent"] == "pm"

    def test_save_workflow_result(
        self,
        tmp_path: Path,
        workflow_result: WorkflowResult,
    ) -> None:
        """Test saving workflow result to file."""
        output_path = tmp_path / "workflow.json"
        save_result_to_file(workflow_result, output_path)

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert data["workflow_name"] == "Test Workflow"

    def test_save_creates_directories(
        self,
        tmp_path: Path,
        success_result: AgentResult,
    ) -> None:
        """Test saving creates parent directories."""
        output_path = tmp_path / "nested" / "dir" / "result.json"
        save_result_to_file(success_result, output_path)

        assert output_path.exists()


@pytest.mark.unit
class TestSaveResultsToFile:
    """Tests for save_results_to_file function."""

    def test_save_results(
        self,
        tmp_path: Path,
        success_result: AgentResult,
        error_result: AgentResult,
    ) -> None:
        """Test saving multiple results to file."""
        output_path = tmp_path / "results.json"
        save_results_to_file([success_result, error_result], output_path)

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert len(data) == 2
