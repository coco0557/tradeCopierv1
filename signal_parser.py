"""
signal_parser.py
----------------
Parses raw Telegram message text into structured trade signals.

Handles the most common signal formats seen in Telegram trading channels:

  Format A (explicit labels):
    BUY XAUUSD
    Entry: 1920.50
    SL: 1915.00
    TP1: 1930.00
    TP2: 1940.00

  Format B (inline):
    SELL EURUSD @ 1.0850  SL 1.0900  TP 1.0780

  Format C (action word only, price on same line):
    📈 BUY GOLD 1920 SL 1910 TP 1935

To support a new signal format, add a parser method and register it in
_PARSERS at the bottom of this file.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TradeSignal:
    """Everything needed to place and manage a trade."""
    action: str                     # "BUY" or "SELL"
    symbol: str                     # e.g. "XAUUSD"
    entry: Optional[float] = None   # None → market order
    sl: Optional[float] = None      # stop-loss price
    tp: list[float] = field(default_factory=list)  # one or more take-profits
    raw_text: str = ""              # original message for logging

    def is_valid(self) -> bool:
        """Minimum viable signal: action + symbol."""
        return bool(self.action and self.symbol)

    def __str__(self):
        tp_str = " / ".join(str(t) for t in self.tp) or "—"
        return (
            f"{self.action} {self.symbol} | "
            f"Entry: {self.entry or 'MARKET'} | "
            f"SL: {self.sl or '—'} | TP: {tp_str}"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Strip emoji, extra whitespace, and normalise common aliases."""
    # Remove emoji and non-ASCII decorations
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip().upper()
    return text


def _parse_float(value: str) -> Optional[float]:
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _parse_labelled(text: str) -> Optional[TradeSignal]:
    """
    Handles the most common 'labelled' format:
        BUY XAUUSD
        Entry: 1920.50
        SL: 1915.00
        TP1: 1930.00  TP2: 1940.00
    """
    clean = _clean(text)

    # Action + symbol (must appear somewhere)
    action_match = re.search(r"\b(BUY|SELL)\b", clean)
    symbol_match = re.search(r"\b(BUY|SELL)\s+([A-Z]{3,10})\b", clean)
    if not action_match:
        return None

    action = action_match.group(1)
    symbol = symbol_match.group(2) if symbol_match else None
    if not symbol:
        return None

    # Entry — labelled "ENTRY:" or "PRICE:" or "@"
    entry = None
    m = re.search(r"(?:ENTRY|PRICE)\s*[:\@]?\s*([\d.,]+)", clean)
    if not m:
        m = re.search(r"@\s*([\d.,]+)", clean)
    if m:
        entry = _parse_float(m.group(1))

    # SL
    sl = None
    m = re.search(r"\bS\.?L\.?\s*[:\-]?\s*([\d.,]+)", clean)
    if m:
        sl = _parse_float(m.group(1))

    # TP — grab all TP1, TP2, TP3 … or plain TP
    tp_values = []
    for m in re.finditer(r"\bT\.?P\.?\d*\s*[:\-]?\s*([\d.,]+)", clean):
        val = _parse_float(m.group(1))
        if val:
            tp_values.append(val)

    return TradeSignal(
        action=action,
        symbol=symbol,
        entry=entry,
        sl=sl,
        tp=tp_values,
        raw_text=text,
    )


def _parse_inline(text: str) -> Optional[TradeSignal]:
    """
    Handles compact inline format:
        SELL EURUSD @ 1.0850 SL 1.0900 TP 1.0780
    """
    clean = _clean(text)

    m = re.match(
        r"(BUY|SELL)\s+([A-Z]{3,10})\s*@?\s*([\d.,]+)?"
        r"(?:.*\bSL\s*([\d.,]+))?(?:.*\bTP\s*([\d.,]+))?",
        clean,
    )
    if not m:
        return None

    action, symbol, entry_s, sl_s, tp_s = m.groups()
    return TradeSignal(
        action=action,
        symbol=symbol,
        entry=_parse_float(entry_s) if entry_s else None,
        sl=_parse_float(sl_s) if sl_s else None,
        tp=[_parse_float(tp_s)] if tp_s else [],
        raw_text=text,
    )


# Order matters — try the most specific parser first
_PARSERS = [_parse_labelled, _parse_inline]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_signal(message_text: str) -> Optional[TradeSignal]:
    """
    Try each registered parser in order.
    Returns the first valid TradeSignal, or None if nothing matched.
    """
    for parser in _PARSERS:
        result = parser(message_text)
        if result and result.is_valid():
            return result
    return None
