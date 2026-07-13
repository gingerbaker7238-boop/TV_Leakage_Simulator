from __future__ import annotations

from collections import defaultdict, deque
from math import inf
from typing import Dict, List, Optional, Set, Tuple


def build_face_groups(mesh, max_faces_per_object: Optional[int] = 4000) -> List[Dict]:
    face_count = len(mesh.faces)
    if face_count == 0:
        return []

    adjacency: List[Set[int]] = [set() for _ in range(face_count)]
    edge_map: Dict[Tuple[int, int], List[int]] = defaultdict(list)

    for idx, face in enumerate(mesh.faces):
        tri = (face.v0, face.v1, face.v2)
        edges = ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0]))
        for a, b in edges:
            key = (a, b) if a < b else (b, a)
            edge_map[key].append(idx)

    for face_indices in edge_map.values():
        for i in range(len(face_indices)):
            a = face_indices[i]
            for j in range(i + 1, len(face_indices)):
                b = face_indices[j]
                adjacency[a].add(b)
                adjacency[b].add(a)

    visited = [False] * face_count
    components: List[Dict] = []
    for start in range(face_count):
        if visited[start]:
            continue
        queue = deque([start])
        visited[start] = True
        face_indices: List[int] = []
        while queue:
            i = queue.popleft()
            face_indices.append(i)
            for nxt in adjacency[i]:
                if not visited[nxt]:
                    visited[nxt] = True
                    queue.append(nxt)

        face_indices.sort()
        min_x = inf
        min_y = inf
        min_z = inf
        max_x = -inf
        max_y = -inf
        max_z = -inf
        area = 0.0
        for fidx in face_indices:
            a, b, c = mesh.face_vertices(fidx)
            area += mesh.area(fidx)
            for vx, vy, vz in (a, b, c):
                min_x = min(min_x, vx)
                max_x = max(max_x, vx)
                min_y = min(min_y, vy)
                max_y = max(max_y, vy)
                min_z = min(min_z, vz)
                max_z = max(max_z, vz)

        if max_faces_per_object is None:
            export_faces = face_indices
            is_truncated = False
        else:
            export_faces = face_indices[: max_faces_per_object + 1]
            is_truncated = len(face_indices) > max_faces_per_object

        components.append(
            {
                "object_name": "Part {}".format(len(components) + 1),
                "object_id": len(components),
                "face_indices": export_faces,
                "face_count": len(face_indices),
                "area_mm2": round(area, 3),
                "bbox_min": [round(min_x, 3), round(min_y, 3), round(min_z, 3)],
                "bbox_max": [round(max_x, 3), round(max_y, 3), round(max_z, 3)],
                "is_truncated": is_truncated,
            }
        )

    components.sort(key=lambda item: item["area_mm2"], reverse=True)
    for idx, item in enumerate(components):
        item["object_id"] = idx
    return components
