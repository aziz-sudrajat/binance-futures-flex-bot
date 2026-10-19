#!/usr/bin/env python3
"""Trade kit reporter — scalping-style terminal lines for flex-bot.

Stdlib only. Prints clear, colored one-line summaries of trade events
(tgl | side | entry | margin | TP/SL | PnL) so the terminal reads like the
azzx-fast-scalping tool instead of raw log records.

Public API:
    print_open(pos, fill_px)          - call on POSITION_OPENED
    print_close(pos, fill_px, net, reason) - call on terminal close
    positions_table(positions) -> str - rows for the kit.py monitor
    fmt_price / fmt_pnl / wib_str      - building blocks
"""

from __future__ import annotations

import datetime

_COLORS = {
    "red": "31", "green": "32", "yellow": "33", "blue": "34",
    "magenta": "35", "cyan": "36", "white": "37",
    "bold": "1", "dim": "2",
}

_WIB = datetime.timedelta(hours=7)


def paint(text: object, *colors: str) -> str:
    """Wrap text in ANSI color codes (same style as azzx-fast-scalping)."""
    codes = [_COLORS[c] for c in colors if c in _COLORS]
    if not codes:
        return str(text)
    return "\033[" + ";".join(codes) + "m" + str(text) + "\033[0m"


def wib_str(ts_ms: int | float | None = None,
            fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a millisecond epoch (or now) as WIB wall time."""
    if ts_ms is None:
        dt = datetime.datetime.now(datetime.timezone.utc)
    else:
        dt = datetime.datetime.fromtimestamp(float(ts_ms) / 1000.0,
                                             tz=datetime.timezone.utc)
    return (dt + _WIB).strftime(fmt)


def fmt_price(px: float | None) -> str:
    if px is None:
        return "-"
    px = float(px)
    if px == 0:
        return "0"
    if abs(px) >= 1000:
        return f"{px:,.2f}"
    if abs(px) >= 1:
        return f"{px:,.4f}".rstrip("0").rstrip(".")
    return f"{px:.8f}".rstrip("0").rstrip(".")


def fmt_pnl(pnl: float | None) -> str:
    if pnl is None:
        return "-"
    pnl = float(pnl)
    sign = "+" if pnl >= 0 else "-"
    return f"{sign}${abs(pnl):.2f}"


def _tp1(pos: dict) -> float | None:
    try:
        return float(pos["tp"]["tp1"]["price"])
    except (KeyError, TypeError, ValueError):
        return None


def open_line(pos: dict, fill_px: float | None = None) -> str:
    """Build the scalping-style OPEN line for a freshly opened position."""
    direction = str(pos.get("direction", "?")).upper()
    symbol = pos.get("symbol", "?")
    entry = fill_px if fill_px is not None else pos.get("entry_price")
    margin = pos.get("margin_usdt")
    lev = pos.get("leverage")
    sl = pos.get("stop_loss")
    ts = wib_str(pos.get("opened_at"))
    margin_s = f"${float(margin):.2f}" if margin is not None else "-"
    line = (f"{ts} | OPEN {direction} {symbol} @ {fmt_price(entry)}"
            f" | margin {margin_s}")
    if lev:
        line += f" | lev {lev}x"
    line += f" | TP {fmt_price(_tp1(pos))} | SL {fmt_price(sl)}"
    return line


def close_line(pos: dict, fill_px: float, net: float,
               reason: str | None = None) -> str:
    """Build the scalping-style CLOSE line for a terminally closed position."""
    direction = str(pos.get("direction", "?")).upper()
    symbol = pos.get("symbol", "?")
    entry = pos.get("entry_price")
    ts = wib_str(pos.get("closed_at"))
    line = (
        f"{ts} | CLOSE {direction} {symbol}"
        f" | entry {fmt_price(entry)} | exit {fmt_price(fill_px)}"
        f" | PnL {fmt_pnl(net)}"
    )
    if reason:
        line += f" [{reason}]"
    return line


def print_open(pos: dict, fill_px: float | None = None) -> None:
    """Print a colored OPEN kit line (green=LONG, red=SHORT)."""
    direction = str(pos.get("direction", "")).upper()
    color = "green" if direction == "LONG" else "red"
    print(paint(open_line(pos, fill_px), color, "bold"), flush=True)


def print_close(pos: dict, fill_px: float, net: float,
                reason: str | None = None) -> None:
    """Print a colored CLOSE kit line (green=profit, red=loss)."""
    color = "green" if float(net) >= 0 else "red"
    print(paint(close_line(pos, fill_px, net, reason), color, "bold"),
          flush=True)


def positions_table(positions: dict) -> str:
    """Render open positions as a plain-text kit table.

    Columns: tgl | symbol | side | entry | margin | lev | TP | SL
    """
    header = (f"{'tgl':19} | {'symbol':12} | {'side':5} | {'entry':12} | "
              f"{'margin':8} | {'lev':4} | {'TP':12} | {'SL':12}")
    sep = "-" * len(header)
    rows = [header, sep]
    for _pid, pos in sorted(positions.items(),
                            key=lambda kv: kv[1].get("opened_at") or 0):
        direction = str(pos.get("direction", "?")).upper()
        margin = pos.get("margin_usdt")
        rows.append(
            f"{wib_str(pos.get('opened_at')):19} | "
            f"{str(pos.get('symbol', '?')):12} | "
            f"{direction:5} | "
            f"{fmt_price(pos.get('entry_price')):12} | "
            f"{('$' + format(float(margin), '.2f')) if margin is not None else '-':8} | "
            f"{(str(pos.get('leverage')) + 'x') if pos.get('leverage') else '-':4} | "
            f"{fmt_price(_tp1(pos)):12} | "
            f"{fmt_price(pos.get('stop_loss')):12}"
        )
    if len(rows) == 2:
        rows.append("(tidak ada posisi terbuka)")
    return "\n".join(rows)
