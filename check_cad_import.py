from __future__ import annotations

import argparse
import json
import pathlib
import sys
import traceback
from datetime import datetime
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.append(str(ROOT / "src"))

from leakage_simulator.importers import import_geometry
from leakage_simulator.roi import build_scene_payload


def _pick_cad_file() -> Optional[str]:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        title="Select CAD file",
        filetypes=[
            ("CAD files", "*.stp *.step *.obj *.stl *.x_t"),
            ("STEP", "*.stp *.step"),
            ("All files", "*.*"),
        ],
    )
    root.destroy()
    return path or None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Direct CAD import checker")
    parser.add_argument("--cad", type=str, default=None, help="Path to CAD file")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/import_check",
        help="Where to save the import summary json",
    )
    parser.add_argument(
        "--no-dialog",
        action="store_true",
        default=False,
        help="Do not open file picker when --cad is omitted",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    cad_path = args.cad
    if not cad_path and not args.no_dialog:
        cad_path = _pick_cad_file()

    if not cad_path:
        print("[ERR] No CAD file selected.")
        print("Use: check_cad_import.py --cad C:\\path\\to\\file.stp")
        return 1

    cad_file = pathlib.Path(cad_path)
    print("[INFO] CAD file:", cad_file)
    print("[INFO] Checking import...")

    try:
        import_result = import_geometry(str(cad_file))
        payload = build_scene_payload(str(cad_file))
    except Exception:
        print("[ERR] Import failed with exception:")
        print(traceback.format_exc())
        return 2

    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = output_dir / f"import_check_{stamp}.json"

    summary = {
        "cad_path": str(cad_file),
        "synthetic": import_result.synthetic,
        "import_note": import_result.note,
        "face_count": len(import_result.mesh.faces),
        "vertex_count": len(import_result.mesh.vertices),
        "receiver_face_hint_count": len(import_result.receiver_face_indices),
        "object_count": len(payload.get("objects", [])),
        "source_file": payload.get("metadata", {}).get("source_file", ""),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[INFO] Import finished.")
    print("[INFO] synthetic =", summary["synthetic"])
    print("[INFO] note      =", summary["import_note"])
    print("[INFO] faces     =", summary["face_count"])
    print("[INFO] vertices  =", summary["vertex_count"])
    print("[INFO] objects   =", summary["object_count"])
    print("[INFO] summary   =", summary_path)

    if summary["synthetic"]:
        print("[WARN] Real CAD import did not complete; synthetic fallback was used.")
        return 3

    print("[OK] Real CAD import succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
