# Templates, Forms and CSRF (Flask 3.1)

Jinja autoescaping, template inheritance, Flask-WTF forms, app-wide CSRF
protection, flash messages, Post/Redirect/Get and the session cookie. Pinned:
Flask 3.1.3, Jinja2 3.1, Flask-WTF 1.3.0 (WTForms 3), Python 3.11+. The
factory and `extensions.py` are in `app-structure.md`; models and
`db.get_or_404` in `database.md`; login, cookie flags and JWT in
`authentication.md`.

## Common Mistakes

| Mistake | Why it breaks | Fix |
| --- | --- | --- |
| Hand-rolled CSRF: a `before_request` hook comparing a form field with a session token | Works for plain form posts only: no `X-CSRFToken` header for `fetch`/AJAX, no token expiry, no HTTPS Referer check, and no clean way to exempt a token-authenticated API | `CSRFProtect` app-wide, even without WTForms classes: `{{ csrf_token() }}` in plain forms |
| `{{ comment.body \| safe }}`, `Markup(user_text)`, `Markup(f"<b>{name}</b>")` | Marks attacker-controlled text as HTML: stored XSS | Leave autoescape alone; build trusted HTML with `Markup("<b>{}</b>").format(name)`, which escapes the argument |
| HTML templates named `page.jinja2`, `page.html.j2` or `email.txt` | Flask autoescapes only `.html`, `.htm`, `.xml`, `.xhtml` and `.svg`; every other name renders unescaped | Name HTML templates `*.html` |
| `<script>const user = "{{ name }}";</script>` or `<a href="{{ user.website }}">` | HTML escaping does not make a value safe inside JavaScript, and does not stop a `javascript:` URL | `{{ data \| tojson }}` in scripts; accept only `http(s)` URLs at input time |
| `render_template(...)` after a successful POST | A browser refresh re-submits the form and creates a duplicate | Redirect after success (Post/Redirect/Get); re-render only when validation fails |
| Secrets, tokens or personal data in `session` | Flask's session is a signed cookie, not an encrypted one: anyone holding it can read it | Keep only small identifiers (user id); store the rest server-side |
| `WTF_CSRF_ENABLED = False` in the shared test config | The suite passes while every real form post returns 400, or while CSRF is missing | Keep CSRF on; switch it off per test with `@pytest.mark.config(WTF_CSRF_ENABLED=False)` (`testing.md`) |

## Autoescaping

`render_template()` autoescapes templates whose names end in `.html`, `.htm`,
`.xml`, `.xhtml` or `.svg` (`Flask.select_jinja_autoescape`);
`render_template_string()` always autoescapes. `&`, `<`, `>`, `"` and `'` are
escaped, so a value inside a quoted attribute is safe too.

Escaping is switched off for a value by `|safe`, by wrapping it in
`markupsafe.Markup`, or by `{% autoescape false %}`. Use them only for HTML you
generated yourself. To combine trusted markup with user text, let `Markup`
escape the user part:

```python
# myapp/formatting.py
from markupsafe import Markup


def user_badge(name: str) -> Markup:
    # format() escapes its arguments; the literal markup stays as written
    return Markup('<span class="badge">{}</span>').format(name)
```

Register it in the factory with `app.add_template_filter(user_badge)` and use
`{{ note.title | user_badge }}`. `from flask import Markup` was removed in
Flask 3.0; import from `markupsafe`.

Two contexts autoescape does not cover:

- **JavaScript.** Pass data with `{{ value | tojson }}`. It serializes with
  `app.json` and escapes `<`, `>`, `&` and `'`, so `</script>` inside a string
  cannot close the tag. Do not wrap it in quotes in a script; in an HTML
  attribute, use single quotes (`data-x='{{ value | tojson }}'`), because `"`
  is not escaped.
- **URLs.** `href="{{ url }}"` is escaped but still runs `javascript:alert(1)`.
  Validate the scheme when the URL is saved.

## Template Inheritance

One base template owns the page skeleton, the CSRF meta tag for scripts and
the flashed messages; pages fill named blocks.

```jinja
{# templates/base.html #}
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>{% block title %}{% endblock %}</title>
  </head>
  <body>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul class="flashes">
          {% for category, message in messages %}
            <li class="{{ category }}">{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
  </body>
</html>
```

```jinja
{# templates/notes/show.html #}
{% extends "base.html" %}
{% block title %}{{ note.title }}{% endblock %}
{% block content %}
  <h1>{{ note.title }}</h1>
  <p>By {{ note.author | user_badge }}</p>
  <p>{{ note.body }}</p>
{% endblock %}
```

Use `{{ super() }}` to extend a parent block instead of replacing it, and
`{% include "partials/x.html" %}` for fragments shared between pages.
Autoescaping is decided per file, by its own name, for parents, children and
includes alike.

## Forms with Flask-WTF

Add `csrf = CSRFProtect()` (`from flask_wtf.csrf import CSRFProtect`) to
`extensions.py` from `app-structure.md` and bind it in the factory (below).
It checks every `POST`, `PUT`, `PATCH` and `DELETE` request app-wide, whether
or not the view uses a WTForms class.

```python
# myapp/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length


class NoteForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    author = StringField("Author", validators=[Length(max=80)])
    body = TextAreaField("Body", validators=[Length(max=10_000)])
```

```python
# myapp/notes.py
from flask import Blueprint, flash, redirect, render_template, url_for

from .extensions import db
from .forms import NoteForm
from .models import Note

bp = Blueprint("notes", __name__)


@bp.route("/notes/new", methods=["GET", "POST"])
def create_note():
    form = NoteForm()
    if form.validate_on_submit():  # POST/PUT/PATCH/DELETE and valid
        note = Note(
            title=form.title.data, author=form.author.data, body=form.body.data
        )
        db.session.add(note)
        db.session.commit()
        flash("Note saved.", "success")
        return redirect(url_for(".show_note", note_id=note.id))
    # GET, or invalid POST: re-render with the user's input and errors
    return render_template("notes/form.html", form=form)


@bp.get("/notes/<int:note_id>")
def show_note(note_id: int):
    note = db.get_or_404(Note, note_id)
    return render_template("notes/show.html", note=note)
```

```jinja
{# templates/notes/form.html #}
{% extends "base.html" %}
{% block title %}New note{% endblock %}
{% block content %}
  <form method="post">
    {{ form.hidden_tag() }}
    {% for field in [form.title, form.author, form.body] %}
      <p>
        {{ field.label }} {{ field() }}
        {% for error in field.errors %}<span class="error">{{ error }}</span>{% endfor %}
      </p>
    {% endfor %}
    <button type="submit">Save</button>
  </form>
{% endblock %}
```

- `form.hidden_tag()` renders the `csrf_token` hidden field (and any other
  hidden fields). Without it every post fails with 400.
- Read values from `form.field.data` rather than `request.form`, and assign
  fields explicitly. `form.populate_obj(note)` copies every form field onto the
  model, which is only safe while the form has no fields the user must not set.
- The token lives in the session, signed with `SECRET_KEY` (or
  `WTF_CSRF_SECRET_KEY`): one key for every worker (`app-structure.md`).

## CSRF Without Form Classes

`CSRFProtect` adds `csrf_token()` to every template, so plain forms need one
hidden input:

```jinja
<form method="post" action="{{ url_for('notes.delete_note', note_id=note.id) }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <button type="submit">Delete</button>
</form>
```

JavaScript reads the token from the meta tag in `base.html` and sends it in
the `X-CSRFToken` header (`X-CSRF-Token` is accepted too; both are the
default `WTF_CSRF_HEADERS`):

```js
const token = document.querySelector('meta[name="csrf-token"]').content;
await fetch("/notes/42/pin", {
  method: "POST",
  headers: { "X-CSRFToken": token },
  credentials: "same-origin",
});
```

Behavior worth knowing on Flask-WTF 1.3:

| Behavior | Default | Change it |
| --- | --- | --- |
| Token lifetime | 3600 s (`WTF_CSRF_TIME_LIMIT`); a form left open longer fails with "The CSRF token has expired." | `WTF_CSRF_TIME_LIMIT = None` ties it to the session |
| Failure response | `CSRFError`, a `BadRequest` (400); the reason ("The CSRF token is missing.") is its `description` | The app-level `HTTPException` handler already receives it; register `@app.errorhandler(CSRFError)` for a friendlier page |
| HTTPS requests | Also require a same-origin `Referer` (`WTF_CSRF_SSL_STRICT`); `Referrer-Policy: no-referrer` makes every post fail | Keep the browser default (`strict-origin-when-cross-origin`) or `same-origin` |
| Methods checked | `POST`, `PUT`, `PATCH`, `DELETE` (`WTF_CSRF_METHODS`) | Never change state in a `GET` view |

## Exempting a Token-Authenticated API

An API authenticated by an `Authorization: Bearer ...` header (a JWT in header
mode, an API key) is not exposed to CSRF: browsers never attach that header
on their own. Exempt its blueprint, or every API `POST` fails with "The CSRF
token is missing.":

```python
# myapp/__init__.py, inside create_app() after the config checks
# plus migrate, error handlers and CLI registration from app-structure.md
db.init_app(app)
csrf.init_app(app)
app.add_template_filter(user_badge)
app.register_blueprint(notes.bp)
app.register_blueprint(api.bp, url_prefix="/api")
csrf.exempt(api.bp)  # header-token auth only; see below
```

Do not exempt routes that authenticate with the Flask session or
Flask-Login's remember cookie: keep `CSRFProtect` and send `X-CSRFToken` from
JavaScript. An API on Flask-JWT-Extended's cookie mode may be exempted only
because that mode runs its own double-submit check, which must stay on
(`JWT_COOKIE_CSRF_PROTECT`, see `authentication.md`). `@csrf.exempt` on a
single view works the same way.

## Flash Messages and Post/Redirect/Get

`flash(message, category)` stores the message in the session;
`get_flashed_messages()` reads and removes it on the next rendered page, so
it survives exactly one redirect: the successful `POST` flashes and redirects,
the `GET` shows the message, and a refresh repeats only the `GET`.

When validation fails, re-render the form directly (no redirect) so the
user's input and the field errors are shown. Messages are autoescaped like any
other value; never pipe them through `|safe` when they include user input.

## The Session Cookie

`session` is a dictionary serialized to JSON, compressed when that is
shorter, base64-encoded and signed with `SECRET_KEY`. The signature stops
tampering; it does not hide anything. Decoding the cookie without the key
shows its contents (the CSRF token, flashed messages, Flask-Login's
`_user_id`).

- Store small identifiers only; roles come from the database on each request
  (`authentication.md`).
- Browsers reject cookies over about 4 KB, and Werkzeug warns when a cookie is
  larger than 4093 bytes. Large or sensitive per-user state belongs in the
  database.
- The cookie lasts until the browser closes unless `session.permanent = True`,
  which uses `PERMANENT_SESSION_LIFETIME` (default 31 days).
- Cookie flags (`Secure`, `SameSite`; `HttpOnly` is on by default) for
  production are in `authentication.md`.

## Testing with CSRF Enabled

Keep CSRF on in tests and read the token from the rendered form, as a browser
does: the `csrf_token` fixture and a login test are in `testing.md`.

## When to Use / When Not to Use

- **Use** `FlaskForm` + `validate_on_submit` + `CSRFProtect` + PRG for
  server-rendered forms; a plain `<form>` with `{{ csrf_token() }}` for a
  one-button form.
- **Do not use** WTForms for a JSON API: validate with Pydantic, or the
  project's existing schema library (`rest-apis.md`).
- **Keep** the existing CSRF mechanism of a project on WTForms without
  Flask-WTF, or on a pinned older stack, unless the task is to replace it.
