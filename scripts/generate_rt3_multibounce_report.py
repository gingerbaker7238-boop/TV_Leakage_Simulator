from __future__ import annotations

import argparse
import html
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "outputs" / ".matplotlib"))

import matplotlib.pyplot as plt

from leakage_simulator.geometry import TriangleMesh
from leakage_simulator.raytracer import DirectRayTraceInput, run_direct_ray_trace
from leakage_simulator.types import EmitterSpec, OpticalProfile, RayTraceConfig, ReceiverSpec


def add_mirror(
    mesh: TriangleMesh,
    center,
    material_id: str,
    component_id: int,
    half_extent: float = 4.0,
) -> None:
    inverse_root_two = 1.0 / math.sqrt(2.0)
    tangent = (inverse_root_two, 0.0, inverse_root_two)
    vertical = (0.0, 1.0, 0.0)

    def point(tangent_scale: float, vertical_scale: float):
        return (
            center[0] + tangent[0] * tangent_scale + vertical[0] * vertical_scale,
            center[1] + tangent[1] * tangent_scale + vertical[1] * vertical_scale,
            center[2] + tangent[2] * tangent_scale + vertical[2] * vertical_scale,
        )

    points = [
        point(-half_extent, -half_extent),
        point(half_extent, -half_extent),
        point(half_extent, half_extent),
        point(-half_extent, half_extent),
    ]
    vertices = [mesh.add_vertex(value) for value in points]
    metadata = {"component_id": component_id}
    mesh.add_face(vertices[0], vertices[1], vertices[2], material_id, metadata)
    mesh.add_face(vertices[0], vertices[2], vertices[3], material_id, metadata)


def build_input(
    max_depth: int,
    ray_count: int,
    min_energy: float = 1e-12,
    termination_mode: str = "threshold",
    store_paths: bool = False,
) -> DirectRayTraceInput:
    mesh = TriangleMesh()
    add_mirror(mesh, (0.0, 0.0, 10.0), "mirror_a", 101)
    add_mirror(mesh, (10.0, 0.0, 10.0), "mirror_b", 202)
    return DirectRayTraceInput(
        mesh=mesh,
        emitters=[
            EmitterSpec(
                emitter_id="source",
                emitter_type="datum_plane",
                center=(0.0, 0.0, 0.0),
                u_axis=(1.0, 0.0, 0.0),
                v_axis=(0.0, 1.0, 0.0),
                width_mm=0.02,
                height_mm=0.02,
                direction_distribution="gaussian",
                gaussian_sigma_deg=0.001,
                power_lumen=1.0,
                ray_count=ray_count,
                seed=20260721,
            )
        ],
        receivers=[
            ReceiverSpec(
                receiver_id="observer",
                center=(10.0, 0.0, 20.0),
                normal=(0.0, 0.0, -1.0),
                width_mm=4.0,
                height_mm=4.0,
                resolution=(20, 20),
            )
        ],
        optical_profiles=[
            OpticalProfile("mirror_a", 0.8, scatter_model="specular"),
            OpticalProfile("mirror_b", 0.5, scatter_model="specular"),
        ],
        config=RayTraceConfig(
            ray_count=ray_count,
            max_depth=max_depth,
            seed=31,
            min_energy=min_energy,
            termination_mode=termination_mode,
            store_ray_paths=store_paths,
            max_stored_paths=3,
        ),
        project_name="RT-3 two-bounce validation",
    )


def result_row(label: str, result) -> dict:
    reflection = result.metrics["_reflection_summary"]
    return {
        "case": label,
        "max_depth": result.config.max_depth,
        "termination_mode": result.config.termination_mode,
        "min_energy_lumen": result.config.min_energy,
        "receiver_hit_count": result.receiver_hit_count,
        "receiver_hit_ratio": result.receiver_hit_count / max(1, result.total_rays),
        "receiver_flux_lumen": result.metrics["observer"]["total_flux_lumen"],
        "surface_hit_count": result.surface_hit_count,
        "reflection_emitted_count": reflection["reflection_emitted_count"],
        "depth_limit_count": reflection["depth_limit_count"],
        "below_energy_count": reflection["reflection_below_energy_count"],
        "roulette_survived_count": reflection["roulette_survived_count"],
        "roulette_terminated_count": reflection["roulette_terminated_count"],
        "runtime_sec": result.runtime_sec,
    }


def create_figure(depth_results, baseline, threshold_result, roulette_result, output_path: Path) -> None:
    plt.rcParams["axes.unicode_minus"] = False
    figure, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    figure.suptitle("RT-3 Multi-Bounce Validation", fontsize=18, fontweight="bold")

    path = baseline.stored_paths[0]
    path_x = [event.point[0] for event in path]
    path_z = [event.point[2] for event in path]
    axes[0, 0].plot([-2.8, 2.8], [7.2, 12.8], color="#58677c", linewidth=7, label="Mirror A (80%)")
    axes[0, 0].plot([7.2, 12.8], [7.2, 12.8], color="#7c5c58", linewidth=7, label="Mirror B (50%)")
    axes[0, 0].plot(path_x, path_z, color="#ffb000", linewidth=3, marker="o", markersize=6, label="2-bounce ray")
    for index, event in enumerate(path):
        axes[0, 0].annotate(
            f"{event.event_type}\nd={event.depth}",
            (event.point[0], event.point[2]),
            xytext=(6, 7 if index % 2 == 0 else -24),
            textcoords="offset points",
            fontsize=8,
        )
    axes[0, 0].set_title("A. Synthetic two-mirror path")
    axes[0, 0].set_xlabel("X (mm)")
    axes[0, 0].set_ylabel("Z (mm)")
    axes[0, 0].set_xlim(-4, 14)
    axes[0, 0].set_ylim(-1, 22)
    axes[0, 0].grid(alpha=0.25)
    axes[0, 0].legend(loc="lower right", fontsize=8)

    depths = list(range(len(depth_results)))
    flux_values = [result.metrics["observer"]["total_flux_lumen"] for result in depth_results]
    hit_ratios = [result.receiver_hit_count / result.total_rays * 100.0 for result in depth_results]
    bars = axes[0, 1].bar(depths, flux_values, color=["#adb5bd", "#adb5bd", "#2f80ed", "#2f80ed"])
    axes[0, 1].set_title("B. Receiver flux vs. max depth")
    axes[0, 1].set_xlabel("Maximum reflection depth")
    axes[0, 1].set_ylabel("Receiver flux (lumen)")
    axes[0, 1].set_xticks(depths)
    axes[0, 1].set_ylim(0.0, 0.46)
    axes[0, 1].grid(axis="y", alpha=0.25)
    for bar, flux_value, hit_ratio in zip(bars, flux_values, hit_ratios):
        axes[0, 1].text(
            bar.get_x() + bar.get_width() / 2.0,
            max(0.008, flux_value + 0.012),
            f"{flux_value:.3f} lm\n{hit_ratio:.0f}% hit",
            ha="center",
            fontsize=9,
        )

    path_energy = [path[0].outgoing_energy_lumen]
    path_energy.extend(event.outgoing_energy_lumen for event in path if event.event_type == "surface")
    normalized_energy = [value / path_energy[0] for value in path_energy]
    axes[1, 0].plot([0, 1, 2], normalized_energy, color="#d35400", linewidth=3, marker="o", markersize=8)
    axes[1, 0].fill_between([0, 1, 2], normalized_energy, alpha=0.15, color="#d35400")
    axes[1, 0].set_title("C. Energy attenuation per bounce")
    axes[1, 0].set_xlabel("Reflection depth")
    axes[1, 0].set_ylabel("Normalized ray power")
    axes[1, 0].set_xticks([0, 1, 2])
    axes[1, 0].set_ylim(0.0, 1.08)
    axes[1, 0].grid(alpha=0.25)
    for depth, value in enumerate(normalized_energy):
        axes[1, 0].annotate(f"{value:.2f}", (depth, value), xytext=(0, 10), textcoords="offset points", ha="center")

    mode_labels = ["Baseline", "Threshold", "Russian\nroulette"]
    comparison_results = [baseline, threshold_result, roulette_result]
    comparison_flux = [result.metrics["observer"]["total_flux_lumen"] for result in comparison_results]
    comparison_hits = [result.receiver_hit_count / result.total_rays * 100.0 for result in comparison_results]
    bars = axes[1, 1].bar(mode_labels, comparison_flux, color=["#2f80ed", "#c0392b", "#27ae60"])
    axes[1, 1].set_title("D. Low-energy termination comparison")
    axes[1, 1].set_ylabel("Receiver flux (lumen)")
    axes[1, 1].set_ylim(0.0, 0.46)
    axes[1, 1].grid(axis="y", alpha=0.25)
    for bar, flux_value, hit_ratio in zip(bars, comparison_flux, comparison_hits):
        axes[1, 1].text(
            bar.get_x() + bar.get_width() / 2.0,
            max(0.008, flux_value + 0.012),
            f"{flux_value:.3f} lm\n{hit_ratio:.1f}% hit",
            ha="center",
            fontsize=9,
        )

    figure.savefig(output_path, dpi=170, facecolor="white")
    plt.close(figure)


def write_html(rows: list[dict], image_path: Path, output_path: Path) -> None:
    table_rows = []
    for row in rows:
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(row['case'])}</td>"
            f"<td>{row['max_depth']}</td>"
            f"<td>{html.escape(row['termination_mode'])}</td>"
            f"<td>{row['receiver_hit_count']}</td>"
            f"<td>{row['receiver_hit_ratio'] * 100.0:.1f}%</td>"
            f"<td>{row['receiver_flux_lumen']:.6f}</td>"
            f"<td>{row['runtime_sec']:.4f}</td>"
            "</tr>"
        )
    output_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>RT-3 report</title>"
        "<style>body{font-family:Segoe UI,Arial,sans-serif;margin:32px;color:#172033}"
        "h1{margin-bottom:8px}.note{padding:14px 18px;background:#eef5ff;border-left:5px solid #2f80ed}"
        "img{max-width:100%;border:1px solid #d7deea;border-radius:10px;margin:22px 0}"
        "table{border-collapse:collapse;width:100%}th,td{padding:10px;border-bottom:1px solid #d7deea;text-align:right}"
        "th:first-child,td:first-child{text-align:left}th{background:#f3f6fa}</style></head><body>"
        "<h1>RT-3 Multi-Bounce Validation</h1>"
        "<p class='note'>Two specular mirrors require two reflections before the receiver. "
        "The expected optical throughput is 1.0 × 0.8 × 0.5 = 0.4 lumen.</p>"
        f"<img src='{html.escape(image_path.name)}' alt='RT-3 validation chart'>"
        "<table><thead><tr><th>Case</th><th>Depth</th><th>Termination</th><th>Hits</th>"
        "<th>Hit ratio</th><th>Flux (lm)</th><th>Runtime (s)</th></tr></thead><tbody>"
        + "".join(table_rows)
        + "</tbody></table></body></html>",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(ROOT / "outputs" / "rt3_multibounce_report"),
    )
    parser.add_argument("--ray-count", type=int, default=5000)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    depth_results = [
        run_direct_ray_trace(build_input(depth, args.ray_count, store_paths=depth == 2))
        for depth in range(4)
    ]
    baseline = depth_results[2]
    initial_ray_power = 1.0 / args.ray_count
    termination_threshold = initial_ray_power * 0.5
    threshold_result = run_direct_ray_trace(
        build_input(2, args.ray_count, termination_threshold, "threshold")
    )
    roulette_result = run_direct_ray_trace(
        build_input(2, args.ray_count, termination_threshold, "russian_roulette")
    )

    rows = [result_row(f"max_depth={depth}", result) for depth, result in enumerate(depth_results)]
    rows.extend(
        [
            result_row("threshold termination", threshold_result),
            result_row("russian roulette", roulette_result),
        ]
    )
    image_path = output_dir / "rt3_multibounce_validation.png"
    html_path = output_dir / "rt3_multibounce_report.html"
    summary_path = output_dir / "summary.json"
    create_figure(depth_results, baseline, threshold_result, roulette_result, image_path)
    write_html(rows, image_path, html_path)
    summary_path.write_text(
        json.dumps(
            {
                "ray_count": args.ray_count,
                "expected_two_bounce_flux_lumen": 0.4,
                "termination_threshold_lumen": termination_threshold,
                "cases": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"image": str(image_path), "html": str(html_path), "summary": str(summary_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
