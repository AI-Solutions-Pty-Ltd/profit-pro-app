#!/usr/bin/env bash
set -e

source .venv/bin/activate

echo "=== Ruff Format ==="
ruff format .

echo ""
echo "=== Ruff Lint (--fix) ==="
ruff check . --fix

echo ""
echo "=== Type Check (ty) ==="
ty check .

echo ""
echo "=== djlint Reformat ==="
djlint --reformat .

echo ""
echo "=== djlint Lint ==="
djlint --lint .

echo ""
echo "=== Tests (pytest + coverage) ==="
python -m pytest -v -n auto --reuse-db --durations=10 --cov=. --cov-report=html

echo ""
echo "All checks passed."
