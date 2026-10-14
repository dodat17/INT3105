import json
import os
import random
from pathlib import Path


def load_data() -> dict:
    path = Path(os.environ.get("LOAD_TEST_TOKEN_FILE", "load_tests/tokens.json"))
    return json.loads(path.read_text(encoding="utf-8"))


def choose_user(data: dict) -> dict[str, str]:
    return random.choice(data["users"])
