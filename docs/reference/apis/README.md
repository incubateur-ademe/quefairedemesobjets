# API Guidelines

This project exposes HTTP APIs using `django-ninja` via a single `NinjaAPI`
instance defined in `webapp/core/api.py` and mounted in `webapp/core/urls.py`.

## Structure

- `webapp/core/api.py` creates the `NinjaAPI` instance and registers routers.
- Each domain app exposes a `router` that is attached to the main API.
  Current routers are:
  - `qfdmo.api` at `/api/qfdmo/`
  - `stats.api` at `/api/stats`
- `webapp/core/urls.py` mounts the API under the `/api/` path.

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

qfdmo.md
stats.md
```
