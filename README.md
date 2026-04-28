# MT5 Telegram Signal Copier

A clean, open-source Python bot that listens to a Telegram channel and
automatically copies trade signals into MetaTrader 5.

## Project Structure

```
trading_bot/
├── main.py                 # Entry point — wire everything together
├── telegram_listener.py    # Watches the Telegram channel for new messages
├── signal_parser.py        # Extracts trade details from message text
├── mt5_trader.py           # Places and manages orders in MT5
├── config.json             # Your credentials and settings
└── requirements.txt
```

## Quick Start

### 1. Install dependencies (Windows)
```bash
pip install -r requirements.txt
```

### 2. Get your Telegram API credentials
1. Go to https://my.telegram.org and log in
2. Click **API development tools**
3. Create a new app (any name/short name)
4. Copy your `api_id` and `api_hash` into `config.json`
5. Set `channel_username_or_id` to the channel link (e.g. `@signalchannel` or a `t.me/+...` invite link)

### 3. Configure your trading settings in config.json
- `master_lot_size` — total lot split across all TP levels
- `magic_number` — unique ID so you can identify this bot's trades in MT5
- `slippage_deviation` — max price slippage in points
- `breakeven_on_tp1` — move SL to entry price when TP1 is hit
- `symbol_mapping` — map common aliases to your broker's exact symbol names

### 4. Open MetaTrader 5
- Log into a **demo account** first
- Make sure **Algo Trading** is enabled (green button in toolbar)

### 5. Run the bot
```bash
python main.py
```

On first run, Telethon will ask for your Telegram phone number to create
a session file. After that, it logs in automatically.

---

## Signal Formats Supported

The parser handles the most common Telegram channel formats:

**Labelled (most common)**
```
BUY XAUUSD
Entry: 1920.50
SL: 1915.00
TP1: 1930.00
TP2: 1940.00
```

**Inline**
```
SELL EURUSD @ 1.0850  SL 1.0900  TP 1.0780
```

**Emoji prefixed**
```
📈 BUY GOLD 1920 SL 1910 TP 1935
```

To add support for a new format, add a parser function to `signal_parser.py`
and register it in the `_PARSERS` list.

---

## How Lot Splitting Works

If `master_lot_size = 0.03` and the signal has 3 TPs:
- Order 1 → 0.01 lot, TP1
- Order 2 → 0.01 lot, TP2
- Order 3 → 0.01 lot, TP3

Each order shares the same SL. When each TP is hit, that partial position closes.

---

## Logging

All activity is printed to the console **and** saved to `bot.log`.
Check the log if any orders are skipped or fail.

---

## ⚠️ Risk Warning

This software is for educational purposes. Automated trading involves
significant financial risk. Always test on a demo account first.
