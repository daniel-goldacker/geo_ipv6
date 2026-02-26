import json
from pathlib import Path

from api import app


def main() -> None:
    schema = app.openapi()
    output = Path("openapi.json")
    output.write_text(
        json.dumps(schema, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
