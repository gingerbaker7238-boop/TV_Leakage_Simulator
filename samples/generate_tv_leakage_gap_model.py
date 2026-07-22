from __future__ import annotations

from pathlib import Path

import cadquery as cq

from generate_tv_leakage_test_models import add_part, box_from_minmax, union_boxes

ROOT = Path(__file__).resolve().parent

GAP_MM = 1.2  # intentional seam gap between Cover_Deco and Chassis_Rear at the bottom edge


def make_full_tv_with_gap(gap_mm: float = GAP_MM) -> cq.Assembly:
    width = 800.0
    height = 450.0
    depth = 45.0
    assembly = cq.Assembly(name="TV_light_leakage_full_with_gap")

    chassis = union_boxes(
        box_from_minmax((0.0, 0.0, 0.0), (width, height, 3.0)),
        box_from_minmax((0.0, 0.0, 3.0), (width, 18.0, 30.0)),
        box_from_minmax((0.0, 0.0, 3.0), (18.0, height, 30.0)),
        box_from_minmax((width - 18.0, 0.0, 3.0), (width, height, 30.0)),
        box_from_minmax((0.0, height - 14.0, 3.0), (width, height, 24.0)),
    )
    lcd_cell = box_from_minmax((24.0, 38.0, 30.0), (width - 24.0, height - 24.0, 33.0))
    frame_middle = union_boxes(
        box_from_minmax((18.0, 18.0, 24.0), (width - 18.0, 42.0, 30.0)),
        box_from_minmax((18.0, 18.0, 18.0), (42.0, 72.0, 24.0)),
        box_from_minmax((width - 42.0, 18.0, 18.0), (width - 18.0, 72.0, 24.0)),
    )

    # Same Cover_Deco footprint as the no-gap baseline, but pulled back by
    # `gap_mm` along the bottom edge (y direction) - opens a real seam
    # between the bottom lip of Cover_Deco and the Chassis_Rear hemming
    # surface it normally sits flush against, instead of only being
    # something a user has to create later via an interactive transform.
    cover_deco = union_boxes(
        box_from_minmax((0.0, gap_mm, 33.0), (width, 36.0, depth)),
        box_from_minmax((0.0, gap_mm, 33.0), (30.0, height, depth)),
        box_from_minmax((width - 30.0, gap_mm, 33.0), (width, height, depth)),
    )

    add_part(assembly, "Chassis_Rear", chassis, (0.18, 0.20, 0.23, 1.0))
    add_part(assembly, "LCD_Cell_3T", lcd_cell, (0.08, 0.16, 0.26, 0.45))
    add_part(assembly, "Frame_Middle_FMB", frame_middle, (0.05, 0.05, 0.05, 1.0))
    add_part(assembly, "Cover_Deco", cover_deco, (0.02, 0.02, 0.025, 1.0))
    return assembly


def main() -> None:
    out_path = ROOT / "tv_leakage_full_assembled_gap_1p2mm.stp"
    assembly = make_full_tv_with_gap(GAP_MM)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    assembly.save(str(out_path), exportType="STEP", mode="default", write_pcurves=False)
    print(f"wrote: {out_path}")


if __name__ == "__main__":
    main()
