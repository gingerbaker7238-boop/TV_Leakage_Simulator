from __future__ import annotations

from pathlib import Path
from typing import Optional
import html
import os

from .types import SimulationOutput


def export_rendering(result: SimulationOutput, output_path: Path) -> Optional[str]:
    if not output_path:
        return None
    try:
        os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib"))
        import matplotlib.pyplot as plt
    except Exception:
        return None

    rows = sorted(result.receiver_metrics, key=lambda row: row.peak_nit, reverse=True)
    receiver_ids = [m.receiver_id for m in rows]
    values = [m.peak_nit for m in rows]
    hit_counts = [m.rays_hit for m in rows]
    area_above = [m.area_above_threshold for m in rows]
    if not receiver_ids:
        return None

    fig, (ax_peak, ax_hit) = plt.subplots(2, 1, figsize=(11, 8))

    x = list(range(len(receiver_ids)))
    max_v = max(values) if values else 0.0

    colors = [
        "#e74c3c" if v > 0 else "#95a5a6"
        for v in values
    ]
    ax_peak.bar(x, values, color=colors)
    ax_peak.set_title("Receiver peak_nit (sorted)")
    ax_peak.set_ylabel("Estimated nits (relative)")
    ax_peak.set_xticks(x)
    ax_peak.set_xticklabels(receiver_ids, rotation=25, ha="right")
    ax_peak.grid(axis="y", alpha=0.3)
    if max_v > 0:
        ax_peak.set_ylim(bottom=0.0, top=max_v * 1.15 + 1e-9)

    ax_hit.plot(x, hit_counts, marker="o", color="#2f6ee4")
    ax_hit.set_title("Receiver rays_hit count")
    ax_hit.set_ylabel("Rays hit")
    ax_hit.set_xticks(x)
    ax_hit.set_xticklabels(receiver_ids, rotation=25, ha="right")
    ax_hit.set_xlabel("Receiver patch")
    ax_hit.grid(axis="y", alpha=0.3)

    ax_area = ax_hit.twinx()
    ax_area.plot(x, area_above, marker="x", color="#16a085", alpha=0.6, linestyle="--")
    ax_area.set_ylabel("Area above threshold (mm^2)")

    for idx, (receiver_id, value) in enumerate(zip(receiver_ids, values)):
        if idx < 5 and value > 0:
            ax_peak.text(idx, value * 1.02, f"{receiver_id}: {value:.2g}", ha="center", va="bottom", fontsize=8)

    fig.tight_layout()
    fig.savefig(str(output_path))
    plt.close(fig)
    return str(output_path)


def export_html_report(
    result: SimulationOutput,
    output_path: Path,
    heatmap_path: Optional[str] = None,
    csv_path: Optional[str] = None,
    json_path: Optional[str] = None,
) -> Optional[str]:
    if not output_path:
        return None
    try:
        metrics_count = len(result.receiver_metrics)
        rows = [
            (
                m.receiver_id,
                round(m.peak_nit, 6),
                round(m.mean_nit, 6),
                round(m.p95_nit, 6),
                int(m.rays_hit),
                round(m.area_above_threshold, 6),
            )
            for m in result.receiver_metrics
        ]
    except Exception:
        return None

    peaks = [m.peak_nit for m in result.receiver_metrics]
    hit_receivers = sum(1 for m in result.receiver_metrics if m.rays_hit > 0)
    max_peak = max(peaks) if peaks else 0.0
    max_hit = max((m.rays_hit for m in result.receiver_metrics), default=0)
    mean_peak = (sum(peaks) / metrics_count) if metrics_count else 0.0
    if result.summary.total_rays > 0:
        hit_ratio = result.summary.hit_count / result.summary.total_rays
    else:
        hit_ratio = 0.0

    if hit_receivers == 0:
        summary_hint = "No receiver received rays. Check emitter and receiver alignment."
    elif hit_ratio < 0.05:
        summary_hint = "Hit ratio is low. geometry, emitter direction, and gap settings should be reviewed first."
    else:
        summary_hint = "Leaked rays are present. Compare peak_nit and hit_count rankings across receivers."

    rows_html = []
    for receiver_id, peak_nit, mean_nit, p95_nit, rays_hit, area_above in rows:
        rid = html.escape(str(receiver_id))
        rows_html.append(
            f"<tr><td>{rid}</td><td>{peak_nit:.6g}</td><td>{mean_nit:.6g}</td>"
            f"<td>{p95_nit:.6g}</td><td>{rays_hit}</td><td>{area_above:.6g}</td></tr>"
        )
    chart_img = ""
    if heatmap_path and Path(heatmap_path).exists():
        rel = html.escape(Path(heatmap_path).name)
        chart_img = f"<p>Heatmap image: <a href=\"{rel}\">{rel}</a></p><img src=\"{rel}\" alt=\"leak heatmap\" style=\"max-width:100%;border:1px solid #ddd;\">"
    csv_link = ""
    json_link = ""
    if csv_path and Path(csv_path).exists():
        rel_csv = html.escape(Path(csv_path).name)
        csv_link = f"<p>Raw output: <a href=\"{rel_csv}\">{rel_csv}</a></p>"
    if json_path and Path(json_path).exists():
        rel_json = html.escape(Path(json_path).name)
        json_link = f"<p>Raw output: <a href=\"{rel_json}\">{rel_json}</a></p>"
    body = f"""
    <html>
    <head>
      <meta charset=\"utf-8\" />
      <title>Leakage simulation report</title>
      <style>
        body{{font-family: Arial, Helvetica, sans-serif; margin: 20px;}}
        table{{border-collapse: collapse; min-width: 780px;}}
        th, td{{border: 1px solid #ddd; padding: 8px;}}
        th{{background: #f2f2f2;}}
        .card{{display:inline-block;padding: 10px 14px;margin: 0 12px 12px 0;border:1px solid #e0e0e0;border-radius: 6px;background:#fafafa;}}
      </style>
    </head>
    <body>
      <h2>Leakage simulation report</h2>
      <div class=\"card\">run_id: {html.escape(result.summary.run_id)}</div>
      <div class=\"card\">source_file: {html.escape(str(result.source_file))}</div>
      <div class=\"card\">project: {html.escape(result.project_name)}</div>
      <div class=\"card\">receiver_count: {metrics_count}</div>
      <div class=\"card\">hit_receivers: {hit_receivers}</div>
      <div class=\"card\">total_rays: {result.summary.total_rays}</div>
      <div class=\"card\">hit_count: {result.summary.hit_count}</div>
      <div class=\"card\">hit_ratio: {round(hit_ratio * 100, 3)}%</div>
      <div class=\"card\">runtime_sec: {round(result.summary.runtime_sec, 3)}</div>
      <div class=\"card\">max_peak_nit: {round(max_peak, 6)}</div>
      <div class=\"card\">mean_peak_nit: {round(mean_peak, 6)}</div>
      <div class=\"card\">max_hit: {max_hit}</div>
      <p><strong>Quick interpretation:</strong> {html.escape(summary_hint)}</p>
      <h3>Receiver summary</h3>
      <table>
        <thead><tr><th>receiver</th><th>peak_nit</th><th>mean_nit</th><th>p95_nit</th><th>rays_hit</th><th>area_above_threshold</th></tr></thead>
        <tbody>{''.join(rows_html)}</tbody>
      </table>
      <h3>Visualization</h3>
      {chart_img}
      {csv_link}
      {json_link}
    </body>
    </html>
    """
    output_path.write_text(body, encoding="utf-8")
    return str(output_path)
