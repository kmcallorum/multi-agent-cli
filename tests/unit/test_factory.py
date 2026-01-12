"""Tests for factory module."""

from __future__ import annotations

from typing import Any

import pytest

from multi_agent_cli.factory import (
    DefaultAgentBridgeFactory,
    MockAgentBridge,
    MockAgentBridgeFactory,
    get_default_factory,
    set_default_factory,
)
from multi_agent_cli.models.agent import AgentsConfig


@pytest.mark.unit
class TestMockAgentBridge:
    """Tests for MockAgentBridge."""

    def test_invoke_with_mock_response(self) -> None:
        """Test invoking with mock response."""
        invocations: list[tuple[str, str, dict[str, Any]]] = []
        mock_responses = {"pm.track_tasks": {"status": "success", "data": {"count": 5}}}
        bridge = MockAgentBridge(mock_responses, invocations)

        result = bridge.invoke_agent("pm", "track_tasks", {"path": "./src"})

        assert result["status"] == "success"
        assert result["data"]["count"] == 5
        assert len(invocations) == 1
        assert invocations[0] == ("pm", "track_tasks", {"path": "./src"})

    def test_invoke_without_mock_response(self) -> None:
        """Test invoking without specific mock response."""
        invocations: list[tuple[str, str, dict[str, Any]]] = []
        bridge = MockAgentBridge({}, invocations)

        result = bridge.invoke_agent("unknown", "action", {"key": "value"})

        assert result["status"] == "success"
        assert result["data"]["agent"] == "unknown"
        assert result["data"]["action"] == "action"


@pytest.mark.unit
class TestMockAgentBridgeFactory:
    """Tests for MockAgentBridgeFactory."""

    def test_create_bridge(self) -> None:
        """Test creating mock bridge."""
        responses = {"pm.track": {"status": "success", "data": {}}}
        factory = MockAgentBridgeFactory(responses)
        config = AgentsConfig()

        bridge = factory.create(config)

        assert isinstance(bridge, MockAgentBridge)

    def test_invocations_tracked(self) -> None:
        """Test that invocations are tracked."""
        factory = MockAgentBridgeFactory()
        config = AgentsConfig()
        bridge = factory.create(config)

        bridge.invoke_agent("pm", "track", {})

        assert len(factory.invocations) == 1


@pytest.mark.unit
class TestDefaultAgentBridgeFactory:
    """Tests for DefaultAgentBridgeFactory."""

    def test_create_bridge(self) -> None:
        """Test creating default bridge (lazy initialization)."""
        factory = DefaultAgentBridgeFactory()
        config = AgentsConfig()

        # Just test that create doesn't fail
        # The actual bridge creation is lazy
        bridge = factory.create(config)
        assert bridge is not None


@pytest.mark.unit
class TestFactoryFunctions:
    """Tests for factory module functions."""

    def test_get_default_factory(self) -> None:
        """Test getting default factory."""
        set_default_factory(None)
        factory = get_default_factory()
        assert factory is not None
        assert isinstance(factory, DefaultAgentBridgeFactory)

    def test_set_default_factory(self) -> None:
        """Test setting default factory."""
        mock_factory = MockAgentBridgeFactory()
        set_default_factory(mock_factory)

        factory = get_default_factory()
        assert factory is mock_factory

        # Clean up
        set_default_factory(None)

    def test_set_default_factory_to_none(self) -> None:
        """Test resetting default factory."""
        mock_factory = MockAgentBridgeFactory()
        set_default_factory(mock_factory)
        set_default_factory(None)

        factory = get_default_factory()
        assert isinstance(factory, DefaultAgentBridgeFactory)
