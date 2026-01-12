#!/usr/bin/env python3
"""Example: Parallel agent analysis.

This example demonstrates how to run multiple agents in parallel
using the multi-agent-cli library.
"""

import asyncio

from multi_agent_cli.config import create_default_config
from multi_agent_cli.coordinator import AgentCoordinator
from multi_agent_cli.executor import AgentExecutor
from multi_agent_cli.factory import get_default_factory
from multi_agent_cli.reporters import RichReporter


async def main() -> None:
    """Run multiple agents in parallel."""
    # Create configuration and executor
    config = create_default_config()
    factory = get_default_factory()
    bridge = factory.create(config)
    executor = AgentExecutor(bridge)

    # Create coordinator with rate limiting
    coordinator = AgentCoordinator(executor, max_workers=3)

    # Define tasks to run in parallel
    tasks = [
        ("pm", "track_tasks", {"path": "./src"}),
        ("research", "analyze_document", {"path": "./README.md"}),
        ("index", "index_repository", {"path": "./src"}),
    ]

    # Execute in parallel
    results = await coordinator.execute_parallel(tasks)

    # Display results
    reporter = RichReporter()
    reporter.display_results(results)


if __name__ == "__main__":
    asyncio.run(main())
