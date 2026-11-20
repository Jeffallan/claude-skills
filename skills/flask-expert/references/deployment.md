# Deployment and Background Jobs (Flask 3.1)

Running a Flask app in production: release order, gunicorn, a reverse proxy
with `ProxyFix`, production config, Windows, and background work with Celery,
RQ and APScheduler under several workers. Pinned: Flask 3.1.3, gunicorn
27.0.1, waitress 3.0.2, Celery 5.7.0, RQ 3.0.0, APScheduler 3.11.3 (not the
4.x pre-releases), redis-py 8.1.0, Python 3.11+. The factory, `wsgi.py` and
logging setup are in `app-structure.md`; migrations in `database.md`; cookie
flags in `authentication.md`.

## Common Mistakes

| Mistake | Why it breaks | Fix |
| --- | --- | --- |
| `db.create_all()` in `create_app()`, often wrapped in `try/except Exception` ("raced with another worker") | Every gunicorn worker (and every Celery/RQ worker and CLI call) runs it at boot; it never alters existing tables, and the `except` hides real errors | `flask db upgrade` once per release, before workers start (`database.md`) |
| `SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)` | Each worker process generates its own key: sessions and CSRF tokens fail whenever a request lands on another worker | One key from the environment, shared by every process (`app-structure.md`) |
| `app = create_app()` at module level in the package | Every importer (Celery and RQ workers, `flask db upgrade`, tests) builds an app and runs its side effects, such as starting a scheduler | Module-level apps only in entry points: `wsgi.py`, `make_celery.py`, `rq_worker.py` |
| APScheduler started in `create_app()` | Runs once per gunicorn worker, plus in every Celery worker and CLI command: 4 workers send the nightly email 4 times | cron + a `flask` command, or the Redis-lease scheduler below |
| Task or job code calls `db.session` / `current_app` directly | Workers have no request, so no app context: `RuntimeError: Working outside of application context` | Celery `FlaskTask`, RQ `FlaskWorker`, scheduler wrapper (all below) |
| Enqueueing before `commit()`, or passing ORM objects to a task | The worker may run before the row exists; model instances do not serialize and belong to the request's session | Commit, then pass the id |
| No `ProxyFix`, or hop counts larger than the real number of proxies | Missing: `request.scheme` is `http`, external URLs and redirects use `http://`. Too many: the client-supplied `X-Forwarded-For` entry becomes `request.remote_addr` | `ProxyFix` with each header's count equal to the proxies that write it |
| `--forwarded-allow-ips="*"` to make HTTPS detection work | gunicorn then trusts `X-Forwarded-Proto` from any peer, and it never changes `REMOTE_ADDR` | Leave gunicorn's default; `ProxyFix` in the app is the one source of truth |
| `app.run(debug=True)`, `flask run` or `FLASK_DEBUG=1` on a server | Single-process development server; the debugger executes arbitrary code | gunicorn (or waitress), `FLASK_DEBUG` unset |
| `gunicorn` on Windows | `ModuleNotFoundError: No module named 'fcntl'` | waitress, or gunicorn in Docker/WSL |

## Release Order

```bash
# once per release, before any new worker serves traffic
flask --app myapp db upgrade
# then start (or gracefully reload) the web server and the job workers
gunicorn -c gunicorn.conf.py wsgi:app
celery -A make_celery worker --loglevel INFO   # or: python rq_worker.py
```

With a single container, the entrypoint can do both:
`sh -c "flask --app myapp db upgrade && exec gunicorn -c gunicorn.conf.py wsgi:app"`
(`exec` makes gunicorn PID 1, so it receives the stop signal and shuts down
gracefully). With several replicas, run the upgrade once as a release job
(a CI step, a Kubernetes `Job`, a platform release phase), not in every
replica's entrypoint. Never from the factory.

## gunicorn

```python
# gunicorn.conf.py: read by `gunicorn -c gunicorn.conf.py wsgi:app`
import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")  # nginx proxies here
workers = int(os.environ.get("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"  # or "gthread" with threads = 4 for I/O-bound views
timeout = 30  # a worker silent this long is killed and replaced
graceful_timeout = 30  # time to finish in-flight requests on reload or stop
max_requests = 1000  # recycle workers to contain slow memory leaks
max_requests_jitter = 100  # so the workers do not all restart together
accesslog = "-"  # stdout
errorlog = "-"  # stderr
```

- **Workers are processes.** Nothing in module globals is shared between
  them: no in-memory caches, rate limits or job queues you expect every
  worker to see. Shared state goes in the database or Redis.
- **Worker count:** `2 × cores + 1` is the usual starting point; measure and
  adjust. In containers `cpu_count()` reports the host's CPUs, not the
  container's limit, so set `WEB_CONCURRENCY` explicitly.
- **Worker class:** `sync` handles one request per process. For views that
  wait on I/O (HTTP APIs, slow queries) use `gthread` with `threads`
  (gunicorn switches to `gthread` itself when `threads > 1`); the app must
  then be thread-safe, which `db.session` and `g` already are.
- **`timeout`** kills requests that run longer: move slow work to a task
  queue instead of raising it. Keep nginx's `proxy_read_timeout` (default
  60 s) above it.
- **Do not set `preload_app`** when `wsgi.py` starts threads (the scheduler
  below): the app is built in the master before forking, and threads do not
  survive `fork()`.
- **Reload:** `kill -HUP <master pid>` (or `systemctl reload`) starts new
  workers with the new code and stops the old ones gracefully.

## Behind a Reverse Proxy

TLS ends at nginx (`listen 443 ssl`, port 80 redirecting to HTTPS). Raise
`client_max_body_size` (default 1m; nginx answers bigger bodies with its own
HTML 413) to at least `MAX_CONTENT_LENGTH`, and optionally serve `/static/`
from nginx with an `alias`. The proxied location needs only these lines:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

gunicorn sees every request as plain HTTP from `127.0.0.1`. `ProxyFix`
(in the factory below) restores the client's scheme and address from the
headers nginx sets. Each count says how many values of **that header** to
trust, so count the proxies that write each header, not the proxies in total:

- `x_for=N` takes the N-th value **from the right** of `X-Forwarded-For`.
  nginx appends the real peer address to whatever the client sent, so with
  one proxy the last entry is trustworthy and the ones before it are not.
  With `x_for=2` behind a single nginx, `request.remote_addr` becomes a value
  the client typed: rate limits, IP allowlists and audit logs are spoofed.
- `x_proto=N` works the same way on `X-Forwarded-Proto`, but the config above
  **replaces** that header (`$scheme`) instead of appending, so it only ever
  has one value: `x_proto=1`.
- Load balancer (TLS ends there) in front of nginx: the balancer and nginx
  both append to `X-Forwarded-For`, so `x_for=2`. nginx now receives plain
  HTTP, so pass the balancer's header on instead of `$scheme`:
  `proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;` and keep
  `x_proto=1`. With `x_proto=2` there is only one value to read, `ProxyFix`
  ignores the header and the scheme stays `http`.
- Add `x_host=N` / `x_prefix=N` only if the proxy sets `X-Forwarded-Host` /
  `X-Forwarded-Prefix`; this config sends `Host` directly.
- Only enable it when a proxy is really in front: without one, any client
  can send the headers. Bind gunicorn to `127.0.0.1` or a private network.

gunicorn's own `forwarded_allow_ips` (default `127.0.0.1,::1`) only sets the
scheme; leave it alone and let `ProxyFix` decide, which also works under
waitress and in tests.

## The Production Factory

The factory from `app-structure.md` gains the deployment pieces: `ProxyFix`
driven by config, a Redis client, an RQ queue and Celery. Add `"REDIS_URL"` to
`REQUIRED_SETTINGS`, import `ProxyFix` (`werkzeug.middleware.proxy_fix`),
`Redis` (`redis`), `Queue` (`rq`) and `celery_init_app` (`.tasks`). This
replaces the body after the config checks in `create_app()` (keep
`register_error_handlers(app)` and the CLI registration from
`app-structure.md`; `views.bp` stands for your blueprints):

```python
# Trusted values per header (FLASK_PROXY_X_FOR, FLASK_PROXY_X_PROTO); 0 = none.
x_for = app.config.get("PROXY_X_FOR", 0)
x_proto = app.config.get("PROXY_X_PROTO", 0)
if x_for or x_proto:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=x_for, x_proto=x_proto)

redis_url = app.config["REDIS_URL"]
app.config.setdefault(
    "CELERY",
    {"broker_url": redis_url, "result_backend": redis_url, "task_ignore_result": True},
)
db.init_app(app)
migrate.init_app(app, db)
app.extensions["redis"] = Redis.from_url(redis_url)
app.extensions["rq"] = Queue(connection=app.extensions["redis"])
celery_init_app(app)
app.register_blueprint(views.bp)
```

Nothing here connects to Redis or the database: clients connect on first
use, so building the app in a test or a CLI command needs neither running.

```python
# myapp/views.py
import os

from flask import Blueprint

from .extensions import db
from .models import Report
from .tasks import build_report_task

bp = Blueprint("main", __name__)


@bp.get("/health")
def health() -> dict[str, object]:
    # Liveness only: no database query, so a database outage does not get every
    # web container restarted. The pid shows which worker answered.
    return {"status": "ok", "pid": os.getpid()}


@bp.post("/reports")
def request_report() -> tuple[dict[str, int], int]:
    report = Report()
    db.session.add(report)
    db.session.commit()  # commit first: the worker loads the row by id
    build_report_task.delay(report.id)
    return {"id": report.id}, 202
```

For a readiness check that does touch the database, use the `check-db`
command from `app-structure.md`.

## Production Configuration

The same values for every process (web, Celery, RQ, scheduler), from the
service manager's environment file, the container platform or a secret store:

```bash
# /etc/myapp/env (systemd EnvironmentFile: no inline comments)
FLASK_SECRET_KEY=generated-once-and-stored-in-your-secret-manager
FLASK_SQLALCHEMY_DATABASE_URI=postgresql+psycopg://myapp:secret@db/myapp
FLASK_REDIS_URL=redis://localhost:6379/0
FLASK_PROXY_X_FOR=1
FLASK_PROXY_X_PROTO=1
FLASK_SESSION_COOKIE_SECURE=true
FLASK_SESSION_COOKIE_SAMESITE=Lax
LOG_LEVEL=INFO
WEB_CONCURRENCY=4
```

- `from_prefixed_env()` parses the values as JSON: `1` is an `int`, `true` a
  `bool`. Add the `REMEMBER_COOKIE_*` / `JWT_COOKIE_*` flags from the table in
  `authentication.md` if the app uses them. The cookie flags come from these
  settings alone, whatever the request's scheme. `ProxyFix` is what makes
  `request.is_secure`, `url_for(..., _external=True)` and redirects see
  HTTPS; without it they say `http`, and checks that only run on HTTPS (such
  as Flask-WTF's strict `Referer` check) are silently skipped.
- **Logging:** the `dictConfig` in `wsgi.py` (`app-structure.md`) writes to
  stdout/stderr, never to files in the app directory; journald or the
  container runtime collects it, with gunicorn's `accesslog`/`errorlog`.

Under systemd, the `[Service]` section of the web unit (with `User=`,
`WorkingDirectory=/srv/myapp` and `Restart=on-failure`) needs:

```ini
EnvironmentFile=/etc/myapp/env
ExecStart=/srv/myapp/.venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
```

## Windows

gunicorn does not run on Windows: it imports `fcntl`, a Unix-only module.

- **waitress** is a pure-Python production server that runs on Windows:
  `waitress-serve --listen=127.0.0.1:8080 wsgi:app`, or
  `waitress-serve --listen=127.0.0.1:8080 --call myapp:create_app` (calls the
  factory; settings come from the environment). It is one process with
  threads (`--threads`, default 4). Keep `ProxyFix` as the source of truth and
  leave waitress's own `--trusted-proxy` options unset.
- **Docker or WSL** run the real Linux stack (gunicorn, the Celery prefork
  pool, RQ's forking worker), which is the closest match to production.
- **Celery** has not supported Windows since 4.x (Celery FAQ). For local
  development only, swap the default prefork pool for one that does not
  start child processes:
  `celery -A make_celery worker --pool=solo` (or `--pool=threads`).
- **RQ's** default `Worker` forks a process per job, and Windows has no
  `fork()`. For local experiments, base `FlaskWorker` (below) on
  `rq.SimpleWorker`, which runs jobs in-process; run the real worker under
  WSL or Docker.

## Background Jobs

| Need | Use |
| --- | --- |
| Run something later, retries, rate limits, workflows, several brokers | Celery |
| Run something later, Redis already there, few features needed | RQ |
| Run something on a schedule | cron or a systemd timer calling a `flask` command; Celery beat if Celery is already used; APScheduler with a lease (below) |
| Work that finishes in well under a second | Do it in the request |

A `threading.Thread` started from a view is not a job queue: it dies with the
worker (gunicorn recycles workers), has no retries, and runs without an app
context; nor is a database table polled by every worker. The examples share
one plain function that needs an app context because it uses `db.session`:

```python
# myapp/jobs.py
from sqlalchemy import delete

from .extensions import db
from .models import Report


def build_report(report_id: int) -> None:
    """The work itself: plain code that needs an app context for db.session."""
    report = db.session.get(Report, report_id)
    if report is None:
        return
    report.status = "done"
    db.session.commit()


def purge_done_reports() -> None:
    db.session.execute(delete(Report).where(Report.status == "done"))
    db.session.commit()
```

Each runner below pushes a fresh app context per job, so each job gets its
own session and teardown.

### Celery

Flask's documented pattern: a `Task` subclass whose `__call__` runs inside
`app.app_context()`, and `@shared_task` so tasks do not import an app.

```python
# myapp/tasks.py
from celery import Celery, Task, shared_task
from flask import Flask

from .jobs import build_report


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


@shared_task
def build_report_task(report_id: int) -> None:
    build_report(report_id)
```

```python
# make_celery.py: the Celery worker's entry point, like wsgi.py for gunicorn
from myapp import create_app

flask_app = create_app()
celery_app = flask_app.extensions["celery"]
```

Run `celery -A make_celery worker --loglevel INFO`. Results are ignored by
default (`task_ignore_result`); mark tasks whose return value you read with
`@shared_task(ignore_result=False)`. In tests, pass
`CELERY={"task_always_eager": True, "task_eager_propagates": True}` in
`test_config`: `.delay()` then runs the task inline, still through
`FlaskTask`.

### RQ

RQ calls plain functions by import path. A small worker entry point runs each
job inside its own app context:

```python
# rq_worker.py: run with `python rq_worker.py`
from rq import Worker

from myapp import create_app

app = create_app()


class FlaskWorker(Worker):
    """Runs every job inside a fresh app context, like Celery's FlaskTask."""

    def perform_job(self, *args, **kwargs) -> bool:
        with app.app_context():
            return super().perform_job(*args, **kwargs)


if __name__ == "__main__":
    FlaskWorker(["default"], connection=app.extensions["redis"]).work()
```

`perform_job` runs in the forked child that executes the job, so the context
is pushed and torn down per job. `rq worker -w rq_worker.FlaskWorker --url
redis://...` uses the same class from the CLI. Enqueue after the commit:

```python
# myapp/views.py with RQ instead of Celery: enqueue the plain function
current_app.extensions["rq"].enqueue(build_report, report.id)
```

### Scheduled jobs

The simplest correct schedule is cron (or a systemd timer) running a `flask`
command: one process, one run, an app context provided by the `flask`
executable. Here `purge-reports` is a `@click.command` that calls
`purge_done_reports()`, registered as in `app-structure.md`:

```bash
# crontab of the app user: 03:00 server time daily, same environment as the web app
0 3 * * * cd /srv/myapp && set -a && . /etc/myapp/env && set +a && .venv/bin/flask --app myapp purge-reports
```

APScheduler runs once per process that starts it, so never in `create_app()`
(Common Mistakes). If the schedule has to live in the app, start the
scheduler from `wsgi.py` only and let a Redis lease decide which process
runs each job. Every worker keeps trying, so when the lease holder dies
another worker takes over within about one lease period.

```python
# myapp/scheduler.py
from collections.abc import Callable, Iterable
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.base import BaseTrigger
from flask import Flask
from redis import Redis
from redis.exceptions import LockError

LEASE_SECONDS = 30


class Leader:
    """A Redis lease that at most one process holds at a time."""

    def __init__(self, redis_client: Redis, name: str = "myapp:scheduler") -> None:
        # thread_local=False: jobs run on APScheduler's pool threads
        self.lock = redis_client.lock(name, timeout=LEASE_SECONDS, thread_local=False)

    def check(self) -> bool:
        """Renew the lease if this process holds it, otherwise try to take it."""
        try:
            return self.lock.reacquire()
        except LockError:  # never held, expired, or held by another process
            return self.lock.acquire(blocking=False)


def start_scheduler(
    app: Flask, schedule: Iterable[tuple[Callable[[], None], BaseTrigger]]
) -> BackgroundScheduler:
    """Start in every worker; each job runs only in the current lease holder."""
    leader = Leader(app.extensions["redis"])

    def run_if_leader(job: Callable[[], None]) -> None:
        if leader.check():
            with app.app_context():
                job()

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        leader.check,
        "interval",
        seconds=LEASE_SECONDS // 3,
        next_run_time=datetime.now(timezone.utc),
    )
    for job, trigger in schedule:
        scheduler.add_job(run_if_leader, trigger, args=[job], name=job.__name__)
    scheduler.start()
    return scheduler
```

```python
# wsgi.py: only the web entry point starts the scheduler
from apscheduler.triggers.cron import CronTrigger

from myapp import create_app
from myapp.jobs import purge_done_reports
from myapp.scheduler import start_scheduler

SCHEDULE = [(purge_done_reports, CronTrigger(hour=3, minute=0, timezone="UTC"))]

app = create_app()
start_scheduler(app, SCHEDULE)
```

- Keep the `dictConfig` logging setup from `app-structure.md` above these
  lines.
- The lease is not released when its holder exits, so a job due in the next
  30 s or so is skipped (APScheduler does not retry it). This is routine,
  not rare: `max_requests` recycles the holder every thousand-odd requests,
  and every `kill -HUP` reload replaces all workers. A lease can also change
  hands mid-run. Make jobs idempotent, and use a dedicated
  scheduler or cron when a missed or doubled run matters.
- Give cron triggers an explicit `timezone`: a `CronTrigger` built without
  one uses the machine's local zone, not the scheduler's.
