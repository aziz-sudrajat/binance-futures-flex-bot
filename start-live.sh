#!/bin/bash
# Starter for the live trading loop (tmux bot-live).
# API keys are NOT stored here; they are sourced from ~/.binance-live.env (chmod 600).
cd /home/azzatssins/binance-futures-strict-bot || exit 1
set -a
source /home/azzatssins/.binance-live.env
set +a
exec .venv/bin/python run_executor.py --live --loop >> live-loop.log 2>&1
