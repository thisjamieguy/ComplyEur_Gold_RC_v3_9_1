#!/usr/bin/env bash
echo "⚠️ Chaos test: simulate DB kill..."
for pid in $(pgrep -f "sqlite3"); do kill -9 $pid || true; done
echo "Chaos complete"
