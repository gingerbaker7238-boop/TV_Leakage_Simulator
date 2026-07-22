from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leakage_simulator.geometry import TriangleMesh
from leakage_simulator.roi import (
    build_point_selection,
    group_faces_by_component,
    resolve_faces_in_xy_box,
    resolve_faces_in_xy_box_grouped,
    resolve_nearest_face_to_point,
)


def build_test_scene() -> tuple[TriangleMesh, list[int | None]]:
    """Three quads (2 triangles each), matching the BLU-stack-shaped test
    case discussed in the plan doc:
    - component 0 ("Frame"): z=0,  x:[0,10] y:[0,10]
    - component 1 ("LGP"):   z=5,  x:[0,10] y:[0,10]  (same XY, different Z -
      this is what proves the box acts as a Z-unbounded prism)
    - component 2 ("Bezel"): z=0,  x:[100,110] y:[100,110] (outside the box
      entirely, in XY)
    """
    mesh = TriangleMesh()
    face_component_ids: list[int | None] = []

    def add_quad(component_id: int, z: float, x0: float, y0: float, x1: float, y1: float) -> None:
        v0 = mesh.add_vertex((x0, y0, z))
        v1 = mesh.add_vertex((x1, y0, z))
        v2 = mesh.add_vertex((x1, y1, z))
        v3 = mesh.add_vertex((x0, y1, z))
        mesh.add_face(v0, v1, v2, "mat")
        face_component_ids.append(component_id)
        mesh.add_face(v0, v2, v3, "mat")
        face_component_ids.append(component_id)

    add_quad(0, 0.0, 0.0, 0.0, 10.0, 10.0)   # Frame
    add_quad(1, 5.0, 0.0, 0.0, 10.0, 10.0)   # LGP - same XY, different Z
    add_quad(2, 0.0, 100.0, 100.0, 110.0, 110.0)  # Bezel - outside the box

    return mesh, face_component_ids


class ResolveFacesInXyBoxTests(unittest.TestCase):
    def test_includes_faces_regardless_of_z_depth(self) -> None:
        mesh, face_component_ids = build_test_scene()
        result = resolve_faces_in_xy_box(mesh, 2.0, 8.0, 2.0, 8.0, face_component_ids)

        included_components = {face_component_ids[i] for i in result}
        self.assertIn(0, included_components)
        self.assertIn(1, included_components, "different Z should not exclude a face - box is an infinite prism")
        self.assertNotIn(2, included_components, "Bezel is outside the box in XY and must be excluded")

    def test_hidden_component_excluded_even_if_xy_overlaps(self) -> None:
        mesh, face_component_ids = build_test_scene()
        # LGP (component 1) hidden - only Frame (0) is visible, even though
        # LGP shares the same XY footprint and would otherwise match.
        result = resolve_faces_in_xy_box(
            mesh, 2.0, 8.0, 2.0, 8.0, face_component_ids, visible_component_ids={0}
        )
        included_components = {face_component_ids[i] for i in result}
        self.assertEqual(included_components, {0})

    def test_box_outside_everything_returns_empty(self) -> None:
        mesh, face_component_ids = build_test_scene()
        result = resolve_faces_in_xy_box(mesh, 500.0, 600.0, 500.0, 600.0, face_component_ids)
        self.assertEqual(result, [])

    def test_box_touching_the_far_corner_includes_the_face(self) -> None:
        # The Frame quad's corner at (10, 10) genuinely sits inside this
        # box, so this is real geometric intersection (not a bounding-box
        # false positive) - it must be included.
        mesh, face_component_ids = build_test_scene()
        result = resolve_faces_in_xy_box(mesh, 8.0, 20.0, 8.0, 20.0, face_component_ids)
        included_components = {face_component_ids[i] for i in result}
        self.assertIn(0, included_components)

    def test_box_missing_a_triangles_actual_shape_excludes_just_that_triangle(self) -> None:
        # Frame's two triangles perfectly tile [0,10]x[0,10] along the
        # y=x diagonal: face 0 = (0,0)-(10,0)-(10,10) covers y<=x (the
        # lower-right half), face 1 = (0,0)-(10,10)-(0,10) covers y>=x
        # (the upper-left half). Both share the same bounding box
        # [0,10]x[0,10], but this box sits only in face 1's actual
        # region (vertex (0,10) is inside it) and never touches face 0's
        # real shape - a naive "does the box overlap the bounding box"
        # test would wrongly include face 0 too, since its bbox is the
        # same square. True triangle-vs-box intersection must only match
        # face 1.
        mesh, face_component_ids = build_test_scene()
        result = resolve_faces_in_xy_box(mesh, 0.0, 3.0, 7.0, 10.0, face_component_ids)
        frame_faces = sorted(i for i in result if face_component_ids[i] == 0)
        self.assertEqual(frame_faces, [1])


class GroupFacesByComponentTests(unittest.TestCase):
    def test_groups_and_sums_area_per_component(self) -> None:
        mesh, face_component_ids = build_test_scene()
        face_indices = resolve_faces_in_xy_box(mesh, 2.0, 8.0, 2.0, 8.0, face_component_ids)
        groups = group_faces_by_component(
            mesh, face_indices, face_component_ids, component_names={0: "Frame", 1: "LGP"}
        )

        by_id = {g.component_id: g for g in groups}
        self.assertEqual(set(by_id.keys()), {0, 1})
        self.assertEqual(by_id[0].component_name, "Frame")
        self.assertEqual(by_id[1].component_name, "LGP")
        # Each quad is 10x10 = 100mm^2 total, both triangles included.
        self.assertAlmostEqual(by_id[0].area_mm2, 100.0, places=6)
        self.assertAlmostEqual(by_id[1].area_mm2, 100.0, places=6)
        self.assertEqual(by_id[0].bbox_min[2], 0.0)
        self.assertEqual(by_id[1].bbox_min[2], 5.0)


class ResolveFacesInXyBoxGroupedTests(unittest.TestCase):
    def test_end_to_end_shape(self) -> None:
        mesh, face_component_ids = build_test_scene()
        result = resolve_faces_in_xy_box_grouped(
            mesh, 2.0, 8.0, 2.0, 8.0, face_component_ids,
            visible_component_ids={0, 1},
            scope_id="bottom-corner",
            view="front_xy",
        )
        self.assertEqual(result.scope_id, "bottom-corner")
        self.assertEqual(result.view, "front_xy")
        self.assertEqual({c.component_id for c in result.components}, {0, 1})
        self.assertEqual(set(result.face_indices), set(result.face_indices))  # flattened accessor works
        self.assertEqual(len(result.face_indices), sum(len(c.face_indices) for c in result.components))


class ResolveNearestFaceToPointTests(unittest.TestCase):
    def test_finds_nearest_face(self) -> None:
        mesh, face_component_ids = build_test_scene()
        # Closest to the Frame quad's centroid area (z=0 side).
        face_index = resolve_nearest_face_to_point(mesh, (5.0, 5.0, 0.1), face_component_ids)
        self.assertIsNotNone(face_index)
        self.assertEqual(face_component_ids[face_index], 0)

    def test_hidden_component_excluded_from_search(self) -> None:
        mesh, face_component_ids = build_test_scene()
        # Same point, but Frame (0) is hidden - nearest eligible should be LGP (1).
        face_index = resolve_nearest_face_to_point(
            mesh, (5.0, 5.0, 0.1), face_component_ids, visible_component_ids={1, 2}
        )
        self.assertIsNotNone(face_index)
        self.assertEqual(face_component_ids[face_index], 1)

    def test_build_point_selection_wraps_result(self) -> None:
        mesh, face_component_ids = build_test_scene()
        selection = build_point_selection(mesh, (5.0, 5.0, 0.1), face_component_ids, note="corner-check")
        self.assertEqual(selection.coordinate, (5.0, 5.0, 0.1))
        self.assertEqual(selection.component_id, 0)
        self.assertEqual(selection.note, "corner-check")


if __name__ == "__main__":
    unittest.main()
