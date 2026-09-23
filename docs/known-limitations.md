# Known Limitations

This document captures the current known limitations of the MLOps Platform as submitted for the technical assignment.

---

## 1. Simulated Deployment Flow

The deployment pipeline (REQUESTED → VALIDATING → DEPLOYING → SUCCEEDED/FAILED) is **fully simulated** using FastAPI's `BackgroundTasks` with `time.sleep()` delays. No real infrastructure is provisioned — no Kubernetes pods are created, no cloud resources are allocated, and no actual container images are deployed.

**Impact:** The platform demonstrates correct state transition logic and failure handling, but cannot be used as-is to deploy real models.

**Planned Fix:** Integrate with a real orchestration layer (e.g., Kubernetes API, AWS SageMaker, or GCP Vertex AI) to execute genuine deployment pipelines.

---

## 2. No Authentication or RBAC

The API has **no authentication layer**. All endpoints are publicly accessible to anyone with network access. There is no Role-Based Access Control (RBAC) to separate admin actions (approve, archive, deploy) from read-only access.

**Impact:** In production, any user could approve or archive any model version without restriction.

**Planned Fix:** Integrate an identity provider (e.g., Auth0, Firebase Auth, or Keycloak) and enforce JWT-based authentication with role claims on protected endpoints.

---

## 3. No Model Deletion

There is currently **no DELETE endpoint** for models or model versions. Once created, models and versions can only be archived (soft-disable), not fully removed from the registry.

**Impact:** The registry will grow indefinitely; test or erroneous models cannot be cleaned up.

**Planned Fix:** Add `DELETE /models/{model_id}` and `DELETE /models/{model_id}/versions/{version_id}` endpoints with cascade logic.

---

## 4. Rollback Does Not Allow Version Selection

When initiating a rollback, the system **automatically selects the most recent previously-SUCCEEDED deployment** in the same environment. The user cannot specify which version they want to roll back to.

**Impact:** In scenarios with multiple older successful deployments, the user has no control over the rollback target.

**Planned Fix:** Accept an optional `target_version_id` in the rollback request body, allowing the user to select any prior SUCCEEDED deployment as the rollback target.

---

## 5. Single PostgreSQL Instance (No High Availability)

The platform uses a single PostgreSQL container with no replication, failover, or connection pooling (e.g., PgBouncer). All state is stored in one node.

**Impact:** Any database restart or failure will cause full platform downtime and potential data loss if volumes are not persisted.

**Planned Fix:** Use a managed database service (e.g., AWS RDS Multi-AZ, Cloud SQL with HA) for production deployments.

---

## 6. No Real-Time Monitoring Stream

Monitoring metrics are **batch-seeded from a CSV** at startup and displayed statically. There is no real-time inference data collection, no live push from a serving layer, and no WebSocket stream to the frontend.

**Impact:** The monitoring dashboard shows historical data only and does not update as models serve traffic.

**Planned Fix:** Integrate a metrics push endpoint (or Prometheus scrape endpoint) and use WebSockets or Server-Sent Events (SSE) to stream live data to the frontend.

---

## 7. No Pagination on Frontend

The backend supports `skip`/`limit` query parameters for pagination, but the Angular frontend always fetches with the default limit of 100 records and has **no pagination UI component**.

**Impact:** Large datasets will either be truncated silently or cause slow page loads.

**Planned Fix:** Implement Angular Material paginator (`mat-paginator`) wired to the `skip`/`limit` API parameters.
