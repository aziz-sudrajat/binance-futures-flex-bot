"""Quiet mode: show ONLY positions + PnL. No logs, no spinner."""
from __future__ import annotations
import logging

def setup_quiet():
    """Silence ALL logging. Only direct print() shows."""
    logging.disable(logging.CRITICAL)
