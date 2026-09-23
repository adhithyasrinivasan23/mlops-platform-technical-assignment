# Test Strategy

This document describes the testing approach for the MLOps Platform, covering all layers of the application from backend unit tests to end-to-end browser automation.

---

## Testing Pyramid

```
         ┌───────────────────┐
         │   E2E (Playwright) │  ← Fewest, slowest, highest confidence
         ├───────────────────┤
         │  Component (Vitest)│  ← Frontend logic & rendering
         ├───────────────────┤
         │ Integration (pytest)│ ← API endpoints with test DB
         ├───────────────────┤
         │   Unit (pytest)    │  ← Business logic, CRUD functions
         └───────────────────┘
```

---

## 1. Backend Tests (Python / pytest)

**Location:** `backend/tests/`

**Run command:**
```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```
Or via Makefile:
```bash
make test-backend
```

**Database:** Tests use an **in-memory SQLite** database (isolated per test session). **No PostgreSQL required** to run the backend unit or integration test suite. The SQLAlchemy `get_db` dependency is overridden at test setup with an in-memory SQLite engine.

> [!NOTE]
> These tests are safe to run in CI without any running database service.

### 1.1 Unit Tests — `test_crud.py`

Tests the CRUD layer functions directly against the database session, bypassing the HTTP layer.

| Test | Description |
|------|-------------|
| `test_create_and_get_model` | Creates a model and retrieves it by ID |
| `test_create_duplicate_model` | Verifies uniqueness constraint on model ID |
| `test_create_model_version` | Creates a version and links it to a model |
| `test_approve_model_version` | Approves a version and checks `approved=True` |
| `test_archive_model_version` | Archives a version and checks `stage=ARCHIVED` |
| `test_create_deployment` | Creates a deployment in `REQUESTED` state |
| `test_rollback_deployment` | Rolls back a `SUCCEEDED` deployment |
| `test_get_metrics` | Retrieves metrics filtered by `model_id` |

### 1.2 Integration Tests — `test_api.py`

Tests the full HTTP request/response cycle using FastAPI's `TestClient`.

| Test | Description |
|------|-------------|
| `test_get_models_empty` | `GET /models` returns empty list on fresh DB |
| `test_create_model` | `POST /models` returns `201` with correct body |
| `test_create_model_duplicate` | `POST /models` returns `400` for duplicate ID |
| `test_get_model_not_found` | `GET /models/{id}` returns `404` for unknown ID |
| `test_create_and_list_versions` | Creates a version and verifies it appears in list |
| `test_approve_version` | `POST .../approve` updates `approved=True` |
| `test_archive_version` | `POST .../archive` updates `stage=ARCHIVED` |
| `test_create_deployment` | `POST /deployments` returns `202 Accepted` |
| `test_retry_failed_deployment` | Retry is only allowed on `FAILED` deployments |
| `test_rollback_succeeded_deployment` | Rollback is only allowed on `SUCCEEDED` deployments |
| `test_deploy_archived_version` | `POST /deployments` returns `400` for archived version |
| `test_deploy_draft_version` | `POST /deployments` returns `400` for unapproved draft |

### 1.3 Metrics Tests — `test_metrics.py`

| Test | Description |
|------|-------------|
| `test_get_metrics_empty` | Returns `[]` for a model with no metrics |
| `test_metrics_are_model_scoped` | Metrics for model A do not appear in model B's response |
| `test_metric_fields_present` | Response includes all expected fields (version, environment, availability, etc.) |

---

## 2. Frontend Component Tests (Vitest / JSDOM)

**Location:** `frontend/src/**/*.spec.ts`

**Run command:**
```bash
cd frontend
npm install --legacy-peer-deps
npx vitest run
```
Or via Makefile:
```bash
make test-frontend
```

**Environment:** Tests run in **JSDOM** (simulated browser DOM), with Angular's `TestBed` for component rendering. HTTP calls are replaced with `jasmine-marbles` or plain RxJS `of()` mocks.

### Covered Components

| Spec File | Component | Tests |
|-----------|-----------|-------|
| `models-list.spec.ts` | `ModelsList` | Renders model table, shows loading spinner, handles empty state |
| `model-detail.spec.ts` | `ModelDetail` | Renders model info, loads versions, loads metrics tab |
| `deployments-list.spec.ts` | `DeploymentsList` | Renders deployment table, shows status badges, handles retry/rollback actions |

---

## 3. End-to-End Tests (Playwright)

**Location:** `frontend/e2e/`

**Run command:**
```bash
cd frontend
npm install --legacy-peer-deps
npx playwright install --with-deps
npx playwright test
```
Or via Makefile:
```bash
make test-e2e
```

**Prerequisite:** The full Docker stack must be running (`docker compose up -d --build`) before running E2E tests, as Playwright communicates with the real backend API.

> [!IMPORTANT]
> **PostgreSQL is required for E2E tests.** The Playwright tests hit the live FastAPI backend which connects to a real PostgreSQL instance. Always start `docker compose up -d` first. Do NOT run E2E tests in the standard `backend-tests` CI job — they run in a dedicated `e2e-tests` job with Docker Compose.

### Test Scenarios — `mlops-scenario.spec.ts`

| Test | Flow |
|------|------|
| **Model Registration** | Navigates to Models, opens Create dialog, fills form, verifies new model appears in table |
| **Version Lifecycle** | Opens a model, creates a new version, approves it, verifies `approved=true` badge |
| **Deployment Flow** | Selects an approved version, deploys to staging, verifies status transitions (REQUESTED → DEPLOYING → SUCCEEDED) |
| **Failure & Retry** | Triggers a deployment with `simulate_failure=true`, verifies `FAILED` state, clicks Retry, verifies new deployment |
| **Rollback** | Rolls back a `SUCCEEDED` deployment, verifies the deployment transitions to `ROLLED_BACK` and a new deployment is created |
| **Monitoring Dashboard** | Navigates to a model's Monitoring Metrics tab, verifies all columns render (Version, Environment, Latency, Availability, Status) |

---

## 4. CI Pipeline

**Location:** `.github/workflows/ci.yml`

The GitHub Actions pipeline runs on every push and pull request to `main`. Jobs run in parallel:

| Job | Steps |
|-----|-------|
| `backend-tests` | Install Python deps → Run `pytest` → Report coverage |
| `frontend-tests` | `npm install` → `npx vitest run` → Angular build validation |
| `e2e-tests` | Start Docker Compose stack → Install Playwright → Run `playwright test` → Upload test report artifact |

---

## 5. Test Coverage Goals (G13 Standard)

| Layer | Target Coverage |
|-------|----------------|
| Backend CRUD & API | ≥ 80% line coverage |
| Frontend Components | Key rendering and interaction paths |
| E2E | Full happy path + 2 error scenarios (failure, rollback) |

---

## 6. Out of Scope

- **Load/performance testing** (no Locust or k6 scripts included)
- **Security testing** (no OWASP ZAP or auth bypass tests — auth is not yet implemented)
- **Visual regression testing** (no screenshot diffing)
