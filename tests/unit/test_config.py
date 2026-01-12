"""Tests for configuration module."""

from __future__ import annotations

from pathlib import Path

import pytest

from multi_agent_cli.config import (
    create_default_config,
    load_config,
    load_workflow,
    load_yaml_file,
    save_config,
    validate_agent_name,
    validate_path,
)
from multi_agent_cli.exceptions import ConfigError, ValidationError


@pytest.mark.unit
class TestLoadYamlFile:
    """Tests for load_yaml_file function."""

    def test_load_valid_file(self, temp_config_file: Path) -> None:
        """Test loading valid YAML file."""
        data = load_yaml_file(temp_config_file)
        assert "agents" in data
        assert "pm" in data["agents"]

    def test_load_empty_file(self, temp_empty_yaml_file: Path) -> None:
        """Test loading empty YAML file."""
        data = load_yaml_file(temp_empty_yaml_file)
        assert data == {}

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading non-existent file."""
        with pytest.raises(ConfigError, match="not found"):
            load_yaml_file(tmp_path / "nonexistent.yaml")

    def test_load_directory(self, tmp_path: Path) -> None:
        """Test loading directory raises error."""
        with pytest.raises(ConfigError, match="Not a file"):
            load_yaml_file(tmp_path)

    def test_load_invalid_yaml(self, temp_invalid_yaml_file: Path) -> None:
        """Test loading invalid YAML raises error."""
        with pytest.raises(ConfigError, match="Failed to parse"):
            load_yaml_file(temp_invalid_yaml_file)

    def test_load_non_mapping_yaml(self, tmp_path: Path) -> None:
        """Test loading non-mapping YAML raises error."""
        list_file = tmp_path / "list.yaml"
        list_file.write_text("- item1\n- item2")
        with pytest.raises(ConfigError, match="expected mapping"):
            load_yaml_file(list_file)


@pytest.mark.unit
class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, temp_config_file: Path) -> None:
        """Test loading valid configuration."""
        config = load_config(temp_config_file)
        assert "pm" in config.agents
        assert config.agents["pm"].enabled is True

    def test_load_config_with_invalid_agent(self, tmp_path: Path) -> None:
        """Test loading config with invalid agent data."""
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("agents:\n  pm: not_a_dict")
        with pytest.raises(ConfigError, match="Invalid agent configuration"):
            load_config(config_file)

    def test_load_config_with_missing_path(self, tmp_path: Path) -> None:
        """Test loading config with missing required field."""
        config_file = tmp_path / "missing.yaml"
        config_file.write_text("agents:\n  pm:\n    enabled: true")
        with pytest.raises(ConfigError, match="Invalid agent configuration"):
            load_config(config_file)


@pytest.mark.unit
class TestLoadWorkflow:
    """Tests for load_workflow function."""

    def test_load_valid_workflow(self, temp_workflow_file: Path) -> None:
        """Test loading valid workflow."""
        workflow = load_workflow(temp_workflow_file)
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 2

    def test_load_invalid_workflow(self, tmp_path: Path) -> None:
        """Test loading invalid workflow."""
        workflow_file = tmp_path / "bad.yaml"
        workflow_file.write_text("name: Test\nsteps: not_a_list")
        with pytest.raises(ConfigError, match="Invalid workflow definition"):
            load_workflow(workflow_file)

    def test_load_workflow_with_invalid_dependencies(self, tmp_path: Path) -> None:
        """Test loading workflow with invalid dependencies."""
        workflow_file = tmp_path / "bad_deps.yaml"
        workflow_file.write_text("""
name: Test
steps:
  - name: Step 1
    agent: pm
    action: track
    depends_on:
      - NonExistent
""")
        with pytest.raises(ConfigError, match="Invalid workflow dependencies"):
            load_workflow(workflow_file)


@pytest.mark.unit
class TestValidateAgentName:
    """Tests for validate_agent_name function."""

    def test_valid_name(self) -> None:
        """Test validating valid agent name."""
        result = validate_agent_name("pm")
        assert result == "pm"

    def test_valid_name_with_underscore(self) -> None:
        """Test validating name with underscore."""
        result = validate_agent_name("my_agent")
        assert result == "my_agent"

    def test_valid_name_with_dash(self) -> None:
        """Test validating name with dash."""
        result = validate_agent_name("my-agent")
        assert result == "my-agent"

    def test_empty_name(self) -> None:
        """Test validating empty name."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_agent_name("")

    def test_invalid_characters(self) -> None:
        """Test validating name with invalid characters."""
        with pytest.raises(ValidationError, match="Invalid agent name"):
            validate_agent_name("agent!")

    def test_unknown_agent(self) -> None:
        """Test validating unknown agent."""
        with pytest.raises(ValidationError, match="Unknown agent"):
            validate_agent_name("unknown", {"pm", "research"})

    def test_known_agent(self) -> None:
        """Test validating known agent."""
        result = validate_agent_name("pm", {"pm", "research"})
        assert result == "pm"


@pytest.mark.unit
class TestValidatePath:
    """Tests for validate_path function."""

    def test_valid_path(self, tmp_path: Path) -> None:
        """Test validating valid path."""
        result = validate_path(str(tmp_path))
        assert result == tmp_path.resolve()

    def test_empty_path(self) -> None:
        """Test validating empty path."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_path("")

    def test_path_within_root(self, tmp_path: Path) -> None:
        """Test validating path within project root."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        result = validate_path(str(subdir), str(tmp_path))
        assert result == subdir.resolve()

    def test_path_outside_root(self, tmp_path: Path) -> None:
        """Test validating path outside project root."""
        with pytest.raises(ValidationError, match="outside project root"):
            validate_path("/tmp", str(tmp_path))


@pytest.mark.unit
class TestCreateDefaultConfig:
    """Tests for create_default_config function."""

    def test_creates_config(self) -> None:
        """Test creating default config."""
        config = create_default_config()
        assert "pm" in config.agents
        assert "research" in config.agents
        assert "index" in config.agents


@pytest.mark.unit
class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_config(self, tmp_path: Path) -> None:
        """Test saving configuration."""
        config = create_default_config()
        output_path = tmp_path / "output.yaml"
        save_config(config, output_path)

        assert output_path.exists()
        loaded = load_config(output_path)
        assert "pm" in loaded.agents

    def test_save_config_creates_directories(self, tmp_path: Path) -> None:
        """Test saving config creates parent directories."""
        config = create_default_config()
        output_path = tmp_path / "nested" / "dir" / "config.yaml"
        save_config(config, output_path)

        assert output_path.exists()
