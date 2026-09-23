# Architecture Document

## System Overview

The MLOps platform is designed using a modern, decoupled client-server architecture. It consists of three primary layers:
1. **Frontend**: An Angular SPA serving as the user interface.
2. **Backend API**: A Python-based FastAPI web service managing business logic and deployments.
3. **Database**: A PostgreSQL relational database for persisting state, models, deployments, and metrics.

All components are containerized and orchestrated using Docker Compose to ensure a consistent execution environment across development, testing, and production.

## 1. Frontend Architecture

The frontend is built with **Angular (v18+)** and styled using custom CSS. 

### Key Characteristics
- **Component-based Architecture**: The UI is broken down into reusable standalone components (e.g., model list, model details, deployment view).
- **Service Layer**: HTTP communication with the backend is abstracted into Angular services (e.g., `ModelsService`, `DeploymentsService`), providing strict typings through TypeScript interfaces.
- **State Management**: Local component state and RxJS observables are used to handle real-time UI updates (e.g., waiting for deployment statuses).
- **Containerization**: Built as a static bundle and served using an **NGINX** web server inside a Docker container for high performance.

## 2. Backend Architecture

The backend is a **FastAPI** Python service. It is designed to be lightweight, asynchronous, and highly performant.

### Key Characteristics
- **RESTful API Design**: The application exposes RESTful endpoints grouped by domain (`/models`, `/deployments`, `/metrics`).
- **Data Validation & Serialization**: Utilizes **Pydantic** models extensively for validating incoming requests and serializing API responses, ensuring strict type safety.
- **ORM**: **SQLAlchemy** is used as the Object Relational Mapper to interact with the database. 
- **Deployment Simulation**: Deployments are currently simulated via background asynchronous tasks using FastAPI's `BackgroundTasks`, which mimic the latency and state transitions of deploying to a Kubernetes cluster without actually provisioning infrastructure.
- **Containerization**: The API is served using **Uvicorn** (ASGI server) inside a lightweight Python Docker container.

## 3. Data Layer Architecture

- **Primary Database**: **PostgreSQL** is utilized as the primary operational database, running as a dedicated Docker service.
- **Schema & Migrations**: The schema manages relational data for Models, Versions, Metrics, and Deployments. Alembic is used for schema migrations.
- **Data Seeding**: A custom `seed.py` script automatically ingests provided `.json` and `.csv` seed files upon backend startup, populating the database with realistic base data.

## 4. CI/CD & Automation

- **Testing**:
  - **Backend**: `pytest` for unit and integration testing against an in-memory SQLite database.
  - **Frontend**: Component tests running via Vitest/JSDOM and End-to-End scenarios running via Playwright.
- **GitHub Actions**: A unified `.github/workflows/ci.yml` pipeline triggers on push/pull-request, running parallel jobs to independently verify the backend and frontend builds and test suites.

## 5. Architectural Decisions & Known Limitations
- Please refer to `known-limitations.md` for current constraints (e.g., simulated deployments, lack of auth).
- The platform uses a single PostgreSQL instance for simplicity, but could easily be scaled horizontally behind a load balancer with read replicas if read traffic increases.
