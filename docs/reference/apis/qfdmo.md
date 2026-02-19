# «Que faire de mes objets et déchets» API

## Overview

The `/api/qfdmo/` endpoint exposes a REST API for accessing data from the «Que faire de mes objets et déchets» map. This API lets you retrieve information about actors (repair shops, donation points, etc.), available actions, object categories, and search for actors by various criteria.

The API is built with `django-ninja` and follows REST conventions. All endpoints return JSON data.

## Interactive documentation

For full details on each endpoint (parameters, response schemas, examples), see the interactive Swagger/OpenAPI documentation at `/api/docs`.

This interface lets you test all endpoints directly from the browser.

## Technical notes

- All endpoints return JSON
- Inactive actors are never returned by the API
- Non-displayable sources and subcategories are filtered out
- Pagination is enabled by default on the `/acteurs` endpoint
- Geographic coordinates use the WGS84 system (SRID 4326)
- Distances are computed using PostGIS

## Tests

Endpoints for this API are covered by integration tests in `webapp/integration_tests/carte/test_qfdmo_api.py`.
