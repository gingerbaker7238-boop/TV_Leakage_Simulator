from __future__ import annotations

from typing import List, Tuple

from .geometry import TriangleMesh, add_box
from .types import EmitterConfig


def generate_synthetic_leakage_scene() -> Tuple[TriangleMesh, List[EmitterConfig], List[int]]:
    mesh = TriangleMesh()
    frame_material = "black_powder_coated_aluminum"
    cavity_material = "black_pc_resin"
    receiver_material = "white_reference"

    add_box(
        mesh,
        x0=0.0,
        y0=0.0,
        z0=0.0,
        x1=500.0,
        y1=300.0,
        z1=40.0,
        material_id=frame_material,
    )

    receiver_face_indices: List[int] = []
    right_hinge_center = 500.0
    panel_y0 = 80.0
    panel_y1 = 220.0
    panel_z0 = 55.0
    panel_z1 = 95.0
    panel = add_box(
        mesh,
        x0=right_hinge_center,
        y0=panel_y0,
        z0=panel_z0,
        x1=right_hinge_center + 20.0,
        y1=panel_y1,
        z1=panel_z1,
        material_id=receiver_material,
    )
    receiver_face_indices.extend([f for f in panel[-10:] if f in range(len(mesh.faces))])

    add_box(
        mesh,
        x0=50.0,
        y0=70.0,
        z0=5.0,
        x1=150.0,
        y1=230.0,
        z1=16.0,
        material_id=cavity_material,
    )

    source_face_candidates = []
    start = max(0, len(mesh.faces) - 24)
    for i in range(start, start + 4):
        source_face_candidates.append(i)

    emitters = [
        EmitterConfig(
            source_id="internal_bottom_slot",
            emitter_type="face",
            strength=1.0,
            direction_mode="toward_receiver",
            face_index=source_face_candidates[0],
            direction_distribution="isotropic",
        ),
        EmitterConfig(
            source_id="virtual_gap_volume",
            emitter_type="volume_box",
            strength=0.4,
            direction_mode="toward_receiver",
            box_min=(470.0, 120.0, 25.0),
            box_max=(520.0, 180.0, 45.0),
            direction_distribution="isotropic",
        ),
    ]
    return mesh, emitters, receiver_face_indices
