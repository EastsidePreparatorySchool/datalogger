# datalogger spec log

## CI/CD and Portainer hosting (replaces Heroku)
- Added `Dockerfile` (python 3.12-slim, gunicorn on port 8000) and `.dockerignore`.
- Added `.github/workflows/ci_cd.yaml`: pytest against a Postgres service on
  every push/PR; on push to main, builds and pushes
  `ghcr.io/eastsidepreparatoryschool/datalogger` (`latest` and short SHA).
- Added `compose.yaml` Portainer stack (postgres + web, external `proxy`
  network, `POSTGRES_PASSWORD` required).
- Added `tests/` (route smoke tests) and `requirements-dev.txt`.
- Removed `Procfile`.
- Schema is created by `db.create_all()` at startup; alembic migrations are
  not run in the container.
