"""Configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from multi_agent_cli.exceptions import ConfigError, ValidationError
from multi_agent_cli.models.agent import AgentConfig, AgentsConfig
from multi_agent_cli.models.workflow import Workflow


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    """Load and parse a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML content as dictionary.

    Raises:
        ConfigError: If file cannot be read or parsed.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    if not file_path.is_file():
        raise ConfigError(f"Not a file: {path}")

    try:
        with file_path.open("r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if content is None:
                return {}
            if not isinstance(content, dict):
                raise ConfigError(f"Invalid YAML structure in {path}: expected mapping")
            return content
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML file {path}: {e}") from e


def load_config(path: str | Path) -> AgentsConfig:
    """Load agents configuration from YAML file.

    Args:
        path: Path to the configuration file.

    Returns:
        AgentsConfig instance.

    Raises:
        ConfigError: If configuration is invalid.
    """
    data = load_yaml_file(path)

    # Parse agents
    agents: dict[str, AgentConfig] = {}
    agents_data = data.get("agents", {})

    for name, agent_data in agents_data.items():
        if not isinstance(agent_data, dict):
            raise ConfigError(f"Invalid agent configuration for '{name}'")

        # Ensure name is set
        agent_data["name"] = name

        try:
            agents[name] = AgentConfig(**agent_data)
        except Exception as e:
            raise ConfigError(f"Invalid agent configuration for '{name}': {e}") from e

    # Build config
    try:
        return AgentsConfig(
            agents=agents,
            settings=data.get("settings", {}),
            output=data.get("output", {}),
        )
    except Exception as e:  # pragma: no cover
        raise ConfigError(f"Invalid configuration: {e}") from e


def load_workflow(path: str | Path) -> Workflow:
    """Load workflow definition from YAML file.

    Args:
        path: Path to the workflow file.

    Returns:
        Workflow instance.

    Raises:
        ConfigError: If workflow is invalid.
    """
    data = load_yaml_file(path)

    try:
        workflow = Workflow(**data)
    except Exception as e:
        raise ConfigError(f"Invalid workflow definition: {e}") from e

    # Validate dependencies
    errors = workflow.validate_dependencies()
    if errors:
        raise ConfigError(f"Invalid workflow dependencies: {'; '.join(errors)}")

    return workflow


def validate_agent_name(name: str, valid_agents: set[str] | None = None) -> str:
    """Validate agent name.

    Args:
        name: Agent name to validate.
        valid_agents: Optional set of valid agent names.

    Returns:
        Validated agent name.

    Raises:
        ValidationError: If agent name is invalid.
    """
    if not name:
        raise ValidationError("Agent name cannot be empty")

    if not name.replace("_", "").replace("-", "").isalnum():
        raise ValidationError(f"Invalid agent name: {name}")

    if valid_agents is not None and name not in valid_agents:
        raise ValidationError(f"Unknown agent: {name}")

    return name


def validate_path(path: str, project_root: str | None = None) -> Path:
    """Validate file path.

    Args:
        path: Path to validate.
        project_root: Optional project root for containment check.

    Returns:
        Resolved Path object.

    Raises:
        ValidationError: If path is invalid or outside project root.
    """
    if not path:
        raise ValidationError("Path cannot be empty")

    resolved = Path(path).resolve()

    if project_root is not None:
        root = Path(project_root).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as e:
            raise ValidationError(f"Path outside project root: {path}") from e

    return resolved


def create_default_config() -> AgentsConfig:
    """Create default configuration.

    Returns:
        AgentsConfig with default settings.
    """
    return AgentsConfig(
        agents={
            "pm": AgentConfig(
                name="pm",
                enabled=True,
                path="./pm/dist/index.js",
                timeout=60,
            ),
            "research": AgentConfig(
                name="research",
                enabled=True,
                path="./research/dist/index.js",
                timeout=90,
            ),
            "index": AgentConfig(
                name="index",
                enabled=True,
                path="./index/dist/index.js",
                timeout=120,
            ),
        },
    )


def save_config(config: AgentsConfig, path: str | Path) -> None:
    """Save configuration to YAML file.

    Args:
        config: Configuration to save.
        path: Path to save to.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "agents": {
            name: {
                "enabled": agent.enabled,
                "path": agent.path,
                "timeout": agent.timeout,
                "env": agent.env,
            }
            for name, agent in config.agents.items()
        },
        "settings": config.settings.model_dump(),
        "output": config.output.model_dump(),
    }

    with file_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
