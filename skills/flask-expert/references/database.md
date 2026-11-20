# Database (Flask-SQLAlchemy 3.1, SQLAlchemy 2.x)

Typed models, `select()` queries, pagination, eager loading, transactions and
Flask-Migrate. Pinned: Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.9, Flask-Migrate
4.1.0, Python 3.11+. The extension setup (`class Base(DeclarativeBase)`,
`db = SQLAlchemy(model_class=Base)`, `db.init_app(app)` and
`migrate.init_app(app, db)` in the factory) is in `app-structure.md`.

## Common Mistakes

| Mistake | Why it breaks | Fix |
| --- | --- | --- |
| `id = db.Column(db.Integer, primary_key=True)` models in new code | Untyped; every non-key column is nullable unless you remember `nullable=False`; editors and mypy see `Any` | `id: Mapped[int] = mapped_column(primary_key=True)`; nullability comes from the annotation |
| `Product.query.get(id)`, `Product.query.filter_by(...)` in new code, or suggested in review | `Query` is SQLAlchemy's legacy API. `Query.get()` emits `LegacyAPIWarning`, a `DeprecationWarning` subclass, so it fails under `-W error::DeprecationWarning` | `db.session.get(Product, id)`, `db.session.scalars(select(Product).where(...))`, `db.get_or_404`, `db.paginate` |
| `db.create_all()` at import time or in `create_app()`, sometimes inside `try/except Exception` | Never alters an existing table, so new columns never arrive; every worker races to run it; the `except` hides the race and any real error | Flask-Migrate: `flask db migrate`, review, `flask db upgrade` once per deploy. `create_all()` only in tests |
| `db.session.execute(text("ALTER TABLE ..."))` at startup | Runs on every boot, fails on the second, no record of what ran, no downgrade | A reviewed Alembic migration |
| `to_dict()` reads a relationship (`self.supplier.name`) and a list view calls it per row | Lazy loading: one extra `SELECT` per row (N+1); invisible with 5 test rows, slow with 500 | `selectinload`/`joinedload` in the list query; `lazy="raise_on_sql"` so a missed one raises in tests |
| `default=datetime.utcnow` | Deprecated in Python 3.12; returns a naive datetime | `server_default=func.now()` or `default=lambda: datetime.now(UTC)`, with `DateTime(timezone=True)` |
| `db.paginate(stmt)` or `Model.query.paginate()` without `max_per_page` | Neither caps `per_page` by default: in 3.1.1 both pass `max_per_page=None` despite the "defaults to 100" in their docstrings (2.5.x has no cap either), so `?per_page=1000000` loads the whole table | Always pass `max_per_page=` |
| No `db.session.rollback()` after an `IntegrityError` | The session stays in the failed transaction; its next statement raises `PendingRollbackError` | `try: commit()` / `except IntegrityError: rollback()`, then return 409 |
| `postgresql://` URL with only `psycopg2-binary` installed | SQLAlchemy 2.1 maps `postgresql://` to psycopg 3: `ModuleNotFoundError: No module named 'psycopg'` | Install `psycopg[binary]`, or write `postgresql+psycopg2://` |

## Check the Installed Versions First

Before writing data-layer code in an existing project, read the pins in
`requirements*.txt`, `pyproject.toml` or the lockfile (`uv.lock`,
`poetry.lock`), or ask the environment:

```bash
python -c "from importlib.metadata import version as v; print(v('flask-sqlalchemy'), v('sqlalchemy'))"
```

| API | FSA 2.5.x + SA 1.3 | FSA 2.5.x + SA 1.4 | FSA 3.0 | FSA 3.1 + SA 2.x |
| --- | --- | --- | --- | --- |
| `M.query`, `M.query.get(pk)`, `M.query.paginate()`, `M.query.get_or_404(pk)` | Yes | Yes | Yes (legacy) | Yes (legacy) |
| `db.session.execute(db.select(M)).scalars()`, `.scalar_one_or_none()` | No | Yes | Yes | Yes |
| `db.session.get(M, pk)` | No | Yes | Yes | Yes |
| `db.paginate`, `db.get_or_404`, `db.first_or_404`, `db.one_or_404` | No | No | Yes | Yes |
| `DeclarativeBase`, `mapped_column` with `SQLAlchemy(model_class=Base)` | No | No (`ImportError`) | No | Yes |

- **Pinned to Flask-SQLAlchemy 2.5.x:** keep the project's `db.Column` models
  and match the surrounding query code. Use `M.query.paginate(max_per_page=100)`
  and `M.query.get_or_404()`, the only pagination and 404 helpers there. With
  SQLAlchemy 1.4, new queries can use `db.session.execute(db.select(...))` and
  `db.session.get()`, which carry over unchanged to 3.x. With SQLAlchemy older
  than 1.4, use only `M.query` and `M.query.get()`: `Session.get()` and
  `select(Model)` need 1.4. Never import a 3.x-only API into a 2.x project.
- **Upgrading is its own task:** Flask-SQLAlchemy 3.1 needs SQLAlchemy ≥ 2.0.16
  and Flask ≥ 2.2.5; 2.5.1 cannot even be imported on Flask 3.0+ (it imports
  the removed `flask._app_ctx_stack`). Bump Flask-SQLAlchemy and SQLAlchemy
  together, then convert models and queries with the tables below and run the
  tests with `-W error::DeprecationWarning`.

## Models: `DeclarativeBase` + `Mapped`

Give `Base` in `extensions.py` (`app-structure.md`) a constraint naming
convention (`from sqlalchemy import MetaData`). Alembic can only drop or alter
constraints that have names, and Flask-Migrate renders migrations in batch
mode (the default since 4.0), so on SQLite a change its `ALTER TABLE` cannot
make is done by copying the table, which needs those names.

```python
class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
```

```python
# myapp/models.py
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class Supplier(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    email: Mapped[str | None] = mapped_column(String(254))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    products: Mapped[list["Product"]] = relationship(
        back_populates="supplier", lazy="raise_on_sql"
    )


class Product(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    in_stock: Mapped[bool] = mapped_column(default=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("supplier.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    supplier: Mapped[Supplier] = relationship(
        back_populates="products", lazy="raise_on_sql"
    )
```

- **Subclass `db.Model`**, which Flask-SQLAlchemy builds from your `Base`; it
  derives `__tablename__` from the class name in snake case (`OrderItem` →
  `order_item`), which is what `ForeignKey("supplier.id")` refers to.
- **The annotation sets type and nullability.** `Mapped[str]` is `NOT NULL`,
  `Mapped[str | None]` (or `Optional[str]`) is `NULL`. Pass a SQL type to
  `mapped_column()` only to refine it: `String(120)` for a length, `Text`,
  `Numeric(10, 2)` for money (`Mapped[Decimal]`, never `float`).
- **Defaults:** `default=` is applied by the ORM in Python at `INSERT`;
  `server_default=` is part of the table DDL, so it also covers raw SQL and
  existing rows when a migration adds a `NOT NULL` column. For timestamps use
  `server_default=func.now()` (the database clock) or
  `default=lambda: datetime.now(UTC)` (`from datetime import UTC`, Python
  3.11+). `onupdate=func.now()` sets the column on every ORM `UPDATE`.
- **Relationships:** `back_populates` on both sides, so each side is explicit
  and typed (no `backref` creating an attribute you cannot see). `lazy=` is
  covered under eager loading below.
- **SQLite caveat:** `DateTime(timezone=True)` values come back naive there
  (PostgreSQL's `timestamptz` returns aware ones) and `Numeric` has no native
  `DECIMAL`; see the SQLite table in `testing.md`.

## Queries: `select()` and the Session

```python
# myapp/queries.py
from sqlalchemy import func, select

from .extensions import db
from .models import Product, Supplier


def find_supplier_by_name(name: str) -> Supplier | None:
    stmt = select(Supplier).where(Supplier.name == name)
    return db.session.execute(stmt).scalar_one_or_none()


def products_in_stock(supplier_id: int) -> list[Product]:
    stmt = (
        select(Product)
        .where(Product.supplier_id == supplier_id, Product.in_stock.is_(True))
        .order_by(Product.name)
    )
    return list(db.session.scalars(stmt))


def count_products() -> int:
    return db.session.scalar(select(func.count()).select_from(Product)) or 0
```

- `db.session.scalars(stmt)` yields model objects; `db.session.execute(stmt)`
  yields `Row` tuples, which is what you want when selecting columns
  (`select(Product.id, Product.name)`). `db.select` is the same `select`.
- `scalar_one_or_none()` returns one object or `None` and raises
  `MultipleResultsFound` if there are more, which catches a missing unique
  constraint; `scalar_one()` also raises `NoResultFound` on zero rows.
- In a `select()` that joins several entities, `filter_by(name=...)` searches
  all of them in SQLAlchemy 2.1 and raises `AmbiguousColumnError` when more
  than one has that column. Use `where(Product.name == ...)` in joins.
- Column expressions, `like()` and `ilike()` send values as bound
  parameters. Only `text()` takes raw SQL: pass values with `:name`
  placeholders, never f-strings.

| Legacy (`Model.query`) | SQLAlchemy 2.x / Flask-SQLAlchemy 3.1 |
| --- | --- |
| `Product.query.get(pk)` | `db.session.get(Product, pk)` |
| `Product.query.get_or_404(pk)` | `db.get_or_404(Product, pk)` |
| `Product.query.filter_by(sku=s).first()` | `db.session.scalars(select(Product).filter_by(sku=s)).first()` |
| `Product.query.filter_by(sku=s).first_or_404()` | `db.first_or_404(select(Product).filter_by(sku=s))` |
| `Product.query.filter(...).one()` | `db.session.execute(select(Product).where(...)).scalar_one()` |
| `Product.query.order_by(Product.name).all()` | `db.session.scalars(select(Product).order_by(Product.name)).all()` |
| `Product.query.count()` | `db.session.scalar(select(func.count()).select_from(Product))` |
| `Product.query.paginate(page=p, per_page=n)` | `db.paginate(select(Product).order_by(...), max_per_page=100)` |

## Views: `get_or_404`, `paginate`, Eager Loading

```python
# myapp/api.py
from decimal import Decimal

from flask import Blueprint, abort, request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from .extensions import db
from .models import Product, Supplier

bp = Blueprint("api", __name__)


def product_to_dict(product: Product) -> dict:
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "price": str(product.price),
        "supplier": product.supplier.name,  # caller must load Product.supplier
    }


@bp.get("/products")
def list_products():
    stmt = (
        select(Product)
        .options(joinedload(Product.supplier))  # many-to-one: JOIN, same query
        .order_by(Product.id)  # a stable order, or rows repeat across pages
    )
    page = db.paginate(stmt, max_per_page=100)  # reads ?page= and ?per_page=
    return {
        "items": [product_to_dict(p) for p in page.items],
        "page": page.page,
        "per_page": page.per_page,
        "pages": page.pages,
        "total": page.total,
    }


@bp.get("/suppliers")
def list_suppliers():
    stmt = (
        select(Supplier)
        .options(selectinload(Supplier.products))  # collection: one SELECT ... IN
        .order_by(Supplier.name)
    )
    return [
        {"id": s.id, "name": s.name, "products": [p.sku for p in s.products]}
        for s in db.session.scalars(stmt)
    ]


@bp.get("/products/<int:product_id>")
def get_product(product_id: int):
    product = db.get_or_404(
        Product, product_id, options=[joinedload(Product.supplier)]
    )
    return product_to_dict(product)
```

- `db.paginate(stmt)` reads `page` and `per_page` from the query string
  (defaults 1 and 20), issues the page query plus one `COUNT`, and with the
  default `error_out=True` returns 404 for a non-integer or out-of-range page
  instead of an empty 200. Pass `count=False` to skip the `COUNT` on very large
  tables. The `Pagination` object also has `has_next`, `next_num`, `prev_num`
  and `iter_pages()` for HTML pagers.
- `db.get_or_404(Model, pk, **kwargs)` passes extra keyword arguments to
  `session.get()` (3.1+), so `options=[...]` eager-loads in the same query.
  `session.get()` returns an object that is already in the session without
  querying, and then the options do not run; in a fresh request session that
  only happens after you loaded the object earlier in the same request.
- `db.first_or_404(stmt)` and `db.one_or_404(stmt)` do the same for a `select()`.
- Offset pagination gets slower deep into a large table and shifts when rows
  are inserted. For infinite scroll or feeds, use keyset pagination
  (`where(Product.id > last_seen_id).order_by(Product.id).limit(n)`).

## Eager Loading and the N+1 Guard

| Loader | SQL | Use for |
| --- | --- | --- |
| `joinedload(Product.supplier)` | `LEFT OUTER JOIN` in the same query | Many-to-one or one-to-one, read on every row |
| `selectinload(Supplier.products)` | One extra `SELECT ... WHERE supplier_id IN (...)` per relationship | One-to-many and many-to-many collections |
| `lazy="raise_on_sql"` on the relationship | Raises `InvalidRequestError` instead of emitting a lazy `SELECT` | The default for every relationship in new models |
| `.options(raiseload("*", sql_only=True))` on one query | Same as `raise_on_sql`, for that query only (plain `raiseload("*")` acts like `lazy="raise"`) | Existing models where changing `lazy=` would break other callers |

`joinedload` on a collection repeats each parent row once per child, and a
`select()` that does it needs `.unique()` on the result. Use `selectinload`
for collections. `lazy="raise_on_sql"` still allows a many-to-one that can be
resolved from the session's identity map without SQL, such as
`product.supplier` after `commit()` expired it while that supplier object is
still in the session; `lazy="raise"` raises there too. (Right after you assign
a relationship, neither raises: the value is already set.) One consequence of
either: a collection that was not loaded cannot be appended to, so build
children from the many side (`Product(supplier=supplier)`) or load the
collection first.

Prove there is no N+1 in a test: count the statements a request issues and
assert the count does not grow with the number of rows.

```python
# tests/test_queries.py: count the SQL statements a request issues
from contextlib import contextmanager

from sqlalchemy import event

from myapp.extensions import db


@contextmanager
def count_statements(engine):
    statements: list[str] = []

    def before_cursor_execute(conn, cursor, statement, params, context, many):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


def test_product_list_query_count_is_constant(app, client, add_products):
    with app.app_context():  # db.engine needs one; the testing.md fixture pushes none
        engine = db.engine
    add_products(3)  # your fixture: commits n more products, each with a supplier
    with count_statements(engine) as small:
        client.get("/api/products")
    add_products(27)
    with count_statements(engine) as large:
        client.get("/api/products")
    assert len(small) == len(large)  # 2: page query + COUNT
```

## Writes, Transactions and the Request Session

```python
class ProductIn(BaseModel):  # Pydantic; 422 handler in rest-apis.md
    model_config = ConfigDict(extra="forbid")

    sku: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


@bp.post("/suppliers/<int:supplier_id>/products")
def create_product(supplier_id: int):
    supplier = db.get_or_404(Supplier, supplier_id)
    data = ProductIn.model_validate(request.get_json())
    product = Product(
        **data.model_dump(),
        supplier=supplier,  # not supplier.products.append(): not loaded
    )
    db.session.add(product)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, description="SKU already exists.")
    return product_to_dict(product), 201
```

- **`db.session` is one session per app context.** Flask-SQLAlchemy calls
  `db.session.remove()` when the context ends (end of every request, CLI
  command, or `with app.app_context():` block). That closes the session:
  anything not committed is rolled back and the connection goes back to the
  pool. Nothing commits automatically, so call `db.session.commit()` once the
  unit of work is complete; an exception before it writes nothing.
- **Objects are detached after the request.** Never keep ORM objects in
  globals or hand them to threads or task queues: pass the primary key.
- **After `commit()`, attributes are expired** (`expire_on_commit=True`): the
  next attribute access reloads the row with one `SELECT` (the primary key
  itself was set at flush, so the product's id is already known).
- **One unit of work, one `commit()`**, with `rollback()` after a failed one
  (Common Mistakes); call `db.session.flush()` when you need generated IDs
  before it.

## Schema Changes: Flask-Migrate

Never `create_all()` or `ALTER TABLE` at startup (Common Mistakes). The
factory only calls `migrate.init_app(app, db)` (see `app-structure.md`).
The schema changes through migration scripts in `migrations/`, committed to
version control:

```bash
flask --app myapp db init                          # once: creates migrations/
flask --app myapp db migrate -m "add product sku"  # autogenerate a revision
# read migrations/versions/<rev>_add_product_sku.py and fix it before applying
flask --app myapp db upgrade                       # apply to the database
flask --app myapp db downgrade                     # undo the last revision
flask --app myapp db check                         # CI: fails if models changed without a migration
```

Review every autogenerated revision before applying it. Autogenerate:

- **Cannot see renames.** A renamed table or column comes out as drop plus
  add, which deletes the data. Rewrite it with `op.rename_table()` or
  `op.alter_column()` and its `new_column_name=` argument.
- **Ignores `server_default` changes** (off by default), and cannot track
  unnamed constraints (hence the naming convention) or `Enum` changes on
  databases without a native enum type.
- **Does not backfill.** Adding a `NOT NULL` column to a table with rows needs
  a `server_default`, or add it nullable, fill it with `op.execute(...)`, then
  alter it to `NOT NULL`.

Run `flask db upgrade` once per release, before the new code serves traffic
(release order in `deployment.md`). To adopt migrations on a database whose
tables were made by `create_all()`, generate the first revision against
an empty database, then mark existing databases as current instead of
upgrading them:

```bash
FLASK_SQLALCHEMY_DATABASE_URI=sqlite:///empty.db flask --app myapp db migrate -m "initial schema"
flask --app myapp db stamp head    # on each existing database
```

Running `flask db upgrade` there instead fails because the tables already
exist. Flask-SQLAlchemy resolves a relative SQLite path against the
`instance/` folder, so the scratch database is `instance/empty.db`.

`db.create_all()` belongs only in tests, on a throwaway database inside the
test app's context. Fixture patterns are in `testing.md`.

## When to Use / When Not to Use

- **Use plain SQLAlchemy** (`create_engine` + `sessionmaker`) for code that
  runs without a Flask app, such as a shared library or a standalone script.
  A Flask CLI command or task worker that already builds the app can use
  `db.session` inside `with app.app_context():`.
- **Do not use `db.paginate`** for exports or feeds over large tables: stream
  with `db.session.scalars(stmt.execution_options(yield_per=1000))` or use
  keyset pagination.
