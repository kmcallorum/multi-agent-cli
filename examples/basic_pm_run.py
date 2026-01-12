#!/usr/bin/env python3
"""Example: Basic PM agent execution.

This example demonstrates how to programmatically run a single agent
using the multi-agent-cli library.
"""

import asyncio

from multi_agent_cli.config import create_default_config
from multi_agent_cli.executor import AgentExecutor
from multi_agent_cli.factory import get_default_factory
from multi_agent_cli.reporters import RichReporter


async def main() -> None:
    """Run PM agent to track tasks."""
    # Create default configuration
    config = create_default_config()

    # Create executor with factory-provided bridge
    factory = get_default_factory()
    bridge = factory.create(config)
    executor = AgentExecutor(bridge)

    # Execute PM agent
    result = await executor.execute(
        agent="pm",
        action="track_tasks",
        params={"path": "./src"},
    )

    # Display result
    reporter = RichReporter(verbose=True)
    reporter.display_result(result)


if __name__ == "__main__":
    asyncio.run(main())
