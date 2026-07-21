from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leakage_simulator.geometry import TriangleMesh
from leakage_simulator.raytracer import DirectRayTraceInput, run_direct_ray_trace
from leakage_simulator.types import EmitterSpec, OpticalProfile, RayTraceConfig, ReceiverSpec


def add_quad(
    mesh: TriangleMesh,
    points,
    material_id: str,
    component_id: int,
) -> None:
    vertices = [mesh.add_vertex(point) for point in points]
    metadata = {"component_id": component_id}
    mesh.add_face(vertices[0], vertices[1], vertices[2], material_id, metadata)
    mesh.add_face(vertices[0], vertices[2], vertices[3], material_id, metadata)


def direct_input(ray_count: int = 300) -> DirectRayTraceInput:
    emitter = EmitterSpec(
        emitter_id="direct_source",
        emitter_type="datum_plane",
        center=(0.0, 0.0, 0.0),
        u_axis=(1.0, 0.0, 0.0),
        v_axis=(0.0, 1.0, 0.0),
        width_mm=0.2,
        height_mm=0.2,
        direction_distribution="gaussian",
        gaussian_sigma_deg=0.01,
        power_lumen=1.0,
        ray_count=ray_count,
        seed=101,
    )
    receiver = ReceiverSpec(
        receiver_id="front_receiver",
        center=(0.0, 0.0, 10.0),
        normal=(0.0, 0.0, -1.0),
        width_mm=10.0,
        height_mm=10.0,
        resolution=(8, 8),
    )
    return DirectRayTraceInput(
        mesh=TriangleMesh(),
        emitters=[emitter],
        receivers=[receiver],
        optical_profiles=[],
        config=RayTraceConfig(
            ray_count=ray_count,
            max_depth=0,
            seed=11,
            contribution_mode="detailed",
        ),
    )


def reflected_input(ray_count: int = 500, with_blocker: bool = False) -> DirectRayTraceInput:
    mesh = TriangleMesh()
    add_quad(
        mesh,
        [
            (-10.0, -10.0, 0.0),
            (10.0, -10.0, 20.0),
            (10.0, 10.0, 20.0),
            (-10.0, 10.0, 0.0),
        ],
        material_id="reflector",
        component_id=10,
    )
    if with_blocker:
        add_quad(
            mesh,
            [
                (8.0, -5.0, 5.0),
                (8.0, 5.0, 5.0),
                (8.0, 5.0, 15.0),
                (8.0, -5.0, 15.0),
            ],
            material_id="blocker",
            component_id=20,
        )
    emitter = EmitterSpec(
        emitter_id="reflection_source",
        emitter_type="datum_plane",
        center=(0.0, 0.0, 0.0),
        u_axis=(1.0, 0.0, 0.0),
        v_axis=(0.0, 1.0, 0.0),
        width_mm=0.1,
        height_mm=0.1,
        direction_distribution="gaussian",
        gaussian_sigma_deg=0.01,
        power_lumen=1.0,
        ray_count=ray_count,
        seed=77,
    )
    receiver = ReceiverSpec(
        receiver_id="side_receiver",
        center=(15.0, 0.0, 10.0),
        normal=(-1.0, 0.0, 0.0),
        width_mm=10.0,
        height_mm=10.0,
        resolution=(10, 10),
    )
    return DirectRayTraceInput(
        mesh=mesh,
        emitters=[emitter],
        receivers=[receiver],
        optical_profiles=[
            OpticalProfile("reflector", 0.5, scatter_model="specular"),
            OpticalProfile("blocker", 0.0, scatter_model="none"),
        ],
        config=RayTraceConfig(
            ray_count=ray_count,
            max_depth=1,
            seed=13,
            contribution_mode="detailed",
        ),
    )


class ContributionRT2DATests(unittest.TestCase):
    def test_direct_flux_is_split_per_receiver(self) -> None:
        result = run_direct_ray_trace(direct_input())
        summary = result.contribution_summary
        receiver = summary.receivers["front_receiver"]

        self.assertEqual(summary.schema_version, "rt-contribution.v1")
        self.assertEqual(summary.direct_receiver_hit_count, 300)
        self.assertEqual(summary.reflected_receiver_hit_count, 0)
        self.assertAlmostEqual(summary.direct_receiver_flux_lumen, 1.0, places=7)
        self.assertEqual(receiver["direct"]["hit_count"], 300)
        self.assertAlmostEqual(receiver["total"]["flux_lumen"], 1.0, places=7)
        self.assertEqual(summary.components, {})

    def test_reflector_contribution_tracks_component_face_material_and_lobe(self) -> None:
        result = run_direct_ray_trace(reflected_input())
        summary = result.contribution_summary
        component = summary.components["10"]
        material = summary.materials["reflector"]
        face_primary_hits = sum(item["primary_hit_count"] for item in summary.faces.values())

        self.assertEqual(summary.reflected_receiver_hit_count, 500)
        self.assertAlmostEqual(summary.reflected_receiver_flux_lumen, 0.5, places=7)
        self.assertEqual(component["primary_hit_count"], 500)
        self.assertEqual(component["reflection_emitted_count"], 500)
        self.assertEqual(component["receiver_hit_count"], 500)
        self.assertAlmostEqual(component["receiver_flux_lumen"], 0.5, places=7)
        self.assertEqual(material["receiver_hit_count"], 500)
        self.assertEqual(face_primary_hits, 500)
        self.assertEqual(summary.lobes["specular"]["receiver_hit_count"], 500)

    def test_secondary_blocker_is_distinguished_from_reflector_outcome(self) -> None:
        result = run_direct_ray_trace(reflected_input(with_blocker=True))
        summary = result.contribution_summary
        reflector = summary.components["10"]
        blocker = summary.components["20"]

        self.assertEqual(result.receiver_hit_count, 0)
        self.assertGreater(reflector["reflection_blocked_count"], 490)
        self.assertGreater(reflector["reflection_blocked_flux_lumen"], 0.49)
        self.assertGreater(blocker["secondary_block_count"], 490)
        self.assertGreater(blocker["secondary_blocked_flux_lumen"], 0.49)
        self.assertGreater(summary.materials["blocker"]["secondary_block_count"], 490)
        self.assertGreater(summary.lobes["specular"]["blocked_count"], 490)

    def test_contribution_contract_is_serialized_at_top_level_and_metrics(self) -> None:
        payload = run_direct_ray_trace(direct_input(ray_count=20)).to_dict()

        self.assertEqual(
            payload["contribution_summary"]["schema_version"],
            "rt-contribution.v1",
        )
        self.assertEqual(
            payload["metrics"]["_contribution_summary"],
            payload["contribution_summary"],
        )


if __name__ == "__main__":
    unittest.main()
