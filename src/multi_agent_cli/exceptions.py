"""Custom exceptions for multi-agent-cli."""

from __future__ import annotations


class MultiAgentCLIError(Exception):
    """Base exception for multi-agent-cli."""

    pass


class ConfigError(MultiAgentCLIError):
    """Configuration error."""

    pass


class AgentError(MultiAgentCLIError):
    """Agent execution error."""

    pass


class WorkflowError(MultiAgentCLIError):
    """Workflow execution error."""

    pass


class ValidationError(MultiAgentCLIError):
    """Validation error."""

    pass
