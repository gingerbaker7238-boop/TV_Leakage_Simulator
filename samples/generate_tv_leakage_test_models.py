from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import cadquery as cq


ROOT = Path(__file__).resolve().parent


def box_from_minmax(min_corner: Tuple[float, float, float], max_corner: Tuple[float, float, float]) -> cq.Workplane:
    x0, y0, z0 = min_corner
    x1, y1, z1 = max_corner
    size = (x1 - x0, y1 - y0, z1 - z0)
    center = ((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5)
    return cq.Workplane("XY").box(size[0], size[1], size[2]).translate(center)


def union_boxes(*boxes: cq.Workplane) -> cq.Workplane:
    if not boxes:
        raise ValueError("At least one box is required")
    body = boxes[0]
    for item in boxes[1:]:
        body = body.union(item)
    return body


def add_part(assembly: cq.Assembly, name: str, body: cq.Workplane, color: Tuple[float, float, float, float]) -> None:
    assembly.add(body, name=name, color=cq.Color(*color))


def make_full_tv() -> cq.Assembly:
    width = 800.0
    height = 450.0
    depth = 45.0
    assembly = cq.Assembly(name="TV_light_leakage_full_no_gap")

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
    cover_deco = union_boxes(
        box_from_minmax((0.0, 0.0, 33.0), (width, 36.0, depth)),
        box_from_minmax((0.0, 0.0, 33.0), (30.0, height, depth)),
        box_from_minmax((width - 30.0, 0.0, 33.0), (width, height, depth)),
    )

    add_part(assembly, "Chassis_Rear", chassis, (0.18, 0.20, 0.23, 1.0))
    add_part(assembly, "LCD_Cell_3T", lcd_cell, (0.08, 0.16, 0.26, 0.45))
    add_part(assembly, "Frame_Middle_FMB", frame_middle, (0.05, 0.05, 0.05, 1.0))
    add_part(assembly, "Cover_Deco", cover_deco, (0.02, 0.02, 0.025, 1.0))
    return assembly


def make_corner_roi(side: str) -> cq.Assembly:
    if side not in {"left", "right"}:
        raise ValueError("side must be left or right")
    width = 60.0
    height = 60.0
    depth = 45.0
    assembly = cq.Assembly(name=f"TV_light_leakage_{side}_bottom_roi_no_gap")

    if side == "left":
        side_wall = box_from_minmax((0.0, 0.0, 3.0), (18.0, height, 30.0))
        deco_side = box_from_minmax((0.0, 0.0, 33.0), (30.0, height, depth))
        fmb_corner = box_from_minmax((18.0, 18.0, 18.0), (42.0, height, 24.0))
        lcd_x0, lcd_x1 = 24.0, width
    else:
        side_wall = box_from_minmax((width - 18.0, 0.0, 3.0), (width, height, 30.0))
        deco_side = box_from_minmax((width - 30.0, 0.0, 33.0), (width, height, depth))
        fmb_corner = box_from_minmax((width - 42.0, 18.0, 18.0), (width - 18.0, height, 24.0))
        lcd_x0, lcd_x1 = 0.0, width - 24.0

    chassis = union_boxes(
        box_from_minmax((0.0, 0.0, 0.0), (width, height, 3.0)),
        box_from_minmax((0.0, 0.0, 3.0), (width, 18.0, 30.0)),
        side_wall,
    )
    lcd_cell = box_from_minmax((lcd_x0, 38.0, 30.0), (lcd_x1, height, 33.0))
    frame_middle = union_boxes(
        box_from_minmax((0.0, 18.0, 24.0), (width, 42.0, 30.0)),
        fmb_corner,
    )
    cover_deco = union_boxes(
        box_from_minmax((0.0, 0.0, 33.0), (width, 36.0, depth)),
        deco_side,
    )

    add_part(assembly, "Chassis_Rear", chassis, (0.18, 0.20, 0.23, 1.0))
    add_part(assembly, "LCD_Cell_3T", lcd_cell, (0.08, 0.16, 0.26, 0.45))
    add_part(assembly, "Frame_Middle_FMB", frame_middle, (0.05, 0.05, 0.05, 1.0))
    add_part(assembly, "Cover_Deco", cover_deco, (0.02, 0.02, 0.025, 1.0))
    return assembly


def export_model(assembly: cq.Assembly, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    assembly.save(str(path), exportType="STEP", mode="fused", write_pcurves=False)


def main() -> None:
    outputs: Dict[str, str] = {
        "full_no_gap": "tv_leakage_full_assembled_no_gap.stp",
        "roi_left_bottom_no_gap": "tv_leakage_roi_left_bottom_no_gap.stp",
        "roi_right_bottom_no_gap": "tv_leakage_roi_right_bottom_no_gap.stp",
    }
    export_model(make_full_tv(), ROOT / outputs["full_no_gap"])
    export_model(make_corner_roi("left"), ROOT / outputs["roi_left_bottom_no_gap"])
    export_model(make_corner_roi("right"), ROOT / outputs["roi_right_bottom_no_gap"])

    metadata = {
        "schema": "tv_leakage_sample_models.v1",
        "units": "mm",
        "coordinate_system": {
            "x": "TV left-right",
            "y": "TV bottom-top",
            "z": "TV rear-front",
        },
        "parts": ["Chassis_Rear", "LCD_Cell_3T", "Frame_Middle_FMB", "Cover_Deco"],
        "models": outputs,
        "full_model_size_mm": [800.0, 450.0, 45.0],
        "roi_model_size_mm": [60.0, 60.0, 45.0],
        "intentional_gap": False,
        "notes": [
            "No-gap assembled baseline model.",
            "Use component transform to create leakage gaps later.",
            "Bottom left/right ROI models are simplified local corner cuts for ray tracing experiments.",
        ],
        "suggested_rt1": {
            "emitter_candidate": "Chassis_Rear inner lower hemming surface around y=18..30, z=24..30",
            "receiver_candidate": "outside front/bottom near Cover_Deco seam, z > 45",
        },
    }
    (ROOT / "tv_leakage_sample_models_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for key, filename in outputs.items():
        print(f"{key}: {ROOT / filename}")
    print(f"metadata: {ROOT / 'tv_leakage_sample_models_metadata.json'}")


if __name__ == "__main__":
    main()
