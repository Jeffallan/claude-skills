# REST APIs (Flask 3.1)

JSON responses, request validation with Pydantic, JSON errors for every
status, pagination, CORS and async views. Pinned: Flask 3.1.3, Werkzeug 3.1.9,
Pydantic 2.14.3, Flask-CORS 6.0.5, Python 3.11+. The factory, the `/api`
blueprint and the app-level `HTTPException` handler that turns errors under
`/api/` into JSON are in `app-structure.md`; models, queries and `db.paginate`
are in `database.md`. This file builds on both.

## Common Mistakes

| Mistake | Why it breaks | Fix |
| --- | --- | --- |
| No JSON error handling in an API | An unknown route, a wrong method or an unhandled exception returns Werkzeug's HTML page; API clients fail to parse it | The app-level `HTTPException` handler from `app-structure.md`, plus the `ValidationError` handler below. Add both to every API, asked for or not |
| `data = request.get_json()` followed by truthiness checks (`if not data.get("title")`) | A list, number or `null` body raises `AttributeError` (500); `{"title": "x", "body": {"a": 1}}` passes and fails inside the database driver (500) | Validate types and shape with a Pydantic model; invalid input is a 422 with field-level details |
| `Note(**request.get_json())` | Unknown keys raise `TypeError` (500); `"id"` or `"owner_id"` in the body is written straight to the row (mass assignment) | `Note(**NoteIn.model_validate(...).model_dump())` with `extra="forbid"` |
| `request.get_json(silent=True) or {}`, or `force=True` | A wrong `Content-Type` or malformed JSON turns into "field required" errors, or into parsing anything as JSON | Plain `request.get_json()`: Flask raises 415 or 400 and the error handler answers in JSON |
| `return {"error": f"{type(e).__name__}: {e}"}, 500` | Sends SQL, file paths, hostnames and sometimes credentials to the client | Let the exception propagate (Flask logs it, the handler returns a generic 500), or log it and `abort(502/503, description=...)` with a safe message |
| `@app.errorhandler(Exception)` as a catch-all | Flask no longer logs the traceback; it also runs with `TESTING=True`, hiding failures from tests; without an `HTTPException` handler it turns every 404 into a 500 | Nothing to add: the `HTTPException` handler already receives unhandled exceptions as `InternalServerError`, after Flask logs them |
| `207 Multi-Status`, or `200` with `{"error": ...}`, for a partly failed batch | 207 is a WebDAV status (RFC 4918) whose body is an XML multistatus document; like a 200 with an error body, it is a 2xx, so clients, retries and monitoring treat the failed request as a success | Validate the whole batch and reject it with one 422 that lists the failing indexes, then write it in one transaction (a per-item 200 only when the API contract is explicitly per-item: 200 = batch processed) |
| `CORS(app)` or `CORS(app, supports_credentials=True)` | The default origin is `*`; with credentials Flask-CORS echoes back any caller's `Origin` with `Allow-Credentials: true`, so any website can call the API as the logged-in user | `origins=` an explicit list from config, on `/api/*` only |
| `async def` views expected to raise throughput | Each request still holds one WSGI worker until the view returns | Use async for concurrent I/O inside one request; for async-heavy apps use Quart or FastAPI |

## Responses and Status Codes

Return a `dict` or a `list` and Flask serializes it with `app.json` (lists
since Flask 2.2); `jsonify()` is not needed. Add a status and headers as a
tuple: `return body, 201, {"Location": url}`.

| Status | When | How |
| --- | --- | --- |
| 200 | Read or update succeeded | `return body` |
| 201 | Created; include `Location` | `return body, 201, {"Location": url_for(...)}` |
| 204 | Deleted, nothing to return | `return "", 204` |
| 400 / 415 | Malformed JSON / `Content-Type` is not JSON | Raised by `request.get_json()` (table below) |
| 401 / 403 | Not authenticated / not allowed | `abort(401)` / `abort(403)`; see `authentication.md` |
| 404 | Unknown route or missing row | Routing; `db.get_or_404(..., description=...)` |
| 405 | Route exists, method does not | Routing; the response keeps the `Allow` header |
| 409 | Unique constraint or state conflict | `abort(409, description="...")` after `rollback()` (`database.md`) |
| 413 | Body larger than `MAX_CONTENT_LENGTH` | Set `MAX_CONTENT_LENGTH` (bytes) in config |
| 422 | Valid JSON or query string, invalid content | Pydantic `ValidationError` + the handler below |
| 502 / 503 | An upstream service failed / you are overloaded | `abort(502, description="...")` after logging |

`abort(code, description="...")` is how a view sends an error with its own
message: the `HTTPException` handler copies `description` into `message`. Only
put text there that is safe for any client to read.

## Reading the Body: `request.get_json()` in Flask 3.1

| Request | `request.get_json()` | `request.get_json(silent=True)` |
| --- | --- | --- |
| `Content-Type` not JSON (form, `text/plain`, missing) | Raises 415 Unsupported Media Type | `None` |
| JSON content type, malformed or empty body | Raises 400 Bad Request with a generic message (the decoder's error only in debug mode) | `None` |
| Valid JSON | The decoded value: `dict`, `list`, `str`, number, `bool` or `None` | Same |

- `application/json` and any `application/*+json` type count as JSON
  (`request.is_json`). `request.json` is the same as `request.get_json()`.
- The 415 is Werkzeug 2.3+; Werkzeug 2.1 and 2.2 raised 400 for a wrong
  content type.
- A valid JSON body can still be `[1, 2]`, `"text"` or `null`. Never index the
  result before it has been validated.

## Validation with Pydantic v2

Use Pydantic models directly in the views; no Flask extension is needed.
One model per input shape; `extra="forbid"` rejects fields the client should
not send (`id`, `owner_id`, `is_admin`) instead of silently ignoring them.

```python
# myapp/schemas.py
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class NoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default="", max_length=10_000)
    priority: int = Field(default=3, ge=1, le=5, strict=True)


# a batch of 1-100 notes, validated as a whole
NoteBatch = TypeAdapter(Annotated[list[NoteIn], Field(min_length=1, max_length=100)])
```

- **Lax vs strict.** By default Pydantic converts `"5"` and `true` to an
  `int`. `strict=True` on a numeric field makes the client send a number. `str`
  fields never accept a list, an object or a number from JSON, even in lax mode.
- Do not set `strict=True` on the whole model while using `model_validate()`:
  `date`, `UUID` and `Decimal` fields then reject the JSON strings that carry
  them. `Model.model_validate_json(request.get_data())` validates the raw body
  in JSON mode, where strict mode accepts those strings; malformed JSON then
  becomes a 422 `json_invalid` error instead of a 400. `get_data()` skips the
  content-type check, so test `request.is_json` first (`abort(415)`).
- `str_strip_whitespace=True` runs before `min_length`, so `"   "` is rejected.
- For PATCH, use a second model with optional fields and apply only
  `model_dump(exclude_unset=True)`; do not let an explicit `null` through to a
  `NOT NULL` column.

```python
# myapp/api.py
from flask import Blueprint, request, url_for
from pydantic import ValidationError
from sqlalchemy import select

from .extensions import db
from .models import Note
from .schemas import NoteBatch, NoteIn

bp = Blueprint("api", __name__)


def note_to_dict(note: Note) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "body": note.body,
        "priority": note.priority,
    }


@bp.post("/notes")
def create_note():
    data = NoteIn.model_validate(request.get_json())  # 415 / 400 / 422
    note = Note(**data.model_dump())  # only validated, known fields
    db.session.add(note)
    db.session.commit()
    location = url_for(".get_note", note_id=note.id)
    return note_to_dict(note), 201, {"Location": location}


@bp.get("/notes/<int:note_id>")
def get_note(note_id: int):
    note = db.get_or_404(Note, note_id, description=f"Note {note_id} does not exist.")
    return note_to_dict(note)
```

`Note` is an ordinary typed model (`database.md`) with `title`, `body` and
`priority` columns. Validation happens before anything touches the session,
so an invalid request writes nothing.

## JSON Errors for Every Status

The app-level `HTTPException` handler in `app-structure.md` already answers
every `HTTPException` status in the table above (including 500, after
Flask logs the traceback) as `{"error": ..., "message": ...}`, for example
`{"error": "Not Found", "message": "Note 42 does not exist."}`. Do not
register a second `HTTPException` or `Exception` handler.

The only addition is Pydantic's `ValidationError`, which is not an
`HTTPException`. Register it on the API blueprint, in the same shape plus
`details`:

```python
@bp.errorhandler(ValidationError)
def handle_validation_error(error: ValidationError):
    return {
        "error": "Unprocessable Entity",
        "message": "The request failed validation.",
        "details": error.errors(
            include_url=False, include_context=False, include_input=False
        ),
    }, 422
```

- `include_input=False` keeps the submitted values (passwords, tokens) out of
  the response; `include_context=False` drops `ctx`, which can hold exception
  objects that are not JSON-serializable. Each detail is
  `{"type", "loc", "msg"}`, for example
  `{"type": "extra_forbidden", "loc": ["owner_id"], "msg": "Extra inputs are not permitted"}`.
- A blueprint error handler covers exceptions raised in that blueprint's
  views. With several API blueprints, register the same function with
  `app.register_error_handler(ValidationError, handle_validation_error)` in
  `register_error_handlers` instead.
- Only call `model_validate` on client input in views. A `ValidationError`
  from server-side data (a settings model, an upstream response) would
  otherwise be reported to the client as its own 422.

### Never send exception text to the client

Let unexpected exceptions propagate: the client gets the generic 500 and the
traceback goes to the log. When a failure is expected and the client can act
on it (an upstream service is down), log it with
`current_app.logger.exception(...)` and `abort(502, description="...")` with a
message written for the client, as in the async example below. To test the
500 path, create the app with `PROPAGATE_EXCEPTIONS=False`; with
`TESTING=True` alone the exception reaches the test instead.

### Batches: all or nothing

```python
@bp.post("/notes/batch")
def create_notes():
    items = NoteBatch.validate_python(request.get_json())  # loc: [1, "title"]
    notes = [Note(**item.model_dump()) for item in items]
    db.session.add_all(notes)
    db.session.commit()  # one transaction: every note or none
    return {"items": [note_to_dict(note) for note in notes]}, 201
```

One invalid item gives one 422 that names it by index and writes nothing. A
per-item contract returns 200 with `results` entries such as
`{"index": 1, "status": 422, "errors": [...]}`, never 207.

## Pagination Envelope

A paginated list returns an object, never a bare list: the `items`, `page`,
`per_page`, `pages`, `total` envelope built from
`db.paginate(stmt, max_per_page=100)` in `database.md` (`list_products`).
`?page=abc`, `?page=0` or a page past the end is a 404, returned as JSON by
the same handler. Unpaginated collections (a short, bounded list) can return
a plain list.

### Query parameters need validation too

`request.args.get("per_page", 20, type=int)` silently falls back to the
default on `?per_page=abc` (`db.paginate` answers 404 instead). When a wrong
value matters, validate the query string like a body; lax mode turns the
query string's `"3"` into `3`, so do not set `strict=True` here:

```python
class NoteFilter(BaseModel):
    priority: int | None = Field(default=None, ge=1, le=5)


@bp.get("/notes/search")
def search_notes():
    query = NoteFilter.model_validate(request.args.to_dict())  # ?priority=abc: 422
    stmt = select(Note).order_by(Note.id).limit(100)
    if query.priority is not None:
        stmt = stmt.where(Note.priority == query.priority)
    return [note_to_dict(note) for note in db.session.scalars(stmt)]
```

## CORS with Flask-CORS

CORS is only needed when a browser page on another origin calls the API; a
frontend served from the same origin needs none. CORS does not protect the
API: other clients ignore it, so authentication and authorization still
apply. Create `cors = CORS()` in `extensions.py` with the other extensions,
add `"CORS_ORIGINS"` to `REQUIRED_SETTINGS` in the factory, and bind it after
the config is loaded:

```python
cors.init_app(
    app,
    resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
)
```

- Set the origins per environment:
  `FLASK_CORS_ORIGINS='["https://app.example.com"]'` becomes a list through
  `from_prefixed_env()`. Missing config stops startup instead of falling back
  to Flask-CORS's default `*`.
- An origin is scheme, host and port, with no path or trailing slash:
  `https://app.example.com/` and `https://app.example.com:8443` never match
  `https://app.example.com`. Literal origins are compared exactly (ignoring
  case).
- A string with regex characters (`*`, `?`, `^`, `$`, brackets, parentheses or
  a backslash) is treated as a regex and matched with `re.match`, which is
  anchored only at the start: end it with `$`
  (`r"https://[a-z0-9-]+\.example\.com$"`).
- Pass `supports_credentials=True` only when the browser must send cookies
  (session or JWT-in-cookie auth) and only with explicit origins. Token auth
  in an `Authorization` header needs no credentials.
- Flask-CORS also adds the headers to error responses, so the browser can
  read the JSON error bodies.

```python
# ❌ CORS that lets other websites in
CORS(app, supports_credentials=True)  # default origins "*": any Origin is echoed back
CORS(app, origins=r"https://.*\.example\.com")  # matches https://a.example.com.evil.net
```

## Async Views

Flask supports `async def` views when installed with the async extra:
`pip install "flask[async]"` (it adds `asgiref`; without it every request to
an async view raises `RuntimeError: Install Flask with the 'async' extra in
order to use async views.`). Use it to run several I/O calls concurrently
inside one request, with an async client such as `httpx.AsyncClient`:

```python
# myapp/rates.py: needs `pip install "flask[async]" httpx`
import asyncio

import httpx
from flask import Blueprint, abort, current_app

bp = Blueprint("rates", __name__)


@bp.get("/rates")
async def get_rates():
    urls = current_app.config["RATE_PROVIDERS"]
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            responses = await asyncio.gather(*(client.get(url) for url in urls))
            for response in responses:
                response.raise_for_status()
        except httpx.HTTPError:
            current_app.logger.exception("rate provider failed")
            abort(502, description="A rate provider is unavailable.")
    return {"quotes": [response.json() for response in responses]}
```

Mount it under the API prefix, `app.register_blueprint(rates.bp,
url_prefix="/api")`: the JSON error handler only answers under `/api/`, so
anywhere else `abort(502)` returns Werkzeug's HTML page.

What Flask does with it, and what to tell the user:

- **Each request still occupies one worker.** Flask is WSGI: for an async
  view it starts an event loop in a thread, runs the view to completion, and
  returns the result. The worker (gunicorn process or thread) is busy for the
  whole request, so the number of requests served at once is unchanged. The
  gain is concurrency within the request (`gather` above), not across
  requests.
- **Inside the view, everything must be async.** `requests`, `time.sleep()`
  and Flask-SQLAlchemy queries block the event loop and serialize the
  `gather`. Awaiting calls one after another gains nothing over a sync view.
- **No state across requests.** Each call runs in a new event loop (in a new
  thread) that is closed when the view returns, so create the `AsyncClient`
  inside the view: one shared at module level fails on a later request with
  `RuntimeError: Event loop is closed` when it reuses a pooled connection.
  `asyncio.create_task()` work still running when the view returns is
  canceled: use a task queue (`deployment.md`).
- **Extensions:** decorators from extensions that predate async support may
  not await the view.
- **When to switch:** if most of the app is async, needs websockets, streams
  or holds many slow requests open at once, use an ASGI framework: Quart
  (Flask's API on ASGI, the smallest port) or FastAPI (see the
  `fastapi-expert` skill). For one or two concurrent upstream calls in an
  otherwise sync app, an async view is fine.

## When to Use / When Not to Use

**Use marshmallow 4 + flask-smorest instead** when you want OpenAPI docs and
Swagger UI generated from the schemas: flask-smorest's `@blp.arguments` and
`@blp.response` validate and serialize with marshmallow schemas and document
the endpoints in one place. Pick one validation library per project.

**Do not use** this for HTML form posts (Flask-WTF, `templates-forms.md`),
or in a project that already validates with marshmallow, webargs or another
library: follow the existing one.
