"""Integration tests for parallel execution."""

from __future__ import annotations

import pytest

from multi_agent_cli.coordinator import AgentCoordinator
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
        },
        "research.analyze_document": {
            "status": "success",
            "data": {"summary": "Test", "completeness": 0.9},
        },
        "index.index_repository": {
            "status": "success",
            "data": {"files": 100, "symbols": 500},
        },
    }
    factory = MockAgentBridgeFactory(responses)
    set_default_factory(factory)
    set_metrics(MetricsRecorder())
    yield
    set_default_factory(None)
    set_metrics(None)


@pytest.mark.integration
class TestParallelExecution:
    """Integration tests for parallel execution."""

    @pytest.mark.asyncio
    async def test_execute_multiple_agents_parallel(self) -> None:
        """Test executing multiple agents in parallel."""
        responses = {
            "pm.track_tasks": {"status": "success", "data": {"count": 1}},
            "research.analyze_document": {"status": "success", "data": {"score": 0.9}},
            "index.index_repository": {"status": "success", "data": {"files": 100}},
        }
        factory = MockAgentBridgeFactory(responses)
        set_default_factory(factory)

        config = AgentsConfig()
        bridge = factory.create(config)
        executor = AgentExecutor(bridge)
        coordinator = AgentCoordinator(executor, max_workers=3)

        tasks = [
            ("pm", "track_tasks", {"path": "./src"}),
            ("research", "analyze_document", {"path": "./README.md"}),
            ("index", "index_repository", {"path": "./src"}),
        ]

        results = await coordinator.execute_parallel(tasks)

        assert len(results) == 3
        assert all(r.status == "success" for r in results)
        assert len(factory.invocations) == 3

    @pytest.mark.asyncio
    async def test_parallel_with_rate_limiting(self) -> None:
        """Test parallel execution respects rate limiting."""
        factory = MockAgentBridgeFactory({})
        set_default_factory(factory)

        config = AgentsConfig()
        bridge = factory.create(config)
        executor = AgentExecutor(bridge)
        coordinator = AgentCoordinator(executor, max_workers=2)

        tasks = [
            ("pm", "action1", {}),
            ("pm", "action2", {}),
            ("pm", "action3", {}),
            ("pm", "action4", {}),
        ]

        results = await coordinator.execute_parallel(tasks)

        assert len(results) == 4
