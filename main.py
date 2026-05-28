# -*- coding: utf-8 -*-
import logging
import sys
from datetime import datetime, timedelta

from src.database_setup import get_engine
from src.toast_api import ToastAPI
from Tables.Orders_Pull_Update import run_order_update

# ── Logging ───────────────────────────────────────────────────────────────────
# Logs to stdout so Azure Container Apps captures them in Log Analytics
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")


def main():
    start = datetime.now()
    logger.info("=" * 60)
    logger.info(f"TOAST NIGHTLY SYNC STARTED — {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Target the previous business day
    target_date = (start - timedelta(days=1)).strftime("%Y%m%d")
    logger.info(f"Target business date: {target_date}")

    # ── Shared resources ──────────────────────────────────────────────────────
    try:
        engine = get_engine()
        logger.info("Database engine initialised.")
    except Exception as e:
        logger.critical(f"Could not create database engine: {e}", exc_info=True)
        sys.exit(1)

    try:
        api = ToastAPI()
        logger.info("Toast API client initialised.")
    except Exception as e:
        logger.critical(f"Could not initialise Toast API client: {e}", exc_info=True)
        sys.exit(1)

    # ── Orders sync ───────────────────────────────────────────────────────────
    try:
        run_order_update(target_date=target_date, engine=engine, API=api)
    except Exception as e:
        logger.critical(f"Orders sync failed: {e}", exc_info=True)
        sys.exit(1)

    # ── Done ──────────────────────────────────────────────────────────────────
    elapsed = datetime.now() - start
    logger.info("=" * 60)
    logger.info(f"NIGHTLY SYNC COMPLETE — elapsed {elapsed}")
    logger.info("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
