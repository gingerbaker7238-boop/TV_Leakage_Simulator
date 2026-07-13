from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent / "src"))

from leakage_simulator.cli import main


if __name__ == "__main__":
    main()
