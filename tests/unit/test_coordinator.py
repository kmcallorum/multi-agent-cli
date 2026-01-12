"""Tests for coordinator module."""

from __future__ import annotations

from typing import Any

import pytest

from multi_agent_cli.coordinator import AgentCoordinator
from multi_agent_cli.exceptions import WorkflowError
from multi_agent_cli.executor import AgentExecutor
from multi_agent_cli.factory import MockAgentBridge, MockAgentBridgeFactory
from multi_agent_cli.metrics import MetricsRecorder
from multi_agent_cli.models.agent import AgentsConfig
from multi_agent_cli.models.workflow import QualityGates, Workflow, WorkflowStep


@pytest.mark.unit
class TestAgentCoordinator:
    """Tests for AgentCoordinator."""

    @pytest.mark.asyncio
    async def test_execute_parallel_empty(
        self,
        mock_factory: MockAgentBridgeFactory,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test parallel execution with empty task list."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, max_workers=3, metrics=mock_metrics)

        results = await coordinator.execute_parallel([])

        assert results == []

    @pytest.mark.asyncio
    async def test_execute_parallel_success(
        self,
        mock_factory: MockAgentBridgeFactory,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test successful parallel execution."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, max_workers=3, metrics=mock_metrics)

        tasks = [
            ("pm", "track_tasks", {"path": "./src"}),
            ("research", "analyze_document", {"path": "./README.md"}),
        ]

        results = await coordinator.execute_parallel(tasks)

        assert len(results) == 2
        assert all(r.status == "success" for r in results)

    @pytest.mark.asyncio
    async def test_execute_parallel_rate_limited(
        self,
        mock_factory: MockAgentBridgeFactory,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test parallel execution respects rate limiting."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, max_workers=2, metrics=mock_metrics)

        # More tasks than workers
        tasks = [
            ("pm", "track_tasks", {}),
            ("research", "analyze_document", {}),
            ("index", "index_repository", {}),
        ]

        results = await coordinator.execute_parallel(tasks)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_execute_workflow_success(
        self,
        mock_factory: MockAgentBridgeFactory,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test successful workflow execution."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test Workflow",
            steps=[
                WorkflowStep(name="Step 1", agent="pm", action="track_tasks"),
                WorkflowStep(
                    name="Step 2",
                    agent="research",
                    action="analyze_document",
                    depends_on=["Step 1"],
                ),
            ],
        )

        result = await coordinator.execute_workflow(workflow)

        assert result.workflow_name == "Test Workflow"
        assert result.steps_completed == 2
        assert result.steps_failed == 0
        assert result.quality_gates_passed is True

    @pytest.mark.asyncio
    async def test_execute_workflow_with_missing_dependency(
        self,
        mock_factory: MockAgentBridgeFactory,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test workflow fails with missing dependency."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(
                    name="Step 1",
                    agent="pm",
                    action="track",
                    depends_on=["NonExistent"],
                ),
            ],
        )

        with pytest.raises(WorkflowError, match="not completed"):
            await coordinator.execute_workflow(workflow)

    @pytest.mark.asyncio
    async def test_execute_workflow_with_failed_dependency(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test workflow fails when dependency failed."""
        invocations: list[tuple[str, str, dict[str, Any]]] = []
        mock_responses = {
            "pm.track_tasks": {"status": "error", "data": {"error": "Failed"}},
        }
        bridge = MockAgentBridge(mock_responses, invocations)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(
                    name="Step 1",
                    agent="pm",
                    action="track_tasks",
                    on_error="continue",
                ),
                WorkflowStep(
                    name="Step 2",
                    agent="research",
                    action="analyze",
                    depends_on=["Step 1"],
                ),
            ],
        )

        with pytest.raises(WorkflowError, match="failed"):
            await coordinator.execute_workflow(workflow)

    @pytest.mark.asyncio
    async def test_execute_workflow_strict_mode(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test workflow strict mode stops on first error."""
        invocations: list[tuple[str, str, dict[str, Any]]] = []
        mock_responses = {
            "pm.track_tasks": {"status": "error", "data": {"error": "Failed"}},
        }
        bridge = MockAgentBridge(mock_responses, invocations)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(
                    name="Step 1",
                    agent="pm",
                    action="track_tasks",
                    on_error="continue",  # Would normally continue
                ),
            ],
        )

        with pytest.raises(WorkflowError):
            await coordinator.execute_workflow(workflow, strict=True)

    @pytest.mark.asyncio
    async def test_execute_workflow_continue_on_error(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test workflow continues on error when configured."""
        invocations: list[tuple[str, str, dict[str, Any]]] = []
        mock_responses = {
            "pm.track_tasks": {"status": "error", "data": {"error": "Failed"}},
            "research.analyze_document": {"status": "success", "data": {}},
        }
        bridge = MockAgentBridge(mock_responses, invocations)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(
                    name="Step 1",
                    agent="pm",
                    action="track_tasks",
                    on_error="continue",
                ),
                WorkflowStep(
                    name="Step 2",
                    agent="research",
                    action="analyze_document",
                    # No dependency on Step 1
                ),
            ],
        )

        result = await coordinator.execute_workflow(workflow)

        assert result.steps_failed == 1
        assert result.steps_completed == 1

    @pytest.mark.asyncio
    async def test_execute_workflow_quality_gates_fail(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test workflow quality gates failure."""
        invocations: list[tuple[str, str, dict[str, Any]]] = []
        mock_responses = {
            "pm.track_tasks": {
                "status": "success",
                "data": {"fixme_count": 20},  # Exceeds gate
            },
        }
        bridge = MockAgentBridge(mock_responses, invocations)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(name="Step 1", agent="pm", action="track_tasks"),
            ],
            quality_gates=QualityGates(max_fixmes=5),
        )

        result = await coordinator.execute_workflow(workflow)

        assert result.quality_gates_passed is False

    @pytest.mark.asyncio
    async def test_execute_workflow_quality_gates_documentation(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test documentation score quality gate."""
        invocations: list[tuple[str, str, dict[str, Any]]] = []
        mock_responses = {
            "research.analyze": {
                "status": "success",
                "data": {"documentation_score": 0.5},  # Below gate
            },
        }
        bridge = MockAgentBridge(mock_responses, invocations)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(name="Step 1", agent="research", action="analyze"),
            ],
            quality_gates=QualityGates(min_documentation_score=0.8),
        )

        result = await coordinator.execute_workflow(workflow)

        assert result.quality_gates_passed is False

    @pytest.mark.asyncio
    async def test_execute_workflow_quality_gates_dead_code(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test dead code quality gate."""
        invocations: list[tuple[str, str, dict[str, Any]]] = []
        mock_responses = {
            "index.scan": {
                "status": "success",
                "data": {"dead_code_percent": 15.0},  # Exceeds gate
            },
        }
        bridge = MockAgentBridge(mock_responses, invocations)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(name="Step 1", agent="index", action="scan"),
            ],
            quality_gates=QualityGates(max_dead_code_percent=10.0),
        )

        result = await coordinator.execute_workflow(workflow)

        assert result.quality_gates_passed is False

    @pytest.mark.asyncio
    async def test_execute_workflow_exception_in_step(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test workflow handles exception in step."""

        class FailingBridge:
            def invoke_agent(
                self, agent: str, action: str, params: dict[str, Any]
            ) -> dict[str, Any]:
                raise RuntimeError("Bridge crashed")

        bridge = FailingBridge()
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(
                    name="Step 1",
                    agent="pm",
                    action="track",
                    on_error="fail",
                ),
            ],
        )

        with pytest.raises(WorkflowError, match="failed"):
            await coordinator.execute_workflow(workflow)

    @pytest.mark.asyncio
    async def test_execute_workflow_exception_continue(
        self,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test workflow continues after exception with on_error=continue."""

        class FailingBridge:
            def invoke_agent(
                self, agent: str, action: str, params: dict[str, Any]
            ) -> dict[str, Any]:
                if agent == "pm":
                    raise RuntimeError("Bridge crashed")
                return {"status": "success", "data": {}}

        bridge = FailingBridge()
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(
                    name="Step 1",
                    agent="pm",
                    action="track",
                    on_error="continue",
                ),
                WorkflowStep(
                    name="Step 2",
                    agent="research",
                    action="analyze",
                ),
            ],
        )

        result = await coordinator.execute_workflow(workflow)
        assert result.steps_failed == 1
        assert result.steps_completed == 1

    def test_execute_parallel_sync(
        self,
        mock_factory: MockAgentBridgeFactory,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test synchronous parallel execution."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        tasks = [("pm", "track_tasks", {})]
        results = coordinator.execute_parallel_sync(tasks)

        assert len(results) == 1

    def test_execute_workflow_sync(
        self,
        mock_factory: MockAgentBridgeFactory,
        mock_metrics: MetricsRecorder,
    ) -> None:
        """Test synchronous workflow execution."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge, mock_metrics)
        coordinator = AgentCoordinator(executor, metrics=mock_metrics)

        workflow = Workflow(
            name="Test",
            steps=[WorkflowStep(name="Step 1", agent="pm", action="track_tasks")],
        )

        result = coordinator.execute_workflow_sync(workflow)

        assert result.workflow_name == "Test"

    @pytest.mark.asyncio
    async def test_execute_parallel_without_metrics(
        self,
        mock_factory: MockAgentBridgeFactory,
    ) -> None:
        """Test parallel execution without metrics."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge)
        coordinator = AgentCoordinator(executor)  # No metrics

        tasks = [("pm", "track_tasks", {})]
        results = await coordinator.execute_parallel(tasks)

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_execute_workflow_without_metrics(
        self,
        mock_factory: MockAgentBridgeFactory,
    ) -> None:
        """Test workflow execution without metrics."""
        config = AgentsConfig()
        bridge = mock_factory.create(config)
        executor = AgentExecutor(bridge)
        coordinator = AgentCoordinator(executor)  # No metrics

        workflow = Workflow(
            name="Test",
            steps=[WorkflowStep(name="Step 1", agent="pm", action="track_tasks")],
        )

        result = await coordinator.execute_workflow(workflow)
        assert result.workflow_name == "Test"
