# LineupIQ ML Backend

Python ML backend for fantasy football stat prediction.

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for package management.

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --dev

# Run the package
uv run python -c "import lineupiq; print(lineupiq.__version__)"
```

## Development

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

## Structure

```
packages/backend/
├── pyproject.toml      # Package configuration
├── src/
│   └── lineupiq/       # Main package
│       └── __init__.py
└── tests/              # Test suite
    └── __init__.py
```
