"""
main.py
-------
Entry point for the MT5 Telegram Signal Copier.

Run with:  python main.py

Flow:
  1. Load config.json
  2. Connect to MT5
  3. Start Telegram listener
  4. For each new channel message:
       a. Parse it into a TradeSignal
       b. If valid → execute it on MT5
       c. If not a signal → log and ignore
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

from signal_parser import parse_signal
from telegram_listener import TelegramListener
from mt5_trader import MT5Trader


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(path: str = "config.json") -> dict:
    config_file = Path(path)
    if not config_file.exists():
        logger.error("config.json not found. Copy config.json.example and fill it in.")
        sys.exit(1)
    with config_file.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(config: dict):
    # --- Connect to MT5 ---
    trader = MT5Trader(config)
    if not trader.connect():
        logger.error("Failed to connect to MT5. Make sure the terminal is open and logged in.")
        sys.exit(1)

    # --- Callback: called by TelegramListener for every new message ---
    def handle_message(text: str):
        signal = parse_signal(text)

        if signal is None:
            logger.info("Message did not match a signal format — skipped.")
            return

        logger.info("Signal parsed: %s", signal)
        results = trader.execute_signal(signal)

        success_count = sum(1 for r in results if r.get("success"))
        logger.info(
            "Executed %d / %d orders for signal: %s",
            success_count, len(results), signal,
        )

    # --- Start Telegram listener (blocks until disconnected) ---
    listener = TelegramListener(config, on_message=handle_message)
    try:
        await listener.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await listener.stop()
        trader.disconnect()


if __name__ == "__main__":
    cfg = load_config()
    asyncio.run(run(cfg))
