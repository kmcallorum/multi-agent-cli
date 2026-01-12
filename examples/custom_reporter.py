#!/usr/bin/env python3
"""Example: Custom reporter implementation.

This example demonstrates how to create a custom reporter
for specialized output formatting.
"""

from multi_agent_cli.models.results import AgentResult, WorkflowResult


class MarkdownReporter:
    """Generate Markdown-formatted reports."""

    def display_result(self, result: AgentResult) -> None:
        """Display result as Markdown."""
        status_emoji = "✅" if result.status == "success" else "❌"
        print(f"## {status_emoji} {result.agent}.{result.action}")
        print()
        print(f"- **Status:** {result.status}")
        print(f"- **Duration:** {result.duration_seconds:.2f}s")
        print(f"- **Timestamp:** {result.timestamp}")
        print()

        if result.error:
            print(f"### Error")
            print(f"```")
            print(result.error)
            print(f"```")
            print()

        if result.data:
            print("### Data")
            print()
            for key, value in result.data.items():
                print(f"- **{key}:** {value}")
            print()

    def display_workflow_result(self, result: WorkflowResult) -> None:
        """Display workflow result as Markdown."""
        status_emoji = "✅" if result.quality_gates_passed else "❌"

        print(f"# {status_emoji} {result.workflow_name}")
        print()
        print("## Summary")
        print()
        print(f"| Metric | Value |")
        print(f"|--------|-------|")
        print(f"| Steps Completed | {result.steps_completed} |")
        print(f"| Steps Failed | {result.steps_failed} |")
        print(f"| Total Duration | {result.total_duration:.2f}s |")
        print(f"| Quality Gates | {'Passed' if result.quality_gates_passed else 'Failed'} |")
        print()
        print("## Step Results")
        print()

        for step_result in result.results:
            self.display_result(step_result)

    def display_results(self, results: list[AgentResult]) -> None:
        """Display multiple results as Markdown."""
        success_count = sum(1 for r in results if r.status == "success")
        print(f"# Parallel Execution Results")
        print()
        print(f"**{success_count}/{len(results)}** tasks succeeded")
        print()

        for result in results:
            self.display_result(result)


def main() -> None:
    """Demonstrate custom reporter."""
    # Create sample results
    results = [
        AgentResult.success(
            agent="pm",
            action="track_tasks",
            data={"count": 5, "fixmes": 2},
            duration_seconds=1.5,
        ),
        AgentResult.failure(
            agent="research",
            action="analyze",
            error="Document not found",
            duration_seconds=0.3,
        ),
    ]

    # Use custom reporter
    reporter = MarkdownReporter()
    reporter.display_results(results)


if __name__ == "__main__":
    main()
