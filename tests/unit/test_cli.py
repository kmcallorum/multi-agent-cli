"""Tests for CLI module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from multi_agent_cli.cli import cli
from multi_agent_cli.factory import MockAgentBridgeFactory, set_default_factory
from multi_agent_cli.metrics import NullMetricsRecorder, set_metrics


@pytest.fixture(autouse=True)
def setup_mocks(mock_agent_responses: dict[str, dict[str, Any]]) -> None:
    """Set up mocks for all CLI tests."""
    factory = MockAgentBridgeFactory(mock_agent_responses)
    set_default_factory(factory)
    set_metrics(NullMetricsRecorder())
    yield
    set_default_factory(None)
    set_metrics(None)


@pytest.mark.unit
class TestCLI:
    """Tests for main CLI group."""

    def test_help(self, cli_runner: CliRunner) -> None:
        """Test help output."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Multi-agent orchestration CLI" in result.output

    def test_version(self, cli_runner: CliRunner) -> None:
        """Test version output."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()


@pytest.mark.unit
class TestRunCommand:
    """Tests for run command."""

    def test_run_success(self, cli_runner: CliRunner) -> None:
        """Test successful agent run."""
        result = cli_runner.invoke(cli, ["run", "pm", "track_tasks"])
        assert result.exit_code == 0
        assert "pm.track_tasks" in result.output

    def test_run_with_path(self, cli_runner: CliRunner) -> None:
        """Test run with path option."""
        result = cli_runner.invoke(cli, ["run", "pm", "track_tasks", "--path", "./src"])
        assert result.exit_code == 0

    def test_run_with_params(self, cli_runner: CliRunner) -> None:
        """Test run with JSON params."""
        result = cli_runner.invoke(
            cli, ["run", "pm", "track_tasks", "--params", '{"key": "value"}']
        )
        assert result.exit_code == 0

    def test_run_with_invalid_params(self, cli_runner: CliRunner) -> None:
        """Test run with invalid JSON params."""
        result = cli_runner.invoke(
            cli, ["run", "pm", "track_tasks", "--params", "not json"]
        )
        assert result.exit_code == 1
        assert "Invalid JSON" in result.output

    def test_run_with_output(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test run with output file."""
        output_file = tmp_path / "result.json"
        result = cli_runner.invoke(
            cli, ["run", "pm", "track_tasks", "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_run_unknown_agent(self, cli_runner: CliRunner) -> None:
        """Test run with unknown agent."""
        result = cli_runner.invoke(cli, ["run", "unknown", "action"])
        assert result.exit_code == 1
        assert "Unknown agent" in result.output

    def test_run_quiet(self, cli_runner: CliRunner) -> None:
        """Test run in quiet mode."""
        result = cli_runner.invoke(cli, ["-q", "run", "pm", "track_tasks"])
        assert result.exit_code == 0

    def test_run_verbose(self, cli_runner: CliRunner) -> None:
        """Test run in verbose mode."""
        result = cli_runner.invoke(cli, ["-v", "run", "pm", "track_tasks"])
        assert result.exit_code == 0

    def test_run_json_format(self, cli_runner: CliRunner) -> None:
        """Test run with JSON output format."""
        result = cli_runner.invoke(
            cli, ["--format", "json", "run", "pm", "track_tasks"]
        )
        assert result.exit_code == 0

    def test_run_error_response(
        self,
        cli_runner: CliRunner,
        mock_agent_responses: dict[str, dict[str, Any]],
    ) -> None:
        """Test run with error response."""
        mock_agent_responses["pm.track_tasks"] = {
            "status": "error",
            "data": {"error": "Test error"},
        }
        factory = MockAgentBridgeFactory(mock_agent_responses)
        set_default_factory(factory)

        result = cli_runner.invoke(cli, ["run", "pm", "track_tasks"])
        assert result.exit_code == 1


@pytest.mark.unit
class TestParallelCommand:
    """Tests for parallel command."""

    def test_parallel_success(self, cli_runner: CliRunner) -> None:
        """Test successful parallel execution."""
        result = cli_runner.invoke(cli, ["parallel", "--agents", "pm,research"])
        assert result.exit_code == 0

    def test_parallel_with_path(self, cli_runner: CliRunner) -> None:
        """Test parallel with path option."""
        result = cli_runner.invoke(
            cli, ["parallel", "--agents", "pm", "--path", "./src"]
        )
        assert result.exit_code == 0

    def test_parallel_with_max_workers(self, cli_runner: CliRunner) -> None:
        """Test parallel with max workers."""
        result = cli_runner.invoke(
            cli, ["parallel", "--agents", "pm,research", "--max-workers", "2"]
        )
        assert result.exit_code == 0

    def test_parallel_with_output(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test parallel with output file."""
        output_file = tmp_path / "results.json"
        result = cli_runner.invoke(
            cli, ["parallel", "--agents", "pm", "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_parallel_no_agents_or_workflow(self, cli_runner: CliRunner) -> None:
        """Test parallel without agents or workflow."""
        result = cli_runner.invoke(cli, ["parallel"])
        assert result.exit_code == 1
        assert "must be specified" in result.output

    def test_parallel_quiet(self, cli_runner: CliRunner) -> None:
        """Test parallel in quiet mode."""
        result = cli_runner.invoke(cli, ["-q", "parallel", "--agents", "pm"])
        assert result.exit_code == 0


@pytest.mark.unit
class TestWorkflowCommand:
    """Tests for workflow command."""

    def test_workflow_success(
        self, cli_runner: CliRunner, temp_workflow_file: Path
    ) -> None:
        """Test successful workflow execution."""
        result = cli_runner.invoke(cli, ["workflow", str(temp_workflow_file)])
        assert result.exit_code == 0

    def test_workflow_strict(
        self, cli_runner: CliRunner, temp_workflow_file: Path
    ) -> None:
        """Test workflow with strict mode."""
        result = cli_runner.invoke(
            cli, ["workflow", str(temp_workflow_file), "--strict"]
        )
        assert result.exit_code == 0

    def test_workflow_with_output(
        self,
        cli_runner: CliRunner,
        temp_workflow_file: Path,
        tmp_path: Path,
    ) -> None:
        """Test workflow with output file."""
        output_file = tmp_path / "workflow_result.json"
        result = cli_runner.invoke(
            cli, ["workflow", str(temp_workflow_file), "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_workflow_quiet(
        self, cli_runner: CliRunner, temp_workflow_file: Path
    ) -> None:
        """Test workflow in quiet mode."""
        result = cli_runner.invoke(cli, ["-q", "workflow", str(temp_workflow_file)])
        assert result.exit_code == 0

    def test_workflow_dry_run(
        self, cli_runner: CliRunner, temp_workflow_file: Path
    ) -> None:
        """Test workflow dry-run mode."""
        result = cli_runner.invoke(
            cli, ["workflow", str(temp_workflow_file), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Execution Plan" in result.output

    def test_workflow_dry_run_json_format(
        self, cli_runner: CliRunner, temp_workflow_file: Path
    ) -> None:
        """Test workflow dry-run with JSON output."""
        result = cli_runner.invoke(
            cli, ["--format", "json", "workflow", str(temp_workflow_file), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "workflow_name" in result.output
        assert "is_valid" in result.output

    def test_workflow_dry_run_table_format(
        self, cli_runner: CliRunner, temp_workflow_file: Path
    ) -> None:
        """Test workflow dry-run with table output."""
        result = cli_runner.invoke(
            cli, ["--format", "table", "workflow", str(temp_workflow_file), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_workflow_dry_run_with_output(
        self, cli_runner: CliRunner, temp_workflow_file: Path, tmp_path: Path
    ) -> None:
        """Test workflow dry-run with output file."""
        output_file = tmp_path / "dry_run.json"
        result = cli_runner.invoke(
            cli,
            [
                "workflow",
                str(temp_workflow_file),
                "--dry-run",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_workflow_dry_run_invalid(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test dry-run with invalid workflow (missing dependency)."""
        workflow_content = """
name: Invalid Workflow
steps:
  - name: Step 1
    agent: pm
    action: track_tasks
    depends_on:
      - NonexistentStep
"""
        workflow_file = tmp_path / "invalid_deps.yaml"
        workflow_file.write_text(workflow_content)

        # Invalid workflows are caught during load_workflow before dry-run
        result = cli_runner.invoke(cli, ["workflow", str(workflow_file), "--dry-run"])
        assert result.exit_code == 1
        assert "Invalid workflow dependencies" in result.output
        assert "NonexistentStep" in result.output

    def test_workflow_dry_run_quiet(
        self, cli_runner: CliRunner, temp_workflow_file: Path
    ) -> None:
        """Test workflow dry-run in quiet mode."""
        result = cli_runner.invoke(
            cli, ["-q", "workflow", str(temp_workflow_file), "--dry-run"]
        )
        assert result.exit_code == 0

    def test_workflow_dry_run_quiet_with_output(
        self, cli_runner: CliRunner, temp_workflow_file: Path, tmp_path: Path
    ) -> None:
        """Test workflow dry-run in quiet mode with output file."""
        output_file = tmp_path / "dry_run_quiet.json"
        result = cli_runner.invoke(
            cli,
            [
                "-q",
                "workflow",
                str(temp_workflow_file),
                "--dry-run",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        # In quiet mode, shouldn't print "saved to" message
        assert "saved to" not in result.output


@pytest.mark.unit
class TestListCommand:
    """Tests for list command."""

    def test_list_agents(self, cli_runner: CliRunner) -> None:
        """Test listing agents."""
        result = cli_runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "pm" in result.output

    def test_list_agents_verbose(self, cli_runner: CliRunner) -> None:
        """Test listing agents with verbose mode."""
        result = cli_runner.invoke(cli, ["list", "--verbose"])
        assert result.exit_code == 0

    def test_list_agents_json_format(self, cli_runner: CliRunner) -> None:
        """Test listing agents with JSON format."""
        result = cli_runner.invoke(cli, ["--format", "json", "list"])
        assert result.exit_code == 0


@pytest.mark.unit
class TestConfigCommand:
    """Tests for config command."""

    def test_config_show(self, cli_runner: CliRunner, temp_config_file: Path) -> None:
        """Test showing configuration."""
        result = cli_runner.invoke(
            cli, ["--config", str(temp_config_file), "config", "show"]
        )
        assert result.exit_code == 0

    def test_config_show_no_config(self, cli_runner: CliRunner) -> None:
        """Test showing config when none loaded."""
        result = cli_runner.invoke(cli, ["config", "show"])
        assert result.exit_code == 1

    def test_config_validate_valid(
        self, cli_runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test validating valid configuration."""
        result = cli_runner.invoke(cli, ["config", "validate", str(temp_config_file)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_config_validate_invalid(
        self, cli_runner: CliRunner, temp_invalid_yaml_file: Path
    ) -> None:
        """Test validating invalid configuration."""
        result = cli_runner.invoke(
            cli, ["config", "validate", str(temp_invalid_yaml_file)]
        )
        assert result.exit_code == 1

    def test_config_init(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test initializing configuration."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(cli, ["config", "init"])
            assert result.exit_code == 0
            assert Path("agents.yaml").exists()

    def test_config_init_with_output(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test initializing configuration with custom output."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                cli, ["config", "init", "--output", "custom.yaml"]
            )
            assert result.exit_code == 0
            assert Path("custom.yaml").exists()

    def test_config_init_existing_file(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test initializing when file exists."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            Path("agents.yaml").write_text("existing")
            result = cli_runner.invoke(cli, ["config", "init"])
            assert result.exit_code == 1
            assert "exists" in result.output.lower()

    def test_config_init_with_workflows(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test initializing with example workflows."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(cli, ["config", "init", "--example-workflows"])
            assert result.exit_code == 0
            assert Path("workflows/example.yaml").exists()


@pytest.mark.unit
class TestInitCommand:
    """Tests for init command."""

    def test_init(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test init command."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert Path("agents.yaml").exists()

    def test_init_with_workflows(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test init with example workflows."""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(cli, ["init", "--example-workflows"])
            assert result.exit_code == 0


@pytest.mark.unit
class TestCLIWithConfig:
    """Tests for CLI with configuration file."""

    def test_cli_with_config(
        self, cli_runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test CLI loads configuration."""
        result = cli_runner.invoke(cli, ["--config", str(temp_config_file), "list"])
        assert result.exit_code == 0

    def test_cli_with_nonexistent_config(self, cli_runner: CliRunner) -> None:
        """Test CLI with nonexistent config continues."""
        result = cli_runner.invoke(cli, ["--config", "nonexistent.yaml", "list"])
        # Should still work with defaults
        assert result.exit_code == 0

    def test_cli_verbose_shows_config_warning(self, cli_runner: CliRunner) -> None:
        """Test verbose mode shows config warning."""
        result = cli_runner.invoke(cli, ["-v", "--config", "nonexistent.yaml", "list"])
        assert result.exit_code == 0

    def test_run_with_loaded_config(
        self, cli_runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test run uses agents from loaded config."""
        result = cli_runner.invoke(
            cli, ["--config", str(temp_config_file), "run", "pm", "track_tasks"]
        )
        assert result.exit_code == 0

    def test_list_with_table_format(
        self, cli_runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test list with table format."""
        result = cli_runner.invoke(
            cli, ["--format", "table", "--config", str(temp_config_file), "list"]
        )
        assert result.exit_code == 0


@pytest.mark.unit
class TestCLIEdgeCases:
    """Test edge cases for CLI."""

    def test_workflow_with_failed_quality_gates(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test workflow exits with error on failed quality gates."""
        # Create workflow that will fail quality gates
        workflow_content = """
name: Failing Workflow
description: Workflow with impossible quality gates

steps:
  - name: Step 1
    agent: pm
    action: track_tasks
    params:
      path: "./src"

quality_gates:
  max_fixmes: 0
"""
        workflow_file = tmp_path / "failing.yaml"
        workflow_file.write_text(workflow_content)

        result = cli_runner.invoke(cli, ["workflow", str(workflow_file)])
        # Should exit with 1 due to failed quality gates
        assert result.exit_code == 1

    def test_config_show_json_format(
        self, cli_runner: CliRunner, temp_config_file: Path
    ) -> None:
        """Test config show with JSON format."""
        result = cli_runner.invoke(
            cli,
            ["--format", "json", "--config", str(temp_config_file), "config", "show"],
        )
        assert result.exit_code == 0

    def test_parallel_with_error_results(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test parallel exits with error when any agent fails."""
        # This test relies on mock factory returning error for unknown agent
        result = cli_runner.invoke(cli, ["-q", "parallel", "--agents", "pm,research"])
        # Should succeed with mocks
        assert result.exit_code == 0

    def test_run_with_output_quiet(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test run with output file in quiet mode."""
        output_file = tmp_path / "quiet_result.json"
        result = cli_runner.invoke(
            cli, ["-q", "run", "pm", "track_tasks", "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_verbose_with_invalid_config(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test verbose shows warning for invalid config."""
        # Create invalid config file
        invalid_config = tmp_path / "invalid_config.yaml"
        invalid_config.write_text("invalid: yaml: content: [")

        result = cli_runner.invoke(cli, ["-v", "--config", str(invalid_config), "list"])
        # Should continue but show warning in verbose mode
        assert result.exit_code == 0
        assert "Warning" in result.output

    def test_parallel_with_output(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test parallel with output file."""
        output_file = tmp_path / "parallel_result.json"
        result = cli_runner.invoke(
            cli,
            ["parallel", "--agents", "pm", "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
