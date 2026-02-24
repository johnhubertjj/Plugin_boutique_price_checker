"""Compatibility entrypoint for running the package from repository root."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from plugin_boutique_price_checker.cli import main


if __name__ == "__main__":
    main()
