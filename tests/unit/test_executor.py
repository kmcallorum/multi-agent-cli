"""Tests for executor module."""

from __future__ import annotations

from typing import Any

import pytest

from multi_agent_cli.executor import AgentExecutor, _get_timestamp
from multi_agent_cli.factory import MockAgentBridge, MockAgentBridgeFactory
from multi_agent_cli.metrics import MetricsRecorder
from multi_agent_cli.models.agent import AgentsConfig


@pytest.mark.unit
class TestAgentExecutor:
    """Tests for AgentExecutor."""

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        mock_factory: MockAgentBridgeFactory,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test successful agent execution."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge, mock_metrics)

        result = await executor.execute("pm", "track_tasks", {"path": "./src"})

        assert result.status == "success"
        assert result.agent == "pm"
        assert result.action == "track_tasks"
        assert result.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_execute_error_response(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test error in agent response."""
        invocations: list[tuple[str, str, dict[str, Any]]] = []
        mock_responses = {
            "pm.track_tasks": {
                "status": "error",
                "data": {"error": "Test error"},
            }
        }
        bridge = MockAgentBridge(mock_responses, invocations)
        executor = AgentExecutor(bridge, mock_metrics)

        result = await executor.execute("pm", "track_tasks", {})

        assert result.status == "error"
        assert result.error == "Test error"

    @pytest.mark.asyncio
    async def test_execute_timeout(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test execution timeout."""

        # Create a bridge that takes too long
        class SlowBridge:
            def invoke_agent(
                self, agent: str, action: str, params: dict[str, Any]
            ) -> dict[str, Any]:
                import time

                time.sleep(2)  # Simulate slow execution
                return {"status": "success", "data": {}}

        bridge = SlowBridge()
        executor = AgentExecutor(bridge, mock_metrics, default_timeout=1)

        result = await executor.execute("pm", "track", {}, timeout=1)

        assert result.status == "error"
        assert "Timeout" in str(result.error)

    @pytest.mark.asyncio
    async def test_execute_exception(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test handling execution exception."""

        class FailingBridge:
            def invoke_agent(
                self, agent: str, action: str, params: dict[str, Any]
            ) -> dict[str, Any]:
                raise RuntimeError("Bridge failed")

        bridge = FailingBridge()
        executor = AgentExecutor(bridge, mock_metrics)

        result = await executor.execute("pm", "track", {})

        assert result.status == "error"
        assert "Bridge failed" in str(result.error)

    @pytest.mark.asyncio
    async def test_execute_without_metrics(
        self,
        mock_factory: MockAgentBridgeFactory,
    ) -> None:
        """Test execution without metrics."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge)  # No metrics

        result = await executor.execute("pm", "track_tasks", {})

        assert result.status == "success"

    def test_execute_sync(
        self,
        mock_factory: MockAgentBridgeFactory,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test synchronous execution."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge, mock_metrics)

        result = executor.execute_sync("pm", "track_tasks", {"path": "./src"})

        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_execute_with_custom_timeout(
        self,
        mock_factory: MockAgentBridgeFactory,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test execution with custom timeout."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge, mock_metrics, default_timeout=30)

        result = await executor.execute("pm", "track_tasks", {}, timeout=60)

        assert result.status == "success"


@pytest.mark.unit
class TestGetTimestamp:
    """Tests for _get_timestamp function."""

    def test_returns_iso_format(self) -> None:
        """Test that timestamp is ISO format."""
        timestamp = _get_timestamp()
        assert "T" in timestamp
        # Should be parseable
        from datetime import datetime

        datetime.fromisoformat(timestamp)
