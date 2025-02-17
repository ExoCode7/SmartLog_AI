import sys  # or any other used import
from src.gui.ui_tk import MinimalUI


def main():
    # We no longer import or use logging here; remove that import
    print("Starting SmartLog AI MVP Phase 1 (no logging needed here).")
    app = MinimalUI()
    app.run()


if __name__ == "__main__":
    main()
