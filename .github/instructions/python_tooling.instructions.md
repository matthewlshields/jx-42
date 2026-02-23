---
applyTo: "**"
description: Python Package Management with uv
---

# Python Package Management

This project uses **`uv`** as the Python package manager. Do NOT use `pip`.

## Package Manager: uv

- **Always use `uv`** for dependency management
- **Never use `pip`** directly
- The project has a `uv.lock` file that must be kept in sync

## Common Commands

### Install dependencies
```bash
uv sync
```

### Install with dev dependencies
```bash
uv sync --extra dev
```

### Add a new dependency
```bash
uv add <package-name>
```

### Add a dev dependency
```bash
uv add --dev <package-name>
```

### Run Python scripts
```bash
uv run python <script.py>
```

### Run pytest
```bash
uv run pytest
```

### Run the CLI
```bash
uv run jx-42 run "your request"
```

## CI/CD Workflows

In GitHub Actions, use the official `astral-sh/setup-uv` action:

```yaml
- name: Set up uv
  uses: astral-sh/setup-uv@v5
  
- name: Install dependencies
  run: uv sync --extra dev
  
- name: Run tests
  run: uv run pytest
```

## Why uv?

- **Fast**: 10-100x faster than pip
- **Deterministic**: Lock file ensures reproducible builds
- **Simple**: Single tool for package management and virtual environments
- **Compatible**: Works with existing `pyproject.toml` and standard Python packaging

## Migration Notes

If you see `pip install` in any documentation, CI workflows, or scripts, replace it with the appropriate `uv` command above.
