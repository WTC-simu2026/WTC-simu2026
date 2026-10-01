"""V8C-ter: shell-model validation for four historic WTC core W shapes."""

from __future__ import annotations

import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
V8B = V8 / "output" / "resultats_wtc1_v8b.json"
AISC = V8 / "data" / "aisc_historic_wf_properties.json"
RUN_DIR = V8 / "calculix_shell_w_validation"
OUT = V8 / "output" / "resultats_wtc1_v8c_shell_w.json"
REPORT = V8 / "output" / "rapport_wtc1_v8c_shell_w.md"
CCX = Path(r"C:\Program Files\FreeCAD 1.1\bin\ccx.exe")

IN_TO_MM = 25.4
IN4_TO_MM4 = IN_TO_MM**4
LENGTH_MM = 3657.6
E_MPA = 206_000.0
NU = 0.3
N_LENGTH = 36
N_FLANGE = 16  # even, so x=0 is a shared flange/web node
N_WEB = 16


def parse_factors(path: Path) -> list[float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    marker = re.search(r"B\s+U\s+C\s+K\s+L\s+I\s+N\s+G\s+F\s+A\s+C\s+T\s+O\s+R\s+O\s+U\s+T\s+P\s+U\s+T", text, re.I)
    tail = text[marker.end():] if marker else text
    values = []
    for m in re.finditer(r"(?im)^\s*\d+\s+([-+0-9.Ee]+)\s*$", tail):
        value = float(m.group(1))
        if value > 0:
            values.append(value)
    return values[:6]


def linspace(a: float, b: float, n_segments: int) -> list[float]:
    return [a + (b - a) * i / n_segments for i in range(n_segments + 1)]


def build_deck(job: str, shape: dict[str, float | str]) -> tuple[str, dict[str, float]]:
    d = float(shape["depth_in"]) * IN_TO_MM
    tw = float(shape["web_thickness_in"]) * IN_TO_MM
    bf = float(shape["flange_width_in"]) * IN_TO_MM
    tf = float(shape["flange_thickness_in"]) * IN_TO_MM
    yf = d / 2.0 - tf / 2.0

    # Cross-section wall paths.  Nodes at the flange/web intersections are
    # shared through the coordinate-keyed registry.
    paths = {
        "WEB": [(0.0, y) for y in linspace(-yf, yf, N_WEB)],
        "TOPFLANGE": [(x, yf) for x in linspace(-bf / 2.0, bf / 2.0, N_FLANGE)],
        "BOTTOMFLANGE": [(x, -yf) for x in linspace(-bf / 2.0, bf / 2.0, N_FLANGE)],
    }
    point_ids: dict[tuple[float, float], int] = {}
    point_xy: dict[int, tuple[float, float]] = {}
    for path in paths.values():
        for x, y in path:
            key = (round(x, 9), round(y, 9))
            if key not in point_ids:
                idx = len(point_ids) + 1
                point_ids[key] = idx
                point_xy[idx] = (x, y)
    n_cross = len(point_ids)

    def node(point_id: int, layer: int) -> int:
        return layer * n_cross + point_id

    lines = ["*HEADING", f"V8C shell W validation {job}", "*NODE"]
    for layer in range(N_LENGTH + 1):
        z = LENGTH_MM * layer / N_LENGTH
        for point_id in range(1, n_cross + 1):
            x, y = point_xy[point_id]
            lines.append(f"{node(point_id, layer)},{x:.9f},{y:.9f},{z:.9f}")

    element_id = 1
    for set_name, path in paths.items():
        lines.append(f"*ELEMENT,TYPE=S4R,ELSET={set_name}")
        pids = [point_ids[(round(x, 9), round(y, 9))] for x, y in path]
        for layer in range(N_LENGTH):
            for a, b in zip(pids[:-1], pids[1:]):
                lines.append(
                    f"{element_id},{node(a, layer)},{node(b, layer)},{node(b, layer + 1)},{node(a, layer + 1)}"
                )
                element_id += 1

    base_nodes = [node(i, 0) for i in range(1, n_cross + 1)]
    lines.append("*NSET,NSET=BASE")
    for start in range(0, len(base_nodes), 16):
        lines.append(",".join(str(v) for v in base_nodes[start : start + 16]))
    lines.extend(
        [
            "*MATERIAL,NAME=STEEL",
            "*ELASTIC",
            f"{E_MPA},{NU}",
            "*SHELL SECTION,ELSET=WEB,MATERIAL=STEEL",
            f"{tw:.9f}",
            "*SHELL SECTION,ELSET=TOPFLANGE,MATERIAL=STEEL",
            f"{tf:.9f}",
            "*SHELL SECTION,ELSET=BOTTOMFLANGE,MATERIAL=STEEL",
            f"{tf:.9f}",
            "*STEP",
            "*BUCKLE",
            "6,0.01",
            "*BOUNDARY",
            "BASE,1,6",
            "*CLOAD",
        ]
    )

    # Lump a unit axial load consistently from the cross-sectional wall
    # lengths and thicknesses.  Shared intersection nodes accumulate weights.
    weights: defaultdict[int, float] = defaultdict(float)
    for set_name, path in paths.items():
        thickness = tw if set_name == "WEB" else tf
        pids = [point_ids[(round(x, 9), round(y, 9))] for x, y in path]
        for (xa, ya), (xb, yb), a, b in zip(path[:-1], path[1:], pids[:-1], pids[1:]):
            segment_area = math.hypot(xb - xa, yb - ya) * thickness
            weights[a] += segment_area / 2.0
            weights[b] += segment_area / 2.0
    total = sum(weights.values())
    for point_id, weight in sorted(weights.items()):
        lines.append(f"{node(point_id, N_LENGTH)},3,{-weight / total:.12g}")
    lines.extend(["*NODE FILE", "U", "*EL FILE", "S,E", "*END STEP", ""])

    # Center-line wall geometry, omitting fillets, for direct comparison.
    hw = 2.0 * yf
    area = tw * hw + 2.0 * tf * bf
    iy = hw * tw**3 / 12.0 + 2.0 * tf * bf**3 / 12.0
    ix = tw * hw**3 / 12.0 + 2.0 * (bf * tf**3 / 12.0 + bf * tf * yf**2)
    meta = {"area_mm2": area, "iy_mm4": iy, "ix_mm4": ix, "node_count": n_cross * (N_LENGTH + 1), "element_count": element_id - 1}
    return "\n".join(lines), meta


def main() -> None:
    model = json.loads(V8B.read_text(encoding="utf-8"))
    props = json.loads(AISC.read_text(encoding="utf-8"))["shapes"]
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for column in ["501", "605", "705", "804"]:
        sec = model["floor_inputs"]["93"]["sections"][column]
        shape = props[sec["designation"]]
        job = f"v8c_shell_f93_c{column}_{sec['designation'].lower()}"
        text, meta = build_deck(job, shape)
        inp = RUN_DIR / f"{job}.inp"
        inp.write_text(text, encoding="ascii")
        result = subprocess.run([str(CCX), job], cwd=RUN_DIR, capture_output=True, text=True, check=False)
        dat = RUN_DIR / f"{job}.dat"
        values = parse_factors(dat) if dat.exists() else []
        ccx = min(values) if values else None
        # Cantilever boundary conditions: fixed base, free loaded top, K=2.
        euler_geom = math.pi**2 * E_MPA * meta["iy_mm4"] / (2.0 * LENGTH_MM) ** 2
        tab_iy = float(shape["iy_in4"]) * IN4_TO_MM4
        euler_tab = math.pi**2 * E_MPA * tab_iy / (2.0 * LENGTH_MM) ** 2
        rows.append(
            {
                "column": int(column),
                "designation": sec["designation"],
                **meta,
                "tabulated_iy_mm4": tab_iy,
                "geometry_vs_tabulated_iy_pct": 100.0 * (meta["iy_mm4"] / tab_iy - 1.0),
                "euler_cantilever_geometry_n": euler_geom,
                "euler_cantilever_tabulated_n": euler_tab,
                "calculix_first_positive_n": ccx,
                "calculix_vs_euler_geometry_pct": None if ccx is None else 100.0 * (ccx / euler_geom - 1.0),
                "buckling_factors": values,
                "returncode": result.returncode,
                "stdout_tail": result.stdout[-1200:],
                "stderr_tail": result.stderr[-1200:],
                "input_file": str(inp),
            }
        )
    payload = {
        "model": "WTC1_V8C_SHELL_W_SECTION_VALIDATION",
        "scope": "cantilever shell buckling validation of historic W shapes; not a collapse result",
        "mesh": {"length_segments": N_LENGTH, "flange_segments": N_FLANGE, "web_segments": N_WEB, "element": "S4R"},
        "cases": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = [
        "# WTC 1 — V8C : validation en coques des profils W",
        "",
        "Les âmes et semelles sont modélisées par des coques S4R avec leurs dimensions historiques. Le cas-test est une console de 3,6576 m, encastrée en pied et comprimée par une charge unitaire répartie sur la section supérieure. La référence analytique est donc Euler avec K=2.",
        "",
        "| Colonne | Profil | Éléments | ΔIy géom./table | Euler K=2 (MN) | CalculiX (MN) | Écart |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        c = row["calculix_first_positive_n"]
        err = row["calculix_vs_euler_geometry_pct"]
        md.append(f"| {row['column']} | {row['designation']} | {row['element_count']} | {row['geometry_vs_tabulated_iy_pct']:+.2f} % | {row['euler_cantilever_geometry_n']/1e6:.4f} | {'échec' if c is None else f'{c/1e6:.4f}'} | {'—' if err is None else f'{err:+.2f} %'} |")
    md.extend(
        [
            "",
            "Un écart faible valide la représentation pour le flambement global. Un premier facteur nettement inférieur à Euler doit être examiné comme mode local possible, pas automatiquement classé comme erreur numérique.",
            "",
        ]
    )
    REPORT.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
