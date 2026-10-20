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
- Bumped gunicorn to 23.0.0 (20.1.0 needs pkg_resources, absent in python:3.12-slim).

## Home page
- `/` now renders `src/templates/home.html`: live stats (`src/data/stats.py`),
  getting-started steps, ESP32 POST example, and read-endpoint reference.
- Field list on the page comes from `Data.settable_columns()`, so it follows the model.
- Replaced the `helloflask` home test with tests for the page; added `tests/test_stats.py`.
