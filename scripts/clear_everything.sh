#!/usr/bin/env bash

echo "Clearing Python code caches..."
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
rm -rf .pytest_cache

echo "Clearing pre-commit cache..."
pre-commit clean

echo "Clearing conda cache..."
conda clean --all --yes

echo "Purging pip cache..."
pip cache purge

echo "All caches cleared!"
