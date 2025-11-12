#!/usr/bin/env bash
set -e
echo "Running mutation tests (long)..."
mutmut run
mutmut results
