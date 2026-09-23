# API Design

The MLOps Platform exposes a RESTful HTTP API built with **FastAPI**. Interactive documentation is available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc` (ReDoc) when the backend is running.

All request and response bodies use **JSON**. Timestamps follow **ISO 8601** format.

---

## Base URL

```
http://localhost:8000
```

---

## Resources

### Models

| Method | Endpoint | Description | Status Code |
|--------|----------|-------------|-------------|
| `GET` | `/models` | List all registered models | `200 OK` |
| `POST` | `/models` | Register a new model | `201 Created` |
| `GET` | `/models/{model_id}` | Get a specific model with its versions | `200 OK` / `404` |
| `GET` | `/models/{model_id}/versions` | List all versions for a model | `200 OK` |
| `POST` | `/models/{model_id}/versions` | Register a new model version | `201 Created` / `400` |
| `POST` | `/models/{model_id}/versions/{version_id}/approve` | Approve a model version | `200 OK` / `404` |
| `POST` | `/models/{model_id}/versions/{version_id}/archive` | Archive a model version | `200 OK` / `404` |
| `GET` | `/models/{model_id}/metrics` | Retrieve monitoring metrics for a model | `200 OK` |

---

### Deployments

| Method | Endpoint | Description | Status Code |
|--------|----------|-------------|-------------|
| `GET` | `/deployments` | List all deployments | `200 OK` |
| `POST` | `/deployments` | Trigger a new deployment | `202 Accepted` |
| `GET` | `/deployments/{deployment_id}` | Get a specific deployment | `200 OK` / `404` |
| `POST` | `/deployments/{deployment_id}/retry` | Retry a failed deployment | `200 OK` / `400` |
| `POST` | `/deployments/{deployment_id}/rollback` | Roll back a succeeded deployment | `200 OK` / `400` |

---

## Request / Response Schemas

### `POST /models` — Register Model

**Request Body:**
```json
{
  "id": "pump-failure-predictor",
  "name": "Pump Failure Predictor",
  "owner": "ml-team",
  "framework": "scikit-learn"
}
```

**Response `201`:**
```json
{
  "id": "pump-failure-predictor",
  "name": "Pump Failure Predictor",
  "owner": "ml-team",
  "framework": "scikit-learn",
  "versions": []
}
```

---

### `POST /models/{model_id}/versions` — Register Version

**Request Body:**
```json
{
  "version": "1.2.0",
  "stage": "DRAFT",
  "approved": false,
  "artifact_uri": "s3://mlops-artifacts/pump-failure-predictor/1.2.0/model.pkl"
}
```

**Version Stage Enum values:** `DRAFT`, `VALIDATED`, `APPROVED`, `STAGING`, `PRODUCTION`, `ARCHIVED`

**Error `400`:** Version already exists.

---

### `POST /deployments` — Trigger Deployment

**Request Body:**
```json
{
  "model_version_id": 3,
  "environment": "staging",
  "simulate_failure": false
}
```

> Setting `simulate_failure: true` forces the deployment to transition to `FAILED` (useful for testing retry/rollback flows).

**Response `202`:**
```json
{
  "id": "dep-a1b2c3d4",
  "model_version_id": 3,
  "environment": "staging",
  "status": "REQUESTED",
  "created_at": "2026-09-23T10:00:00",
  "updated_at": "2026-09-23T10:00:00"
}
```

**Idempotency Behaviour:**

If an in-flight deployment for the same `model_version_id` and `environment` already exists (i.e. its status is `REQUESTED`, `VALIDATING`, or `DEPLOYING`), the endpoint returns that **existing deployment** instead of creating a new one. The response body and `202` status code are identical.

Once a deployment reaches a terminal state (`SUCCEEDED`, `FAILED`, `ROLLED_BACK`), a new call will create a fresh deployment.

| Existing deployment status | Behaviour |
|----------------------------|-----------|
| `REQUESTED` / `VALIDATING` / `DEPLOYING` | Returns existing deployment (idempotent) |
| `SUCCEEDED` / `FAILED` / `ROLLED_BACK` | Creates a new deployment |
| None | Creates a new deployment |

**Deployment Status Enum values:** `REQUESTED`, `VALIDATING`, `DEPLOYING`, `SUCCEEDED`, `FAILED`, `ROLLED_BACK`

---

### `GET /models/{model_id}/metrics` — Monitoring Metrics

**Response `200`:**
```json
[
  {
    "id": 1,
    "model_id": "pump-failure-predictor",
    "timestamp": "2026-07-01T00:00:00",
    "version": "1.0.0",
    "environment": "production",
    "latency": 86.33,
    "throughput": 875.42,
    "error_rate": 0.0195,
    "quality_score": 0.8309,
    "drift_score": 0.1876,
    "availability": 99.366
  }
]
```

---

## Error Responses

All errors return a standard JSON body:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| `400 Bad Request` | Invalid input (e.g. duplicate model, version already exists, invalid state transition) |
| `404 Not Found` | Resource does not exist |
| `422 Unprocessable Entity` | Request body failed Pydantic validation |
| `500 Internal Server Error` | Unexpected server error |

---

## Design Decisions

- **`POST` for state transitions** (approve, archive, retry, rollback) rather than `PATCH`, to keep endpoints explicit and easy to reason about.
- **`202 Accepted`** for deployment creation because processing happens asynchronously in a background task.
- **No DELETE endpoints** currently (see `known-limitations.md`).
- **Pagination** is supported via `?skip=0&limit=100` query parameters on all list endpoints.
