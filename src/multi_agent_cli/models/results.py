"""Result models for agent and workflow execution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    """Result from single agent execution."""

    agent: str = Field(..., description="Agent name")
    action: str = Field(..., description="Action performed")
    status: Literal["success", "error"] = Field(..., description="Execution status")
    data: dict[str, Any] = Field(default_factory=dict, description="Result data")
    duration_seconds: float = Field(..., description="Execution duration in seconds")
    timestamp: str = Field(..., description="ISO timestamp of execution")
    error: str | None = Field(default=None, description="Error message if failed")

    @classmethod
    def success(
        cls,
        agent: str,
        action: str,
        data: dict[str, Any],
        duration_seconds: float,
    ) -> AgentResult:
        """Create a success result."""
        return cls(
            agent=agent,
            action=action,
            status="success",
            data=data,
            duration_seconds=duration_seconds,
            timestamp=datetime.now().isoformat(),
            error=None,
        )

    @classmethod
    def failure(
        cls,
        agent: str,
        action: str,
        error: str,
        duration_seconds: float,
    ) -> AgentResult:
        """Create a failure result."""
        return cls(
            agent=agent,
            action=action,
            status="error",
            data={},
            duration_seconds=duration_seconds,
            timestamp=datetime.now().isoformat(),
            error=error,
        )


class DryRunStep(BaseModel):
    """Represents a step in dry-run preview."""

    order: int = Field(..., description="Execution order (1-based)")
    name: str = Field(..., description="Step name")
    agent: str = Field(..., description="Agent to execute")
    action: str = Field(..., description="Action to perform")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Action parameters"
    )
    depends_on: list[str] = Field(default_factory=list, description="Step dependencies")
    timeout: int | None = Field(default=None, description="Step-specific timeout")
    on_error: str = Field(default="fail", description="Error handling behavior")


class DryRunResult(BaseModel):
    """Result from dry-run workflow validation."""

    workflow_name: str = Field(..., description="Workflow name")
    workflow_description: str = Field(default="", description="Workflow description")
    total_steps: int = Field(..., description="Total number of steps")
    steps: list[DryRunStep] = Field(
        default_factory=list, description="Steps to execute"
    )
    validation_errors: list[str] = Field(
        default_factory=list, description="Validation errors found"
    )
    quality_gates: dict[str, Any] = Field(
        default_factory=dict, description="Quality gate configuration"
    )
    is_valid: bool = Field(..., description="Whether workflow is valid")


class WorkflowResult(BaseModel):
    """Result from workflow execution."""

    workflow_name: str = Field(..., description="Workflow name")
    steps_completed: int = Field(..., description="Number of completed steps")
    steps_failed: int = Field(..., description="Number of failed steps")
    total_duration: float = Field(..., description="Total execution duration")
    results: list[AgentResult] = Field(
        default_factory=list, description="Individual step results"
    )
    quality_gates_passed: bool = Field(..., description="Whether quality gates passed")
    summary: dict[str, Any] = Field(
        default_factory=dict, description="Summary information"
    )

    @classmethod
    def from_results(
        cls,
        workflow_name: str,
        results: list[AgentResult],
        quality_gates_passed: bool,
    ) -> WorkflowResult:
        """Create workflow result from individual results."""
        completed = sum(1 for r in results if r.status == "success")
        failed = sum(1 for r in results if r.status == "error")
        total_duration = sum(r.duration_seconds for r in results)

        return cls(
            workflow_name=workflow_name,
            steps_completed=completed,
            steps_failed=failed,
            total_duration=total_duration,
            results=results,
            quality_gates_passed=quality_gates_passed,
            summary={
                "total_steps": len(results),
                "success_rate": completed / len(results) if results else 0.0,
            },
        )
