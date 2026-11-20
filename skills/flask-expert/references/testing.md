# Testing (pytest, Flask 3.1)

pytest fixtures over the app factory, the test client and CLI runner, a fresh
database per test, logged-in clients, CSRF-enabled form tests, and where
SQLite stops standing in for PostgreSQL. Pinned: pytest 9.2.0, Flask 3.1.3,
Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.9, Flask-Login 0.6.3,
Flask-JWT-Extended 4.7.4, Flask-WTF 1.3.0, Python 3.11+. The factory
(`create_app(test_config)`) is in `app-structure.md`; the example app's
models, login view and token API are in `authentication.md`.

## Common Mistakes

| Mistake | Why it breaks | Fix |
| --- | --- | --- |
| `with app.app_context(): yield app` in the `app` fixture | Every test-client request reuses that context: one `db.session`, one `g`, no per-request teardown. A view that forgets `commit()` still passes | Push a context only around setup and assertions (fixtures below) |
| One database for the whole run (module-level app, session-scoped fixture, a shared `test.db`) | Results depend on test order and on what ran before | A new app and an empty database per test |
| `create_app()` in tests without both required settings | The factory refuses to start without `SECRET_KEY` and `SQLALCHEMY_DATABASE_URI`; leaving the URI to the environment can point tests at the dev database | Pass both in `test_config`, which the factory applies last |
| `WTF_CSRF_ENABLED = False` in the shared test config | No test posts a form the way a browser does, so a template missing its token ships and every real post returns 400 | Keep CSRF on; switch it off per test with `@pytest.mark.config(WTF_CSRF_ENABLED=False)` |
| Asserting the JSON 500 response with `TESTING=True` | The exception is raised into the test instead of reaching the error handler | `@pytest.mark.config(PROPAGATE_EXCEPTIONS=False)`; see `rest-apis.md` |
| Mocking `db.session` or `Model.query` | The mock accepts any query: wrong SQL, missing joins and constraint violations all pass | A real database; mock only external services |
| `client.post(url, data=json.dumps(payload))` | No JSON content type: `request.get_json()` answers 415 | `client.post(url, json=payload)`, then `response.get_json()` |
| SQLite in tests, PostgreSQL in production, and nothing else | Foreign keys off, string lengths unchecked, `LIKE` case-insensitive: some bugs only production sees | Foreign-key pragma in `conftest.py`; run CI against PostgreSQL |

## Fixtures

The minimal set, copy-paste ready. Delete the fixtures (and imports) for
extensions the project does not use.

```python
# tests/conftest.py
import os
import re
import sqlite3

import pytest
from flask_jwt_extended import create_access_token
from flask_login import FlaskLoginClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from myapp import create_app
from myapp.extensions import db
from myapp.models import User


def pytest_configure(config):
    config.addinivalue_line("markers", "config(**settings): extra test_config")


@event.listens_for(Engine, "connect")
def _sqlite_foreign_keys(dbapi_connection, connection_record):
    # SQLite ignores FOREIGN KEY constraints unless each connection opts in.
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest.fixture
def app(request):
    test_config = {
        "TESTING": True,
        "SECRET_KEY": "x" * 32,  # PyJWT warns if shorter
        # A new in-memory SQLite database per app. TEST_DATABASE_URL may name a
        # throwaway PostgreSQL database instead: every table the models define
        # is dropped.
        "SQLALCHEMY_DATABASE_URI": os.environ.get("TEST_DATABASE_URL", "sqlite://"),
    }
    marker = request.node.get_closest_marker("config")
    if marker is not None:
        test_config.update(marker.kwargs)
    app = create_app(test_config)
    with app.app_context():
        db.create_all()
    yield app  # no app context stays pushed while the test runs
    with app.app_context():
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def user_id(app):
    with app.app_context():
        user = User(email="alice@example.com")
        user.set_password("correct horse battery staple")
        db.session.add(user)
        db.session.commit()
        return user.id  # not the object: it is detached once the context ends


@pytest.fixture
def logged_in_client(app, user_id):
    app.test_client_class = FlaskLoginClient  # writes Flask-Login's session cookie
    with app.app_context():
        return app.test_client(user=db.session.get(User, user_id))


@pytest.fixture
def auth_headers(app):
    def headers_for(user_id: int) -> dict[str, str]:
        with app.app_context():
            token = create_access_token(identity=str(user_id))
        return {"Authorization": f"Bearer {token}"}

    return headers_for


@pytest.fixture
def csrf_token():
    def token_from(client, url: str) -> str:
        page = client.get(url).get_data(as_text=True)
        return re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page).group(1)

    return token_from
```

- **`@pytest.mark.config(...)` changes one test's settings**, for example
  `WTF_CSRF_ENABLED=False` or `PROPAGATE_EXCEPTIONS=False`, and every fixture
  built on `app` picks it up.
- **Fixtures return ids, not ORM objects.** An object created inside a
  fixture's `with app.app_context():` is detached when the block ends, and
  reading an attribute that the commit expired raises
  `DetachedInstanceError`. Load it again inside the test's own context.
- **`logged_in_client`** uses Flask-Login's `FlaskLoginClient`, which writes the
  user id into the session cookie, as `login_user()` would. Test the login
  view itself once with a real form post (below).

## Do Not Keep an App Context Pushed

```python
# ❌ the app context stays pushed for the whole test
@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SECRET_KEY": "x" * 32, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        db.create_all()
        yield app
```

When a test-client request starts, Flask creates an app context only if no
context for the same app is already active (`RequestContext.push` in
`flask/ctx.py`); otherwise the request runs inside the test's context. With
the fixture above, then:

- every request in the test shares the test's `db.session` and identity map.
  A view that changes an object and forgets `commit()` still passes, because
  the test reads the same in-memory object instead of the database;
- `teardown_appcontext` handlers run once, when the test ends, not after each
  request. Flask-SQLAlchemy removes the session there, so a request's
  uncommitted changes are not rolled back, the objects it loaded stay in the
  identity map for the next request, and values stored on `g` carry over.

The fixtures above push a context only for setup. Push one in a test only
around the lines that touch `db` directly, after the requests:

```python
# tests/test_notes_api.py
from myapp.extensions import db
from myapp.models import Note


def test_create_note(app, client, auth_headers, user_id):
    response = client.post(
        "/api/notes", json={"title": "Buy milk"}, headers=auth_headers(user_id)
    )
    assert response.status_code == 201
    note_id = response.get_json()["id"]
    with app.app_context():  # a new session: sees only what the view committed
        assert db.session.get(Note, note_id).title == "Buy milk"
```

`response.get_json()` returns `None` for a non-JSON response. Use
`query_string={...}` for query parameters and `headers={...}` for tokens.

## A Fresh Database per Test

The `app` fixture gives every test a new app, a new engine and an empty
schema:

- **In-memory SQLite (`sqlite://`, the default above).** Flask-SQLAlchemy
  gives an in-memory database a `StaticPool`, so all sessions of that app
  share one connection and one database, which disappears with the engine.
  Creating it costs milliseconds.
- **A file or a PostgreSQL database (`TEST_DATABASE_URL`).** The data outlives
  the app, so the fixture's teardown drops every table and disposes of the
  engine (which also releases the file on Windows). Use a database that
  exists only for tests.

This isolates tests even when the code under test commits. A
rollback-per-test fixture is not a drop-in alternative: the classic recipe,
`db.session.configure(bind=connection)` inside an outer transaction that the
fixture rolls back, is silently ignored on Flask-SQLAlchemy 3.x. Its
`Session.get_bind()` returns the app's engine, so the test's commits are real
and the outer rollback undoes nothing. For a large schema on
PostgreSQL, where `create_all()` per test gets slow, create the tables once
per session and delete every table's rows after each test instead. With
pytest-xdist, give each worker its own database.

## Forms with CSRF On

Read the token from the rendered form as a browser does, and turn CSRF off
only for tests that are about something else (setup: `templates-forms.md`).

```python
# tests/test_login.py
import pytest

CREDENTIALS = {"email": "alice@example.com", "password": "correct horse battery staple"}


def test_login_with_csrf_token(client, csrf_token, user_id):
    assert client.post("/login", data=CREDENTIALS).status_code == 400  # no token
    data = {**CREDENTIALS, "csrf_token": csrf_token(client, "/login")}
    assert client.post("/login", data=data).status_code == 302
    assert client.get("/notes").status_code == 200


@pytest.mark.config(WTF_CSRF_ENABLED=False)  # this test is about the password
def test_login_rejects_wrong_password(client, user_id):
    response = client.post("/login", data={**CREDENTIALS, "password": "wrong"})
    assert response.status_code == 200  # form re-rendered with an error
    assert client.get("/notes").status_code == 302
```

Fetch the token with the same client that posts: it is tied to that
client's session cookie. A token-authenticated API exempted with
`csrf.exempt(api.bp)` needs no token.

## CLI Commands

`runner.invoke(args=[...])` calls `app.cli` in-process and captures the
output (a plain `@click.command` needs `@with_appcontext` here:
`app-structure.md`).

```python
# tests/test_cli.py
def test_check_db_command(runner):
    result = runner.invoke(args=["check-db"])
    assert result.exit_code == 0
    assert "database: ok" in result.output
```

## SQLite Is Not PostgreSQL

| Behavior | SQLite | PostgreSQL |
| --- | --- | --- |
| Foreign keys | Not enforced unless each connection runs `PRAGMA foreign_keys=ON` (the `conftest.py` listener does) | Enforced |
| `String(200)` length | Ignored: longer values are stored | Error: `value too long for type character varying(200)` |
| `LIKE` | Case-insensitive for ASCII letters | Case-sensitive; write `ilike()` when you mean it (`=` is case-sensitive in both) |
| `DateTime(timezone=True)`, `Numeric` | Offset dropped; no native decimal (`database.md`) | Native |
| `ARRAY`, `INET`, `CITEXT` and other dialect types | `create_all()` fails to compile them; `JSONB` becomes `JSON`, and its `@>` operator then fails at query time | Native |
| Row locks, concurrency | `with_for_update()` renders nothing; one writer per database file; the in-memory test database is a single shared connection | Row locks and concurrent transactions |
| Migrations | Limited `ALTER TABLE`; Alembic copies tables (batch mode) | Real `ALTER TABLE` |

Run the suite against the production engine (a `postgres` service in CI, or
a local container) whenever the tests are meant to catch any of the rows
above: constraint and length violations, case-sensitive lookups, PostgreSQL
types, locking or concurrent updates, raw SQL, and `flask db upgrade` on the
real migrations. Use the same major version as production and set
`TEST_DATABASE_URL`. SQLite stays useful as the fast local loop for code that
uses none of those.

## pytest Configuration

```toml
# pyproject.toml (pytest 9.0+; on pytest 8 use [tool.pytest.ini_options] without `strict`)
[tool.pytest]
testpaths = ["tests"]
strict = true  # unknown config keys, unregistered markers and XPASS fail
filterwarnings = [
    "error::DeprecationWarning",
    # Flask-Login 0.6.3 calls datetime.utcnow() when it sets the remember-me
    # cookie (deprecated in Python 3.12): library code, so ignore it for that
    # module only.
    'ignore:datetime\.datetime\.utcnow\(\) is deprecated:DeprecationWarning:flask_login\.login_manager',
]
```

`error::DeprecationWarning` turns removed-API use in your code into
failures before an upgrade does. When a library's own code warns, add a
filter for that library's module with a comment, never a blanket `ignore`.
The `config` marker is registered in `conftest.py`, so `strict` accepts it.

## When to Use / When Not to Use

| Situation | Do |
| --- | --- |
| Views, error handlers, login, CSRF, JSON shape | The test client: it runs routing, hooks, handlers and teardown |
| A helper that needs `request` or `url_for` but no HTTP round trip | `with app.test_request_context("/path"):` |
| Outbound HTTP, email, payments, `task.delay()` | Mock or fake at that boundary (never `db.session`) |
| An existing suite with its own fixture style | Extend it; adopt these fixtures only when they fix a real problem (leaking state, CSRF never tested) |
