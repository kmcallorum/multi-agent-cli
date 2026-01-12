"""Integration tests for single agent execution."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from multi_agent_cli.cli import cli
from multi_agent_cli.executor import AgentExecutor
from multi_agent_cli.factory import MockAgentBridgeFactory, set_default_factory
from multi_agent_cli.metrics import MetricsRecorder, set_metrics
from multi_agent_cli.models.agent import AgentsConfig


@pytest.fixture(autouse=True)
def setup_mocks() -> None:
    """Set up mocks for all tests."""
    responses = {
        "pm.track_tasks": {
            "status": "success",
            "data": {"tasks": [], "count": 0},
        }
    }
    factory = MockAgentBridgeFactory(responses)
    set_default_factory(factory)
    set_metrics(MetricsRecorder())
    yield
    set_default_factory(None)
    set_metrics(None)


@pytest.mark.integration
class TestSingleAgentExecution:
    """Integration tests for single agent execution."""

    @pytest.mark.asyncio
    async def test_execute_pm_agent(self) -> None:
        """Test executing PM agent."""
        responses = {
            "pm.track_tasks": {
                "status": "success",
                "data": {
                    "tasks": [{"id": "1", "type": "todo", "description": "Test"}],
                    "count": 1,
                },
            }
        }
        factory = MockAgentBridgeFactory(responses)
        set_default_factory(factory)

        config = AgentsConfig()
        bridge = factory.create(config)
        executor = AgentExecutor(bridge)

        result = await executor.execute("pm", "track_tasks", {"path": "./src"})

        assert result.status == "success"
        assert result.data["count"] == 1

    def test_cli_run_pm_agent(self, cli_runner: CliRunner) -> None:
        """Test CLI run command for PM agent."""
        result = cli_runner.invoke(cli, ["run", "pm", "track_tasks", "--path", "."])
        assert result.exit_code == 0
        assert "pm.track_tasks" in result.output


@pytest.mark.integration
@pytest.mark.requires_agents
class TestRealAgentIntegration:
    """Integration tests with real agents (skipped by default)."""

    def test_pm_agent_real(self) -> None:
        """Test PM agent with real agent bridge."""
        # This test is skipped unless explicitly requested
        # It would require actual pytest-agents setup
        pytest.skip("Requires real agent setup")
