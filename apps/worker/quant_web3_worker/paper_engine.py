from __future__ import annotations

import time

from apps.api.app.core.config import get_settings
from apps.api.app.db.session import SessionLocal
from apps.api.app.services.paper_trading import process_all_paper_accounts


def process_paper_cycle() -> int:
    with SessionLocal() as db:
        try:
            filled = process_all_paper_accounts(db)
            db.commit()
            return filled
        except Exception:
            db.rollback()
            raise


def main() -> None:
    settings = get_settings()
    while True:
        try:
            process_paper_cycle()
        except Exception as exc:
            print(f"paper engine cycle failed: {exc}", flush=True)
        time.sleep(settings.paper_engine_poll_seconds)


if __name__ == "__main__":
    main()
