# Public statistics API

## Overview

The `/api/stats` endpoint returns public statistics on **oriented visitors**: visitors who viewed a product page or performed a search on the map.

Data is aggregated from PostHog according to the requested periodicity.

## Endpoint

```text
GET /api/stats
```

## Query parameters

| Parameter     | Type    | Required | Default | Description                                                                           |
| ------------- | ------- | -------- | ------- | ------------------------------------------------------------------------------------- |
| `periodicity` | string  | No       | `month` | KPI grouping granularity. Allowed values: `day`, `week`, `month`, `year`              |
| `since`       | integer | No       | `null`  | Number of period iterations to include (e.g. `30` for 30 days when `periodicity=day`) |

## Request examples

### Monthly statistics (default)

```bash
GET /api/stats
```

### Last 30 days statistics

```bash
GET /api/stats?periodicity=day&since=30
```

### Last 12 months statistics

```bash
GET /api/stats?periodicity=month&since=12
```

### Last 4 weeks statistics

```bash
GET /api/stats?periodicity=week&since=4
```

## Response

### Format

```json
{
  "description": "Oriented visitors: visitors who viewed a product page or performed a search on the map",
  "stats": [
    {
      "date": 1704067200,
      "iso_date": "2024-01-01T00:00:00+00:00",
      "value": 1234
    },
    {
      "date": 1704153600,
      "iso_date": "2024-01-02T00:00:00+00:00",
      "value": 1456
    }
  ]
}
```

### Response fields

<!-- markdownlint-disable MD060 -->

| Field              | Type    | Description                                          |
| ------------------ | ------- | ---------------------------------------------------- |
| `description`      | string  | Description of the returned metric                   |
| `stats`            | array   | List of data points, sorted by ascending date        |
| `stats[].date`     | integer | Unix timestamp (seconds) for the start of the period |
| `stats[].iso_date` | string  | ISO 8601 date for the start of the period (UTC)      |
| `stats[].value`    | float   | Number of oriented visitors for this period          |

<!-- markdownlint-enable MD060 -->

## Interactive documentation

This API route can be tested at `/api/docs`, which provides an interactive Swagger/OpenAPI interface to try the endpoint directly from the browser.

## Technical notes

- Data is fetched from PostHog via the Query API
- Dates are normalized to the start of the requested period (e.g. start of month for `month`)
- If communication with PostHog fails, the API returns an HTTP 502 error
- The `since` parameter limits the time range of returned data (e.g. `since=30` with `periodicity=day` returns the last 30 days)
