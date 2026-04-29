# tradeCopierv1

A Python bot that monitors a Telegram group for trading signals and automatically executes them on MetaTrader 5.
This is not finnancial advice
---

## How It Works

The bot is split into four modules, each with a single responsibility:

**`telegram_listener.py`**
Uses the Telethon library to connect to Telegram as a user account (not a bot token). Monitors a specified group or channel for new messages and fires a callback for each one.

**`signal_parser.py`**
Takes raw message text and uses regex pattern matching to extract structured trade data — action (BUY/SELL), symbol, entry price, stop loss, and one or more take profit levels. Returns a TradeSignal object or None if the message is not a signal.

**`mt5_trader.py`**
Connects to a running MetaTrader 5 terminal via the official MetaTrader5 Python package. Takes a TradeSignal and places market orders, splitting the configured lot size evenly across each TP level.

**`main.py`**
Entry point. Loads config, initialises the MT5 connection (if available), and wires the Telegram listener to the signal parser and trader.

---

## Signal Formats Supported

Labelled:
  BUY XAUUSD
  Entry: 1920.50
  SL: 1915.00
  TP1: 1930.00
  TP2: 1940.00

Inline:
  SELL EURUSD @ 1.0850 SL 1.0900 TP 1.0780

Emoji prefixed:
  BUY GOLD 1920 SL 1910 TP 1935

---

## Requirements

- Python 3.10+
- Windows OS (required for MetaTrader5 package)
- MetaTrader 5 terminal installed and logged in
- Telegram account and API credentials from my.telegram.org

On macOS/Linux the bot runs in signal monitor mode — it connects to Telegram and logs detected signals but does not place trades. MT5 is Windows only.

---

## Setup

1. Clone the repo
   git clone https://github.com/coco0557/tradeCopierv1.git
   cd tradeCopierv1

2. Install dependencies
   pip install -r requirements.txt

3. Configure
   cp config.example.json config.json
   Fill in api_id, api_hash, and channel_username_or_id in config.json
   Get credentials from my.telegram.org
   Use @username for public channels or -100XXXXXXXXXX for private groups

4. Open MetaTrader 5
   Log into your account and enable Algo Trading (green button in toolbar)

5. Run
   python main.py
   On first run Telethon will ask for your phone number and a verification code.
   After that a session file is saved and login is automatic.

---

## Lot Splitting

If master_lot_size = 0.03 and the signal has 3 TPs, the bot places:
  Order 1 - 0.01 lot, TP1
  Order 2 - 0.01 lot, TP2
  Order 3 - 0.01 lot, TP3

Each order shares the same entry and SL.

---

## Logs

All activity is written to both the console and bot.log.

---

## Notes

- config.json is excluded from version control via .gitignore — never commit it
- The session file (.session) is also excluded — it contains your Telegram login
- Always test on a demo account before running on a live account
