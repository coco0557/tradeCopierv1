
```
BUY XAUUSD
Entry: 1920.50
SL: 1915.00
TP1: 1930.00
TP2: 1940.00
```

**Inline**
```
SELL EURUSD @ 1.0850 SL 1.0900 TP 1.0780
```

---

## Requirements

- Python 3.10+
- Windows OS (required for MetaTrader5 package)
- MetaTrader 5 terminal installed and logged in
- Telegram account and API credentials from my.telegram.org

On macOS/Linux the bot runs in signal monitor mode — MT5 is Windows only.

---

## Setup

1. Clone the repo: git clone https://github.com/coco0557/tradeCopierv1.git
2. Install dependencies: pip install -r requirements.txt
3. Copy config: cp config.example.json config.json
4. Fill in your api_id, api_hash, and channel ID in config.json
5. Open MT5 and enable Algo Trading
6. Run: python main.py

---

## Notes

- config.json is excluded via .gitignore — never commit it
- Always test on a demo account first
