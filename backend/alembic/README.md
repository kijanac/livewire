# Alembic migrations

To create a new migration:

```
uv run alembic revision --autogenerate -m "description"
```

Review the generated file under `alembic/versions/` before committing —
autogenerate doesn't always capture index renames, server defaults, or check
constraints correctly.

To apply migrations against your local DB:

```
uv run alembic upgrade head
```

`init_db()` runs `alembic upgrade head` programmatically on app startup, so
the dev/prod servers self-migrate. Pre-Alembic legacy DBs are detected and
stamped at head on first run.
