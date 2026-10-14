# API and technical decisions

- Runtime: Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL 16, pytest, Ruff,
  import-linter, and Locust.
- Identifiers: UUID values represented as strings at API and domain boundaries.
- Time: timezone-aware UTC internally; ISO 8601 values with offsets in JSON.
- Money: integer VND. VIP price is `base_price * 13 // 10`, avoiding floating point.
- Room deletion: intentionally outside the API because the authoritative endpoint table does not
  define `DELETE /rooms/{id}`. Admins can create and list rooms.
- Database setup: `create_all` is sufficient for this coursework scope; Alembic is not included.
- Error body: `{ "code": string, "message": string, "details": object }`.
- Out of scope: real payments, temporary seat holds, promotions, email, and refresh tokens.
