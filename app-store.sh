#!/bin/bash
# pi-app-store: 1
# pi-app-store-category: beta
# pi-app-store-description: Stock watchlist with on-device estimates: moving averages plus trend projection, clearly labeled as estimates, not financial advice. No API key, no account.
set -eu
cd -- "$(dirname -- "$0")"
case "${1:-}" in
 install) python3 -c 'from pathlib import Path;[compile(p.read_bytes(),str(p),"exec") for p in Path(".").glob("*.py")]' ;;
 run) shift; exec python3 stocks.py "$@" ;;
 *) echo 'Use: bash app-store.sh install OR bash app-store.sh run';exit 1 ;;
esac
