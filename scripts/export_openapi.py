"""Write docs/openapi.yaml from the app's own OpenAPI schema, so the two never drift.

uv run python scripts/export_openapi.py
"""

from pathlib import Path

import yaml

from app.bootstrap.application import create_app

OPENAPI_FILE = Path(__file__).resolve().parents[1] / "docs" / "openapi.yaml"


def render() -> str:
    return yaml.safe_dump(create_app().openapi(), allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    OPENAPI_FILE.write_text(render(), encoding="utf-8")
