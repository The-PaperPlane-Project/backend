# Paper Plane Backend

Backend API for the Paper Plane airport application.

## Start

```bash
$env:Path += ";$env:APPDATA\Python\Scripts"
poetry install
poetry run uvicorn src.main:app --reload
```

## Configuration

Runtime settings are loaded from environment variables. Use `.env.example` as the local template and keep real credentials outside markdown files.

## Endpoints

- `GET /docs` opens the interactive API documentation.
- `GET /api/database` returns the airport snapshot used by the frontend.
- `PUT /api/database` replaces airport data from the admin panel.

## Data

The backend seeds SQLite from `data/airport_data.json` on first launch and keeps SQL as the runtime source of truth.
