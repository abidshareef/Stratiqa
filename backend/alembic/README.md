# Migrations

Autogenerate after model changes:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

`alembic/env.py` reads the database URL from app settings and binds to
`app.models` metadata, so all 55+ tables are tracked automatically.
