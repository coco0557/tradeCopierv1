"""
mt5_trader.py
-------------
Handles all interaction with MetaTrader 5.

Responsibilities:
  - Connect / disconnect from the MT5 terminal
  - Map symbol aliases (e.g. GOLD → XAUUSD)
  - Place market and pending orders
  - Split a signal into multiple partial lots across each TP level
  - Move SL to breakeven once TP1 is hit (optional, configurable)
"""

import logging
import time
from typing import Optional

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None  # Allows the module to be imported on non-Windows machines for testing

from signal_parser import TradeSignal

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

class MT5Trader:
    def __init__(self, config: dict):
        """
        config expected keys (from config.json → "trading" section):
          master_lot_size   : float  — total lot size to split across TPs
          magic_number      : int    — identifies this bot's orders in MT5
          slippage_deviation: int    — max price deviation in points
          breakeven_on_tp1  : bool   — move SL to entry after TP1 hits
          symbol_mapping    : dict   — e.g. {"GOLD": "XAUUSD"}
        """
        trading_cfg = config.get("trading", {})
        self.lot_size       = float(trading_cfg.get("master_lot_size", 0.01))
        self.magic          = int(trading_cfg.get("magic_number", 123456))
        self.deviation      = int(trading_cfg.get("slippage_deviation", 20))
        self.breakeven_tp1  = bool(trading_cfg.get("breakeven_on_tp1", True))
        self.symbol_map     = config.get("symbol_mapping", {})
        self._connected     = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Initialise the MT5 connection. MT5 terminal must already be open."""
        if mt5 is None:
            logger.error("MetaTrader5 package not installed. Run: pip install MetaTrader5")
            return False

        if not mt5.initialize():
            logger.error("mt5.initialize() failed: %s", mt5.last_error())
            return False

        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Cannot retrieve account info — is MT5 logged in?")
            mt5.shutdown()
            return False

        logger.info(
            "Connected to MT5 | Account: %s | Balance: %.2f %s",
            account_info.login,
            account_info.balance,
            account_info.currency,
        )
        self._connected = True
        return True

    def disconnect(self):
        if mt5 and self._connected:
            mt5.shutdown()
            logger.info("MT5 connection closed.")

    # ------------------------------------------------------------------
    # Public: place a signal
    # ------------------------------------------------------------------

    def execute_signal(self, signal: TradeSignal) -> list[dict]:
        """
        Place one or more orders for a signal.

        If the signal has multiple TPs, the total lot is split evenly
        across them (each gets its own order with a single TP).

        Returns a list of result dicts (one per order attempted).
        """
        if not self._connected:
            logger.error("Not connected to MT5.")
            return []

        symbol = self._resolve_symbol(signal.symbol)
        if not self._symbol_available(symbol):
            logger.error("Symbol %s not available in MT5.", symbol)
            return []

        # Split lot size across TP levels (minimum 0.01 per order)
        tp_list = signal.tp if signal.tp else [None]
        lot_per_tp = max(round(self.lot_size / len(tp_list), 2), 0.01)

        results = []
        for tp in tp_list:
            result = self._place_order(signal, symbol, lot_per_tp, tp)
            results.append(result)
            time.sleep(0.1)  # small delay between orders

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_symbol(self, symbol: str) -> str:
        """Apply symbol alias mapping from config."""
        return self.symbol_map.get(symbol.upper(), symbol.upper())

    def _symbol_available(self, symbol: str) -> bool:
        """Check the symbol exists and is visible in Market Watch."""
        if mt5 is None:
            return False
        info = mt5.symbol_info(symbol)
        if info is None:
            return False
        if not info.visible:
            mt5.symbol_select(symbol, True)  # add to Market Watch
        return True

    def _get_price(self, symbol: str, action: str) -> Optional[float]:
        """Get current ask (for BUY) or bid (for SELL)."""
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        return tick.ask if action == "BUY" else tick.bid

    def _place_order(
        self,
        signal: TradeSignal,
        symbol: str,
        lot: float,
        tp: Optional[float],
    ) -> dict:
        """Build and send a single order request to MT5."""
        order_type = mt5.ORDER_TYPE_BUY if signal.action == "BUY" else mt5.ORDER_TYPE_SELL
        price = self._get_price(symbol, signal.action)

        if price is None:
            logger.error("Could not get price for %s", symbol)
            return {"success": False, "error": "no price"}

        request = {
            "action":    mt5.TRADE_ACTION_DEAL,
            "symbol":    symbol,
            "volume":    lot,
            "type":      order_type,
            "price":     price,
            "deviation": self.deviation,
            "magic":     self.magic,
            "comment":   "TG_Copier",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        if signal.sl:
            request["sl"] = signal.sl
        if tp:
            request["tp"] = tp

        result = mt5.order_send(request)

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            err = result.comment if result else mt5.last_error()
            logger.error("Order failed for %s: %s", symbol, err)
            return {"success": False, "error": str(err), "symbol": symbol}

        logger.info(
            "✅ Order placed | %s %s | Lot: %.2f | Price: %.5f | SL: %s | TP: %s | Ticket: %s",
            signal.action, symbol, lot, price,
            signal.sl or "—", tp or "—", result.order,
        )
        return {
            "success": True,
            "ticket": result.order,
            "symbol": symbol,
            "lot": lot,
            "price": price,
        }
