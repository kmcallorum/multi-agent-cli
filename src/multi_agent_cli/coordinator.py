"""Multi-agent coordination logic."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from multi_agent_cli.exceptions import WorkflowError
from multi_agent_cli.executor import AgentExecutor
from multi_agent_cli.metrics import MetricsRecorder, NullMetricsRecorder
from multi_agent_cli.models.results import AgentResult, WorkflowResult
from multi_agent_cli.models.workflow import Workflow


class AgentCoordinator:
    """Coordinate multiple agent executions."""

    def __init__(
        self,
        executor: AgentExecutor,
        max_workers: int = 3,
        metrics: MetricsRecorder | NullMetricsRecorder | None = None,
    ) -> None:
        """Initialize coordinator.

        Args:
            executor: Agent executor instance.
            max_workers: Maximum parallel workers.
            metrics: Optional metrics recorder.
        """
        self.executor = executor
        self.max_workers = max_workers
        self.metrics = metrics

    async def execute_parallel(
        self,
        tasks: list[tuple[str, str, dict[str, Any]]],
    ) -> list[AgentResult]:
        """Execute multiple agents in parallel with rate limiting.

        Args:
            tasks: List of (agent, action, params) tuples.

        Returns:
            List of AgentResult for each task.
        """
        if not tasks:
            return []

        start = time.time()
        semaphore = asyncio.Semaphore(self.max_workers)

        async def rate_limited_execute(
            agent: str, action: str, params: dict[str, Any]
        ) -> AgentResult:
            async with semaphore:
                return await self.executor.execute(agent, action, params)

        results = await asyncio.gather(
            *[
                rate_limited_execute(agent, action, params)
                for agent, action, params in tasks
            ]
        )

        duration = time.time() - start
        if self.metrics:
            self.metrics.record_parallel_execution(self.max_workers, duration)

        return list(results)

    async def execute_workflow(
        self,
        workflow: Workflow,
        strict: bool = False,
    ) -> WorkflowResult:
        """Execute workflow steps in order, respecting dependencies.

        Args:
            workflow: Workflow to execute.
            strict: If True, fail on first error regardless of on_error setting.

        Returns:
            WorkflowResult with execution results.

        Raises:
            WorkflowError: If a dependency is not satisfied.
        """
        start = time.time()
        completed_steps: dict[str, AgentResult] = {}
        results: list[AgentResult] = []

        if self.metrics:
            self.metrics.record_workflow_start(workflow.name, len(workflow.steps))

        for step in workflow.steps:
            # Check dependencies
            for dep in step.depends_on:
                if dep not in completed_steps:
                    raise WorkflowError(f"Dependency '{dep}' not completed")

                # Check if dependency succeeded
                dep_result = completed_steps[dep]
                if dep_result.status == "error":
                    raise WorkflowError(
                        f"Dependency '{dep}' failed: {dep_result.error}"
                    )

            # Execute step
            try:
                result = await self.executor.execute(
                    step.agent,
                    step.action,
                    step.params,
                    timeout=step.timeout,
                )
                results.append(result)
                completed_steps[step.name] = result

                # Handle errors
                if result.status == "error" and (strict or step.on_error == "fail"):
                    # Record metrics before raising
                    duration = time.time() - start
                    if self.metrics:  # pragma: no branch
                        self.metrics.record_workflow_complete(
                            workflow.name,
                            success=False,
                            duration=duration,
                            failed_steps=1,
                        )
                    raise WorkflowError(f"Step '{step.name}' failed: {result.error}")
                # Continue on error if configured

            except WorkflowError:
                raise
            except Exception as e:  # pragma: no cover
                error_result = AgentResult.failure(
                    agent=step.agent,
                    action=step.action,
                    error=str(e),
                    duration_seconds=0,
                )
                results.append(error_result)
                completed_steps[step.name] = error_result

                if strict or step.on_error == "fail":
                    duration = time.time() - start
                    if self.metrics:
                        self.metrics.record_workflow_complete(
                            workflow.name,
                            success=False,
                            duration=duration,
                            failed_steps=1,
                        )
                    raise WorkflowError(f"Step '{step.name}' failed: {e}") from e

        # Check quality gates
        quality_gates_passed = self._check_quality_gates(workflow, results)

        duration = time.time() - start
        failed_count = sum(1 for r in results if r.status == "error")

        if self.metrics:
            self.metrics.record_workflow_complete(
                workflow.name,
                success=failed_count == 0 and quality_gates_passed,
                duration=duration,
                failed_steps=failed_count,
            )

        return WorkflowResult.from_results(
            workflow_name=workflow.name,
            results=results,
            quality_gates_passed=quality_gates_passed,
        )

    def _check_quality_gates(
        self,
        workflow: Workflow,
        results: list[AgentResult],
    ) -> bool:
        """Check if quality gates pass.

        Args:
            workflow: Workflow with quality gates.
            results: Execution results.

        Returns:
            True if all quality gates pass.
        """
        gates = workflow.quality_gates

        # Check max_fixmes if specified
        if gates.max_fixmes is not None:
            for result in results:
                fixmes = result.data.get("fixme_count", 0)
                if isinstance(fixmes, int) and fixmes > gates.max_fixmes:
                    return False

        # Check min_documentation_score if specified
        if gates.min_documentation_score is not None:
            for result in results:
                score = result.data.get("documentation_score")
                if (
                    isinstance(score, (int, float))
                    and score < gates.min_documentation_score
                ):
                    return False

        # Check max_dead_code_percent if specified
        if gates.max_dead_code_percent is not None:  # pragma: no branch
            for result in results:  # pragma: no branch
                dead_code = result.data.get("dead_code_percent")
                if (  # pragma: no branch
                    isinstance(dead_code, (int, float))
                    and dead_code > gates.max_dead_code_percent
                ):
                    return False

        return True

    def execute_parallel_sync(
        self,
        tasks: list[tuple[str, str, dict[str, Any]]],
    ) -> list[AgentResult]:
        """Execute parallel tasks synchronously.

        Args:
            tasks: List of (agent, action, params) tuples.

        Returns:
            List of AgentResult for each task.
        """
        return asyncio.run(self.execute_parallel(tasks))

    def execute_workflow_sync(
        self,
        workflow: Workflow,
        strict: bool = False,
    ) -> WorkflowResult:
        """Execute workflow synchronously.

        Args:
            workflow: Workflow to execute.
            strict: If True, fail on first error.

        Returns:
            WorkflowResult with execution results.
        """
        return asyncio.run(self.execute_workflow(workflow, strict))
