"""Tests for data models."""

from __future__ import annotations

import pytest

from multi_agent_cli.models.agent import (
    AgentConfig,
    AgentsConfig,
    OutputConfig,
    SettingsConfig,
)
from multi_agent_cli.models.results import (
    AgentResult,
    DryRunResult,
    DryRunStep,
    WorkflowResult,
)
from multi_agent_cli.models.workflow import QualityGates, Workflow, WorkflowStep


@pytest.mark.unit
class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_create_with_required_fields(self) -> None:
        """Test creating config with required fields."""
        config = AgentConfig(name="pm", path="./pm/dist/index.js")
        assert config.name == "pm"
        assert config.path == "./pm/dist/index.js"
        assert config.enabled is True
        assert config.timeout == 60
        assert config.env == {}

    def test_create_with_all_fields(self) -> None:
        """Test creating config with all fields."""
        config = AgentConfig(
            name="research",
            enabled=False,
            path="./research/dist/index.js",
            timeout=120,
            env={"KEY": "value"},
        )
        assert config.name == "research"
        assert config.enabled is False
        assert config.timeout == 120
        assert config.env == {"KEY": "value"}


@pytest.mark.unit
class TestAgentsConfig:
    """Tests for AgentsConfig model."""

    def test_create_empty(self) -> None:
        """Test creating empty config."""
        config = AgentsConfig()
        assert config.agents == {}
        assert isinstance(config.settings, SettingsConfig)
        assert isinstance(config.output, OutputConfig)

    def test_get_enabled_agents(self, sample_agents_config: AgentsConfig) -> None:
        """Test getting enabled agents."""
        enabled = sample_agents_config.get_enabled_agents()
        assert "pm" in enabled
        assert "research" in enabled
        assert "index" not in enabled

    def test_get_agent(self, sample_agents_config: AgentsConfig) -> None:
        """Test getting agent by name."""
        pm = sample_agents_config.get_agent("pm")
        assert pm is not None
        assert pm.name == "pm"

        unknown = sample_agents_config.get_agent("unknown")
        assert unknown is None

    def test_to_dict(self, sample_agents_config: AgentsConfig) -> None:
        """Test converting to dictionary."""
        data = sample_agents_config.to_dict()
        assert "agents" in data
        assert "settings" in data
        assert "output" in data


@pytest.mark.unit
class TestSettingsConfig:
    """Tests for SettingsConfig model."""

    def test_defaults(self) -> None:
        """Test default values."""
        settings = SettingsConfig()
        assert settings.max_parallel_workers == 3
        assert settings.default_timeout == 60
        assert settings.metrics_enabled is True
        assert settings.metrics_port == 9090


@pytest.mark.unit
class TestOutputConfig:
    """Tests for OutputConfig model."""

    def test_defaults(self) -> None:
        """Test default values."""
        output = OutputConfig()
        assert output.format == "rich"
        assert output.verbose is False
        assert output.save_results is True
        assert output.results_dir == "./results"


@pytest.mark.unit
class TestWorkflowStep:
    """Tests for WorkflowStep model."""

    def test_create_minimal(self) -> None:
        """Test creating step with minimal fields."""
        step = WorkflowStep(name="Test Step", agent="pm", action="track_tasks")
        assert step.name == "Test Step"
        assert step.agent == "pm"
        assert step.action == "track_tasks"
        assert step.params == {}
        assert step.on_error == "fail"
        assert step.depends_on == []
        assert step.timeout is None

    def test_create_full(self) -> None:
        """Test creating step with all fields."""
        step = WorkflowStep(
            name="Full Step",
            agent="research",
            action="analyze",
            params={"path": "./src"},
            on_error="continue",
            depends_on=["Previous Step"],
            timeout=120,
        )
        assert step.params == {"path": "./src"}
        assert step.on_error == "continue"
        assert step.depends_on == ["Previous Step"]
        assert step.timeout == 120


@pytest.mark.unit
class TestWorkflow:
    """Tests for Workflow model."""

    def test_create_workflow(self) -> None:
        """Test creating workflow."""
        workflow = Workflow(
            name="Test Workflow",
            description="Test description",
            steps=[
                WorkflowStep(name="Step 1", agent="pm", action="track"),
                WorkflowStep(name="Step 2", agent="research", action="analyze"),
            ],
        )
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 2

    def test_get_step(self) -> None:
        """Test getting step by name."""
        workflow = Workflow(
            name="Test",
            steps=[WorkflowStep(name="Step 1", agent="pm", action="track")],
        )
        step = workflow.get_step("Step 1")
        assert step is not None
        assert step.name == "Step 1"

        assert workflow.get_step("Unknown") is None

    def test_get_step_dependencies(self) -> None:
        """Test getting step dependencies."""
        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(name="Step 1", agent="pm", action="track"),
                WorkflowStep(
                    name="Step 2",
                    agent="research",
                    action="analyze",
                    depends_on=["Step 1"],
                ),
            ],
        )
        deps = workflow.get_step_dependencies("Step 2")
        assert deps == ["Step 1"]

        assert workflow.get_step_dependencies("Unknown") == []

    def test_validate_dependencies_valid(self) -> None:
        """Test validating valid dependencies."""
        workflow = Workflow(
            name="Test",
            steps=[
                WorkflowStep(name="Step 1", agent="pm", action="track"),
                WorkflowStep(
                    name="Step 2",
                    agent="research",
                    action="analyze",
                    depends_on=["Step 1"],
                ),
            ],
        )
        errors = workflow.validate_dependencies()
        assert errors == []

    def test_validate_dependencies_invalid(self) -> None:
        """Test validating invalid dependencies."""
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
        errors = workflow.validate_dependencies()
        assert len(errors) == 1
        assert "NonExistent" in errors[0]


@pytest.mark.unit
class TestQualityGates:
    """Tests for QualityGates model."""

    def test_defaults(self) -> None:
        """Test default values."""
        gates = QualityGates()
        assert gates.max_fixmes is None
        assert gates.min_documentation_score is None
        assert gates.max_dead_code_percent is None

    def test_with_values(self) -> None:
        """Test with specified values."""
        gates = QualityGates(
            max_fixmes=5,
            min_documentation_score=0.8,
            max_dead_code_percent=10.0,
        )
        assert gates.max_fixmes == 5
        assert gates.min_documentation_score == 0.8
        assert gates.max_dead_code_percent == 10.0


@pytest.mark.unit
class TestAgentResult:
    """Tests for AgentResult model."""

    def test_create_result(self) -> None:
        """Test creating result."""
        result = AgentResult(
            agent="pm",
            action="track_tasks",
            status="success",
            data={"count": 5},
            duration_seconds=1.5,
            timestamp="2024-01-01T00:00:00",
        )
        assert result.agent == "pm"
        assert result.status == "success"
        assert result.error is None

    def test_success_factory(self) -> None:
        """Test success factory method."""
        result = AgentResult.success(
            agent="pm",
            action="track",
            data={"count": 1},
            duration_seconds=0.5,
        )
        assert result.status == "success"
        assert result.error is None
        assert result.timestamp  # Has timestamp

    def test_failure_factory(self) -> None:
        """Test failure factory method."""
        result = AgentResult.failure(
            agent="pm",
            action="track",
            error="Something went wrong",
            duration_seconds=0.5,
        )
        assert result.status == "error"
        assert result.error == "Something went wrong"
        assert result.data == {}


@pytest.mark.unit
class TestWorkflowResult:
    """Tests for WorkflowResult model."""

    def test_create_result(self) -> None:
        """Test creating result."""
        result = WorkflowResult(
            workflow_name="Test",
            steps_completed=2,
            steps_failed=1,
            total_duration=3.0,
            results=[],
            quality_gates_passed=True,
        )
        assert result.workflow_name == "Test"
        assert result.steps_completed == 2
        assert result.steps_failed == 1

    def test_from_results(self) -> None:
        """Test creating from results."""
        agent_results = [
            AgentResult.success("pm", "track", {"count": 1}, 1.0),
            AgentResult.failure("research", "analyze", "Error", 0.5),
        ]
        result = WorkflowResult.from_results(
            workflow_name="Test",
            results=agent_results,
            quality_gates_passed=False,
        )
        assert result.steps_completed == 1
        assert result.steps_failed == 1
        assert result.total_duration == 1.5
        assert result.summary["success_rate"] == 0.5

    def test_from_results_empty(self) -> None:
        """Test creating from empty results."""
        result = WorkflowResult.from_results(
            workflow_name="Empty",
            results=[],
            quality_gates_passed=True,
        )
        assert result.steps_completed == 0
        assert result.summary["success_rate"] == 0.0


@pytest.mark.unit
class TestDryRunStep:
    """Tests for DryRunStep model."""

    def test_create_step(self) -> None:
        """Test creating dry-run step."""
        step = DryRunStep(
            order=1,
            name="Test Step",
            agent="pm",
            action="track_tasks",
            params={"path": "./src"},
            depends_on=["Previous"],
            timeout=60,
            on_error="continue",
        )
        assert step.order == 1
        assert step.name == "Test Step"
        assert step.agent == "pm"
        assert step.action == "track_tasks"
        assert step.params == {"path": "./src"}
        assert step.depends_on == ["Previous"]
        assert step.timeout == 60
        assert step.on_error == "continue"

    def test_create_step_minimal(self) -> None:
        """Test creating dry-run step with minimal fields."""
        step = DryRunStep(
            order=1,
            name="Minimal",
            agent="research",
            action="analyze",
        )
        assert step.params == {}
        assert step.depends_on == []
        assert step.timeout is None
        assert step.on_error == "fail"


@pytest.mark.unit
class TestDryRunResult:
    """Tests for DryRunResult model."""

    def test_create_valid_result(self) -> None:
        """Test creating valid dry-run result."""
        result = DryRunResult(
            workflow_name="Test Workflow",
            workflow_description="A test",
            total_steps=2,
            steps=[
                DryRunStep(order=1, name="Step 1", agent="pm", action="track"),
                DryRunStep(order=2, name="Step 2", agent="research", action="analyze"),
            ],
            validation_errors=[],
            quality_gates={"max_fixmes": 10},
            is_valid=True,
        )
        assert result.workflow_name == "Test Workflow"
        assert result.total_steps == 2
        assert len(result.steps) == 2
        assert result.is_valid is True
        assert result.validation_errors == []

    def test_create_invalid_result(self) -> None:
        """Test creating invalid dry-run result."""
        result = DryRunResult(
            workflow_name="Invalid Workflow",
            workflow_description="",
            total_steps=1,
            steps=[
                DryRunStep(
                    order=1,
                    name="Step 1",
                    agent="pm",
                    action="track",
                    depends_on=["Missing"],
                ),
            ],
            validation_errors=["Step 'Step 1' depends on non-existent step 'Missing'"],
            quality_gates={},
            is_valid=False,
        )
        assert result.is_valid is False
        assert len(result.validation_errors) == 1
        assert "Missing" in result.validation_errors[0]

    def test_default_values(self) -> None:
        """Test default values for dry-run result."""
        result = DryRunResult(
            workflow_name="Test",
            total_steps=0,
            is_valid=True,
        )
        assert result.workflow_description == ""
        assert result.steps == []
        assert result.validation_errors == []
        assert result.quality_gates == {}
