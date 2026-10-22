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

## Teacher admin area (`/admin`)
- New `src/admin/` package: `auth` (password + session + CSRF), `sql_console`
  (single statement, read-only transaction, timeout, row cap, CSV export),
  `db_stats` (database/table sizes, readings per day), `user_stats` (per
  username usage, misuse flags, devices, recent readings, delete), `routes`.
- Disabled (404) unless `ADMIN_PASSWORD` is set; `compose.yaml` now requires
  it. `SECRET_KEY` falls back to a key derived from the password so both
  gunicorn workers share sessions.
- Writes in the SQL console need the "Allow changes" checkbox.
- Flag thresholds (`HIGH_HOURLY_RATE`, `MANY_DEVICES`) are in `user_stats.py`.
- Tests: `test_admin_auth.py`, `test_sql_console.py`, `test_admin_stats.py`;
  `conftest.py` gained `app` and `admin_client` fixtures.
- Not done: login throttling.

## Staged changes and backups
- `src/admin/backups.py`: copies every public table into a
  `backup_<UTC time>` schema in the same database; keeps the newest 5.
  "Back up now" button on the dashboard; "Restore deleted rows" loads an
  INSERT ... WHERE id NOT IN into the console.
- `src/admin/staged_changes.py`: any non-SELECT console statement (and the
  user-page delete) takes a backup, then runs in one held-open transaction
  (savepoint per statement). Commit/Roll back from the SQL page; reads
  during review run inside it; auto-rollback after 180 s idle; lock_timeout 5 s.
- `sql_console.run` is now read-only only; `allow_write` moved to
  `staged_changes.submit`. The user-page delete no longer needs the typed
  username: the commit step is the gate.
- Dockerfile now runs gunicorn with 1 worker + 4 threads because the pending
  transaction is process-local.
- Fixed: backup prune ran before the new backup was visible (kept 6).
- Tests: `test_staged_changes.py`, `test_backups.py`; conftest cleans up
  pending transactions and backup schemas between tests.
