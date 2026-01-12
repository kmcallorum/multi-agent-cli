"""Pytest configuration and fixtures."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from multi_agent_cli.factory import (
    MockAgentBridgeFactory,
    set_default_factory,
)
from multi_agent_cli.metrics import NullMetricsRecorder, set_metrics
from multi_agent_cli.models.agent import AgentConfig, AgentsConfig


@pytest.fixture
def mock_agent_responses() -> dict[str, dict[str, Any]]:
    """Standard mock responses for testing."""
    return {
        "pm.track_tasks": {
            "status": "success",
            "data": {
                "tasks": [{"id": "1", "type": "todo", "description": "Test task"}],
                "count": 1,
                "fixme_count": 2,
            },
        },
        "research.analyze_document": {
            "status": "success",
            "data": {
                "summary": "Test document",
                "completeness": 0.9,
                "documentation_score": 0.85,
            },
        },
        "index.index_repository": {
            "status": "success",
            "data": {
                "files_indexed": 100,
                "symbols": 500,
                "dead_code_percent": 3.5,
            },
        },
    }


@pytest.fixture
def mock_factory(
    mock_agent_responses: dict[str, dict[str, Any]],
) -> Generator[MockAgentBridgeFactory, None, None]:
    """Mock factory for testing."""
    factory = MockAgentBridgeFactory(mock_agent_responses)
    set_default_factory(factory)
    yield factory
    set_default_factory(None)


@pytest.fixture
def mock_metrics() -> Generator[NullMetricsRecorder, None, None]:
    """Mock metrics recorder for testing."""
    metrics = NullMetricsRecorder()
    set_metrics(metrics)
    yield metrics
    set_metrics(None)


@pytest.fixture
def sample_agents_config() -> AgentsConfig:
    """Sample agents configuration."""
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
                enabled=False,
                path="./index/dist/index.js",
                timeout=120,
            ),
        }
    )


@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create temporary config file."""
    config_content = """
agents:
  pm:
    enabled: true
    path: "./pm/dist/index.js"
    timeout: 60
  research:
    enabled: true
    path: "./research/dist/index.js"
    timeout: 90

settings:
  max_parallel_workers: 3
  default_timeout: 60
  metrics_enabled: true
  metrics_port: 9090

output:
  format: rich
  verbose: false
"""
    config_file = tmp_path / "agents.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def temp_workflow_file(tmp_path: Path) -> Path:
    """Create temporary workflow file."""
    workflow_content = """
name: Test Workflow
description: Test workflow description

steps:
  - name: Step 1
    agent: pm
    action: track_tasks
    params:
      path: "./src"
    on_error: continue

  - name: Step 2
    agent: research
    action: analyze_document
    params:
      path: "./README.md"
    on_error: fail
    depends_on:
      - Step 1

quality_gates:
  max_fixmes: 10
  min_documentation_score: 0.7
"""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text(workflow_content)
    return workflow_file


@pytest.fixture
def temp_invalid_yaml_file(tmp_path: Path) -> Path:
    """Create temporary invalid YAML file."""
    invalid_file = tmp_path / "invalid.yaml"
    invalid_file.write_text("invalid: yaml: content: [")
    return invalid_file


@pytest.fixture
def temp_empty_yaml_file(tmp_path: Path) -> Path:
    """Create temporary empty YAML file."""
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("")
    return empty_file
