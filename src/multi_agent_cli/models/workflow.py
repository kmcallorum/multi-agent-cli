"""Workflow definition models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """Single workflow step definition."""

    name: str = Field(..., description="Step name")
    agent: str = Field(..., description="Agent to execute")
    action: str = Field(..., description="Action to perform")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Action parameters"
    )
    on_error: Literal["fail", "continue"] = Field(
        default="fail", description="Error handling behavior"
    )
    depends_on: list[str] = Field(default_factory=list, description="Step dependencies")
    timeout: int | None = Field(default=None, description="Step-specific timeout")


class QualityGates(BaseModel):
    """Quality gate configuration."""

    max_fixmes: int | None = Field(default=None, description="Maximum FIXME count")
    min_documentation_score: float | None = Field(
        default=None, description="Minimum documentation score"
    )
    max_dead_code_percent: float | None = Field(
        default=None, description="Maximum dead code percentage"
    )


class Workflow(BaseModel):
    """Complete workflow definition."""

    name: str = Field(..., description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    steps: list[WorkflowStep] = Field(..., description="Workflow steps")
    quality_gates: QualityGates = Field(
        default_factory=QualityGates, description="Quality gate configuration"
    )

    def get_step(self, name: str) -> WorkflowStep | None:
        """Get step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def get_step_dependencies(self, step_name: str) -> list[str]:
        """Get dependencies for a step."""
        step = self.get_step(step_name)
        if step is None:
            return []
        return step.depends_on

    def validate_dependencies(self) -> list[str]:
        """Validate that all dependencies exist. Returns list of errors."""
        errors: list[str] = []
        step_names = {step.name for step in self.steps}

        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_names:
                    errors.append(
                        f"Step '{step.name}' depends on non-existent step '{dep}'"
                    )

        return errors
