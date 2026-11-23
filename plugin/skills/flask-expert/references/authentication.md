# Authentication and Authorization (Flask 3.1)

Password hashing, session login with Flask-Login, token auth with
Flask-JWT-Extended (header and cookie modes), cookie flags, and ownership and
role checks. Pinned: Flask 3.1.3, Werkzeug 3.1.9, Flask-Login 0.6.3,
Flask-JWT-Extended 4.7.4 (requires PyJWT 2.11+), Flask-WTF 1.3.0, Python
3.11+. The factory and the `SECRET_KEY` check are in `app-structure.md`;
`CSRFProtect` and the session cookie in `templates-forms.md`; Pydantic
validation and the JSON error shape in `rest-apis.md`.

## Common Mistakes

| Mistake | Why it breaks | Fix |
| --- | --- | --- |
| `JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)` | Each gunicorn worker signs with its own key: a token issued by one worker fails on the next with "Signature verification failed", and every restart logs everyone out | One key from the environment, shared by every worker. Flask-JWT-Extended falls back to `SECRET_KEY`, which the factory in `app-structure.md` already requires |
| `create_access_token(identity=user.id)` | PyJWT 2.10+ requires `sub` to be a string; the token is issued, then every request with it fails with "Subject must be a string" (422 by default) | `identity=str(user.id)`; convert back with `int(get_jwt_identity())` |
| A view that changes or reveals a row protected only by `@login_required` / `@jwt_required()` | Any logged-in user can read, edit or delete any row by changing the id in the URL | Filter the query by owner (`Note.owner_id == current_user.id`) and return 404; check roles explicitly |
| JWT in cookies with `JWT_COOKIE_CSRF_PROTECT = False` | The browser attaches the cookie to requests from any site: CSRF | Keep the default (`True`); JavaScript sends the `csrf_access_token` cookie value in `X-CSRF-TOKEN` |
| Production cookies left at their defaults | `SESSION_COOKIE_SECURE`, `REMEMBER_COOKIE_SECURE` and `JWT_COOKIE_SECURE` default to `False`: the cookies are also sent over plain HTTP | Set the flags in the table below in the production environment |
| `password_hash = mapped_column(String(128))` | Werkzeug's default scrypt hash is 162 characters: PostgreSQL rejects the insert, SQLite stores it silently, so tests pass | `String(255)` |
| JWT access tokens in `localStorage` | Any XSS on the site can read and exfiltrate them | Browser clients: session login, or Flask-JWT-Extended's cookie mode |

## Password Hashing

`werkzeug.security` is already installed with Flask and is enough for most
apps. On Werkzeug 3.1, `generate_password_hash(password)` uses
`scrypt:32768:8:1` with a 16-character salt. The method and its parameters
are stored in the hash, so `check_password_hash` still verifies hashes made
with older defaults (`pbkdf2:sha256:260000$...`) and future defaults can
change without breaking logins.

```python
# myapp/models.py
from flask_login import UserMixin
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # scrypt: 162 chars
    is_admin: Mapped[bool] = mapped_column(default=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Note(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
```

`UserMixin` supplies `is_authenticated`, `is_active` and `get_id()` (which
returns `str(self.id)`). The login view below re-hashes old pbkdf2 hashes the
next time the user logs in. Use a dedicated library (argon2-cffi, bcrypt)
only when a policy requires that algorithm.

## Extensions and the Factory

```python
# myapp/extensions.py: add to the module from app-structure.md
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # without it, login_required returns 401
jwt = JWTManager()
```

```python
# myapp/__init__.py, inside create_app() after the config checks
# plus migrate, error handlers and CLI registration from app-structure.md
db.init_app(app)
csrf.init_app(app)
login_manager.init_app(app)
jwt.init_app(app)
register_jwt_errors(jwt)
app.register_blueprint(auth.bp)
app.register_blueprint(notes.bp)
app.register_blueprint(api.bp, url_prefix="/api")
csrf.exempt(api.bp)  # header tokens, or cookie mode with its own CSRF check
```

Flask-JWT-Extended signs with `JWT_SECRET_KEY`, or with `SECRET_KEY` when
that is unset; if you set a separate JWT key (`FLASK_JWT_SECRET_KEY`), add
`"JWT_SECRET_KEY"` to the factory's required settings. With HS256, PyJWT
2.11+ warns (`InsecureKeyLengthWarning`) for keys shorter than 32 bytes;
`secrets.token_hex()` returns 32 random bytes as 64 hex characters.

## Session Login with Flask-Login

`LoginForm` is a plain `FlaskForm` with `email`, `password` and `remember`
fields:

```python
# myapp/forms.py
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Length(max=254)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
```

```python
# myapp/auth.py
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_required, login_user, logout_user
from sqlalchemy import select

from .extensions import db, login_manager
from .forms import LoginForm
from .models import User

bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))


def safe_next(target: str | None) -> str | None:
    """Return target only if it is a path on this site."""
    if not target or not target.startswith("/") or target.startswith("//"):
        return None
    if "\\" in target or not target.isprintable():  # browsers rewrite these
        return None
    return target


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.scalar(select(User).where(User.email == email))
        if user is not None and user.check_password(form.password.data):
            if not user.password_hash.startswith("scrypt:"):
                user.set_password(form.password.data)  # upgrade an old hash
                db.session.commit()
            session.clear()  # drop anything left from before the login
            login_user(user, remember=form.remember.data)
            next_url = safe_next(request.args.get("next"))
            return redirect(next_url or url_for("notes.list_notes"))
        flash("Invalid email or password.", "error")
    return render_template("auth/login.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for(".login"))
```

- `user_loader` receives the id as a string and must return `None` (not
  raise) for a deleted user; Flask-Login then treats the request as anonymous.
- `@login_required` redirects to `login_view` with `?next=/the/path` (relative
  for same-host URLs). `safe_next` rejects absolute URLs, `//host`, and
  backslash or control-character tricks that browsers turn into `//host`.
  The login form posts back to its own URL, so `next` survives the `POST`.
- Log out with a `POST` form carrying `{{ csrf_token() }}`, not a link.
- `login_user(remember=True)` sets a separate `remember_token` cookie that
  logs the user back in after the session cookie expires
  (`REMEMBER_COOKIE_DURATION`, default 365 days). Without it, the login lasts
  until the browser closes.
- On Python 3.12+, Flask-Login 0.6.3's own code warns about
  `datetime.utcnow()` when it sets the remember cookie: harmless; the filter
  for module `flask_login.login_manager` only is in `testing.md`.

## Cookie Flags for Production

| Setting | Default | Production |
| --- | --- | --- |
| `SESSION_COOKIE_SECURE` | `False` | `True` (HTTPS only) |
| `SESSION_COOKIE_SAMESITE` | `None` (attribute not sent) | `"Lax"` |
| `REMEMBER_COOKIE_SECURE` | `False` | `True` |
| `REMEMBER_COOKIE_SAMESITE` | `None` | `"Lax"` |
| `REMEMBER_COOKIE_DURATION` | 365 days | Shorter, e.g. 14 days (seconds or `timedelta`) |
| `JWT_COOKIE_SECURE` | `False` | `True` |
| `JWT_COOKIE_SAMESITE` | `None` | `"Lax"` |

Set them in the production environment rather than in code, as
`FLASK_<NAME>` (`FLASK_SESSION_COOKIE_SECURE=true`,
`FLASK_REMEMBER_COOKIE_DURATION=1209600`; `from_prefixed_env()` parses JSON):
browsers do not send `Secure` cookies over plain HTTP (some exempt
`localhost`), so a hard-coded `True` can break local login. The flags do not
depend on the request's scheme; what does (`request.is_secure`, `ProxyFix`)
is in `deployment.md`. `SameSite=Lax` reduces CSRF exposure but does not
replace `CSRFProtect`.

## Authorization: Authentication Is Not Enough

`@login_required` only proves who the user is. Every query that reads or
changes a user's data must also say whose data it may touch:

```python
# myapp/notes.py
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from .extensions import db
from .models import Note, User

bp = Blueprint("notes", __name__)


def admin_required(view):
    @login_required
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@bp.get("/notes")
@login_required
def list_notes():
    notes = db.session.scalars(
        select(Note).where(Note.owner_id == current_user.id).order_by(Note.id)
    ).all()
    return render_template("notes/list.html", notes=notes)


@bp.post("/notes/<int:note_id>/delete")
@login_required
def delete_note(note_id: int):
    # the owner filter is the authorization check: other users' notes are 404
    note = db.first_or_404(
        select(Note).where(Note.id == note_id, Note.owner_id == current_user.id)
    )
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "success")
    return redirect(url_for(".list_notes"))


@bp.get("/admin/users")
@admin_required
def list_users():
    users = db.session.scalars(select(User).order_by(User.id)).all()
    return render_template("admin/users.html", users=users)
```

- Return 404, not 403, for another user's row: a 403 confirms the id exists.
  Use 403 for "you are signed in but lack the role".
- Read roles from the database (`current_user` is loaded per request), never
  from the session or from a claim the client could have kept after a
  demotion.
- The same rule applies to the JWT API below: filter by
  `int(get_jwt_identity())`.

## Token Auth with Flask-JWT-Extended

Use Flask-JWT-Extended rather than a hand-rolled decorator around PyJWT's
`jwt.decode`: it already handles access and refresh tokens, expiry, headers
or cookies, the cookie CSRF check, fresh tokens and revocation
(`@jwt.token_in_blocklist_loader`).

Defaults on 4.7.4: access tokens expire after 15 minutes
(`JWT_ACCESS_TOKEN_EXPIRES`), refresh tokens after 30 days
(`JWT_REFRESH_TOKEN_EXPIRES`), algorithm HS256, tokens read from the
`Authorization: Bearer` header only (`JWT_TOKEN_LOCATION = ["headers"]`).
Set `JWT_TOKEN_LOCATION = ["headers", "cookies"]` to serve both modes from one
API; a token found in a cookie is CSRF-checked, one from the header is not.

### Header mode

```python
# myapp/api.py
from flask import Blueprint, abort, jsonify, make_response, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from .extensions import db
from .models import Note, User

bp = Blueprint("api", __name__)


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=254)
    password: str = Field(max_length=1024)


class NoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)


def authenticate() -> User:
    data = Credentials.model_validate(request.get_json())  # 422 handler: rest-apis.md
    email = data.email.strip().lower()
    user = db.session.scalar(select(User).where(User.email == email))
    if user is None or not user.check_password(data.password):
        abort(401, description="Invalid email or password.")
    return user


@bp.post("/token")
def issue_tokens():
    identity = str(authenticate().id)  # `sub` must be a string
    return {
        "access_token": create_access_token(identity=identity),
        "refresh_token": create_refresh_token(identity=identity),
    }


@bp.post("/token/refresh")
@jwt_required(refresh=True)
def refresh_access_token():
    return {"access_token": create_access_token(identity=get_jwt_identity())}


@bp.get("/me")
@jwt_required()
def me():
    user = db.get_or_404(User, int(get_jwt_identity()))
    return {"id": user.id, "email": user.email}


@bp.post("/notes")
@jwt_required()
def create_note():
    data = NoteIn.model_validate(request.get_json())
    note = Note(title=data.title, owner_id=int(get_jwt_identity()))
    db.session.add(note)
    db.session.commit()
    return {"id": note.id, "title": note.title}, 201
```

Setting `JWT_VERIFY_SUB = False` hides the "Subject must be a string" error
instead of fixing the token; do not.

### Cookie mode for browser clients

```python
# myapp/api.py (continued): cookie mode
@bp.post("/session")
def create_session():
    user = authenticate()
    identity = str(user.id)
    response = jsonify(id=user.id)
    set_access_cookies(response, create_access_token(identity=identity))
    set_refresh_cookies(response, create_refresh_token(identity=identity))
    return response


@bp.delete("/session")
def delete_session():
    response = make_response("", 204)
    unset_jwt_cookies(response)
    return response
```

`set_access_cookies` sets two cookies: `access_token_cookie` (`HttpOnly`, the
JWT) and `csrf_access_token` (readable by JavaScript). With
`JWT_COOKIE_CSRF_PROTECT = True`, the default, every `POST`, `PUT`, `PATCH`
and `DELETE` (`JWT_CSRF_METHODS`) that authenticates with the cookie must send
that cookie's value in the `X-CSRF-TOKEN` header; otherwise it fails with
"Missing CSRF token" or "CSRF double submit tokens do not match". `GET` is not
checked, so `GET` views must not change state. Refreshing in cookie mode sends
`csrf_refresh_token` the same way.

```js
const csrf = document.cookie.match(/(?:^|; )csrf_access_token=([^;]*)/)?.[1];
await fetch("/api/notes", {
  method: "POST",
  credentials: "same-origin",
  headers: { "Content-Type": "application/json", "X-CSRF-TOKEN": csrf },
  body: JSON.stringify({ title: "Groceries" }),
});
```

The API blueprint is exempt from Flask-WTF (factory above) because
Flask-JWT-Extended performs this check itself. Never turn off both.

### Error responses

Flask-JWT-Extended registers its own error handlers, so the app-level
`HTTPException` handler never sees token failures. Its defaults answer
`{"msg": "..."}`: 401 for a missing token or CSRF value or an expired token,
422 for a malformed token, a bad signature or a non-string `sub`. To give
clients the same `{"error", "message"}` shape as every other API error, and a
401 for every bad credential:

```python
# myapp/jwt_errors.py
from flask_jwt_extended import JWTManager


def register_jwt_errors(jwt: JWTManager) -> None:
    def unauthorized(message: str):
        return {"error": "Unauthorized", "message": message}, 401

    jwt.unauthorized_loader(unauthorized)  # no token, or no CSRF value
    jwt.invalid_token_loader(unauthorized)  # bad signature, wrong type, bad sub
    jwt.expired_token_loader(lambda header, payload: unauthorized("Token has expired"))
```

## Sessions or JWT?

| Client | Use |
| --- | --- |
| Server-rendered pages | Flask-Login sessions + `CSRFProtect` |
| JavaScript on the same origin | Flask-Login sessions + `X-CSRFToken`, or Flask-JWT-Extended cookie mode |
| Mobile app, CLI, another service, another origin | Flask-JWT-Extended header mode |
| Must revoke logins (log out everywhere, password change) | Server-side state either way: Flask's session is a signed cookie, so a copied cookie stays valid until it expires. Make `get_id()` return an alternative token such as `f"{id}:{session_version}"` and compare it in `user_loader`, or use `token_in_blocklist_loader` (Redis or the database) for JWTs |

## When to Use / When Not to Use

- **Do not** build your own login when the organization already has an
  identity provider: use OIDC (Authlib) and keep only the session handling
  from this file.
- **Do not** add Flask-JWT-Extended to a purely server-rendered app: sessions
  are simpler.
- **Do not** replace a working auth layer in a pinned legacy project (for
  example Flask-Security or Flask-User) unless the task is the migration.
