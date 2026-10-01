"""WTC 1 V8K - Figure-constrained Floor 96 cut-set audit.

V8K replaces only the seven V8J cut-boundary edges with an explicit
transcription of NIST NCSTAR 1-6C Figure 5-59.  It does not infer a complete
as-built model from a raster image.  The test is deliberately topology-first:
beam capacity cannot rescue a loaded node for which the official subsystem
figure shows no surviving local Floor 96 path.
"""

from __future__ import annotations

import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
sys.path.insert(0, str((V8 / "scripts").resolve()))
import run_v8i_core_slab_catenary as v8i  # noqa: E402
import run_v8j_cold_load_path_gate as v8j  # noqa: E402


CONFIG = V8 / "data" / "v8k_floor96_nist_topology.json"
V8J_RESULT = V8 / "output" / "resultats_wtc1_v8j_gate_froid.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8k_topologie_nist.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8k_topologie_nist.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8k_topologie_nist.png"

CUT_NODES = {503, 504, 505, 604}
UNSUPPORTED_NODES = {503, 504, 604}
CANDIDATE_SUPPORTED_NODES = {505}


def load_inputs() -> dict[str, object]:
    return {
        "config": json.loads(CONFIG.read_text(encoding="utf-8")),
        "v8j_result": json.loads(V8J_RESULT.read_text(encoding="utf-8")),
        "v8j_inputs": v8j.load_inputs(),
    }


def replay_incoming_floor96(
    inputs: dict[str, object],
) -> tuple[dict[int, float], list[dict[str, object]], dict[str, object]]:
    v8j_inputs = inputs["v8j_inputs"]
    model = v8j.prepare_model(v8j_inputs)
    demand = float(
        v8j_inputs["transfer"]["nist_global_core_loads_floor_98_kip"]
        ["case_b_time_history"]["after_impact"]
    )
    prepared = model["prepared"]
    incoming = v8i.v8b.initial_loads(
        demand, prepared[99]["sections"], {}, "capacity_proportional"
    )
    slab_case = v8j.slab_case(v8j_inputs, "cold_upper_envelope")
    width_m = v8i.area_normalized_width_m(
        model["coords"],
        model["edges"],
        float(slab_case["active_area_fraction"]),
    )[0]
    floors: list[dict[str, object]] = []
    for floor in [99, 98, 97]:
        state = v8i.story_response(
            incoming,
            {column: 20.0 for column in model["coords"]},
            prepared[floor]["sections"],
            prepared[floor]["removed"],
            model["coords"],
            model["edges"],
            model["beam_shape"],
            slab_case,
            width_m,
            model["fy_params"],
            model["e_params"],
        )
        floors.append(
            {
                "floor": floor,
                "equilibrium": bool(state["equilibrium"]),
                "final_peak_dcr": float(state["final_peak_dcr"]),
                "maximum_abs_displacement_in": float(
                    state["maximum_abs_displacement_in"]
                ),
            }
        )
        incoming = {
            int(key): float(value) for key, value in state["final_loads"].items()
        }
    return incoming, floors, model


def candidate_path_proxy(
    inputs: dict[str, object], model: dict[str, object], demand_kip: float
) -> dict[str, object]:
    definitions = {
        tuple(sorted((int(row["i"]), int(row["j"])))): row
        for row in v8j.edge_definitions_at_20c(
            inputs["v8j_inputs"], model, "cold_upper_envelope"
        )
    }
    rows: list[dict[str, object]] = []
    laws: list[dict[str, object]] = []
    for edge in [(505, 506), (505, 605)]:
        law = definitions[tuple(sorted(edge))]
        laws.append(law)
        membrane = law["membrane_law"]
        rows.append(
            {
                "edge": list(edge),
                "section_assignment": v8i.BEAM_PROFILE,
                "section_status": "inherited_proxy_not_as_built",
                "beam_initial_stiffness_kip_per_in": float(
                    law["beam_stiffness"]
                ),
                "beam_yield_force_kip": float(law["beam_capacity"]),
                "beam_yield_displacement_in": float(
                    law["beam_yield_displacement"]
                ),
                "beam_ultimate_displacement_in": float(
                    law["beam_ultimate_displacement"]
                ),
                "slab_reinforcement_axial_yield_kip": float(
                    membrane["axial_yield_kip"]
                ),
                "slab_ultimate_vertical_displacement_in": float(
                    membrane["ultimate_delta_in"]
                ),
            }
        )

    maximum_delta = max(
        float(law["membrane_law"]["ultimate_delta_in"]) for law in laws
    )
    deltas = [maximum_delta * index / 20000 for index in range(20001)]
    for law in laws:
        deltas.extend(
            [
                0.999999 * float(law["beam_ultimate_displacement"]),
                float(law["beam_ultimate_displacement"]),
                0.999999 * float(law["membrane_law"]["ultimate_delta_in"]),
            ]
        )

    def total_force(delta_in: float) -> float:
        total = 0.0
        for law in laws:
            stiffness = float(law["beam_stiffness"])
            yield_delta = float(law["beam_yield_displacement"])
            ultimate_delta = float(law["beam_ultimate_displacement"])
            if delta_in <= yield_delta:
                total += stiffness * delta_in
            elif delta_in <= ultimate_delta:
                total += float(law["beam_capacity"]) + (
                    v8i.v8h.HARDENING_RATIO
                    * stiffness
                    * (delta_in - yield_delta)
                )
            membrane = v8i.membrane_state_at_delta(
                delta_in, law["membrane_law"]
            )
            if not bool(membrane["fractured"]):
                total += float(membrane["vertical_force_kip"])
        return total

    force_rows = [(delta, total_force(delta)) for delta in deltas]
    peak_delta, peak_force = max(force_rows, key=lambda row: row[1])
    return {
        "edges": rows,
        "node": 505,
        "incoming_demand_kip": demand_kip,
        "maximum_combined_proxy_force_kip": peak_force,
        "displacement_at_maximum_in": peak_delta,
        "proxy_capacity_deficit_kip": demand_kip - peak_force,
        "proxy_screen_passed": peak_force >= demand_kip,
        "interpretation": "This is a common-displacement two-edge envelope using the inherited 14WF136 and cold-upper slab laws. It is not an as-built capacity because the beam sections and connections in Figure 5-59 are unlabeled.",
    }


def topology_audit(
    inputs: dict[str, object], incoming: dict[int, float]
) -> dict[str, object]:
    config = inputs["config"]
    edge_rows = config["figure_transcription"]["edge_rows"]
    node_rows: list[dict[str, object]] = []
    for row in config["figure_transcription"]["node_path_rows"]:
        column = int(row["column"])
        node_rows.append(
            {
                **row,
                "incoming_load_kip": float(incoming.get(column, 0.0)),
                "topology_gate_pass": column in CANDIDATE_SUPPORTED_NODES,
            }
        )
    unsupported_load = sum(float(incoming.get(node, 0.0)) for node in UNSUPPORTED_NODES)
    candidate_supported_load = sum(
        float(incoming.get(node, 0.0)) for node in CANDIDATE_SUPPORTED_NODES
    )
    original_cut_load = float(
        inputs["v8j_result"]["cold_cut_set"]["disconnected_loaded_component"]
        ["incoming_load_kip"]
    )
    counts: dict[str, int] = {}
    for row in edge_rows:
        key = str(row["figure_status"])
        counts[key] = counts.get(key, 0) + 1
    return {
        "edge_rows": edge_rows,
        "edge_status_counts": counts,
        "node_rows": node_rows,
        "v8j_original_cut_load_kip": original_cut_load,
        "figure_constrained_unsupported_nodes": sorted(UNSUPPORTED_NODES),
        "figure_constrained_unsupported_load_kip": unsupported_load,
        "candidate_supported_nodes": sorted(CANDIDATE_SUPPORTED_NODES),
        "candidate_supported_load_kip": candidate_supported_load,
        "load_conservation_check_kip": unsupported_load
        + candidate_supported_load
        - original_cut_load,
        "unsupported_fraction_of_v8j_cut": unsupported_load / original_cut_load,
        "gate_passed": False,
        "reason": "positive incoming load remains on three removed nodes with no visible surviving local Floor 96 beam path",
    }


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render_plot(payload: dict[str, object], model: dict[str, object]) -> None:
    canvas = Image.new("RGB", (1900, 1120), "white")
    draw = ImageDraw.Draw(canvas)
    navy = (31, 43, 61)
    red = (190, 57, 57)
    green = (50, 145, 90)
    amber = (222, 148, 50)
    blue = (62, 118, 177)
    grey = (180, 185, 193)
    topology = payload["topology_audit"]
    incoming = {int(key): float(value) for key, value in payload["incoming_loads_floor96_kip"].items()}

    draw.text(
        (950, 48),
        "WTC 1 V8K - topologie NIST du cut-set au niveau 96",
        anchor="mm",
        font=font(36, True),
        fill=navy,
    )

    # Left: only the locally audited orthogonal cut boundary.
    x0, y0, w, h = 90, 150, 910, 720
    draw.text(
        (x0 + w / 2, y0 - 40),
        "Figure 5-59(b) : chemins apres impact",
        anchor="mm",
        font=font(27, True),
        fill=navy,
    )
    coords = model["coords"]
    subset = {502, 503, 504, 505, 506, 603, 604, 605}
    xs = [coords[node][0] for node in subset]
    ys = [coords[node][1] for node in subset]
    sx = (w - 130) / (max(xs) - min(xs))
    sy = (h - 150) / (max(ys) - min(ys))

    def point(node: int) -> tuple[float, float]:
        x, y = coords[node]
        return x0 + 65 + (x - min(xs)) * sx, y0 + 75 + (max(ys) - y) * sy

    status_colors = {
        "removed_after_impact": red,
        "visible_after_impact": green,
        "not_a_direct_beam_path": amber,
    }
    for row in topology["edge_rows"]:
        first, second = (int(value) for value in row["edge"])
        color = status_colors[str(row["figure_status"])]
        if row["figure_status"] == "not_a_direct_beam_path":
            a, b = point(first), point(second)
            for step in range(0, 20, 2):
                t0, t1 = step / 20, min(1.0, (step + 1) / 20)
                draw.line(
                    (
                        a[0] + (b[0] - a[0]) * t0,
                        a[1] + (b[1] - a[1]) * t0,
                        a[0] + (b[0] - a[0]) * t1,
                        a[1] + (b[1] - a[1]) * t1,
                    ),
                    fill=color,
                    width=6,
                )
        else:
            draw.line((*point(first), *point(second)), fill=color, width=8)
    for node in sorted(subset):
        px, py = point(node)
        if node in UNSUPPORTED_NODES:
            fill = red
        elif node in CANDIDATE_SUPPORTED_NODES:
            fill = green
        else:
            fill = blue
        draw.ellipse((px - 17, py - 17, px + 17, py + 17), fill=fill, outline="white", width=3)
        draw.text((px, py - 27), str(node), anchor="ms", font=font(20, True), fill=navy)
    draw.text((x0 + 90, y0 + h - 25), "rouge : retire", font=font(19, True), fill=red)
    draw.text((x0 + 300, y0 + h - 25), "vert : visible", font=font(19, True), fill=green)
    draw.text((x0 + 525, y0 + h - 25), "orange : diagonale proxy", font=font(19, True), fill=amber)

    # Right: incoming loads split by topology outcome.
    rx, ry, rw, rh = 1080, 150, 720, 720
    draw.text(
        (rx + rw / 2, ry - 40),
        "Charge arrivant sur les 4 noeuds",
        anchor="mm",
        font=font(27, True),
        fill=navy,
    )
    loads = {node: incoming[node] for node in sorted(CUT_NODES)}
    max_load = max(loads.values()) * 1.18
    bar_w = 115
    gap = 45
    base_y = ry + rh - 95
    chart_h = rh - 180
    for index, node in enumerate(sorted(CUT_NODES)):
        bx = rx + 70 + index * (bar_w + gap)
        value = loads[node]
        bh = chart_h * value / max_load
        color = green if node in CANDIDATE_SUPPORTED_NODES else red
        draw.rounded_rectangle((bx, base_y - bh, bx + bar_w, base_y), radius=12, fill=color)
        draw.text((bx + bar_w / 2, base_y - bh - 16), f"{value:.0f}", anchor="ms", font=font(20, True), fill=navy)
        draw.text((bx + bar_w / 2, base_y + 32), str(node), anchor="ma", font=font(23, True), fill=navy)
        draw.text(
            (bx + bar_w / 2, base_y + 62),
            "chemin" if node in CANDIDATE_SUPPORTED_NODES else "sans chemin",
            anchor="ma",
            font=font(16, True),
            fill=color,
        )
    unsupported = float(topology["figure_constrained_unsupported_load_kip"])
    draw.rounded_rectangle((rx + 55, ry + rh - 30, rx + rw - 55, ry + rh + 70), radius=18, fill=(249, 229, 229))
    draw.text((rx + rw / 2, ry + rh), f"{unsupported:.0f} kip restent sans chemin local", anchor="mm", font=font(25, True), fill=red)
    draw.text((rx + rw / 2, ry + rh + 38), f"{100*float(topology['unsupported_fraction_of_v8j_cut']):.1f} % du cut V8J", anchor="mm", font=font(20), fill=navy)

    draw.rounded_rectangle((90, 970, 1810, 1070), radius=18, fill=(244, 232, 191))
    draw.text((950, 1000), "GATE FROID NON VALIDE - chemin local Floor 96 rejete", anchor="mm", font=font(29, True), fill=(135, 88, 20))
    draw.text((950, 1041), "Le prochain mecanisme a tester est la redistribution multi-etages; la figure NIST n'applique pas de charge verticale en tete de poteau.", anchor="mm", font=font(20, True), fill=navy)
    canvas.save(OUT_PNG)


def write_report(payload: dict[str, object]) -> None:
    topology = payload["topology_audit"]
    rows = [
        "# WTC 1 - V8K : topologie NIST du cut-set au niveau 96",
        "",
        "## Resultat principal",
        "",
        "La V8K remplace les sept aretes `nearest-four` du cut-set V8J par une transcription locale de la Figure 5-59(b) du modele NIST du niveau 96. Le resultat est plus contraignant que V8J : **une des sept aretes etait une diagonale de proxy qui n'apparait pas dans le plan orthogonal**, quatre liaisons de bord sont retirees dans le modele apres impact, et seulement les chemins 505-506 et 505-605 restent visibles.",
        "",
        "En rejouant les niveaux 99 a 97 de V8J, les colonnes retirees 503, 504 et 604 recoivent encore ensemble **{:.0f} kip**, soit **{:.1f} %** des 3 256 kip du cut V8J, sans chemin local visible vers un poteau survivant au niveau 96. La colonne 505 conserve un chemin candidat vers 506/605, mais sa section 14WF136 reste un proxy non as-built.".format(float(topology["figure_constrained_unsupported_load_kip"]), 100.0 * float(topology["unsupported_fraction_of_v8j_cut"])),
        "",
        "La conclusion n'est pas que la tour reelle aurait du tomber a froid. Elle est que **les poutres locales du niveau 96 montrees par NIST ne peuvent pas, seules, reparer le chemin manquant de V8J**. La redistribution reelle observee doit donc impliquer des mecanismes absents de ce sous-modele : action de portique sur plusieurs niveaux, flexion/cisaillement des troncons de poteaux, planchers de bureau vers les facades, hat truss, ou une combinaison de ces chemins.",
        "",
        "## Faits et resultats du modele officiel",
        "",
        "- La Figure 2-2 fournit l'implantation et la numerotation des poteaux du noyau au niveau 96.",
        "- Le modele complet du plancher 96 vient d'un modele SAP2000 converti et comprend poutres du noyau, dalle, fermes, poteaux et elements de rupture; il ne s'agit pas d'une nomenclature as-built publiee dans la figure.",
        "- NIST precise que les dommages raffines Case A/B n'ont jamais ete utilises dans le modele complet de plancher; le dommage structurel Case Ai a aussi ete reutilise pour Case Bi faute de donnees disponibles au moment du calcul.",
        "- Les poteaux endommages mais non severes ont ete conserves comme intacts dans cette analyse.",
        "- Point essentiel : aucune charge verticale n'a ete appliquee en tete des poteaux dans l'analyse gravitaire/thermique de ce sous-systeme. La Figure 5-59 documente donc une topologie de modele, pas une validation officielle du transfert des charges verticales du bloc superieur.",
        "",
        "## Transcription du cut-set",
        "",
        "| Arete V8J | Statut dans la Figure 5-59(b) | Qualification |",
        "|---|---|---|",
    ]
    for edge in topology["edge_rows"]:
        rows.append(
            "| {}-{} | {} | {} |".format(
                edge["edge"][0], edge["edge"][1], edge["figure_status"], edge["geometry_status"]
            )
        )
    rows.extend(
        [
            "",
            "| Noeud retire | Charge entrante V8J | Chemin local Figure 5-59 | Gate topologique |",
            "|---:|---:|---|---|",
        ]
    )
    for node in topology["node_rows"]:
        rows.append(
            "| {} | {:.1f} kip | {} | {} |".format(
                node["column"],
                float(node["incoming_load_kip"]),
                node["post_impact_local_path"],
                "passe provisoirement" if node["topology_gate_pass"] else "echoue",
            )
        )
    rows.extend(
        [
            "",
            "## Hypotheses propres au modele",
            "",
            "- Les charges entrantes sont celles du reseau reduit V8J apres redistribution aux niveaux 99, 98 et 97. Elles ne sont ni mesurees ni extraites d'un fichier de resultats NIST poteau par poteau.",
            "- La transcription porte uniquement sur les sept aretes du cut-set. Elle ne transforme pas l'image ANSYS en un modele complet de 46 280 elements.",
            "- Le statut de 505-605 est de confiance moyenne parce que la poutre est graphiquement decalee du centroide du poteau et reliee par la zone de noeud modelisee. Cette ambiguite ne change pas le sort des noeuds 503, 504 et 604.",
            "- Les lois 14WF136+dalle heritees ne sont conservees que pour documenter le chemin candidat du noeud 505; elles ne sont pas creditees aux trois noeuds sans topologie survivante.",
            "",
            "## Ecran force-deplacement du seul chemin candidat",
            "",
            "Avec les deux aretes visibles 505-506 et 505-605 imposees au meme deplacement, l'enveloppe 14WF136+dalle heritee atteint au maximum **{:.0f} kip** pour une demande de **{:.0f} kip** sur 505; le deficit du proxy vaut **{:.0f} kip**. Ce resultat echoue lui aussi, mais il ne qualifie pas la capacite as-built puisque les sections et assemblages de la Figure 5-59 ne sont pas identifies.".format(
                float(payload["candidate_505_force_displacement_proxy"]["maximum_combined_proxy_force_kip"]),
                float(payload["candidate_505_force_displacement_proxy"]["incoming_demand_kip"]),
                float(payload["candidate_505_force_displacement_proxy"]["proxy_capacity_deficit_kip"]),
            ),
            "",
            "## Contradictions et zones d'incertitude",
            "",
            "- La tour est restee debout apres impact, alors que le chemin local Figure 5-59 laisse une charge positive sans appui dans notre empilement unidimensionnel. C'est une contradiction avec le **sous-modele V8J/V8K autonome**, pas avec la structure reelle complete.",
            "- Le modele complet de plancher utilise une ancienne definition Case Ai et n'a jamais integre les dommages raffines Case A/B. Il est donc impropre a une reproduction definitive du cas officiel final.",
            "- La Figure 5-59 ne donne ni sections de poutres, ni assemblages, ni lois force-deplacement, ni affectation de sieges. Drawing Book 5/6 ou les entrees SAP/ANSYS restent necessaires pour une verification as-built.",
            "- Puisque les charges verticales en tete de poteau etaient absentes du sous-systeme NIST, son maintien sous ses propres charges de plancher ne valide pas le transfert vertical de {:.0f} kip teste ici.".format(float(topology["v8j_original_cut_load_kip"])),
            "",
            "## Decision et suite",
            "",
            "**GATE FROID NON VALIDE.** La V8K rejette le plancher 96 local comme solution autonome au cut-set. La V8L doit construire un chemin multi-etages explicite pour 503/504/604, avec flexion/cisaillement des poteaux et poutres sur 95-99, puis comparer sa redistribution froide aux sorties globales NIST. Aucune transition thermique ni animation Blender dynamique n'est encore autorisee.",
            "",
            f"Temps d'execution : {payload['runtime_seconds']:.2f} s. La transcription, les charges rejouees et les limites epistemiques sont conservees dans le JSON V8K.",
        ]
    )
    OUT_REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    inputs = load_inputs()
    incoming, floors, model = replay_incoming_floor96(inputs)
    topology = topology_audit(inputs, incoming)
    candidate_proxy = candidate_path_proxy(
        inputs, model, float(incoming.get(505, 0.0))
    )
    runtime_seconds = time.perf_counter() - started
    payload = {
        "model": "WTC1_V8K_FLOOR96_NIST_TOPOLOGY",
        "version": "8.10.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": runtime_seconds,
        "configuration_file": str(CONFIG.relative_to(ROOT)).replace("\\", "/"),
        "facts_transferred": inputs["config"]["official_facts"],
        "model_assumptions": inputs["config"]["model_hypotheses"],
        "gate_definition": inputs["config"]["gate"],
        "replayed_floors": floors,
        "incoming_loads_floor96_kip": {
            str(node): float(incoming.get(node, 0.0)) for node in sorted(incoming)
        },
        "topology_audit": topology,
        "candidate_505_force_displacement_proxy": candidate_proxy,
        "gate_result": {
            "passed": False,
            "status": "LOCAL_FLOOR96_PATH_REJECTED_MULTISTORY_PATH_REQUIRED",
            "reason": topology["reason"],
            "thermal_runs_authorized": False,
            "blender_coupling_authorized": False,
        },
        "next_iteration": {
            "id": "V8L",
            "objective": "Construct an explicit multistory 95-99 frame-action path for Columns 503, 504 and 604, including column-segment flexure/shear, surviving beam connections and comparison with NIST cold post-impact global redistribution before thermal loading.",
        },
    }
    OUT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_report(payload)
    render_plot(payload, model)
    print(
        json.dumps(
            {
                "status": "ok",
                "gate_passed": False,
                "unsupported_nodes": sorted(UNSUPPORTED_NODES),
                "unsupported_load_kip": topology[
                    "figure_constrained_unsupported_load_kip"
                ],
                "outputs": [str(OUT_JSON), str(OUT_REPORT), str(OUT_PNG)],
                "runtime_seconds": runtime_seconds,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
