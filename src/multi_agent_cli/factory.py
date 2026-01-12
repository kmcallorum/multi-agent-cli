"""Factory pattern for dependency injection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from multi_agent_cli.models.agent import AgentsConfig


class AgentBridge(Protocol):
    """Protocol defining the agent bridge interface."""

    def invoke_agent(
        self, agent: str, action: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Invoke an agent with the given action and parameters.

        Args:
            agent: Agent name.
            action: Action to perform.
            params: Action parameters.

        Returns:
            Result dictionary with 'status' and 'data' keys.
        """
        ...


class AgentBridgeFactory(Protocol):
    """Protocol for agent bridge factories."""

    def create(self, config: AgentsConfig) -> AgentBridge:
        """Create agent bridge from config.

        Args:
            config: Agents configuration.

        Returns:
            Agent bridge instance.
        """
        ...


class DefaultAgentBridge:
    """Default agent bridge using pytest-agents."""

    def __init__(self, config: AgentsConfig) -> None:
        """Initialize bridge with configuration.

        Args:
            config: Agents configuration.
        """
        self._config = config
        self._bridge: Any = None

    def _get_bridge(self) -> Any:  # pragma: no cover
        """Lazily initialize the pytest-agents bridge."""
        if self._bridge is None:
            from pytest_agents import (  # type: ignore[attr-defined]
                AgentBridge as PytestAgentBridge,
            )
            from pytest_agents import (  # type: ignore[attr-defined]
                PytestAgentsConfig,
            )

            pm = self._config.agents.get("pm")
            research = self._config.agents.get("research")
            index = self._config.agents.get("index")

            pytest_config = PytestAgentsConfig(
                agent_pm_enabled=pm is not None and pm.enabled,
                agent_pm_path=pm.path if pm else "",
                agent_research_enabled=research is not None and research.enabled,
                agent_research_path=research.path if research else "",
                agent_index_enabled=index is not None and index.enabled,
                agent_index_path=index.path if index else "",
            )
            self._bridge = PytestAgentBridge(pytest_config)

        return self._bridge

    def invoke_agent(  # pragma: no cover
        self, agent: str, action: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Invoke an agent via pytest-agents.

        Args:
            agent: Agent name.
            action: Action to perform.
            params: Action parameters.

        Returns:
            Result dictionary.
        """
        bridge = self._get_bridge()
        result: dict[str, Any] = bridge.invoke_agent(agent, action, params)
        return result


class DefaultAgentBridgeFactory:
    """Default factory using pytest-agents."""

    def create(self, config: AgentsConfig) -> AgentBridge:
        """Create real agent bridge.

        Args:
            config: Agents configuration.

        Returns:
            DefaultAgentBridge instance.
        """
        return DefaultAgentBridge(config)


class MockAgentBridge:
    """Mock agent bridge for testing."""

    def __init__(
        self,
        mock_responses: dict[str, dict[str, Any]],
        invocations: list[tuple[str, str, dict[str, Any]]],
    ) -> None:
        """Initialize mock bridge.

        Args:
            mock_responses: Dict mapping 'agent.action' to response dicts.
            invocations: List to record invocations for verification.
        """
        self.mock_responses = mock_responses
        self.invocations = invocations

    def invoke_agent(
        self, agent: str, action: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Return mock response for agent invocation.

        Args:
            agent: Agent name.
            action: Action to perform.
            params: Action parameters.

        Returns:
            Mock response dictionary.
        """
        self.invocations.append((agent, action, params))

        key = f"{agent}.{action}"
        if key in self.mock_responses:
            return self.mock_responses[key]

        # Default response
        return {
            "status": "success",
            "data": {"agent": agent, "action": action, "params": params},
        }


class MockAgentBridgeFactory:
    """Factory for testing with mock responses."""

    def __init__(self, mock_responses: dict[str, dict[str, Any]] | None = None) -> None:
        """Initialize with mock responses.

        Args:
            mock_responses: Dict mapping 'agent.action' to response dicts.
        """
        self.mock_responses: dict[str, dict[str, Any]] = mock_responses or {}
        self.invocations: list[tuple[str, str, dict[str, Any]]] = []

    def create(self, config: AgentsConfig) -> AgentBridge:  # noqa: ARG002
        """Create mock agent bridge.

        Args:
            config: Agents configuration (ignored for mock).

        Returns:
            MockAgentBridge instance.
        """
        return MockAgentBridge(self.mock_responses, self.invocations)


# Global factory instance
_default_factory: AgentBridgeFactory | None = None


def get_default_factory() -> AgentBridgeFactory:
    """Get default factory instance.

    Returns:
        Current default factory.
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = DefaultAgentBridgeFactory()
    return _default_factory


def set_default_factory(factory: AgentBridgeFactory | None) -> None:
    """Set default factory (primarily for testing).

    Args:
        factory: Factory to set as default, or None to reset.
    """
    global _default_factory
    _default_factory = factory
