from __future__ import annotations

import argparse
from typing import Dict, List, Optional, Tuple

from .engine import execute_run
from .materials import default_material_library
from .types import EmitterConfig, GapRule, RunConfig


def _parse_int_list(raw: Optional[str]) -> Optional[List[int]]:
    if not raw:
        return None
    out: List[int] = []
    for token in raw.split(","):
        token = token.strip()
        if token:
            out.append(int(token))
    return out


def _parse_float_tuple(raw: Optional[str]) -> Optional[Tuple[float, float, float]]:
    if not raw:
        return None
    vals = [float(v.strip()) for v in raw.split(",") if v.strip()]
    if len(vals) != 3:
        raise argparse.ArgumentTypeError("tuple string must be x,y,z")
    return (vals[0], vals[1], vals[2])


def _parse_gap_rule(args: argparse.Namespace) -> GapRule:
    return GapRule(
        rule_id="cli_gap_rule",
        target_face_indices=_parse_int_list(args.gap_face_indices) or [],
        nominal_gap_mm=args.gap_nominal,
        sigma_gap_mm=args.gap_sigma,
        enable_tunnel=True,
        transmissive_threshold=args.gap_transmissive_threshold,
        gap_mode=args.gap_mode,
        target_component_ids=_parse_int_list(args.gap_component_ids) or [],
        move_vector_mm=_parse_float_tuple(args.gap_move_xyz),
        rotation_vector_deg=_parse_float_tuple(args.gap_tilt_xyz),
        bbox_min=_parse_float_tuple(args.gap_box_min),
        bbox_max=_parse_float_tuple(args.gap_box_max),
    )


def _parse_material_override(args: argparse.Namespace) -> Optional[Dict[str, float]]:
    parsed: Dict[str, float] = {}
    for key in [
        "material_reflectance",
        "material_diffuse",
        "material_specular",
        "material_roughness",
        "material_absorption",
        "material_alpha",
    ]:
        value = getattr(args, key)
        if value is not None:
            parsed[key.replace("material_", "")] = value
    return parsed or None


def _build_custom_emitter(args: argparse.Namespace) -> Optional[EmitterConfig]:
    if not args.emitter_type:
        return None
    return EmitterConfig(
        source_id="custom_emitter",
        emitter_type=args.emitter_type,
        strength=args.emitter_strength,
        direction_mode=args.emitter_direction_mode,
        direction_distribution=args.emitter_direction_distribution,
        face_index=args.emitter_face_index,
        normal_hint=_parse_float_tuple(args.emitter_normal_hint),
        box_min=_parse_float_tuple(args.emitter_box_min),
        box_max=_parse_float_tuple(args.emitter_box_max),
        sphere_center=_parse_float_tuple(args.emitter_sphere_center),
        sphere_radius=args.emitter_sphere_radius,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TV leakage simulator V1")
    parser.add_argument("--cad", type=str, default=None)
    parser.add_argument("--output", type=str, default="outputs")
    parser.add_argument("--rays", type=int, default=4000)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--k-abs", type=float, default=0.12)
    parser.add_argument("--k-brdf", type=float, default=1.0)
    parser.add_argument("--gap-nominal", type=float, default=0.08)
    parser.add_argument("--gap-sigma", type=float, default=0.03)
    parser.add_argument("--gap-transmissive-threshold", type=float, default=0.4)
    parser.add_argument("--gap-mode", type=str, default="face_gap", choices=["face_gap", "component_move_gap", "bbox_gap"])
    parser.add_argument("--gap-face-indices", type=str, default=None)
    parser.add_argument("--gap-component-ids", type=str, default=None)
    parser.add_argument("--gap-move-xyz", type=str, default=None, help="x,y,z")
    parser.add_argument("--gap-tilt-xyz", type=str, default=None, help="rx,ry,rz in deg")
    parser.add_argument("--gap-box-min", type=str, default=None, help="x,y,z")
    parser.add_argument("--gap-box-max", type=str, default=None, help="x,y,z")
    parser.add_argument("--roi-face-indices", type=str, default=None)
    parser.add_argument("--replace-import-emitter", action="store_true", default=False)

    parser.add_argument("--emitter-type", type=str, default=None, choices=["face", "volume_box", "volume_sphere"])
    parser.add_argument("--emitter-strength", type=float, default=1.0)
    parser.add_argument("--emitter-face-index", type=int, default=None)
    parser.add_argument("--emitter-normal-hint", type=str, default=None, help="x,y,z")
    parser.add_argument("--emitter-direction-mode", type=str, default="toward_receiver")
    parser.add_argument("--emitter-direction-distribution", type=str, default="isotropic")
    parser.add_argument("--emitter-box-min", type=str, default=None, help="x,y,z")
    parser.add_argument("--emitter-box-max", type=str, default=None, help="x,y,z")
    parser.add_argument("--emitter-sphere-center", type=str, default=None, help="x,y,z")
    parser.add_argument("--emitter-sphere-radius", type=float, default=None)

    library = default_material_library()
    parser.add_argument("--material-preset", type=str, default=None, choices=list(library.keys()))
    parser.add_argument("--material-reflectance", type=float, default=None)
    parser.add_argument("--material-diffuse", type=float, default=None)
    parser.add_argument("--material-specular", type=float, default=None)
    parser.add_argument("--material-roughness", type=float, default=None)
    parser.add_argument("--material-absorption", type=float, default=None)
    parser.add_argument("--material-alpha", type=float, default=None)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = RunConfig(
        ray_count=args.rays,
        max_depth=args.max_depth,
        seed=args.seed,
        k_abs=args.k_abs,
        k_brdf=args.k_brdf,
    )
    run_emitter = _build_custom_emitter(args)
    emitter_list = [run_emitter] if run_emitter else None
    roi_faces = _parse_int_list(args.roi_face_indices)
    output = execute_run(
        input_cad=args.cad,
        output_dir=args.output,
        run_config=config,
        gaps=[_parse_gap_rule(args)],
        roi_face_indices=roi_faces,
        emitters=emitter_list,
        replace_emitters=args.replace_import_emitter and emitter_list is not None,
        material_preset_id=args.material_preset,
        material_override=_parse_material_override(args),
        out_prefix="run",
    )
    print(output["run_id"])
    print(output["json"])
    print(output["csv"])
    if output["heatmap"]:
        print(output["heatmap"])
    if output.get("report"):
        print(output["report"])


if __name__ == "__main__":
    main()
