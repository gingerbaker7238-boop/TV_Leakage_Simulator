from .engine import compare_outputs, execute_run
from .roi import build_default_receivers, build_scene_payload, resolve_receiver_faces
from .raytracer import run_simulation
from .types import (
    MaterialProfile,
    EmitterConfig,
    GapRule,
    ReceiverPatchConfig,
    RunConfig,
    ReceiverMetrics,
    SimulationOutput,
)

__all__ = [
    "execute_run",
    "compare_outputs",
    "build_default_receivers",
    "build_scene_payload",
    "resolve_receiver_faces",
    "MaterialProfile",
    "EmitterConfig",
    "GapRule",
    "ReceiverPatchConfig",
    "RunConfig",
    "ReceiverMetrics",
    "SimulationOutput",
    "run_simulation",
]
