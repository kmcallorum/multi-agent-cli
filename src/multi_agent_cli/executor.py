"""Agent execution engine."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from multi_agent_cli.factory import AgentBridge
from multi_agent_cli.metrics import MetricsRecorder, NullMetricsRecorder
from multi_agent_cli.models.results import AgentResult


class AgentExecutor:
    """Execute individual agent actions."""

    def __init__(
        self,
        agent_bridge: AgentBridge,
        metrics: MetricsRecorder | NullMetricsRecorder | None = None,
        default_timeout: int = 60,
    ) -> None:
        """Initialize executor.

        Args:
            agent_bridge: Bridge for invoking agents.
            metrics: Optional metrics recorder.
            default_timeout: Default timeout in seconds.
        """
        self.bridge = agent_bridge
        self.metrics = metrics
        self.default_timeout = default_timeout

    async def execute(
        self,
        agent: str,
        action: str,
        params: dict[str, Any],
        timeout: int | None = None,
    ) -> AgentResult:
        """Execute single agent action.

        Args:
            agent: Agent name.
            action: Action to perform.
            params: Action parameters.
            timeout: Optional timeout override.

        Returns:
            AgentResult with execution results.
        """
        start = time.time()
        effective_timeout = timeout if timeout is not None else self.default_timeout

        # Track invocation
        if self.metrics:
            self.metrics.record_agent_invocation(agent, action)

        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.bridge.invoke_agent(agent, action, params),
                ),
                timeout=effective_timeout,
            )

            duration = time.time() - start

            # Check for error in result
            status = result.get("status", "success")
            error_msg = None
            if status == "error":
                error_msg = result.get("data", {}).get("error", "Unknown error")
                if self.metrics:  # pragma: no branch
                    self.metrics.record_agent_error(agent, action)
            else:
                if self.metrics:  # pragma: no branch
                    self.metrics.record_agent_success(agent, action, duration)

            return AgentResult(
                agent=agent,
                action=action,
                status=status,
                data=result.get("data", {}),
                duration_seconds=duration,
                timestamp=_get_timestamp(),
                error=error_msg,
            )

        except TimeoutError:
            duration = time.time() - start
            if self.metrics:  # pragma: no branch
                self.metrics.record_agent_error(agent, action)

            return AgentResult.failure(
                agent=agent,
                action=action,
                error=f"Timeout after {effective_timeout} seconds",
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start
            if self.metrics:  # pragma: no branch
                self.metrics.record_agent_error(agent, action)

            return AgentResult.failure(
                agent=agent,
                action=action,
                error=str(e),
                duration_seconds=duration,
            )

    def execute_sync(
        self,
        agent: str,
        action: str,
        params: dict[str, Any],
        timeout: int | None = None,
    ) -> AgentResult:
        """Execute agent action synchronously.

        Args:
            agent: Agent name.
            action: Action to perform.
            params: Action parameters.
            timeout: Optional timeout override.

        Returns:
            AgentResult with execution results.
        """
        return asyncio.run(self.execute(agent, action, params, timeout))


def _get_timestamp() -> str:
    """Get current ISO timestamp.

    Returns:
        ISO format timestamp string.
    """
    from datetime import datetime

    return datetime.now().isoformat()
