# Identity Platform API

FastAPI authorization server for the Identity Platform monorepo.

## Setup

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
# from repo root
docker compose up -d
cd apps/api
uvicorn identity_api.main:app --reload --port 8000
```

## Lint / format / test

```bash
ruff check .
ruff format .
pytest
```
