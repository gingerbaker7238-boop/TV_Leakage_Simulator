from __future__ import annotations

from typing import Dict, Optional

from .types import MaterialProfile


def default_material_library() -> Dict[str, MaterialProfile]:
    return {
        "black_powder_coated_aluminum": MaterialProfile(
            material_id="black_powder_coated_aluminum",
            name="Black powder coated aluminum",
            reflectance_total=0.12,
            diffuse_ratio=0.85,
            specular_ratio=0.15,
            roughness=0.7,
            absorption_ratio=0.1,
            alpha=0.96,
        ),
        "black_pc_resin": MaterialProfile(
            material_id="black_pc_resin",
            name="Black PC resin",
            reflectance_total=0.06,
            diffuse_ratio=0.92,
            specular_ratio=0.08,
            roughness=0.85,
            absorption_ratio=0.2,
            alpha=0.98,
        ),
        "anodized_aluminum": MaterialProfile(
            material_id="anodized_aluminum",
            name="Anodized aluminum",
            reflectance_total=0.18,
            diffuse_ratio=0.7,
            specular_ratio=0.3,
            roughness=0.5,
            absorption_ratio=0.05,
            alpha=1.0,
        ),
        "matte_black_abs": MaterialProfile(
            material_id="matte_black_abs",
            name="Matte black ABS",
            reflectance_total=0.08,
            diffuse_ratio=0.88,
            specular_ratio=0.12,
            roughness=0.9,
            absorption_ratio=0.2,
            alpha=1.0,
        ),
        "white_reference": MaterialProfile(
            material_id="white_reference",
            name="Reference white",
            reflectance_total=0.9,
            diffuse_ratio=0.95,
            specular_ratio=0.05,
            roughness=0.2,
            absorption_ratio=0.0,
            alpha=1.0,
        ),
    }


def get_material_profile(material_library: Dict[str, MaterialProfile], material_id: str) -> MaterialProfile:
    return material_library.get(material_id, material_library["black_pc_resin"])


def build_custom_material_profile(
    base: MaterialProfile,
    override: Optional[Dict[str, float]] = None,
) -> MaterialProfile:
    if not override:
        return base
    return MaterialProfile(
        material_id=f"{base.material_id}_custom",
        name=f"{base.name} (Custom)",
        reflectance_total=override.get("reflectance_total", base.reflectance_total),
        diffuse_ratio=override.get("diffuse_ratio", base.diffuse_ratio),
        specular_ratio=override.get("specular_ratio", base.specular_ratio),
        roughness=override.get("roughness", base.roughness),
        absorption_ratio=override.get("absorption_ratio", base.absorption_ratio),
        alpha=override.get("alpha", base.alpha),
    )
