"""Agent configuration models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for a single agent."""

    name: str = Field(..., description="Agent name (pm, research, index)")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    path: str = Field(..., description="Path to agent's index.js")
    timeout: int = Field(default=60, description="Execution timeout in seconds")
    env: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )


class OutputConfig(BaseModel):
    """Output configuration."""

    format: str = Field(default="rich", description="Output format: rich, json, table")
    verbose: bool = Field(default=False, description="Verbose output")
    save_results: bool = Field(default=True, description="Save results to file")
    results_dir: str = Field(default="./results", description="Results directory")


class SettingsConfig(BaseModel):
    """Global settings configuration."""

    max_parallel_workers: int = Field(default=3, description="Max parallel workers")
    default_timeout: int = Field(default=60, description="Default timeout in seconds")
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Prometheus metrics port")


class AgentsConfig(BaseModel):
    """Complete agents configuration."""

    agents: dict[str, AgentConfig] = Field(
        default_factory=dict, description="Agent configurations"
    )
    settings: SettingsConfig = Field(
        default_factory=SettingsConfig, description="Global settings"
    )
    output: OutputConfig = Field(
        default_factory=OutputConfig, description="Output configuration"
    )

    def get_enabled_agents(self) -> list[str]:
        """Get list of enabled agent names."""
        return [name for name, config in self.agents.items() if config.enabled]

    def get_agent(self, name: str) -> AgentConfig | None:
        """Get agent configuration by name."""
        return self.agents.get(name)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump()
