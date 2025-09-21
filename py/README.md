# AI-6 - Python

This is the root directory of the Python implementation of AI-6.

The package contains:
- **backend/**: AI-6 engine, agents, tools, and core functionality (packaged)
- **frontend/**: CLI and Slack frontend interfaces (development only)

# Installation

## Option 1: Install from PyPI (Recommended)

```bash
# Install the published package
pip install ai-six

# Use in Python code
from ai_six.agent import Agent
```

## Option 2: Development Setup with uv

For development or running from source:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and sync development environment
uv sync --dev

# Run the CLI frontend
uv run python -m frontend.cli.ai6 --help
```

**Important**: After making dependency changes, run `uv lock` to update the lock file for reproducible builds.

## Option 3: Traditional pip setup

```bash
# Create virtual environment
python -m venv venv --prompt ai6
source venv/bin/activate

# Install in development mode
pip install -e .
```

# Building the Package

To build distribution packages:

```bash
uv build
```

This creates both wheel (`.whl`) and source (`.tar.gz`) distributions in the `dist/` directory.

## Publishing to PyPI

1. Create account at [PyPI.org](https://pypi.org)
2. Generate API token in PyPI account settings
3. Publish the package:
   ```bash
   uv publish --token <your-api-token>
   ```
   Or set environment variable: `export UV_PUBLISH_TOKEN=<your-token>`

**Recommended**: Test on [TestPyPI](https://test.pypi.org) first:
```bash
uv publish --index-url https://test.pypi.org/legacy/ --token <test-token>
```

For complete publishing guide: [uv Publishing Documentation](https://docs.astral.sh/uv/guides/publish/)

# Reference
