"""V8D pilot: nonlinear force-displacement of a real Floor 95 core column.

The pilot intentionally remains an isolated, pin-ended shell column.  It is a
constitutive/member-response test used before assembling the 47-column core.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
TRANSFER = V8 / "data" / "nist_wtc1_transfer.json"
V8B = V8 / "output" / "resultats_wtc1_v8b.json"
AISC = V8 / "data" / "aisc_historic_wf_properties.json"
RUN_DIR = V8 / "calculix_v8d_force_displacement"
OUT = V8 / "output" / "resultats_wtc1_v8d_force_deplacement.json"
REPORT = V8 / "output" / "rapport_wtc1_v8d_force_deplacement.md"
CCX = Path(r"C:\Program Files\FreeCAD 1.1\bin\ccx.exe")

IN_TO_MM = 25.4
LENGTH_MM = 3657.6
SHORTENING_MM = 400.0
NU = 0.3
N_LENGTH = 24
N_FLANGE = 12
N_WEB = 12


def linspace(a: float, b: float, n: int) -> list[float]:
    return [a + (b - a) * i / n for i in range(n + 1)]


def yield_ratio(temp_c: float, p: dict[str, float]) -> float:
    return (1.0 - p["A2"]) * math.exp(
        -0.5 * ((temp_c / p["s1_c"]) ** p["m1"] + (temp_c / p["s2_c"]) ** p["m2"])
    ) + p["A2"]


def modulus_gpa(temp_c: float, p: dict[str, float]) -> tuple[float, str]:
    def poly(t: float) -> float:
        return p["e0"] + p["e1"] * t + p["e2"] * t**2 + p["e3"] * t**3

    if temp_c <= 600.0:
        return poly(max(temp_c, 0.0)), "NIST polynomial 0-600 C"
    # NIST's reported polynomial is not valid above 600 C.  The pilot uses the
    # more conservative V8B sensitivity tail, linear to 5% of E20 at 1000 C.
    e20 = poly(20.0)
    e600 = poly(600.0)
    f = min(max((temp_c - 600.0) / 400.0, 0.0), 1.0)
    return e600 + f * (0.05 * e20 - e600), "V8B linear tail E600 to 5% E20 at 1000 C"


def add_set(lines: list[str], name: str, nodes: list[int]) -> None:
    lines.append(f"*NSET,NSET={name}")
    for start in range(0, len(nodes), 16):
        lines.append(",".join(str(v) for v in nodes[start : start + 16]))


def make_deck(job: str, shape: dict[str, float | str], e_mpa: float, fy_mpa: float, imperfection_mm: float) -> tuple[str, dict[str, int]]:
    d = float(shape["depth_in"]) * IN_TO_MM
    tw = float(shape["web_thickness_in"]) * IN_TO_MM
    bf = float(shape["flange_width_in"]) * IN_TO_MM
    tf = float(shape["flange_thickness_in"]) * IN_TO_MM
    yf = d / 2.0 - tf / 2.0
    paths = {
        "WEB": [(0.0, y) for y in linspace(-yf, yf, N_WEB)],
        "TOPFLANGE": [(x, yf) for x in linspace(-bf / 2.0, bf / 2.0, N_FLANGE)],
        "BOTTOMFLANGE": [(x, -yf) for x in linspace(-bf / 2.0, bf / 2.0, N_FLANGE)],
    }
    point_ids: dict[tuple[float, float], int] = {}
    xy: dict[int, tuple[float, float]] = {}
    for path in paths.values():
        for x, y in path:
            key = (round(x, 9), round(y, 9))
            if key not in point_ids:
                pid = len(point_ids) + 1
                point_ids[key] = pid
                xy[pid] = (x, y)
    n_cross = len(point_ids)

    def node(pid: int, layer: int) -> int:
        return layer * n_cross + pid

    lines = ["*HEADING", f"V8D {job}", "*NODE"]
    for layer in range(N_LENGTH + 1):
        z = LENGTH_MM * layer / N_LENGTH
        crooked = imperfection_mm * math.sin(math.pi * z / LENGTH_MM)
        for pid in range(1, n_cross + 1):
            x, y = xy[pid]
            lines.append(f"{node(pid, layer)},{x + crooked:.9f},{y:.9f},{z:.9f}")
    ref_base = n_cross * (N_LENGTH + 1) + 1
    rot_base = ref_base + 1
    ref_top = ref_base + 2
    rot_top = ref_base + 3
    lines.extend(
        [
            f"{ref_base},0.,0.,0.",
            f"{rot_base},0.,0.,0.",
            f"{ref_top},0.,0.,{LENGTH_MM}",
            f"{rot_top},0.,0.,{LENGTH_MM}",
        ]
    )
    eid = 1
    for set_name, path in paths.items():
        lines.append(f"*ELEMENT,TYPE=S4R,ELSET={set_name}")
        pids = [point_ids[(round(x, 9), round(y, 9))] for x, y in path]
        for layer in range(N_LENGTH):
            for a, b in zip(pids[:-1], pids[1:]):
                lines.append(f"{eid},{node(a, layer)},{node(b, layer)},{node(b, layer + 1)},{node(a, layer + 1)}")
                eid += 1
    base_nodes = [node(pid, 0) for pid in range(1, n_cross + 1)]
    top_nodes = [node(pid, N_LENGTH) for pid in range(1, n_cross + 1)]
    add_set(lines, "BASE", base_nodes)
    add_set(lines, "TOP", top_nodes)
    add_set(lines, "BASE_REF", [ref_base])
    add_set(lines, "BASE_ROT", [rot_base])
    add_set(lines, "TOP_REF", [ref_top])
    add_set(lines, "TOP_ROT", [rot_top])
    lines.extend(
        [
            f"*RIGID BODY,NSET=BASE,REF NODE={ref_base},ROT NODE={rot_base}",
            f"*RIGID BODY,NSET=TOP,REF NODE={ref_top},ROT NODE={rot_top}",
            "*MATERIAL,NAME=STEEL",
            "*ELASTIC",
            f"{e_mpa:.9f},{NU}",
            "*PLASTIC",
            f"{fy_mpa:.9f},0.",
            f"{fy_mpa * 1.01:.9f},0.10",
            "*SHELL SECTION,ELSET=WEB,MATERIAL=STEEL",
            f"{tw:.9f}",
            "*SHELL SECTION,ELSET=TOPFLANGE,MATERIAL=STEEL",
            f"{tf:.9f}",
            "*SHELL SECTION,ELSET=BOTTOMFLANGE,MATERIAL=STEEL",
            f"{tf:.9f}",
            "*STEP,NLGEOM,INC=1000",
            "*STATIC",
            "0.002,1.,1.e-8,0.02",
            "*BOUNDARY",
            "BASE_REF,1,3",
            "BASE_ROT,3,3",
            "TOP_REF,1,2",
            f"TOP_REF,3,3,{-SHORTENING_MM}",
            "*NODE PRINT,NSET=TOP_REF,FREQUENCY=1",
            "U",
            "*NODE PRINT,NSET=BASE_REF,TOTALS=ONLY,FREQUENCY=1",
            "RF",
            "*NODE PRINT,NSET=BASE,TOTALS=ONLY,FREQUENCY=1",
            "RF",
            "*END STEP",
            "",
        ]
    )
    return "\n".join(lines), {"nodes": n_cross * (N_LENGTH + 1) + 4, "elements": eid - 1, "top_reference_node": ref_top}


def parse_curve(dat: Path, ref_node: int) -> list[dict[str, float]]:
    text = dat.read_text(encoding="utf-8", errors="replace")
    values: dict[float, dict[str, float]] = {}
    header = re.compile(
        r"(?im)^\s*(displacements|forces|total force).*?for set\s+(TOP_REF|BASE_REF|BASE)\s+and time\s+([-+0-9.Ee]+)\s*$"
    )
    node_line = re.compile(
        rf"(?im)^\s*{ref_node}\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s*$"
    )
    total_line = re.compile(
        r"(?im)^\s*([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s*$"
    )
    headers = list(header.finditer(text))
    for i, match in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        time = float(match.group(3))
        row = values.setdefault(time, {"time": time})
        kind = match.group(1).lower()
        set_name = match.group(2).upper()
        if kind.startswith("displacement"):
            node_match = node_line.search(text, match.end(), end)
            if set_name == "TOP_REF" and node_match:
                row["u3_mm"] = float(node_match.group(3))
        else:
            total_match = total_line.search(text, match.end(), end)
            if total_match:
                row[f"rf3_{set_name.lower()}_n"] = float(total_match.group(3))
    for row in values.values():
        reactions = [
            row[key]
            for key in ("rf3_base_ref_n", "rf3_base_n")
            if key in row
        ]
        if reactions:
            row["rf3_n"] = max(reactions, key=lambda value: abs(value))
    return [row for _, row in sorted(values.items()) if "u3_mm" in row and "rf3_n" in row]


def main() -> None:
    transfer = json.loads(TRANSFER.read_text(encoding="utf-8"))
    model = json.loads(V8B.read_text(encoding="utf-8"))
    shapes = json.loads(AISC.read_text(encoding="utf-8"))["shapes"]
    yp = transfer["steel_temperature_model"]["yield_ratio_parameters"]
    ep = transfer["steel_temperature_model"]["young_modulus_parameters"]
    section = model["floor_inputs"]["95"]["sections"]["705"]
    shape = shapes[section["designation"]]
    fy_room_mpa = float(section["fy_ksi"]) * 6.894757293168
    # Floor 95, 100 min: 52-761 C.  The midpoint is a sensitivity only, not a
    # NIST mean or median.
    cases = [
        (52.0, LENGTH_MM / 1000.0),
        (406.5, LENGTH_MM / 1000.0),
        (761.0, LENGTH_MM / 1000.0),
        (406.5, LENGTH_MM / 500.0),
    ]
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for temp_c, imperfection in cases:
        e_gpa, e_note = modulus_gpa(temp_c, ep)
        fy_mpa = fy_room_mpa * yield_ratio(temp_c, yp)
        job = f"v8d_f95_c705_t{str(temp_c).replace('.', 'p')}_i{round(LENGTH_MM / imperfection)}"
        deck, mesh = make_deck(job, shape, e_gpa * 1000.0, fy_mpa, imperfection)
        inp = RUN_DIR / f"{job}.inp"
        inp.write_text(deck, encoding="ascii")
        run = subprocess.run([str(CCX), job], cwd=RUN_DIR, capture_output=True, text=True, check=False)
        dat = RUN_DIR / f"{job}.dat"
        curve = parse_curve(dat, mesh["top_reference_node"]) if dat.exists() else []
        # Reactions oppose imposed negative displacement; use positive compression.
        clean = sorted(
            ({"shortening_mm": max(0.0, -p["u3_mm"]), "compression_n": max(0.0, p["rf3_n"])} for p in curve),
            key=lambda p: p["shortening_mm"],
        )
        energy_j = 0.0
        for a, b in zip(clean[:-1], clean[1:]):
            energy_j += 0.5 * (a["compression_n"] + b["compression_n"]) * (b["shortening_mm"] - a["shortening_mm"]) / 1000.0
        results.append(
            {
                "floor": 95,
                "column": 705,
                "designation": section["designation"],
                "temperature_c": temp_c,
                "temperature_status": "NIST Case B Floor 95 100-min minimum" if temp_c == 52.0 else ("NIST Case B Floor 95 100-min maximum" if temp_c == 761.0 else "arithmetic midpoint sensitivity; not a NIST mean/median"),
                "imperfection_mm": imperfection,
                "imperfection_ratio": LENGTH_MM / imperfection,
                "e_gpa": e_gpa,
                "e_model": e_note,
                "fy_mpa": fy_mpa,
                "mesh": mesh,
                "returncode": run.returncode,
                "curve_point_count": len(clean),
                "max_compression_n": max((p["compression_n"] for p in clean), default=None),
                "last_shortening_mm": max((p["shortening_mm"] for p in clean), default=None),
                "absorbed_energy_to_last_point_j": energy_j,
                "curve": clean,
                "stdout_tail": run.stdout[-1800:],
                "stderr_tail": run.stderr[-1000:],
                "input_file": str(inp),
            }
        )
    payload = {
        "model": "WTC1_V8D_F95_C705_NONLINEAR_FORCE_DISPLACEMENT_PILOT",
        "scope": "isolated pin-ended shell column pilot; no floor framing, creep, thermal gradient, strain-rate, connection fracture or load redistribution",
        "shortening_target_mm": SHORTENING_MM,
        "material": "NIST Fy(T), NIST E(T) to 600 C, explicit V8B tail above 600 C, 1% numerical hardening",
        "cases": results,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = [
        "# WTC 1 — V8D : pilote force–déplacement de la colonne 705 au niveau 95",
        "",
        "## Portée",
        "",
        "Le profil 14WF43 est modélisé en coques, bi-articulé, avec une imperfection sinusoïdale. Cette étape mesure la réponse d’un membre isolé; elle ne représente pas encore le noyau, les planchers ou la tour entière.",
        "",
        "| Température | Statut | Imperfection | E (GPa) | Fy (MPa) | Maximum convergé (MN) | Dernier déplacement (mm) | Énergie (MJ) |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in results:
        peak = row["max_compression_n"]
        last = row["last_shortening_mm"]
        md.append(f"| {row['temperature_c']:.1f} °C | {row['temperature_status']} | L/{row['imperfection_ratio']:.0f} | {row['e_gpa']:.1f} | {row['fy_mpa']:.1f} | {'échec' if peak is None else f'{peak/1e6:.3f}'} | {'—' if last is None else f'{last:.1f}'} | {row['absorbed_energy_to_last_point_j']/1e6:.3f} |")
    md.extend(
        [
            "",
            "## Limites de décision",
            "",
            "La valeur à 406,5 °C n’est qu’une interpolation de sensibilité entre le minimum et le maximum spatial publiés par NIST. Au-dessus de 600 °C, le module suit une extrapolation explicite et non une donnée NIST. Aucun résultat de ce pilote ne peut être additionné 47 fois sans carte spatiale des températures, charges individuelles et liaisons de planchers.",
            "",
        ]
    )
    REPORT.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
