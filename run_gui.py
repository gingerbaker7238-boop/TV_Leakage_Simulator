from __future__ import annotations

import pathlib
import sys
import threading
from typing import Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

sys.path.append(str(pathlib.Path(__file__).resolve().parent / "src"))

from leakage_simulator.engine import execute_run
from leakage_simulator.materials import default_material_library
from leakage_simulator.types import EmitterConfig, GapRule, RunConfig


def _parse_int(text: str) -> Optional[int]:
    text = text.strip()
    if not text:
        return None
    return int(text)


def _parse_float(text: str) -> Optional[float]:
    text = text.strip()
    if not text:
        return None
    return float(text)


def _parse_int_list(raw: str) -> Optional[List[int]]:
    if not raw.strip():
        return None
    return [int(v.strip()) for v in raw.split(",") if v.strip()]


def _parse_tuple(raw: str) -> Optional[Tuple[float, float, float]]:
    vals = [float(v.strip()) for v in raw.split(",") if v.strip()]
    if not vals:
        return None
    if len(vals) != 3:
        raise ValueError("value must be x,y,z")
    return (vals[0], vals[1], vals[2])


def _build_material_override(material_id: str, ui_values: Dict[str, tk.StringVar]) -> Dict[str, float]:
    key_map = {
        "reflectance_total": ui_values["reflectance_total"],
        "diffuse_ratio": ui_values["diffuse_ratio"],
        "specular_ratio": ui_values["specular_ratio"],
        "roughness": ui_values["roughness"],
        "absorption_ratio": ui_values["absorption_ratio"],
        "alpha": ui_values["alpha"],
    }
    values: Dict[str, float] = {}
    for key, var in key_map.items():
        parsed = _parse_float(var.get())
        if parsed is not None:
            values[key] = parsed
    return values or None


class LeakageSimulatorGUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("TV Leakage Simulator")
        self.root.geometry("720x620")

        material_library = list(default_material_library().keys())
        self.material_library = material_library

        self.status = tk.StringVar(value="Ready")
        self.last_report = tk.StringVar(value="")

        self.inputs: Dict[str, tk.StringVar] = {
            "cad_path": tk.StringVar(),
            "output_dir": tk.StringVar(value="outputs"),
            "rays": tk.StringVar(value="4000"),
            "max_depth": tk.StringVar(value="2"),
            "seed": tk.StringVar(value="42"),
            "k_abs": tk.StringVar(value="0.12"),
            "k_brdf": tk.StringVar(value="1.0"),
            "gap_nominal": tk.StringVar(value="0.08"),
            "gap_sigma": tk.StringVar(value="0.03"),
            "gap_transmissive_threshold": tk.StringVar(value="0.4"),
            "roi_faces": tk.StringVar(value=""),
            "emitter_type": tk.StringVar(value="volume_box"),
            "emitter_strength": tk.StringVar(value="1.0"),
            "emitter_face_index": tk.StringVar(value=""),
            "emitter_normal_hint": tk.StringVar(value=""),
            "emitter_direction_mode": tk.StringVar(value="toward_receiver"),
            "emitter_direction_distribution": tk.StringVar(value="isotropic"),
            "emitter_box_min": tk.StringVar(value="470,120,25"),
            "emitter_box_max": tk.StringVar(value="520,180,45"),
            "emitter_sphere_center": tk.StringVar(value="250,150,40"),
            "emitter_sphere_radius": tk.StringVar(value="20.0"),
            "material_preset": tk.StringVar(value=material_library[1]),
            "reflectance_total": tk.StringVar(value=""),
            "diffuse_ratio": tk.StringVar(value=""),
            "specular_ratio": tk.StringVar(value=""),
            "roughness": tk.StringVar(value=""),
            "absorption_ratio": tk.StringVar(value=""),
            "alpha": tk.StringVar(value=""),
            "replace_import_emitter": tk.StringVar(value="0"),
        }

        self.include_import_emitter = tk.BooleanVar(value=True)
        self.show_advanced = tk.BooleanVar(value=False)

        self._build_main_layout()

    def _add_input_row(self, parent: ttk.Frame, label: str, var_name: str, row: int, col_span: int = 2) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=(0, 8), pady=3)
        widget = ttk.Entry(parent, textvariable=self.inputs[var_name])
        widget.grid(row=row, column=1, sticky=tk.EW, columnspan=col_span)

    def _build_main_layout(self) -> None:
        scroll = ttk.Frame(self.root, padding=12)
        scroll.pack(fill=tk.BOTH, expand=True)
        scroll.columnconfigure(1, weight=1)

        # basic
        ttk.Label(scroll, text="CAD file").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(scroll, textvariable=self.inputs["cad_path"]).grid(row=0, column=1, sticky=tk.EW)
        ttk.Button(scroll, text="Browse", command=self._select_cad).grid(row=0, column=2)

        row = 1
        for item in [
            ("Rays", "rays"),
            ("Max Depth", "max_depth"),
            ("Seed", "seed"),
            ("k_abs", "k_abs"),
            ("k_brdf", "k_brdf"),
        ]:
            self._add_input_row(scroll, item[0], item[1], row)
            row += 1

        ttk.Label(scroll, text="Output folder").grid(row=row, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(scroll, textvariable=self.inputs["output_dir"]).grid(row=row, column=1, sticky=tk.EW)
        ttk.Button(scroll, text="Browse", command=self._select_output).grid(row=row, column=2)
        row += 1

        # quick launch
        ttk.Checkbutton(scroll, text="Show advanced options", variable=self.show_advanced, command=self._toggle_advanced).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(8, 4))
        row += 1

        self.basic_section_end_row = row

        # advanced frame container
        self.advanced_frame = ttk.LabelFrame(scroll, text="Advanced", padding=10)
        self.advanced_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW)
        self.advanced_frame.columnconfigure(1, weight=1)
        self.advanced_visible = False
        self._build_advanced_fields()
        self._toggle_advanced()
        self.advanced_frame.grid_remove()
        row += 1

        action = ttk.Frame(scroll)
        action.grid(row=row, column=0, columnspan=3, pady=(10, 6), sticky=tk.EW)
        action.columnconfigure(0, weight=1)
        ttk.Button(action, text="Run", command=self._run).grid(row=0, column=0, sticky=tk.W)

        ttk.Checkbutton(action, text="Include importer emitters", variable=self.include_import_emitter).grid(row=0, column=1, sticky=tk.W, padx=12)

        ttk.Button(action, text="Open report", command=self._open_report).grid(row=0, column=3, sticky=tk.W, padx=12)

        ttk.Label(self.root, textvariable=self.status, anchor="w", padding=(12, 8)).pack(fill=tk.X)

    def _build_advanced_fields(self) -> None:
        adv = self.advanced_frame
        for child in adv.winfo_children():
            child.destroy()

        row = 0
        for item in [
            ("Receiver face indices (comma)", "roi_faces"),
            ("Gap nominal (mm)", "gap_nominal"),
            ("Gap sigma (mm)", "gap_sigma"),
            ("Gap transmissive threshold", "gap_transmissive_threshold"),
        ]:
            self._add_input_row(adv, item[0], item[1], row, 2)
            row += 1

        # emitter
        em_box = ttk.LabelFrame(adv, text="Emitter", padding=8)
        em_box.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(8, 4))
        em_box.columnconfigure(1, weight=1)
        ttk.Label(em_box, text="type").grid(row=0, column=0, sticky=tk.W)
        emitter_type = ttk.Combobox(em_box, textvariable=self.inputs["emitter_type"], width=20)
        emitter_type["values"] = ["face", "volume_box", "volume_sphere"]
        emitter_type.grid(row=0, column=1, sticky=tk.W, padx=(0, 8))
        self._add_combo_row(em_box, "direction mode", self.inputs["emitter_direction_mode"], ["toward_receiver", "upward", "downward", "isotropic"], row=1)
        self._add_input_row(em_box, "strength", "emitter_strength", 2)
        self._add_input_row(em_box, "face index", "emitter_face_index", 3)
        self._add_input_row(em_box, "normal hint (x,y,z)", "emitter_normal_hint", 4)
        self._add_input_row(em_box, "box min (x,y,z)", "emitter_box_min", 5)
        self._add_input_row(em_box, "box max (x,y,z)", "emitter_box_max", 6)
        self._add_input_row(em_box, "sphere center (x,y,z)", "emitter_sphere_center", 7)
        self._add_input_row(em_box, "sphere radius", "emitter_sphere_radius", 8)
        self._add_combo_row(
            em_box,
            "direction distribution",
            self.inputs["emitter_direction_distribution"],
            ["isotropic", "random_cosine", "uniform_toward_normal"],
            row=9,
        )
        row += 1

        # material
        mat_box = ttk.LabelFrame(adv, text="Material", padding=8)
        mat_box.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(8, 4))
        mat_box.columnconfigure(1, weight=1)
        ttk.Label(mat_box, text="Material preset").grid(row=0, column=0, sticky=tk.W)
        preset = ttk.Combobox(mat_box, textvariable=self.inputs["material_preset"], width=30)
        preset["values"] = self.material_library
        preset.grid(row=0, column=1, sticky=tk.W)

        mat_fields = [
            ("reflectance_total", "reflectance_total"),
            ("diffuse_ratio", "diffuse_ratio"),
            ("specular_ratio", "specular_ratio"),
            ("roughness", "roughness"),
            ("absorption_ratio", "absorption_ratio"),
            ("alpha", "alpha"),
        ]
        for i, (label, key) in enumerate(mat_fields, 1):
            self._add_input_row(mat_box, label, key, i)

    def _add_combo_row(self, parent: ttk.Frame, label: str, var: tk.StringVar, values: List[str], row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W)
        combo = ttk.Combobox(parent, textvariable=var, width=20)
        combo["values"] = values
        combo.grid(row=row, column=1, sticky=tk.W)

    def _toggle_advanced(self) -> None:
        if self.show_advanced.get() and not self.advanced_visible:
            self.advanced_frame.grid()
            self.advanced_visible = True
        elif not self.show_advanced.get() and self.advanced_visible:
            self.advanced_frame.grid_remove()
            self.advanced_visible = False

    def _select_cad(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CAD Files", "*.stp;*.step;*.x_t;*.obj;*.stl;*.*")])
        if path:
            self.inputs["cad_path"].set(path)

    def _select_output(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.inputs["output_dir"].set(path)

    def _run(self) -> None:
        try:
            config = RunConfig(
                ray_count=int(self.inputs["rays"].get()),
                max_depth=int(self.inputs["max_depth"].get()),
                seed=int(self.inputs["seed"].get()),
                k_abs=float(self.inputs["k_abs"].get()),
                k_brdf=float(self.inputs["k_brdf"].get()),
            )
            gap_rule = GapRule(
                rule_id="ui_gap",
                target_face_indices=_parse_int_list(self.inputs["roi_faces"].get()) or [],
                nominal_gap_mm=_parse_float(self.inputs["gap_nominal"].get()) or 0.08,
                sigma_gap_mm=_parse_float(self.inputs["gap_sigma"].get()) or 0.03,
                enable_tunnel=True,
                transmissive_threshold=_parse_float(self.inputs["gap_transmissive_threshold"].get()) or 0.4,
            )
            emitter_type = self.inputs["emitter_type"].get().strip() or None
            custom_emitter = None
            if emitter_type:
                custom_emitter = EmitterConfig(
                    source_id="ui_custom_emitter",
                    emitter_type=emitter_type,
                    strength=float(self.inputs["emitter_strength"].get()),
                    direction_mode=self.inputs["emitter_direction_mode"].get(),
                    direction_distribution=self.inputs["emitter_direction_distribution"].get(),
                    face_index=_parse_int(self.inputs["emitter_face_index"].get()),
                    normal_hint=_parse_tuple(self.inputs["emitter_normal_hint"].get()),
                    box_min=_parse_tuple(self.inputs["emitter_box_min"].get()),
                    box_max=_parse_tuple(self.inputs["emitter_box_max"].get()),
                    sphere_center=_parse_tuple(self.inputs["emitter_sphere_center"].get()),
                    sphere_radius=_parse_float(self.inputs["emitter_sphere_radius"].get()),
                )
            material_override = _build_material_override(self.inputs["material_preset"].get(), self.inputs)
            self.status.set("Running...")
            self.root.update_idletasks()
        except Exception as ex:
            messagebox.showerror("Input Error", str(ex))
            return

        self._run_async(config, gap_rule, custom_emitter, material_override)

    def _run_async(
        self,
        config: RunConfig,
        gap_rule: GapRule,
        emitter: Optional[EmitterConfig],
        material_override: Optional[Dict[str, float]],
    ) -> None:
        def worker() -> None:
            try:
                output = execute_run(
                    input_cad=self.inputs["cad_path"].get() or None,
                    output_dir=self.inputs["output_dir"].get(),
                    run_config=config,
                    gaps=[gap_rule],
                    roi_face_indices=_parse_int_list(self.inputs["roi_faces"].get()),
                    emitters=[emitter] if emitter else None,
                    replace_emitters=(emitter is not None and not self.include_import_emitter.get()),
                    material_preset_id=self.inputs["material_preset"].get(),
                    material_override=material_override,
                    out_prefix="run",
                )
                report = output.get("report", "")
                self.last_report.set(report)
                msg = f"Done. JSON: {output['json']}"
                if report:
                    msg += f" | Report: {report}"
                self.root.after(0, self.status.set, msg)
            except Exception as ex:
                self.root.after(0, messagebox.showerror, "Run failed", str(ex))
                self.root.after(0, self.status.set, "Failed")
            finally:
                self.root.after(0, lambda: None)

        threading.Thread(target=worker, daemon=True).start()

    def _open_report(self) -> None:
        report = self.last_report.get()
        if not report:
            messagebox.showwarning("Notice", "No report yet. Run simulation first.")
            return
        messagebox.showinfo("Report", f"Report path: {report}")


def main() -> None:
    app = LeakageSimulatorGUI()
    app.root.mainloop()


if __name__ == "__main__":
    main()
