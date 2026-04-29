# tradeCopierv1

A Python bot that monitors a Telegram group for trading signals and automatically executes them on MetaTrader 5.

---

## How It Works

The bot is split into four modules, each with a single responsibility:

**`telegram_listener.py`**
Uses the Telethon library to connect to Telegram as a user account (not a bot token). Monitors a specified group or channel for new messages and fires a callback for each one.

**`signal_parser.py`**
Takes raw message text and uses regex pattern matching to extract structured trade data — action (BUY/SELL), symbol, entry price, stop loss, and one or more take profit levels. Returns a `TradeSignal` object or `None` if the message is not a signal.

**`mt5_trader.py`**
Connects to a running MetaTrader 5 terminal via the official `MetaTrader5` Python package. Takes a `TradeSignal` and places market orders, splitting the configured lot size evenly across each TP level.

**`main.py`**
Entry point. Loads config, initialises the MT5 connection (if available), and wires the Telegram listener to the signal parser and trader.

---

## Signal Formats Supported

**Labelled**
