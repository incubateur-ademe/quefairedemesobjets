# API Guidelines

This project exposes HTTP APIs using `django-ninja` via a single `NinjaAPI`
instance defined in `webapp/core/api.py` and mounted in `webapp/core/urls.py`.

## Structure

- `webapp/core/api.py` creates two `NinjaAPI` instances and registers routers:
  - `api`, the historical one, mounted at `/api/` (docs at `/api/docs`):
    `qfdmo.api` at `/api/qfdmo/`, `stats.api` at `/api/stats`
  - `api_v1`, the public versioned one, mounted at `/api/v1/` (docs at
    `/api/v1/docs`): `assistant.api`, see [v1.md](v1.md)
- `webapp/core/urls.py` mounts both; `api/v1/` comes first, or Django would
  look for `v1/…` inside the historical API.

## How to add a new API

1. Create a router in your Django app:
   - Add a `api.py` with a `router = Router()` definition.
   - Define endpoints using `@router.get`, `@router.post`, etc.
2. Register the router in `webapp/core/api.py`:
   - Import it as `from <app>.api import router as <app>_router`.
   - Add it with `api.add_router("/<app>/", <app>_router, tags=[...])`.
3. The router will be automatically exposed under `/api/<app>/`.

## Conventions

- Keep the main API definition centralized in `webapp/core/api.py`.
- Use clear `tags` for each router to group endpoints in the OpenAPI docs.
- Prefer app-level routers to keep responsibilities isolated.
- Follow Django-Ninja schemas for input/output validation when relevant.

## Testing

- API endpoints must be covered by tests.
- Use integration tests for HTTP behavior; see
  `webapp/integration_tests/carte/test_qfdmo_api.py` as a reference.

## More details about API by router

```{toctree}
:maxdepth: 2

v1.md
qfdmo.md
stats.md
```
