from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math
import random

from .components import build_face_groups
from .geometry import TriangleMesh, vec_dot
from .types import GapRule, Vec3


@dataclass
class GapSample:
    rule_id: str
    face_index: int
    gap_mm: float
    transmissive: float


def sample_gap_profiles(rules: List[GapRule], rng: random.Random, mesh: TriangleMesh) -> Dict[int, GapSample]:
    results: Dict[int, GapSample] = {}
    component_cache = build_face_groups(mesh, max_faces_per_object=None)
    component_map = {item["object_id"]: item for item in component_cache}

    for rule in rules:
        target_faces = _resolve_target_faces(rule, mesh, component_map)
        if not target_faces:
            continue
        pivot = _resolve_pivot(rule, target_faces, mesh, component_map)
        for face_idx in target_faces:
            if face_idx < 0 or face_idx >= len(mesh.faces):
                continue
            effective_nominal = _effective_face_gap(rule, mesh, face_idx, pivot)
            gap = rng.gauss(effective_nominal, rule.sigma_gap_mm)
            if gap <= 0.0:
                continue
            transmissive = min(1.0, gap / max(0.1, rule.transmissive_threshold))
            results[face_idx] = GapSample(
                rule_id=rule.rule_id,
                face_index=face_idx,
                gap_mm=gap,
                transmissive=transmissive,
            )
    return results


def _resolve_target_faces(rule: GapRule, mesh: TriangleMesh, component_map: Dict[int, Dict]) -> List[int]:
    if rule.gap_mode == "component_move_gap":
        faces: List[int] = []
        for component_id in rule.target_component_ids:
            item = component_map.get(component_id)
            if item:
                faces.extend(item.get("face_indices", []))
        return sorted(set(faces))

    if rule.gap_mode == "bbox_gap":
        return _resolve_bbox_faces(rule, mesh)

    return sorted(set(rule.target_face_indices))


def _resolve_pivot(
    rule: GapRule,
    target_faces: List[int],
    mesh: TriangleMesh,
    component_map: Dict[int, Dict],
) -> Vec3:
    if rule.gap_mode == "component_move_gap" and rule.target_component_ids:
        centers: List[Vec3] = []
        for component_id in rule.target_component_ids:
            item = component_map.get(component_id)
            if not item:
                continue
            bbox_min = item.get("bbox_min")
            bbox_max = item.get("bbox_max")
            if bbox_min and bbox_max:
                centers.append(
                    (
                        (float(bbox_min[0]) + float(bbox_max[0])) * 0.5,
                        (float(bbox_min[1]) + float(bbox_max[1])) * 0.5,
                        (float(bbox_min[2]) + float(bbox_max[2])) * 0.5,
                    )
                )
        if centers:
            return (
                sum(c[0] for c in centers) / len(centers),
                sum(c[1] for c in centers) / len(centers),
                sum(c[2] for c in centers) / len(centers),
            )
    return _centroid_of_faces(target_faces, mesh)


def _effective_face_gap(rule: GapRule, mesh: TriangleMesh, face_idx: int, pivot: Vec3) -> float:
    base_gap = max(0.0, rule.nominal_gap_mm)
    normal = mesh.normal(face_idx)
    translation_gap = _projected_translation_gap(rule.move_vector_mm, normal)
    rotation_gap = _projected_rotation_gap(rule.rotation_vector_deg, mesh.centroid(face_idx), pivot, normal)
    return base_gap + translation_gap + rotation_gap


def _projected_translation_gap(move_vector_mm: Optional[Vec3], normal: Vec3) -> float:
    if move_vector_mm is None:
        return 0.0
    return abs(vec_dot(normal, move_vector_mm))


def _projected_rotation_gap(
    rotation_vector_deg: Optional[Vec3],
    point: Vec3,
    pivot: Vec3,
    normal: Vec3,
) -> float:
    if rotation_vector_deg is None:
        return 0.0
    rotated = _rotate_point(point, pivot, rotation_vector_deg)
    displacement = (
        rotated[0] - point[0],
        rotated[1] - point[1],
        rotated[2] - point[2],
    )
    return abs(vec_dot(normal, displacement))


def _rotate_point(point: Vec3, pivot: Vec3, rotation_vector_deg: Vec3) -> Vec3:
    rx = math.radians(rotation_vector_deg[0])
    ry = math.radians(rotation_vector_deg[1])
    rz = math.radians(rotation_vector_deg[2])
    x = point[0] - pivot[0]
    y = point[1] - pivot[1]
    z = point[2] - pivot[2]

    if abs(rx) > 1e-12:
        cos_x = math.cos(rx)
        sin_x = math.sin(rx)
        y, z = (y * cos_x - z * sin_x, y * sin_x + z * cos_x)

    if abs(ry) > 1e-12:
        cos_y = math.cos(ry)
        sin_y = math.sin(ry)
        x, z = (x * cos_y + z * sin_y, -x * sin_y + z * cos_y)

    if abs(rz) > 1e-12:
        cos_z = math.cos(rz)
        sin_z = math.sin(rz)
        x, y = (x * cos_z - y * sin_z, x * sin_z + y * cos_z)

    return (x + pivot[0], y + pivot[1], z + pivot[2])


def _centroid_of_faces(face_indices: List[int], mesh: TriangleMesh) -> Vec3:
    if not face_indices:
        return (0.0, 0.0, 0.0)
    accum_x = 0.0
    accum_y = 0.0
    accum_z = 0.0
    for face_idx in face_indices:
        cx, cy, cz = mesh.centroid(face_idx)
        accum_x += cx
        accum_y += cy
        accum_z += cz
    inv = 1.0 / float(len(face_indices))
    return (accum_x * inv, accum_y * inv, accum_z * inv)


def _resolve_bbox_faces(rule: GapRule, mesh: TriangleMesh) -> List[int]:
    if rule.bbox_min is None or rule.bbox_max is None:
        return []
    min_x = min(rule.bbox_min[0], rule.bbox_max[0])
    min_y = min(rule.bbox_min[1], rule.bbox_max[1])
    min_z = min(rule.bbox_min[2], rule.bbox_max[2])
    max_x = max(rule.bbox_min[0], rule.bbox_max[0])
    max_y = max(rule.bbox_min[1], rule.bbox_max[1])
    max_z = max(rule.bbox_min[2], rule.bbox_max[2])
    selected: List[int] = []
    for face_idx in range(len(mesh.faces)):
        cx, cy, cz = mesh.centroid(face_idx)
        if min_x <= cx <= max_x and min_y <= cy <= max_y and min_z <= cz <= max_z:
            selected.append(face_idx)
    return selected
