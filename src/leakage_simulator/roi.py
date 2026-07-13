from __future__ import annotations

from typing import Dict, List, Optional

from .components import build_face_groups
from .importers import import_geometry
from .types import ReceiverPatchConfig


def build_default_receivers(
    face_indices: List[int],
    name: str = "viewer_side",
) -> List[ReceiverPatchConfig]:
    return [ReceiverPatchConfig(receiver_id=name, face_indices=face_indices, weight=1.0)]


def resolve_receiver_faces(
    import_receiver_faces: List[int],
    roi_face_indices: Optional[List[int]],
) -> List[int]:
    if roi_face_indices:
        return roi_face_indices
    return import_receiver_faces


def build_scene_payload(cad_path: Optional[str]) -> Dict:
    import_result = import_geometry(cad_path)
    mesh = import_result.mesh
    objects = build_face_groups(mesh, max_faces_per_object=None)
    return {
        "mesh": {
            "vertices": [[round(v[0], 6), round(v[1], 6), round(v[2], 6)] for v in mesh.vertices],
            "faces": [[face.v0, face.v1, face.v2] for face in mesh.faces],
        },
        "objects": objects,
        "metadata": {
            "face_count": len(mesh.faces),
            "vertex_count": len(mesh.vertices),
            "source_file": cad_path or "",
            "synthetic": import_result.synthetic,
            "import_note": import_result.note,
            "receiver_face_hint": import_result.receiver_face_indices[
                : min(30, len(import_result.receiver_face_indices))
            ],
        },
    }
