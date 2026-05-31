#!/usr/bin/env bash
# Restart loop for BrainDrop bot.
# Usage: bash run_bot.sh
# Automatically restarts the bot if it exits unexpectedly.
# Press Ctrl+C twice to stop.

set -euo pipefail

RESTART_DELAY=5

trap 'echo "Stopping bot..."; exit 0' SIGINT SIGTERM

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting BrainDrop bot..."
    python -m bot.main || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot exited. Restarting in ${RESTART_DELAY}s... (Ctrl+C to stop)"
    sleep "$RESTART_DELAY"
done
