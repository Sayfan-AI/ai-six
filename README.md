# AI-6
Agentic AI focused on ubiquitous tool using.

![](ai-6.png)

The current implementation is in Python. check out the [py](py/README.MD) directory.

There may be implementations in other languages too, in the near future.

See this [link](https://deepwiki.com/Sayfan-AI/ai-six) for a super-deep dive into the project.

# LLM Access

Obviously, it delegates all the heavy lifting to an LLM provider. At the moment it is OpenAI-compatible or Ollama local models.

For OpenAI-compatible LLM providers the environment variable `OPENAI_API_KEY` must be set.

# Installation & Usage

## Option 1: Install from PyPI (Easiest)

```bash
pip install ai-six

# Use in Python code
from ai_six.agent import Agent
```

## Option 2: Development Setup

Using uv (recommended for development):

```bash
cd py/
uv sync --dev
# Run CLI frontend
uv run python -m frontend.cli.ai6 --help
```

**Note**: Run `uv lock` after dependency changes to maintain reproducible builds.

## Option 3: Traditional Development Setup

After you activate the virtualenv and install the dependencies, you can run an AI-6 frontend using the startup script (`ai6.sh`).

**Example — Run the CLI frontend:**

```
./ai6.sh cli
```

## Building and Publishing the Package

To build the Python package for distribution:

```bash
cd py/
uv build
```

This creates distribution files in `py/dist/`:
- `ai_six-*.whl` (wheel distribution)
- `ai_six-*.tar.gz` (source distribution)

## Publishing to PyPI

Publishing is handled automatically by GitHub Actions when you push a version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This triggers the workflow that builds and publishes the package to PyPI.

**One-time setup**: Add `PYPI_API_TOKEN` to repository secrets in GitHub.
