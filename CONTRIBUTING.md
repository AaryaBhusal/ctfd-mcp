# Contributing

## Setup

This repo uses `uv` and Python 3.13.

```bash
uv sync --group dev
```

## Lint / format

```bash
uv run ruff check .
uv run ruff format .
```

To auto-fix what Ruff can:

```bash
uv run ruff check --fix .
```

## Tests

```bash
uv run python -m unittest discover -s tests
```

`tests/test_ctfd_client.py` includes live tests that only run when `CTFD_URL` and credentials are set; otherwise they are skipped.

## Pre-commit

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```
