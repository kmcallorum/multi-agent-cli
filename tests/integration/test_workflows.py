"""Integration tests for workflow execution."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from multi_agent_cli.cli import cli
from multi_agent_cli.coordinator import AgentCoordinator
from multi_agent_cli.executor import AgentExecutor
from multi_agent_cli.factory import MockAgentBridgeFactory, set_default_factory
from multi_agent_cli.metrics import MetricsRecorder, set_metrics
from multi_agent_cli.models.agent import AgentsConfig
from multi_agent_cli.models.workflow import Workflow, WorkflowStep


@pytest.fixture(autouse=True)
def setup_mocks() -> None:
    """Set up mocks for all tests."""
    responses = {
        "pm.track_tasks": {
            "status": "success",
            "data": {"tasks": [], "count": 0, "fixme_count": 2},
        },
        "research.analyze_document": {
            "status": "success",
            "data": {"summary": "Test", "documentation_score": 0.85},
        },
        "index.index_repository": {
            "status": "success",
            "data": {"files": 100, "dead_code_percent": 3.0},
        },
    }
    factory = MockAgentBridgeFactory(responses)
    set_default_factory(factory)
    set_metrics(MetricsRecorder())
    yield
    set_default_factory(None)
    set_metrics(None)


@pytest.mark.integration
class TestWorkflowExecution:
    """Integration tests for workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_sequential_workflow(self) -> None:
        """Test executing sequential workflow."""
        factory = MockAgentBridgeFactory(
            {
                "pm.track_tasks": {"status": "success", "data": {}},
                "research.analyze_document": {"status": "success", "data": {}},
            }
        )
        set_default_factory(factory)

        config = AgentsConfig()
        bridge = factory.create(config)
        executor = AgentExecutor(bridge)
        coordinator = AgentCoordinator(executor)

        workflow = Workflow(
            name="Test Workflow",
            steps=[
                WorkflowStep(name="Step 1", agent="pm", action="track_tasks"),
                WorkflowStep(
                    name="Step 2",
                    agent="research",
                    action="analyze_document",
                    depends_on=["Step 1"],
                ),
            ],
        )

        result = await coordinator.execute_workflow(workflow)

        assert result.workflow_name == "Test Workflow"
        assert result.steps_completed == 2
        assert result.steps_failed == 0

    @pytest.mark.asyncio
    async def test_workflow_with_quality_gates(self) -> None:
        """Test workflow with quality gate checking."""
        from multi_agent_cli.models.workflow import QualityGates

        factory = MockAgentBridgeFactory(
            {
                "pm.track_tasks": {
                    "status": "success",
                    "data": {"fixme_count": 3},
                },
            }
        )
        set_default_factory(factory)

        config = AgentsConfig()
        bridge = factory.create(config)
        executor = AgentExecutor(bridge)
        coordinator = AgentCoordinator(executor)

        workflow = Workflow(
            name="Quality Check",
            steps=[
                WorkflowStep(name="Step 1", agent="pm", action="track_tasks"),
            ],
            quality_gates=QualityGates(max_fixmes=5),
        )

        result = await coordinator.execute_workflow(workflow)

        assert result.quality_gates_passed is True

    def test_cli_workflow_command(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test CLI workflow command."""
        workflow_content = """
name: CLI Test Workflow
steps:
  - name: Step 1
    agent: pm
    action: track_tasks
"""
        workflow_file = tmp_path / "test_workflow.yaml"
        workflow_file.write_text(workflow_content)

        result = cli_runner.invoke(cli, ["workflow", str(workflow_file)])
        assert result.exit_code == 0
        assert "CLI Test Workflow" in result.output
