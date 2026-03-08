# Contributing to Convoy

Thank you for your interest in contributing to Convoy! This document provides guidelines and instructions for contributing.

## Ways to Contribute

- **Report bugs** - Open an issue describing the bug and how to reproduce it
- **Suggest features** - Open an issue describing the feature and its use case
- **Submit pull requests** - Fix bugs or implement new features
- **Improve documentation** - Fix typos, clarify explanations, add examples

## Development Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)
- [Python](https://www.python.org/) (3.11+)
- [uv](https://github.com/astral-sh/uv) (for Python dependency management)
- [Node.js](https://nodejs.org/) (for commit hooks)

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/cnvy-ai/convoy.git
cd convoy
```

2. Install Node.js dependencies (for commit hooks):
```bash
npm install
```

3. Start the development environment:
```bash
docker compose up -d
```

4. Verify services are running:
```bash
curl http://localhost:8000/health
```

### Running Tests

Run the full test suite:
```bash
docker compose --profile tests run --rm convoy-tests
```

Run a specific test file:
```bash
docker compose --profile tests run --rm convoy-tests uv run pytest test_batch_flow.py -v -s
```

### Service Access

| Service | URL |
|---------|-----|
| Convoy API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Temporal UI | http://localhost:8080 |

## Code Style

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use type hints for function signatures
- Write docstrings for public functions and classes

### Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/). Commit messages are validated automatically.

Format:
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

Examples:
```
feat(api): add batch status endpoint
fix(worker): handle timeout in callback delivery
docs: update README with new examples
```

## Pull Request Process

1. **Fork the repository** and create a branch from `main`
2. **Make your changes** following the code style guidelines
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Ensure all tests pass** locally
6. **Submit a pull request** with a clear description

### PR Guidelines

- Keep PRs focused on a single change
- Reference related issues in the PR description
- Respond to review feedback promptly
- Squash commits before merging if requested

## Reporting Issues

When reporting bugs, please include:

- Convoy version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Relevant logs or error messages
- Environment details (OS, Docker version, etc.)

## Questions?

- Check the [documentation](https://docs.cnvy.ai)
- Open a [discussion](https://github.com/cnvy-ai/convoy/discussions)

## License

By contributing to Convoy, you agree that your contributions will be licensed under the [MIT License](LICENSE).
