"""Tests for trade_kit.py — scalping-style terminal display (display only)."""
import re

import trade_kit
from trade_kit import (close_line, fmt_pnl, fmt_price, open_line, paint,
                       positions_table, wib_str)

POS = {
    "symbol": "BTCUSDT", "direction": "LONG", "entry_price": 82800.5,
    "qty": 0.0012, "leverage": 10, "margin_usdt": 1.0,
    "stop_loss": 81500.0, "tp": {"tp1": {"price": 84456.5}},
    "opened_at": 1760879721000, "closed_at": 1760883764000,
}


def _strip_ansi(s):
    return re.sub(r"\033\[[0-9;]+m", "", s)


def test_paint_wraps_ansi():
    out = paint("hi", "green", "bold")
    assert out.startswith("\033[")
    assert _strip_ansi(out) == "hi"


def test_paint_unknown_color_passthrough():
    assert paint("hi", "nope") == "hi"


def test_wib_str_format():
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
                    wib_str(1760879721000))


def test_fmt_price_tiers():
    assert fmt_price(82800.5) == "82,800.50"
    assert fmt_price(0.023456) == "0.023456"
    assert fmt_price(None) == "-"


def test_fmt_pnl_sign():
    assert fmt_pnl(0.21) == "+$0.21"
    assert fmt_pnl(-0.05) == "-$0.05"
    assert fmt_pnl(0.0) == "+$0.00"


def test_open_line_fields():
    line = open_line(POS, 82800.5)
    for needle in ("OPEN LONG BTCUSDT", "82,800.50", "margin $1.00",
                   "lev 10x", "84,456.50", "81,500.00"):
        assert needle in line, needle


def test_close_line_fields():
    line = close_line(POS, 84460.0, 0.21, "TP")
    for needle in ("CLOSE LONG BTCUSDT", "82,800.50", "84,460.00",
                   "+$0.21", "[TP]"):
        assert needle in line, needle


def test_positions_table_columns():
    tbl = positions_table({"p1": POS})
    assert "tgl" in tbl and "symbol" in tbl and "margin" in tbl
    assert "BTCUSDT" in tbl and "LONG" in tbl


def test_positions_table_empty():
    assert "tidak ada posisi terbuka" in positions_table({})


def test_cycle_line():
    from trade_kit import cycle_line
    line = cycle_line(3, {"approved": 2, "opened": 1, "managed": 1,
                          "errors": []})
    for needle in ("cycle 3", "approved 2", "dibuka 1", "kelola 1",
                   "error 0"):
        assert needle in line, needle
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line)


def test_cycle_line_counts_error_list():
    from trade_kit import cycle_line
    line = cycle_line(1, {"approved": 0, "opened": 0, "managed": 0,
                          "errors": ["boom", "bam"]})
    assert "error 2" in line


def test_short_err_http():
    from data import _short_err

    class Resp:
        status_code = 400

    class HTTPError(Exception):
        def __init__(self):
            super().__init__("400 Client Error: Bad Request for url: "
                             "https://fapi.binance.com/fapi/v1/klines?"
                             "symbol=USDT&interval=15m&limit=222")
            self.response = Resp()

    assert _short_err(HTTPError()) == "HTTP 400"


def test_short_err_plain():
    from data import _short_err
    assert _short_err(ValueError("no OKX SWAP mapping for USDT")) == \
        "no OKX SWAP mapping for USDT"


def test_short_err_empty():
    from data import _short_err
    assert _short_err(ValueError()) == "ValueError"
