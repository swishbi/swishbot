# Development

## Setup

1. Clone the repo:

    ```bash
    git clone https://github.com/swishbi/swishbot.git
    cd swishbot
    ```

2. Install in dev mode with test dependencies:

    ```bash
    uv sync --extra test
    ```

3. Set up pre-commit hooks:

    ```bash
    uv run pre-commit install
    uv run pre-commit install --hook-type pre-push
    ```

## Running checks

```bash
# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/

# Tests
uv run pytest -v
```

If you installed the pre-commit hooks, lint and format run automatically on every commit, and tests run before every push. CI also runs all three on every PR.

## CI

CI runs on every push to `main` and on all pull requests. It tests against Python 3.10, 3.11, 3.12, and 3.13:

1. `ruff check` — lint
2. `ruff format --check` — format verification
3. `pytest -v` — tests

## Commit checklist

- [ ] `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/` pass
- [ ] `uv run pytest -v` passes
- [ ] Version bumped in `pyproject.toml` if release-worthy
- [ ] Skill tables updated in `README.md` and `CLAUDE.md` if skills changed
- [ ] New skills have correct `name` and `description` in frontmatter
- [ ] Project structure in `README.md` updated if files/directories added
