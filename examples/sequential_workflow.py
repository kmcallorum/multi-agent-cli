#!/usr/bin/env python3
"""Example: Sequential workflow execution.

This example demonstrates how to execute a workflow with
dependencies between steps.
"""

import asyncio

from multi_agent_cli.config import create_default_config
from multi_agent_cli.coordinator import AgentCoordinator
from multi_agent_cli.executor import AgentExecutor
from multi_agent_cli.factory import get_default_factory
from multi_agent_cli.models.workflow import QualityGates, Workflow, WorkflowStep
from multi_agent_cli.reporters import RichReporter


async def main() -> None:
    """Execute a sequential workflow."""
    # Create configuration and executor
    config = create_default_config()
    factory = get_default_factory()
    bridge = factory.create(config)
    executor = AgentExecutor(bridge)
    coordinator = AgentCoordinator(executor)

    # Define workflow programmatically
    workflow = Workflow(
        name="Code Quality Check",
        description="Sequential code quality analysis",
        steps=[
            WorkflowStep(
                name="Track Tasks",
                agent="pm",
                action="track_tasks",
                params={"path": "./src"},
                on_error="continue",
            ),
            WorkflowStep(
                name="Analyze Docs",
                agent="research",
                action="analyze_document",
                params={"path": "./README.md"},
                on_error="fail",
                depends_on=["Track Tasks"],
            ),
            WorkflowStep(
                name="Index Code",
                agent="index",
                action="index_repository",
                params={"path": "./src"},
                depends_on=["Track Tasks"],
            ),
        ],
        quality_gates=QualityGates(
            max_fixmes=10,
            min_documentation_score=0.7,
        ),
    )

    # Execute workflow
    result = await coordinator.execute_workflow(workflow)

    # Display results
    reporter = RichReporter()
    reporter.display_workflow_result(result)


if __name__ == "__main__":
    asyncio.run(main())
