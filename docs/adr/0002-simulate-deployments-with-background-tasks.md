# ADR-002: Simulate Deployments with Background Tasks

## Status
Accepted

## Context
The platform must demonstrate the ability to deploy machine learning models. In a real-world production environment, deploying a model requires interacting with an orchestrator (like Kubernetes or AWS SageMaker) to pull a model artifact and expose it as an inference endpoint. However, provisioning actual cloud infrastructure or requiring a local Kubernetes cluster introduces significant complexity and overhead for a technical assignment.

## Decision
We decided to abstract the deployment process by simulating it using **FastAPI BackgroundTasks**. When a deployment is requested, a background thread is spawned that waits for a set duration, transitioning the deployment status through `VALIDATING`, `DEPLOYING`, and finally `SUCCEEDED` (or `FAILED`), mimicking the exact latency and state transitions of a real orchestrator.

## Alternatives Considered
- **Kubernetes (Minikube/Kind):** Too heavy and error-prone for reviewers to set up locally just to verify assignment functionality.
- **External Message Brokers (Celery/RabbitMQ):** Adds unnecessary complexity and extra containers to the `docker-compose` stack for what is essentially a simulated timeout.

## Consequences
### Positive
- **Simplicity:** Eliminates the need for reviewers to install Kubernetes or configure cloud credentials to test the core deployment tracking and state machine logic.
- **Speed:** The platform remains entirely self-contained inside a lightweight `docker-compose` setup, ensuring it runs reliably on any machine.
- **Idempotency Testing:** We can thoroughly test idempotent API behaviors and rollback mechanics without waiting for real pods to spin up.

### Negative
- **No real inference:** We cannot actually serve HTTP inference requests to the deployed models since no real container is created.
- **Lack of true isolation:** The background tasks run inside the FastAPI process. In a scaled production system, this would tie up web workers.

## Follow-up Actions
- Implement explicit idempotency checks in the API routers to prevent multiple background tasks from spinning up for the same deployment ID.
- Create mock tests that bypass the sleep timers so unit tests run instantly.
