from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import json

from .types import (
    EmitterConfig,
    GapRule,
    MaterialProfile,
    RunConfig,
)
from .materials import build_custom_material_profile, default_material_library, get_material_profile
from .importers import import_geometry
from .roi import build_default_receivers, resolve_receiver_faces
from .raytracer import EngineInput, run_simulation
from .render import export_html_report, export_rendering
from .types import fresh_run_id
from .types import SimulationOutput, ReceiverMetrics


def execute_run(
    input_cad: Optional[str],
    output_dir: str,
    run_config: Optional[RunConfig] = None,
    gaps: Optional[List[GapRule]] = None,
    roi_face_indices: Optional[List[int]] = None,
    emitters: Optional[List[EmitterConfig]] = None,
    material_preset_id: Optional[str] = None,
    material_override: Optional[Dict[str, float]] = None,
    replace_emitters: bool = False,
    out_prefix: str = "run",
    auto_default_gap: bool = True,
) -> Dict:
    config = run_config if run_config is not None else RunConfig()
    import_result = import_geometry(input_cad)
    emitter_list: List[EmitterConfig] = []
    if not (replace_emitters and emitters):
        emitter_list.extend(import_result.emitters)
    if emitters:
        emitter_list.extend(emitters)
    receiver_faces = resolve_receiver_faces(import_result.receiver_face_indices, roi_face_indices)
    receivers = build_default_receivers(receiver_faces)

    materials = default_material_library()
    materials = {key: MaterialProfile(**vars(mat)) for key, mat in materials.items()}
    selected_material_id: Optional[str] = None
    if material_preset_id or material_override:
        base_id = material_preset_id if material_preset_id else "black_pc_resin"
        base = get_material_profile(materials, base_id)
        custom = build_custom_material_profile(base, material_override)
        if custom.material_id != base.material_id:
            materials[custom.material_id] = custom
        selected_material_id = custom.material_id

    if selected_material_id is not None:
        for idx in range(len(import_result.mesh.faces)):
            import_result.mesh.face_material[idx] = selected_material_id

    gap_rules: List[GapRule] = gaps if gaps is not None else []
    if gap_rules:
        for gap in gap_rules:
            if gap.gap_mode == "face_gap" and len(gap.target_face_indices) == 0 and len(receiver_faces) > 0:
                gap.target_face_indices = receiver_faces[: min(3, len(receiver_faces))]
    if auto_default_gap and not gap_rules:
        if len(receiver_faces) > 0:
            gap_rules = [
                GapRule(
                    rule_id="auto_leak_gap",
                    target_face_indices=receiver_faces[: min(3, len(receiver_faces))],
                    nominal_gap_mm=0.08,
                    sigma_gap_mm=0.03,
                    enable_tunnel=True,
                    transmissive_threshold=0.4,
                )
            ]

    engine_input = EngineInput(
        source_file=input_cad,
        mesh=import_result.mesh,
        emitters=emitter_list,
        gap_rules=gap_rules,
        receivers=receivers,
        materials=materials,
        config=config,
        project_name="TV-Leakage-Simulator",
        source_is_synthetic=import_result.synthetic,
        import_note=import_result.note,
    )

    output = run_simulation(engine_input)
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    run_id = out_prefix + "-" + fresh_run_id("result")
    out_json = output_dir_path / f"{run_id}.json"
    out_csv = output_dir_path / f"{run_id}_receiver.csv"
    out_png = output_dir_path / f"{run_id}_heatmap.png"
    out_html = output_dir_path / f"{run_id}_report.html"
    with out_json.open("w", encoding="utf-8") as file:
        json.dump(output.to_dict(), file, ensure_ascii=False, indent=2)
    with out_csv.open("w", encoding="utf-8") as file:
        file.write("receiver_id,peak_nit,mean_nit,p95_nit,area_mm2,area_above_threshold,rays_hit\n")
        for row in output.receiver_metrics:
            file.write(
                ",".join(
                    [
                        row.receiver_id,
                        str(row.peak_nit),
                        str(row.mean_nit),
                        str(row.p95_nit),
                        str(row.area_mm2),
                        str(row.area_above_threshold),
                        str(row.rays_hit),
                    ]
                )
                + "\n"
            )
    exported_png = export_rendering(output, out_png)
    exported_html = export_html_report(
        output,
        out_html,
        exported_png,
        str(out_csv),
        str(out_json),
    )
    return {
        "run_id": output.summary.run_id,
        "json": str(out_json),
        "csv": str(out_csv),
        "heatmap": exported_png,
        "report": exported_html,
        "import_note": import_result.note,
        "synthetic": import_result.synthetic,
        "summary": output.summary.__dict__,
    }


def compare_outputs(base: SimulationOutput, candidate: SimulationOutput) -> Dict:
    base_map = {m.receiver_id: m for m in base.receiver_metrics}
    candidate_map = {m.receiver_id: m for m in candidate.receiver_metrics}
    delta = {}
    for receiver_id in sorted(set(base_map.keys()) | set(candidate_map.keys())):
        base_metric = base_map.get(receiver_id, ReceiverMetrics(receiver_id=receiver_id, irradiance_sum=0.0, peak_nit=0.0, mean_nit=0.0, p95_nit=0.0, area_mm2=0.0, area_above_threshold=0.0, rays_hit=0))
        candidate_metric = candidate_map.get(receiver_id, ReceiverMetrics(receiver_id=receiver_id, irradiance_sum=0.0, peak_nit=0.0, mean_nit=0.0, p95_nit=0.0, area_mm2=0.0, area_above_threshold=0.0, rays_hit=0))
        delta[receiver_id] = {
            "peak_nit_delta": candidate_metric.peak_nit - base_metric.peak_nit,
            "mean_nit_delta": candidate_metric.mean_nit - base_metric.mean_nit,
            "p95_nit_delta": candidate_metric.p95_nit - base_metric.p95_nit,
            "area_above_threshold_delta": candidate_metric.area_above_threshold - base_metric.area_above_threshold,
        }
    return delta
