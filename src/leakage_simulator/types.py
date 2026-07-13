from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
import math
import random
import uuid

Vec3 = Tuple[float, float, float]

def clamp(value: float, min_value: float, max_value: float) -> float:
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


@dataclass
class MaterialProfile:
    material_id: str
    name: str
    reflectance_total: float
    diffuse_ratio: float
    specular_ratio: float
    roughness: float
    absorption_ratio: float = 0.0
    alpha: float = 1.0

    def __post_init__(self) -> None:
        self.reflectance_total = clamp(self.reflectance_total, 0.0, 1.0)
        self.diffuse_ratio = clamp(self.diffuse_ratio, 0.0, 1.0)
        self.specular_ratio = clamp(self.specular_ratio, 0.0, 1.0)
        self.absorption_ratio = clamp(self.absorption_ratio, 0.0, 1.0)
        self.alpha = clamp(self.alpha, 0.0, 1.0)


@dataclass
class EmitterConfig:
    source_id: str
    emitter_type: str
    strength: float
    direction_mode: str
    normal_hint: Optional[Vec3] = None
    face_index: Optional[int] = None
    box_min: Optional[Vec3] = None
    box_max: Optional[Vec3] = None
    sphere_center: Optional[Vec3] = None
    sphere_radius: Optional[float] = None
    direction_distribution: str = "isotropic"
    enabled: bool = True


@dataclass
class GapRule:
    rule_id: str
    nominal_gap_mm: float
    target_face_indices: List[int] = field(default_factory=list)
    sigma_gap_mm: float = 0.0
    enable_tunnel: bool = True
    max_depth_penetration: int = 1
    transmissive_threshold: float = 0.4
    gap_mode: str = "face_gap"
    target_component_ids: List[int] = field(default_factory=list)
    move_vector_mm: Optional[Vec3] = None
    rotation_vector_deg: Optional[Vec3] = None
    bbox_min: Optional[Vec3] = None
    bbox_max: Optional[Vec3] = None


@dataclass
class ReceiverPatchConfig:
    receiver_id: str
    face_indices: List[int]
    weight: float = 1.0


@dataclass
class RunConfig:
    ray_count: int = 4000
    max_depth: int = 2
    seed: int = 42
    k_abs: float = 0.12
    k_brdf: float = 1.0
    random_seed: Optional[int] = None


@dataclass
class RunResultSummary:
    run_id: str
    total_rays: int
    hit_count: int
    max_depth: int
    runtime_sec: float
    metadata: Dict


@dataclass
class ReceiverMetrics:
    receiver_id: str
    irradiance_sum: float
    peak_nit: float
    mean_nit: float
    p95_nit: float
    area_mm2: float
    area_above_threshold: float
    rays_hit: int


@dataclass
class SimulationOutput:
    run_id: str
    project_name: str
    source_file: Optional[str]
    summary: RunResultSummary
    receiver_metrics: List[ReceiverMetrics]
    mesh_info: Dict
    emitter_count: int
    gap_rule_count: int

    def to_dict(self) -> Dict:
        return asdict(self)


def fresh_run_id(prefix: str = "run") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def random_unit_vector(rng: random.Random) -> Vec3:
    z = rng.uniform(-1.0, 1.0)
    a = rng.uniform(0.0, 2.0 * math.pi)
    r = math.sqrt(max(0.0, 1.0 - z * z))
    return (r * math.cos(a), r * math.sin(a), z)
