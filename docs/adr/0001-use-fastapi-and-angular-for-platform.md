# ADR-001: Use FastAPI and Angular for the MLOps Platform

## Status
Accepted

## Context
The technical assignment requires building an MLOps platform featuring an API for managing machine learning models, versions, and deployments, along with a user interface to interact with these entities. We needed to select a technology stack that is modern, scalable, and easy to containerize, while remaining maintainable.

## Decision
We chose **FastAPI (Python)** for the backend and **Angular (TypeScript)** for the frontend.

## Alternatives Considered
- **Backend:** Flask or Django. Flask lacks built-in async support and automatic OpenAPI generation. Django is too heavy for a simple API-first service.
- **Frontend:** React or Vue.js. While viable, Angular was chosen for its highly opinionated structure, built-in dependency injection, and RxJS integration which handles complex asynchronous polling gracefully.

## Consequences
### Positive
- **FastAPI** provides automatic OpenAPI (Swagger) documentation, highly performant asynchronous request handling, and strong type safety out of the box via Pydantic.
- **Angular** offers a robust framework for building single-page applications. The RxJS observables make it highly effective for managing state dynamically.
- Both frameworks integrate easily with Docker for reproducible builds.

### Negative
- Angular has a steeper learning curve compared to simple component libraries, requiring strict TypeScript and module structuring.
- FastAPI's strict async/await rules require careful management of database sessions (e.g., SQLAlchemy) to avoid blocking the event loop.

## Follow-up Actions
- Ensure all CI/CD pipelines use the correct Node.js versions for Angular builds.
- Configure Pytest with synchronous SQLite in-memory databases to safely test FastAPI routes without async IO conflicts.
