---
name: flask-expert
description: "Builds, modernizes and audits Flask 3.x applications: application factories and blueprints, Flask-SQLAlchemy 3.1 with SQLAlchemy 2.x typed models and Flask-Migrate, JSON APIs validated with Pydantic or marshmallow and JSON errors, Jinja templates with Flask-WTF CSRF, Flask-Login and Flask-JWT-Extended auth, pytest fixtures over the factory, and gunicorn or waitress deployment with Celery, RQ or APScheduler jobs. Use when code imports from flask or flask_* extensions (create_app, Blueprint, app.route, flask_sqlalchemy, flask_login, flask_wtf), when adding login, an API endpoint, forms, tests, background jobs or production deployment to a Flask app, when reviewing or upgrading an existing Flask project, or when diagnosing Flask errors such as 'Working outside of application context' or a 500 that only appears under gunicorn. Not for Django or FastAPI projects."
license: MIT
metadata:
  author: https://github.com/Saifullah1999Pk
  version: "1.0.0"
  domain: backend
  triggers: Flask, Flask app, Flask API, create_app, Blueprint, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, Flask-JWT-Extended, Jinja2, Werkzeug, gunicorn, application context
  role: expert
  scope: implementation
  output-format: code
  related-skills: django-expert, fastapi-expert
---

# Flask Expert

Senior Flask engineer for Flask 3.1 and SQLAlchemy 2.x on Python 3.11+: factory-built apps that start only with real configuration, typed models, JSON APIs that never answer in HTML, and tests that build a fresh app per test.

## When to Use This Skill

- Building a new Flask JSON API or server-rendered Flask app
- Adding models, migrations, login, JWT auth, forms or validation to an existing Flask app
- Writing pytest tests for a Flask app, or making an existing suite isolate its tests
- Preparing a Flask app for production: gunicorn or waitress, reverse proxy, secure cookies, background jobs
- Reviewing or modernizing legacy Flask code (module-level `app`, `db.Column`, `Model.query`, removed 2.x APIs)

## Core Workflow

1. **Structure** — Check the pinned Flask and Flask-SQLAlchemy versions and the existing layout; build new apps with `create_app(test_config=None)`, unbound extensions and blueprints, settings from `FLASK_*` environment variables
2. **Data** — `Mapped`/`mapped_column` models and `select()` queries with eager loading; schema changes go through Flask-Migrate
3. **Interface** — JSON blueprints with schema validation (Pydantic, or the project's marshmallow) and an app-level JSON error handler, or Jinja templates with Flask-WTF forms and Post/Redirect/Get
4. **Secure** — `CSRFProtect` for browser forms, Flask-Login sessions or Flask-JWT-Extended tokens, ownership checks on every row, production cookie flags
5. **Test & deploy** — pytest fixtures that call the factory with a fresh database per test, or the project's existing fixtures (run them before calling the work done), then gunicorn behind `ProxyFix` (waitress on Windows) and jobs that run in an app context

## Reference Guide

| Topic | Reference | Load When |
| --- | --- | --- |
| App structure | `references/app-structure.md` | Factory, config and secrets, extensions, blueprints, error handlers, CLI commands, Flask 3.x removals |
| Database | `references/database.md` | Models, queries, pagination, N+1, transactions, Flask-Migrate, projects pinned to Flask-SQLAlchemy 2.x |
| REST APIs | `references/rest-apis.md` | JSON responses, Pydantic validation, JSON errors, pagination envelope, CORS, `async def` views |
| Templates & forms | `references/templates-forms.md` | Jinja autoescaping, Flask-WTF forms, CSRF, flash messages, session cookie |
| Authentication | `references/authentication.md` | Password hashing, Flask-Login, Flask-JWT-Extended, cookie flags, ownership and roles |
| Testing | `references/testing.md` | pytest fixtures over the factory, per-test database, logged-in clients, CSRF-on tests, SQLite vs PostgreSQL |
| Deployment & jobs | `references/deployment.md` | gunicorn, waitress on Windows, `ProxyFix`, production config, Celery, RQ, scheduled jobs |

## Minimal Working Example

A factory, one blueprint and one typed model, configured from `FLASK_SECRET_KEY` and `FLASK_SQLALCHEMY_DATABASE_URI`:

```python
# app.py: run with `flask --app app run --debug`
from flask import Blueprint, Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
bp = Blueprint("notes", __name__)


class Note(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))


@bp.get("/notes")
def list_notes() -> dict:
    notes = db.session.scalars(select(Note).order_by(Note.id)).all()
    return {"items": [{"id": n.id, "title": n.title} for n in notes]}


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_prefixed_env()  # FLASK_SECRET_KEY -> SECRET_KEY
    if test_config is not None:
        app.config.from_mapping(test_config)
    for key in ("SECRET_KEY", "SQLALCHEMY_DATABASE_URI"):
        if not app.config.get(key):
            raise RuntimeError(f"Set FLASK_{key}")
    db.init_app(app)
    app.register_blueprint(bp, url_prefix="/api")
    return app
```

Tables come from Flask-Migrate (`flask db upgrade`); only tests call `db.create_all()`. An API also needs the app-level `HTTPException` handler from `app-structure.md`.

## Auditing an Existing Flask Project

First read the pins: on Flask-SQLAlchemy 2.x, items 1 and 3 do not apply (`database.md`). Run each command from the project root, adding `--exclude-dir=.venv` (your virtualenv); hits in test files are expected. Ordered by how often unaided code got it wrong:

1. **Models** — `grep -rnE 'db\.Column\(' --include='*.py' .` → no hits; columns are `Mapped[...] = mapped_column(...)` (`database.md`).
2. **Factory** — `grep -rnE '^[a-z_]*app = (Flask|create_app)\(' --include='*.py' .` → only entry points nothing imports (`wsgi.py`, Celery/RQ worker modules) (`app-structure.md`).
3. **Queries** — `grep -rnE '\b[A-Z]\w*\.query\b' --include='*.py' .` → no hits; `db.session.get`, `select()`, `db.get_or_404`, `db.paginate(max_per_page=...)` (`database.md`).
4. **Secrets** — `grep -rnE 'SECRET_KEY["'\'']*\]? *= *["'\'']|SECRET_KEY.*(get(env)?\([^)]*,|\) or |token_(hex|urlsafe|bytes))' --include='*.py' .` → no hits: no literal, default or per-process random key; the factory raises when it is missing; and `git ls-files | grep -E '(^|/)\.env$'` → no output and `git check-ignore -q .env` succeeds (exit 0): `.env` is git-ignored, only `.env.example` is committed (`app-structure.md`).
5. **API errors** — `grep -rnE '(errorhandler|register_error_handler)\(HTTPException' --include='*.py' .` → one app-level handler that answers JSON under `/api/` (no output = HTML error pages) (`rest-apis.md`).
6. **Removed APIs** — `grep -rnE 'FLASK_ENV|\bapp\.env\b|before_(app_)?first_request|flask\.__version__|from flask import .*\b(Markup|escape)\b' --include='*.py' --include='.env*' --include='.flaskenv' .` → no hits (`app-structure.md`).
7. **Input** — `grep -rn 'request.get_json(' --include='*.py' .` → each body goes through one schema (Pydantic `model_validate`/`TypeAdapter` with `extra="forbid"`, or the project's existing marshmallow schema): no truthiness checks, `Model(**data)`, `silent=` or `force=` (`rest-apis.md`).
8. **Schema** — `grep -rnE 'create_all\(|text\(["'\'']ALTER' --include='*.py' .` → only in tests; a `migrations/` folder exists and deploys run `flask db upgrade` (`database.md`).
9. **CSRF** — `grep -rn 'CSRFProtect(' --include='*.py' .` → initialized in the factory, `{{ csrf_token() }}` in every POST form, no hand-rolled token check (`templates-forms.md`).
10. **N+1** — `grep -rn 'relationship(' --include='*.py' .` → `lazy="raise_on_sql"` (or per-query `raiseload("*", sql_only=True)`), and list queries that serialize a relationship use `selectinload`/`joinedload` (`database.md`).
11. **SQL** — `grep -rniE '(select|insert|update|delete) .*(" *\+|\+ *"|%s|\.format\()|f["'\''](select|insert|update|delete) ' --include='*.py' .` → no hits; `text()` takes values as `:name` parameters (`database.md`).
12. **Dev server** — `grep -rnE 'debug=True|app\.run\(' --include='*.py' .` → no `debug=True`; production starts gunicorn or waitress, never `app.run` (`deployment.md`).
13. **Scheduler** — `grep -rnE 'BackgroundScheduler\(|scheduler\.start\(' --include='*.py' .` → never in `create_app()` or at import: cron plus a `flask` command, or the Redis lease started from `wsgi.py` (`deployment.md`).
14. **Async views** — `grep -rn 'async def' --include='*.py' .` → `flask[async]` installed, and nobody expects more throughput: each request still holds a worker (`rest-apis.md`).

## Constraints

### MUST DO

- Build new apps with `create_app(test_config=None)`; a module-level `app` lives only in `wsgi.py`. An existing app keeps its structure and style: add the feature in place and suggest the factory, never convert it unasked
- Require `SECRET_KEY` and the database URI from the environment, one value shared by every worker, and raise when missing
- Write `DeclarativeBase` + `Mapped` models and `select()` queries; match the existing style on a Flask-SQLAlchemy 2.x pin
- Change schemas with Flask-Migrate; pass `max_per_page=` to every `paginate`
- Give every API an app-level JSON `HTTPException` handler; validate every JSON body with one schema library, Pydantic by default or the project's existing marshmallow/flask-smorest (422 on failure)
- Use `CSRFProtect` app-wide for browser forms, hash passwords with Werkzeug, filter rows by owner
- Ship pytest tests with a fresh database per test, through a fixture that calls the factory (an existing app without one: extend its own suite and fixtures, `testing.md`)

### MUST NOT DO

- Hardcode a secret, fall back to a literal or `secrets.token_*()` value, or commit `.env`: dev secrets go in a git-ignored `.env`, with only a placeholder `.env.example` committed
- Use `FLASK_ENV`, `before_first_request`, `flask.__version__` or `from flask import Markup`
- Return HTML error pages or exception text from an API
- Call `db.create_all()` or `ALTER TABLE` at import or in `create_app()`
- Build SQL with f-strings, `+`, `%` or `.format()`
- Serve with `app.run()`/`debug=True` on a server, or gunicorn on Windows; start APScheduler in `create_app()`

## Output Templates

When implementing a Flask feature, provide:

1. Factory (or existing app setup), extension and config changes, with the environment variables to set
2. Models plus the `flask db migrate`/`upgrade` commands, and the blueprint views
3. pytest tests using the factory fixture (or the project's existing fixtures), and a short note on decisions, version assumptions and caveats (an `async def` view still holds one worker per request), written into the README or a comment by the code, not only the chat

## Knowledge Reference

Flask 3.1, Werkzeug, application factory, blueprints, Flask-SQLAlchemy 3.1, SQLAlchemy 2.x, Mapped, mapped_column, select(), Flask-Migrate, Alembic, Pydantic v2, marshmallow, flask-smorest, Flask-CORS, Jinja2, Flask-WTF, CSRFProtect, Flask-Login, Flask-JWT-Extended, pytest, gunicorn, waitress, ProxyFix, Celery, RQ, APScheduler

## Related Skills

- `django-expert` — batteries-included Python web apps with the Django ORM, admin and DRF
- `fastapi-expert` — async-first Python APIs; prefer it over `async def` Flask views for async-heavy work

[Documentation](https://jeffallan.github.io/claude-skills/skills/backend/flask-expert/)
