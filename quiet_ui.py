"""Quiet UI for flex-bot: spinner + log suppression (user 2026-10-19).

The user wants a clean terminal: no executor INFO logs, just positions
and PnL. A spinner shows "life" during the scan phase.
"""
from __future__ import annotations

import logging
import sys
import threading
import time


class Spinner:
    """Simple terminal spinner (thread-based).

    Usage:
        sp = Spinner("Scanning")
        sp.start()
        ... work ...
        sp.stop()  # clears the line
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Scanning"):
        self.message = message
        self._stop = threading.Event()
        self._thread = None

    def _run(self):
        i = 0
        while not self._stop.is_set():
            frame = self.FRAMES[i % len(self.FRAMES)]
            sys.stdout.write(f"\r{frame} {self.message}...")
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)
        # Clear the line.
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None


def setup_quiet():
    """Suppress INFO logs; only WARNING+ and direct prints show.

    The trade_kit lines (positions, PnL, cycle summaries) use print(),
    so they still appear. All the verbose executor INFO logs are hidden.
    """
    # Root logger to WARNING — silences all INFO logs.
    logging.getLogger().setLevel(logging.WARNING)
    # Explicitly quiet the noisy ones.
    for name in ("executor", "bot.httputil", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)
