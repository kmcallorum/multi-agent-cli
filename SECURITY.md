# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public issue
2. Email the maintainers directly with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Best Practices

### For Users

1. **Keep updated**: Always use the latest version
2. **Validate configs**: Use `multi-agent-cli config validate` before running
3. **Secure credentials**: Never commit API tokens or secrets in config files
4. **Use environment variables**: Store sensitive values in environment variables
5. **Review workflows**: Audit workflow files before execution

### For Developers

1. **Input validation**: All user inputs are validated
2. **No eval/exec**: Never use `eval()` or `exec()` on user input
3. **Path validation**: File paths are validated to prevent traversal attacks
4. **Safe YAML loading**: Uses `yaml.safe_load()` exclusively
5. **Dependency scanning**: Dependencies are regularly scanned with Dependabot

## Security Features

- CodeQL analysis on every push
- Dependency vulnerability scanning
- Input validation on all CLI commands
- Path containment checks
- No arbitrary code execution

## Acknowledgments

We appreciate security researchers who help improve the security of this project.
