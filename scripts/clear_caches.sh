#!/usr/bin/env bash

echo "Clearing Python caches..."

# Remove all __pycache__ directories
find . -type d -name "__pycache__" -exec rm -r {} +

# Remove .pyc, .pyo, .pyd files
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Remove Pytest cache
rm -rf .pytest_cache

echo "All caches cleared!" 