from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.services.workspace_reset import reset_workspace_to_blueprint


def main() -> int:
    with SessionLocal() as db:
        servers = reset_workspace_to_blueprint(db)

    print("Workspace reset complete.")
    for server in servers:
        print(f"- {server.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
