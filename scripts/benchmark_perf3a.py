from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "outputs" / ".matplotlib"))

import matplotlib.pyplot as plt

from generate_rt2c_reflection_report import build_model_input
from leakage_simulator.raytracer import run_direct_ray_trace


RT2D_BASELINE_SEC = 21.490163564682007
RT3_PRE_PERF3A_SEC = 25.094383001327515


def run_case(contribution_mode: str, ray_count: int) -> dict:
    trace_input = build_model_input("gaussian")
    trace_input.emitters[0].ray_count = ray_count
    trace_input.config.ray_count = ray_count
    trace_input.config.max_depth = 1
    trace_input.config.contribution_mode = contribution_mode
    trace_input.config.store_ray_paths = False
    start = time.perf_counter()
    result = run_direct_ray_trace(trace_input)
    wall_time = time.perf_counter() - start
    performance = result.metrics["_performance_summary"]
    return {
        "contribution_mode": contribution_mode,
        "runtime_sec": result.runtime_sec,
        "wall_time_sec": wall_time,
        "rays_per_sec": performance["rays_per_sec"],
        "execution_path": performance["execution_path"],
        "receiver_hit_count": result.receiver_hit_count,
        "receiver_flux_lumen": result.metrics["observer"]["total_flux_lumen"],
    }


def write_chart(summary: dict, output_path: Path) -> None:
    labels = ["RT-2D\n기준", "RT-3\n최적화 전", "PERF-3A\nFast summary", "PERF-3A\nDetailed"]
    fast = summary["cases"]["summary"]
    detailed = summary["cases"]["detailed"]
    runtimes = [RT2D_BASELINE_SEC, RT3_PRE_PERF3A_SEC, fast["runtime_sec"], detailed["runtime_sec"]]
    colors = ["#64748b", "#dc2626", "#16a34a", "#2563eb"]
    plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    figure, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    bars = axes[0].bar(labels, runtimes, color=colors)
    axes[0].set_title("백만 Ray · 1회 반사 실행 시간", fontweight="bold")
    axes[0].set_ylabel("실행 시간 (초)")
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].set_ylim(0, max(runtimes) * 1.18)
    for bar, runtime in zip(bars, runtimes):
        axes[0].text(bar.get_x() + bar.get_width() / 2, runtime + 0.35, f"{runtime:.2f}s", ha="center", fontweight="bold")

    mode_labels = ["Fast summary", "Detailed contribution"]
    throughputs = [fast["rays_per_sec"], detailed["rays_per_sec"]]
    bars = axes[1].bar(mode_labels, throughputs, color=["#16a34a", "#2563eb"])
    axes[1].set_title("PERF-3A 처리량", fontweight="bold")
    axes[1].set_ylabel("Rays / second")
    axes[1].grid(axis="y", alpha=0.25)
    axes[1].set_ylim(0, max(throughputs) * 1.18)
    for bar, throughput in zip(bars, throughputs):
        axes[1].text(bar.get_x() + bar.get_width() / 2, throughput + 600, f"{throughput:,.0f}", ha="center", fontweight="bold")
    figure.suptitle("PERF-3A 단일 반사 Fast Path 검증", fontsize=16, fontweight="bold")
    figure.savefig(output_path, dpi=170, facecolor="white")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ray-count", type=int, default=1_000_000)
    parser.add_argument(
        "--output",
        default=str(ROOT / "docs" / "reports" / "perf3a"),
    )
    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    fast = run_case("summary", args.ray_count)
    detailed = run_case("detailed", args.ray_count)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "ray_count": args.ray_count,
        "rt2d_baseline_sec": RT2D_BASELINE_SEC,
        "rt3_pre_perf3a_sec": RT3_PRE_PERF3A_SEC,
        "cases": {"summary": fast, "detailed": detailed},
        "fast_slowdown_vs_rt2d_percent": (fast["runtime_sec"] / RT2D_BASELINE_SEC - 1.0) * 100.0,
        "fast_improvement_vs_rt3_percent": (1.0 - fast["runtime_sec"] / RT3_PRE_PERF3A_SEC) * 100.0,
        "result_flux_delta_lumen": abs(fast["receiver_flux_lumen"] - detailed["receiver_flux_lumen"]),
    }
    summary_path = output_dir / "summary.json"
    chart_path = output_dir / "perf3a_single_bounce.png"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_chart(summary, chart_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"summary={summary_path}")
    print(f"chart={chart_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
