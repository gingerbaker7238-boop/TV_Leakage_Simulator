from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

from .types import Vec3, clamp


def vec_add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_mul(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def vec_div(a: Vec3, s: float) -> Vec3:
    return (a[0] / s, a[1] / s, a[2] / s)


def vec_dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec_cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vec_len(a: Vec3) -> float:
    return math.sqrt(vec_dot(a, a))


def vec_norm(a: Vec3) -> Vec3:
    length = vec_len(a)
    if length < 1e-12:
        return (0.0, 0.0, 1.0)
    return vec_div(a, length)


def vec_reflect(v: Vec3, n: Vec3) -> Vec3:
    scale = 2.0 * vec_dot(v, n)
    return vec_sub(v, vec_mul(n, scale))


def clamp01(value: float) -> float:
    return clamp(value, 0.0, 1.0)


def sample_point_on_triangle(
    a: Vec3, b: Vec3, c: Vec3, u: float, v: float
) -> Vec3:
    return vec_add(
        vec_add(a, vec_mul(vec_sub(b, a), u)),
        vec_mul(vec_sub(c, a), v),
    )


def face_area(a: Vec3, b: Vec3, c: Vec3) -> float:
    return 0.5 * vec_len(vec_cross(vec_sub(b, a), vec_sub(c, a)))


def face_normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    n = vec_norm(vec_cross(vec_sub(b, a), vec_sub(c, a)))
    return n


def midpoint(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    return ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0, (a[2] + b[2] + c[2]) / 3.0)


@dataclass
class TriangleFace:
    v0: int
    v1: int
    v2: int


@dataclass
class HitRecord:
    t: float
    point: Vec3
    normal: Vec3
    face_index: int
    triangle: TriangleFace


class TriangleMesh:
    def __init__(self) -> None:
        self.vertices: List[Vec3] = []
        self.faces: List[TriangleFace] = []
        self.face_material: Dict[int, str] = {}
        self.face_metadata: Dict[int, Dict] = {}

    def add_vertex(self, vertex: Vec3) -> int:
        self.vertices.append(vertex)
        return len(self.vertices) - 1

    def add_face(
        self,
        v0: int,
        v1: int,
        v2: int,
        material_id: str,
        metadata: Optional[Dict] = None,
    ) -> int:
        face = TriangleFace(v0=v0, v1=v1, v2=v2)
        self.faces.append(face)
        idx = len(self.faces) - 1
        self.face_material[idx] = material_id
        self.face_metadata[idx] = metadata if metadata is not None else {}
        return idx

    def face_vertices(self, index: int) -> Tuple[Vec3, Vec3, Vec3]:
        face = self.faces[index]
        return (
            self.vertices[face.v0],
            self.vertices[face.v1],
            self.vertices[face.v2],
        )

    def area(self, index: int) -> float:
        a, b, c = self.face_vertices(index)
        return face_area(a, b, c)

    def centroid(self, index: int) -> Vec3:
        a, b, c = self.face_vertices(index)
        return midpoint(a, b, c)

    def normal(self, index: int) -> Vec3:
        a, b, c = self.face_vertices(index)
        return face_normal(a, b, c)

    def material_id(self, index: int) -> str:
        return self.face_material.get(index, "")

    def metadata(self, index: int) -> Dict:
        return self.face_metadata.get(index, {})

    def intersect_ray(self, origin: Vec3, direction: Vec3, ignore_face: Optional[int] = None) -> Optional[HitRecord]:
        best: Optional[HitRecord] = None
        eps = 1e-8
        for idx, face in enumerate(self.faces):
            if ignore_face is not None and idx == ignore_face:
                continue
            v0, v1, v2 = self.face_vertices(idx)
            e1 = vec_sub(v1, v0)
            e2 = vec_sub(v2, v0)
            p = vec_cross(direction, e2)
            det = vec_dot(e1, p)
            if abs(det) < eps:
                continue
            inv_det = 1.0 / det
            tvec = vec_sub(origin, v0)
            u = vec_dot(tvec, p) * inv_det
            if u < 0.0 or u > 1.0:
                continue
            q = vec_cross(tvec, e1)
            v = vec_dot(direction, q) * inv_det
            if v < 0.0 or u + v > 1.0:
                continue
            t = vec_dot(e2, q) * inv_det
            if t < eps:
                continue
            if best is None or t < best.t:
                pnt = vec_add(origin, vec_mul(direction, t))
                n = vec_norm(vec_cross(e1, e2))
                if vec_dot(n, direction) > 0.0:
                    n = vec_mul(n, -1.0)
                best = HitRecord(t=t, point=pnt, normal=n, face_index=idx, triangle=face)
        return best


def add_box(
    mesh: TriangleMesh,
    x0: float,
    y0: float,
    z0: float,
    x1: float,
    y1: float,
    z1: float,
    material_id: str,
    metadata: Optional[Dict] = None,
) -> List[int]:
    vs = [
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    ]
    idx = [mesh.add_vertex(v) for v in vs]
    i0, i1, i2, i3, i4, i5, i6, i7 = idx
    mesh.add_face(i0, i1, i2, material_id, metadata)
    mesh.add_face(i0, i2, i3, material_id, metadata)
    mesh.add_face(i4, i6, i5, material_id, metadata)
    mesh.add_face(i4, i7, i6, material_id, metadata)
    mesh.add_face(i0, i4, i5, material_id, metadata)
    mesh.add_face(i0, i5, i1, material_id, metadata)
    mesh.add_face(i3, i2, i6, material_id, metadata)
    mesh.add_face(i3, i6, i7, material_id, metadata)
    mesh.add_face(i0, i3, i7, material_id, metadata)
    mesh.add_face(i0, i7, i4, material_id, metadata)
    mesh.add_face(i1, i5, i6, material_id, metadata)
    mesh.add_face(i1, i6, i2, material_id, metadata)
    return list(range(len(mesh.faces) - 12, len(mesh.faces)))
