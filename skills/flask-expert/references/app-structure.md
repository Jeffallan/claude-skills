# Application Structure (Flask 3.1)

Factory, configuration, extensions, blueprints, error handlers, CLI commands,
logging and the WSGI entry point for Flask 3.1 on Python 3.11+.

## Common Mistakes

| Mistake | Why it breaks | Fix |
| --- | --- | --- |
| `app = Flask(__name__)` at module level in new code, even in a one-file demo | Config is frozen at import; every test shares one app; modules import `app` from each other and hit circular imports | `create_app()` factory; extensions created unbound and attached with `init_app` (an existing module-level app: see "When not to restructure") |
| `app = create_app()` at module level in the package (`myapp/__init__.py`, `app.py`) | Every `import` (tests, Celery/RQ workers, Alembic) builds an app and runs its side effects | Module-level `app` only in `wsgi.py`, which nothing else imports |
| `os.environ.get("SECRET_KEY", "dev")` | A missing variable in production silently signs sessions with a key that is in your git history | Require the key; raise at startup when it is missing |
| `os.environ.get("SECRET_KEY") or secrets.token_hex()` | Each gunicorn worker generates its own key: a cookie signed by worker A fails on worker B, so logins and CSRF tokens fail at random, and all are invalidated on every restart | One key from the environment, shared by every worker |
| `FLASK_ENV=production` / `app.env` / `app.config["ENV"]` as a switch | Removed in Flask 2.3; the variable is silently ignored | `FLASK_DEBUG=1` or `flask run --debug` for development; real settings come from the environment |
| `flask.__version__` | Deprecated in 3.0 (warns), removed in 3.2 | `importlib.metadata.version("flask")`, or feature detection |
| `@app.before_first_request` for setup | Removed in Flask 2.3 | Do setup in `create_app`, or in a `flask` CLI command for one-off tasks |
| `@bp.errorhandler(404)` to give an API blueprint JSON 404s | Never fires for unknown URLs: routing fails before any blueprint is chosen | App-level `HTTPException` handler that checks `request.path` |

## When to Use a Factory

**When not to restructure:** a project pinned to an older Flask, or one
already built around a module-level app, keeps its existing style unless the
task is the restructure itself (see the end of the removals section). Add the
requested feature in place, in the project's own structure, and offer the
factory as a suggestion; converting the app unasked breaks its run command,
its imports and any existing database the new migrations do not know about.

**Always for a new app, including a one-file demo.** The factory costs a few lines,
`flask --app app run --debug` finds `create_app` in `app.py` on its own, tests
get a fresh app per call, and the file grows into the package layout below
without a rewrite. The Minimal Working Example in `SKILL.md` is that shape:
an unbound `db` and blueprint at module level, and a `create_app()` that binds
them and refuses to start without its settings. Move to the package layout
once there is a second module, migrations or a deployment.

## Layout

```text
project/
├── myapp/
│   ├── __init__.py      # create_app(); no module-level app
│   ├── extensions.py    # db = SQLAlchemy(), migrate = Migrate() (unbound)
│   ├── main.py          # HTML blueprint
│   ├── api.py           # JSON blueprint, mounted at /api
│   ├── errors.py        # register_error_handlers(app)
│   └── cli.py           # custom `flask` commands
├── instance/            # git-ignored; optional instance/config.py per host
├── tests/
├── wsgi.py              # app = create_app(), for gunicorn/waitress only
├── .flaskenv            # committed: FLASK_APP, FLASK_DEBUG (dev CLI only)
└── .env                 # git-ignored: dev secrets (dev CLI only)
```

Larger apps turn `main.py`/`api.py` into packages (`myapp/api/__init__.py`
holding `bp`, plus `routes.py`, `schemas.py`); the factory does not change.

## The Factory

The official tutorial's signature, `create_app(test_config=None)`, with
configuration from the environment: tests pass a plain dict instead of a
parallel tree of `DevelopmentConfig`/`TestingConfig` classes. Unlike the
tutorial, there is no `SECRET_KEY="dev"` default: missing required settings
stop the app at startup.

```python
# myapp/__init__.py
from collections.abc import Mapping
from typing import Any

from flask import Flask

from . import api, main
from .cli import check_db_command
from .errors import register_error_handlers
from .extensions import db, migrate

REQUIRED_SETTINGS = ("SECRET_KEY", "SQLALCHEMY_DATABASE_URI")


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # 1. Optional instance/config.py (git-ignored) for per-host values.
    app.config.from_pyfile("config.py", silent=True)
    # 2. FLASK_* environment variables: FLASK_SECRET_KEY -> SECRET_KEY.
    app.config.from_prefixed_env()
    # 3. Tests pass explicit overrides last.
    if test_config is not None:
        app.config.from_mapping(test_config)

    missing = [key for key in REQUIRED_SETTINGS if not app.config.get(key)]
    if missing:
        raise RuntimeError(
            f"Missing required config: {', '.join(missing)}. Set FLASK_<NAME> "
            "in the environment (one value shared by every worker) or in "
            "instance/config.py."
        )

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp, url_prefix="/api")
    register_error_handlers(app)
    app.cli.add_command(check_db_command)

    return app
```

Rules the factory follows:

- **No import-time work.** Importing `myapp` defines functions and unbound
  extension objects only. Nothing connects, creates tables, or reads secrets
  until `create_app()` runs.
- **Setup goes in the factory**, not in a `before_request` hook guarded by a
  flag; schema changes go through migrations (`database.md`).
- **Circular imports disappear** because no module imports an `app` object.
  Views reach the app through `current_app`, extensions through
  `myapp.extensions`.

## Configuration from the Environment

`from_prefixed_env()` (Flask 2.1+) copies every `FLASK_*` variable into
`app.config` without the prefix, parsing values as JSON where possible
(`FLASK_MAX_CONTENT_LENGTH=1048576` becomes an `int`).

```python
# ❌ every one of these starts "successfully" with a broken or public key
SECRET_KEY = os.environ.get("SECRET_KEY", "dev")  # public key in production
SECRET_KEY = os.getenv("SECRET_KEY") or "change-me"  # same problem
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)  # per worker
app.config["SECRET_KEY"] = secrets.token_urlsafe()  # per worker, per restart
```

The random variants break sessions, Flask-WTF CSRF tokens, JWTs and
itsdangerous tokens across workers (Common Mistakes). Generate the key once,
store it in your secret manager, and give the same value to every process. To
rotate it, move the old value into `SECRET_KEY_FALLBACKS` (Flask 3.1+, a
list): Flask's session still accepts it for unsigning, but each extension must
add its own support.

### Development defaults without production fallbacks

Dev values live in files that only the `flask` command (and `app.run()`) load,
and only when `python-dotenv` is installed. gunicorn and waitress never read
them, so a production process with no real environment fails fast instead of
picking up a dev key.

```bash
# .flaskenv (committed: no secrets)
FLASK_APP=myapp
FLASK_DEBUG=1

# .env (git-ignored: each developer generates their own key once)
#   python -c "import secrets; print(secrets.token_hex())"
FLASK_SECRET_KEY=paste-the-generated-value-here
FLASK_SQLALCHEMY_DATABASE_URI=sqlite:///dev.db
```

Add `.env` to `.gitignore` before the first commit, and commit only a
`.env.example` with placeholders (`FLASK_SECRET_KEY=change-me`). Never commit a
real or literal key, even a "dev-only" one: python-dotenv loads it on every
`flask run`, so it becomes the app's real secret, and git history keeps it.
`git ls-files | grep -E '(^|/)\.env$'` must print nothing, and
`git check-ignore -q .env` must succeed (exit 0).

`FLASK_DEBUG=1` turns on the reloader and debugger; it does not select a
config, and never belongs in production (the debugger executes arbitrary
code). On a server, set the variables in the service manager, container or
platform, or in `instance/config.py` (outside version control).

## Extensions: the `init_app` Pattern

Create each extension once, unbound, in its own module, and bind it inside the
factory. Models, views and CLI commands import `db` from `extensions.py`;
nothing imports an `app` object.

```python
# myapp/extensions.py
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
```

One unbound object serves any number of apps (each test builds its own), and
inside a request or app context it finds the active app through
`current_app`. The same applies to `LoginManager()`, `CSRFProtect()`,
`JWTManager()`, `CORS()` and `Mail()`. Models and queries are covered in
`database.md`.

## Blueprints

`myapp/main.py` is the same with `Blueprint("main", __name__)`:

```python
# myapp/api.py
from flask import Blueprint

bp = Blueprint("api", __name__)


@bp.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- Set the prefix in `register_blueprint(..., url_prefix="/api")` so every
  URL is visible in the factory. Passing `url_prefix` to `Blueprint(...)`
  works too; pick one place per project.
- `@bp.before_request` and `@bp.errorhandler` apply only to requests that
  matched one of that blueprint's routes; use `@bp.before_app_request` and
  `@bp.app_errorhandler` for app-wide hooks.

## Error Handlers: JSON for the API, HTML for Pages

Register handlers in the factory so every app instance, including test apps,
gets them. One `HTTPException` handler covers 404 and 405 (raised by routing,
before any blueprint is involved) and 500: for an unhandled exception Flask
logs the traceback, then passes an `InternalServerError` to this handler.

```python
# myapp/errors.py
import json

from flask import Flask, request
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        if not request.path.startswith("/api/"):
            return error  # Werkzeug's HTML page; or render_template(...)
        response = error.get_response()  # keeps status and headers (Allow)
        response.data = json.dumps(
            {"error": error.name, "message": error.description}
        )
        response.content_type = "application/json"
        return response
```

The 500 body is Werkzeug's generic description, never the exception text, so
internals do not leak to clients. With `TESTING=True` (or in debug mode)
unhandled exceptions propagate instead, which is what you want in tests.
Validation errors (422), error envelopes and `abort()` with payloads are in
`rest-apis.md`.

## Custom `flask` Commands

Use CLI commands for one-off and scheduled work (seeding, cleanup, nightly
reports run from cron) instead of routes or startup hooks.

```python
# myapp/cli.py
import click
from flask.cli import with_appcontext
from sqlalchemy import text

from .extensions import db


@click.command("check-db")
@with_appcontext
def check_db_command() -> None:
    """Exit non-zero if the database is unreachable (deploy/readiness check)."""
    db.session.execute(text("SELECT 1"))
    click.echo("database: ok")
```

Registered with `app.cli.add_command(check_db_command)` in the factory, it
runs as `flask --app myapp check-db`. Keep `@with_appcontext` on a plain
`@click.command`: the `flask` executable pushes an app context for every
command (Flask 2.2+), but `app.test_cli_runner().invoke(args=[...])` calls
`app.cli` directly, and without the decorator `db.session` raises "Working
outside of application context" in tests. Commands created with
`@app.cli.command()` or `@bp.cli.command("name")` are wrapped automatically.
Blueprint commands are namespaced as `flask <blueprint> name` unless the
blueprint is created with `cli_group=None`.

## Logging

`app.logger` is `logging.getLogger(app.name)` (for example `myapp`), not
`"flask.app"`. Without configured handlers Flask adds one writing to stderr,
enough for `flask run`. In production, configure logging once in the entry
point, before the app is created (`wsgi.py` below): Flask then adds no
handler, and all loggers propagate to the same root handler. Inside the
package, log with `current_app.logger` or `logging.getLogger(__name__)`, and
never call `logging.basicConfig()` from library or view code.

## The WSGI Entry Point

`wsgi.py` is the one place a module-level `app` belongs: the WSGI server needs
a global to import, and nothing else imports this file, so its side effects
(logging setup, building the app) run exactly once per worker process.

```python
# wsgi.py
import logging.config
import os

from myapp import create_app

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "default"}
        },
        "root": {"level": os.environ.get("LOG_LEVEL", "INFO"), "handlers": ["console"]},
    }
)

app = create_app()
```

Serve it with `gunicorn -w 4 wsgi:app` (Linux/macOS) or
`waitress-serve wsgi:app` (Windows). Workers, proxies and secure cookies are
in `deployment.md`. Development uses `flask run --debug`; with
`FLASK_APP=myapp` from `.flaskenv` it finds and calls `create_app()` itself.

```python
# ❌ myapp/__init__.py: app built as a side effect of import
from flask import Flask

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
db.init_app(app)
with app.app_context():
    db.create_all()  # runs in every test, worker and migration that imports myapp
```

## Flask 3.x Removals and Deprecations

Pinned: Flask 3.1.3, Werkzeug 3.1.9. "Removed" means an `ImportError` or
`AttributeError` on these versions.

| Old API | Status | Use instead |
| --- | --- | --- |
| `FLASK_ENV`, `app.env`, `ENV` config key | Deprecated 2.2, removed 2.3 (env var silently ignored) | `FLASK_DEBUG=1` / `flask run --debug`; config from the environment |
| `@app.before_first_request`, `@bp.before_app_first_request` | Deprecated 2.2, removed 2.3 | Setup in `create_app()`, or a CLI command |
| `app.json_encoder` / `app.json_decoder`, `flask.json.JSONEncoder` / `JSONDecoder` | Deprecated 2.2, removed 2.3 | Subclass `flask.json.provider.DefaultJSONProvider`; `app.json = MyProvider(app)` |
| `JSON_AS_ASCII`, `JSON_SORT_KEYS`, `JSONIFY_MIMETYPE`, `JSONIFY_PRETTYPRINT_REGULAR` | Deprecated 2.2, removed 2.3 | `app.json.ensure_ascii`, `.sort_keys`, `.mimetype`, `.compact` |
| `send_file(attachment_filename=, cache_timeout=, add_etags=)` | Deprecated 2.0, removed 2.2 | `download_name=`, `max_age=`, `etag=` |
| `from flask import Markup, escape` | Deprecated 2.3, removed 3.0 | `from markupsafe import Markup, escape` |
| `flask._app_ctx_stack`, `flask._request_ctx_stack` | Deprecated 2.2, removed 3.0 | `current_app`, `g` (extensions: `g._myext_name`), `has_request_context()` |
| `flask.__version__` | Deprecated 3.0, removed 3.2 | `importlib.metadata.version("flask")` |
| `werkzeug.urls.url_parse`, `url_quote`, `url_encode`, `url_decode`, ... | Deprecated Werkzeug 2.3, removed 3.0 | `urllib.parse` (`urlsplit`, `quote`, `urlencode`, `parse_qs`) |
| `werkzeug.__version__` | Deprecated Werkzeug 3.0, removed 3.1 | `importlib.metadata.version("werkzeug")` |
| `werkzeug.security.safe_str_cmp` | Removed Werkzeug 2.1 | `hmac.compare_digest` |

On a project pinned to an older Flask, keep its existing idioms and APIs
unless the task is the upgrade; if it is, follow the table top to bottom and
run the tests with `-W error::DeprecationWarning`.
