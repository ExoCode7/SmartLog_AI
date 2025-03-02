#!/usr/bin/env zsh

# First try to find and source conda.sh to make conda available as a command
if [[ -z "${CONDA_EXE}" ]]; then
    # Search for conda in common locations
    POSSIBLE_CONDA_LOCATIONS=(
        "$HOME/miniconda3"
        "$HOME/anaconda3"
        "$HOME/opt/miniconda3"
        "$HOME/opt/anaconda3"
        "/opt/miniconda3"
        "/opt/anaconda3"
        "/usr/local/miniconda3"
        "/usr/local/anaconda3"
        "/miniconda"
    )

    for loc in "${POSSIBLE_CONDA_LOCATIONS[@]}"; do
        if [[ -f "$loc/etc/profile.d/conda.sh" ]]; then
            echo "Found conda installation at $loc"
            . "$loc/etc/profile.d/conda.sh"
            break
        fi
    done
fi

echo "Clearing Python code caches..."
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
rm -rf .pytest_cache

echo "Clearing pre-commit cache..."
pre-commit clean

# Try to use conda with full error handling
if command -v conda >/dev/null 2>&1; then
    echo "Clearing conda cache..."
    if conda clean --all --yes; then
        echo "Conda cache cleared successfully."
    else
        echo "Error clearing conda cache."
    fi
else
    echo "Conda command not found, skipping conda cache cleanup."
    echo "Current PATH: $PATH"
fi

echo "Purging pip cache..."
pip cache purge

echo "All caches cleared!"
