# Contributing to multi-agent-cli

Thank you for your interest in contributing to multi-agent-cli!

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/multi-agent-cli.git
   cd multi-agent-cli
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Code Quality Standards

### Testing

- **100% test coverage is required** - No exceptions
- Run tests with: `pytest`
- Check coverage with: `pytest --cov=src/multi_agent_cli --cov-report=term-missing`
- All new code must have corresponding tests

### Linting

```bash
# Check code style
ruff check src tests

# Format code
ruff format src tests
```

### Type Checking

```bash
# Run mypy in strict mode
mypy src
```

All functions must have type hints. Avoid `Any` types unless absolutely necessary.

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, ensuring:
   - All tests pass
   - 100% coverage is maintained
   - Code passes linting and type checking
   - Documentation is updated if needed

3. Commit with conventional commit messages:
   ```
   feat: add new feature
   fix: fix bug in executor
   docs: update README
   test: add tests for coordinator
   refactor: improve factory pattern
   ```

4. Push and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Fill out the PR template with:
   - Description of changes
   - Related issues
   - Testing performed

## Coding Guidelines

### Style

- Follow PEP 8 (enforced by ruff)
- Maximum line length: 88 characters
- Use double quotes for strings
- Use type hints on all functions

### Documentation

- All public APIs must have docstrings
- Use Google-style docstrings
- Keep docstrings concise but complete

Example:
```python
def execute(self, agent: str, action: str, params: dict[str, Any]) -> AgentResult:
    """Execute single agent action.

    Args:
        agent: Agent name.
        action: Action to perform.
        params: Action parameters.

    Returns:
        AgentResult with execution results.

    Raises:
        AgentError: If execution fails.
    """
```

### Testing

- Use pytest fixtures for shared test setup
- Mark tests appropriately (`@pytest.mark.unit`, `@pytest.mark.integration`)
- Test both success and error cases
- Test edge cases

### Architecture

- Prefer composition over inheritance
- Use dependency injection for testability
- Keep functions small and focused
- Avoid over-engineering

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v1.0.0`
4. Push the tag: `git push origin v1.0.0`
5. GitHub Actions will automatically publish to PyPI

## Questions?

Open an issue for questions or discussions about contributions.
