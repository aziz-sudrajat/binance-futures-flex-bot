#!/usr/bin/env python3
"""kit.py — monitor trading kit flex-bot di terminal (gaya azzx-fast-scalping).

Baca state file lalu tampilkan ringkasan jelas:
  tgl | symbol | side | entry | margin | lev | TP | SL | PnL

Read-only: tidak mengubah state, tidak menyentuh loop yang sedang jalan.

Pakai:
    .venv/bin/python kit.py              # paper (default)
    .venv/bin/python kit.py --mode live  # state live
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

import trade_kit
from trade_kit import paint, wib_str, fmt_pnl, fmt_price

STATE_FILES = {
    "paper": "state-paper.json",
    "live": "state-live.json",
    "testnet": "state-testnet.json",
}


def _today_wib() -> str:
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=7)).strftime("%Y-%m-%d")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Monitor trading kit flex-bot")
    ap.add_argument("--mode", default="paper",
                    choices=sorted(STATE_FILES),
                    help="state file mana yang dibaca (default: paper)")
    args = ap.parse_args(argv)

    path = STATE_FILES[args.mode]
    if not os.path.exists(path):
        print(paint(f"state file tidak ada: {path}", "red", "bold"))
        return 1
    with open(path) as f:
        st = json.load(f)

    positions = st.get("positions", {}) or {}
    daily = st.get("daily", {}) or {}
    today = _today_wib()

    open_pos = {pid: p for pid, p in positions.items()
                if not p.get("closed")}
    closed_today = [p for p in positions.values()
                    if p.get("closed") and p.get("closed_at")
                    and wib_str(p["closed_at"], "%Y-%m-%d") == today]
    closed_today.sort(key=lambda p: p.get("closed_at") or 0)

    mode_tag = args.mode.upper()
    mode_color = "red" if args.mode == "live" else "cyan"
    print(paint(f"=== FLEX-BOT KIT [{mode_tag}] ===", mode_color, "bold"),
          paint(wib_str(), "dim"))

    start_bal = daily.get("start_balance")
    realized = float(daily.get("realized_pnl", 0.0) or 0.0)
    if start_bal is not None:
        cur = float(start_bal) + realized
        print(f"saldo: ${cur:,.2f}  (awal hari ${float(start_bal):,.2f} "
              f"| realized hari ini {paint(fmt_pnl(realized), 'green' if realized >= 0 else 'red', 'bold')})")

    print()
    print(paint("--- POSISI TERBUKA ---", "yellow", "bold"))
    print(trade_kit.positions_table(open_pos))

    print()
    print(paint(f"--- TRADE DITUTUP HARI INI ({today}) ---", "yellow", "bold"))
    if not closed_today:
        print("(belum ada)")
    else:
        wins = sum(1 for p in closed_today
                   if float(p.get("realized", 0.0) or 0.0) >= 0)
        for p in closed_today:
            net = float(p.get("realized", 0.0) or 0.0)
            line = (f"{wib_str(p.get('closed_at'))} | "
                    f"{str(p.get('direction', '?')).upper():5} "
                    f"{p.get('symbol', '?'):12} | "
                    f"entry {fmt_price(p.get('entry_price'))} | "
                    f"exit {fmt_price(p.get('close_price'))} | "
                    f"PnL {fmt_pnl(net)} [{p.get('closed_reason', '-')}]")
            print(paint(line, "green" if net >= 0 else "red"))
        tot = sum(float(p.get("realized", 0.0) or 0.0) for p in closed_today)
        wr = 100.0 * wins / len(closed_today)
        print(f"\nringkasan: {len(closed_today)} trade, {wins} win "
              f"({wr:.0f}%), total {paint(fmt_pnl(tot), 'green' if tot >= 0 else 'red', 'bold')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
