"""V11B controlled replay: unchanged scenarios, explicit start and mass accounts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import run_v10y_integrated_exploratory_chain as legacy
import v11b_propagation as physics

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "wtc1_simulation_v8/data/v11b_initialization_mass_predeclaration.json"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def write_csv(path: Path, rows: list) -> None:
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def typed_rows(path: Path) -> list:
    def cast(value):
        if value == "": return None
        if value in ("True", "False"): return value == "True"
        try: return float(value)
        except ValueError: return value
    return [{k: cast(v) for k, v in row.items()} for row in legacy.read_csv(path)]


def equal(actual, expected) -> bool:
    if isinstance(actual, (int, float)) and not isinstance(actual, bool) and isinstance(expected, (int, float)):
        return math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
    return actual == expected


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def contexts(cfg: dict, baseline: dict) -> tuple[list, list]:
    old_rows = typed_rows(ROOT/cfg["baseline_named_summary"]) + typed_rows(ROOT/cfg["baseline_grid_summary"])
    old_by_id = {r["scenario_id"]: r for r in old_rows}
    scenarios = [{"scenario_class": "NAMED_EXPLORATORY_ENVELOPE", **s} for s in baseline["exploratory_model"]["named_scenarios"]] + legacy.grid_scenarios(baseline)
    temp_path = baseline["documented_inputs"]["temperature_envelopes"]["path"]
    damage_path = next(r["path"] for r in baseline["regression_files"] if r["role"] == "v10p_damage_matrix")
    temperatures = legacy.build_temperature_index(legacy.read_csv(ROOT/temp_path))
    damage = legacy.build_core_damage_retention(legacy.read_csv(ROOT/damage_path), baseline)
    cache, output, checks = {}, [], []
    if len(old_by_id) != len(scenarios):
        raise RuntimeError("Scenario count mismatch")
    for scenario in scenarios:
        sid = scenario["scenario_id"]
        old = old_by_id[sid]
        input_match = all(equal(value, old[key]) for key, value in scenario.items())
        key = tuple(scenario[k] for k in cfg["thermal_cache_key_fields"])
        if key not in cache:
            trigger, audit, _, snapshot = legacy.evaluate_initiation(scenario, baseline, temperatures, damage, False)
            cache[key] = trigger, audit, snapshot
        trigger, audit, snapshot = cache[key]
        # Cached thermal states carry the first scenario's ID; update metadata only.
        trigger = None if trigger is None else {**trigger, "scenario_id": sid}
        snapshot = {f: {**row, "scenario_id": sid} for f, row in snapshot.items()}
        fields = {
            **audit,
            "initiation_time_s_after_impact": None if trigger is None else trigger["time_s"],
            "initiation_floor": None if trigger is None else trigger["floor"],
            "initiation_dcr": None if trigger is None else trigger["demand_over_capacity"],
        }
        thermal_match = all(equal(value, old[k]) for k, value in fields.items())
        if not input_match or not thermal_match:
            raise RuntimeError(f"Frozen scenario or initiation mismatch: {sid}")
        checks.append({"scenario_id": sid, "inputs_unchanged": input_match,
                       "initiation_and_thermal_audit_unchanged": thermal_match,
                       "capacity_trigger_time_s": fields["initiation_time_s_after_impact"],
                       "capacity_trigger_floor": fields["initiation_floor"]})
        output.append({"scenario": scenario, "old": old, "trigger": trigger, "snapshot": snapshot})
    return output, [{"thermal_cache_unique_evaluations": len(cache), "scenario_count": len(scenarios)}, *checks]


def calculate(cfg: dict, baseline: dict, cached: list) -> dict:
    summaries, comparisons, ledger, timeline, legacy_timeline, replay_checks = [], [], [], [], [], []
    transition_counts = Counter()
    for context in cached:
        scenario, old, trigger, snapshot = [context[k] for k in ("scenario", "old", "trigger", "snapshot")]
        keep = scenario["scenario_id"] in cfg["detailed_scenario_ids"]
        reference, _, old_events = legacy.propagate(scenario, trigger, snapshot, baseline, keep)
        mismatches = [k for k, v in reference.items() if not equal(v, old[k])]
        replay_checks.append({"scenario_id": scenario["scenario_id"], "field_count": len(reference),
                              "pass": not mismatches, "mismatched_fields": "|".join(mismatches)})
        legacy_timeline.extend(old_events)
        by_variant = {}
        for variant in cfg["variants"]:
            summary, rows, events = physics.run_stack(scenario, trigger, snapshot, baseline, variant, keep)
            summaries.append(summary)
            by_variant[variant["id"]] = summary
            ledger.extend(rows)
            timeline.extend(events)
            if scenario["scenario_class"] == "DETERMINISTIC_SENSITIVITY_GRID_NOT_PROBABILITY":
                transition_counts[(variant["id"], reference["outcome_label"], summary["outcome"])] += 1
        new = by_variant["V11B_CORRECTED"]
        comparisons.append({**scenario,
            "capacity_trigger_time_s": new["capacity_trigger_time_s"], "capacity_trigger_floor": new["capacity_trigger_floor"],
            "legacy_outcome": reference["outcome_label"], "corrected_outcome": new["outcome"],
            "legacy_duration_excluding_first_drop_s": reference["collapse_duration_s"],
            "time_only_duration_s": by_variant["TIME_ONLY_DIAGNOSTIC"]["motion_duration_s"],
            "time_and_resistance_duration_s": by_variant["TIME_AND_RESISTANCE_DIAGNOSTIC"]["motion_duration_s"],
            "corrected_duration_from_rest_s": new["motion_duration_s"],
            "legacy_initial_mass_kg": reference["initial_upper_block_mass_kg"],
            "corrected_initial_mass_kg": new["initial_cluster_mass_kg"],
            "legacy_final_cluster_mass_kg": reference["final_moving_mass_kg"],
            "corrected_final_cluster_mass_kg": new["cluster_mass_kg"],
            "corrected_unaccreted_mass_kg": new["unaccreted_mass_kg"],
            "corrected_omitted_mass_kg": new["diagnostic_omitted_mass_kg"],
            "corrected_total_mass_kg": new["total_tower_mass_kg"],
            "legacy_final_kinetic_energy_J": reference["final_kinetic_energy_j"],
            "corrected_final_kinetic_energy_J": new["final_kinetic_energy_J"],
            "corrected_final_velocity_m_s": new["final_velocity_m_s"],
            "corrected_initial_resistance_to_weight": new["initial_force_capacity_to_weight"],
            "debris_settled_simulated": False})
    transitions = [{"variant_id": v, "legacy_outcome": old, "new_outcome": new, "grid_case_count": count}
                   for (v, old, new), count in sorted(transition_counts.items())]
    return {"variant_summaries": summaries, "comparison_cases": comparisons,
            "detailed_energy_mass_momentum_ledger": ledger, "detailed_motion_timeline": timeline,
            "legacy_detailed_motion_timeline": legacy_timeline,
            "legacy_propagation_replay_audit": replay_checks, "outcome_transitions": transitions}


def audit(cfg: dict, baseline: dict, data: dict, replay_digest: str, initiation_checks: list) -> dict:
    tests = physics.analytical_tests()
    def check(name, condition, evidence):
        tests.append({"name": name, "pass": bool(condition), "evidence": evidence})
    comparisons, summaries = data["comparison_cases"], data["variant_summaries"]
    corrected = [r for r in summaries if r["variant_id"] == "V11B_CORRECTED"]
    expected = cfg["acceptance"]["named_scenarios"]+cfg["acceptance"]["grid_scenarios"]
    check("all_declared_scenarios", len(comparisons) == expected, len(comparisons))
    check("all_three_variants", len(summaries) == 3*expected, len(summaries))
    check("scenario_parameters_and_initiation_unchanged", all(r["inputs_unchanged"] and r["initiation_and_thermal_audit_unchanged"] for r in initiation_checks[1:]), len(initiation_checks)-1)
    check("frozen_legacy_propagation_reproduced", all(r["pass"] for r in data["legacy_propagation_replay_audit"]), sum(r["field_count"] for r in data["legacy_propagation_replay_audit"]))
    new_digest = digest(data)
    check("exact_deterministic_replay", new_digest == replay_digest, new_digest)
    mapping = {"NO_INITIATION_WITHIN_THERMAL_WINDOW": "NO_CAPACITY_TRIGGER_IN_WINDOW",
               "INITIATED_THEN_ARRESTED": "DOWNWARD_MOTION_ARRESTED",
               "GLOBAL_PROGRESSION_TO_GROUND_IN_REDUCED_MODEL": "LOWER_MODEL_BOUNDARY_REACHED_WITH_RESIDUAL_MOTION"}
    by_id = {(r["scenario_id"], r["variant_id"]): r for r in summaries}
    time_errors = []
    time_only_invariant = True
    for row in comparisons:
        diagnostic = by_id[row["scenario_id"], "TIME_ONLY_DIAGNOSTIC"]
        time_only_invariant &= mapping[row["legacy_outcome"]] == diagnostic["outcome"]
        if row["capacity_trigger_time_s"] is not None:
            freefall = math.sqrt(2*baseline["documented_inputs"]["tower"]["upper_office_story_height_m"]*row["initial_drop_fraction_of_story"]/baseline["exploratory_model"]["gravity_m_s2"])
            time_errors.append(abs(diagnostic["motion_duration_s"]-row["legacy_duration_excluding_first_drop_s"]-freefall))
            time_only_invariant &= equal(diagnostic["cluster_mass_kg"], row["legacy_final_cluster_mass_kg"])
            time_only_invariant &= equal(diagnostic["final_kinetic_energy_J"], row["legacy_final_kinetic_energy_J"])
    check("time_only_change_preserves_legacy_outcomes_mass_and_KE", time_only_invariant, True)
    check("time_only_adds_exact_freefall_duration", max(time_errors) < 1e-10, max(time_errors))
    check("initial_mass_preserved_independently_of_gap_fraction", all(r["legacy_initial_mass_kg"] == r["corrected_initial_mass_kg"] for r in comparisons), expected)
    check("corrected_omitted_mass_zero", all(r["diagnostic_omitted_mass_kg"] == 0 for r in corrected), expected)
    check("corrected_mass_closes_at_every_recorded_event", all(abs(r["cluster_mass_kg"]+r["unaccreted_mass_kg"]-r["total_mass_kg"]) <= 1e-12*r["total_mass_kg"] for r in data["detailed_motion_timeline"] if r["variant_id"] == "V11B_CORRECTED"), True)
    boundaries = [r for r in corrected if r["outcome"] == "LOWER_MODEL_BOUNDARY_REACHED_WITH_RESIDUAL_MOTION"]
    check("boundary_arrivals_have_full_mass_and_unresolved_motion", all(r["cluster_mass_kg"] == r["total_tower_mass_kg"] and r["unaccreted_mass_kg"] == 0 and r["final_velocity_m_s"] > 0 and r["final_kinetic_energy_J"] > 0 and not r["debris_settled_simulated"] for r in boundaries), len(boundaries))
    no_starts = [r for r in corrected if r["outcome"] == "CAPACITY_TRIGGER_NO_DOWNWARD_START_UNDER_CONSTANT_RESISTANCE"]
    check("no_start_is_not_hidden_initial_motion", all(r["actual_motion_start_time_s"] is None and r["displacement_m"] == r["motion_duration_s"] == r["final_kinetic_energy_J"] == 0 and r["initial_force_capacity_to_weight"] >= 1 for r in no_starts), len(no_starts))
    arrested = [r for r in corrected if r["outcome"] == "DOWNWARD_MOTION_ARRESTED"]
    check("arrest_has_zero_velocity_and_no_KE", all(r["final_velocity_m_s"] == r["final_kinetic_energy_J"] == 0 for r in arrested), len(arrested))
    check("initial_event_really_at_rest_and_zero_displacement", all(r["velocity_m_s"] == r["downward_displacement_m"] == r["kinetic_energy_J"] == 0 for r in data["detailed_motion_timeline"] if r["event"] == "CAPACITY_TRIGGER_AT_REST"), True)
    check("valid_outcome_vocabulary", all(r["outcome"] in cfg["outcome_vocabulary"] for r in summaries), True)
    energy = max(max(r["maximum_interval_energy_error"], r["normalized_global_energy_error"]) for r in summaries)
    momentum = max(r["maximum_momentum_error"] for r in summaries)
    mass = max(r["maximum_mass_inventory_error"] for r in summaries)
    for label, value in (("energy", energy), ("momentum", momentum), ("mass", mass)):
        check(f"all_{label}_ledgers_close", value <= cfg["acceptance"][f"maximum_normalized_{label}_residual"], value)
    return {"iteration": "V11B", "status": "PASS" if all(r["pass"] for r in tests) else "FAIL",
            "tests_passed": sum(r["pass"] for r in tests), "test_count": len(tests), "tests": tests,
            "numerical_digest_sha256": new_digest, "maximum_energy_error": energy,
            "maximum_momentum_error": momentum, "maximum_mass_error": mass,
            "maximum_time_only_comparison_error_s": max(time_errors), "historical_validation": False}


SHORT_LABELS = {"NO_CAPACITY_TRIGGER_IN_WINDOW": "Pas de seuil franchi",
    "CAPACITY_TRIGGER_NO_DOWNWARD_START_UNDER_CONSTANT_RESISTANCE": "Seuil franchi, sans départ",
    "DOWNWARD_MOTION_ARRESTED": "Mouvement puis arrêt",
    "LOWER_MODEL_BOUNDARY_REACHED_WITH_RESIDUAL_MOTION": "Limite basse atteinte"}


def counts_by_variant(data: dict) -> dict:
    return {variant: dict(Counter(r["outcome"] for r in data["variant_summaries"] if r["scenario_id"].startswith("GRID-") and r["variant_id"] == variant))
            for variant in ("TIME_ONLY_DIAGNOSTIC", "TIME_AND_RESISTANCE_DIAGNOSTIC", "V11B_CORRECTED")}


def figure(path: Path, data: dict) -> None:
    image = Image.new("RGB", (1550, 1050), "#f4f7fa")
    draw = ImageDraw.Draw(image)
    def text(x, y, value, size=22, color="#24334a", bold=False):
        file = "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
        draw.text((x, y), value, font=ImageFont.truetype(file, size), fill=color)
    text(40, 25, "WTC 1 · V11B · Départ au repos et masse complète", 35, bold=True)
    text(40, 80, "Même grille de paramètres · seules l'initialisation et la comptabilité mécanique changent", 23)
    text(40, 130, "729 scénarios — les comptes ne sont pas des probabilités historiques", 25, bold=True)
    counts = counts_by_variant(data)
    heads = [(50, "Résultat dans le modèle"), (590, "V10Y"), (810, "+ temps"), (1030, "+ résistance"), (1280, "+ masse")]
    draw.rectangle((35, 178, 1515, 221), fill="#dce7f2")
    for x, value in heads: text(x, 184, value, 23, bold=True)
    legacy_counts = {"NO_CAPACITY_TRIGGER_IN_WINDOW": 297, "CAPACITY_TRIGGER_NO_DOWNWARD_START_UNDER_CONSTANT_RESISTANCE": 0,
                     "DOWNWARD_MOTION_ARRESTED": 144, "LOWER_MODEL_BOUNDARY_REACHED_WITH_RESIDUAL_MOTION": 288}
    for n, (key, label) in enumerate(SHORT_LABELS.items()):
        y = 235+49*n
        text(50, y, label, 23)
        for x, value in zip((625, 845, 1090, 1330), (legacy_counts.get(key,0), *[counts[v].get(key,0) for v in counts])):
            text(x, y, str(value), 25, bold=True)
    text(45, 447, "Ancien cas animé GRID-0119 — conservé pour comparaison, sans nouvelle sélection", 24, bold=True)
    selected = next(r for r in data["comparison_cases"] if r["scenario_id"] == "GRID-0119")
    text(50, 505, "Début du déplacement (zoom sur 2 secondes)", 23, bold=True)
    x0, y0, x1, y1 = 100, 600, 730, 905
    draw.line((x0,y0,x0,y1,x1,y1), fill="#5b6e84", width=2)
    max_drop = 24.0
    text(550, 575, "Déplacement (m)", 17)
    for t in (0, .5, 1, 1.5, 2):
        x = x0+(x1-x0)*t/2
        draw.line((x,y0,x,y1), fill="#dce3eb")
        text(x-10, y1+10, f"{t:g}", 19)
    for d in (0,8,16,24):
        y = y1-(y1-y0)*d/max_drop
        draw.line((x0,y,x1,y), fill="#dce3eb")
        text(x0-43,y-12,str(d),18)
    series = [
        ([(r["relative_time_s"],r["upper_block_drop_m"],r["velocity_m_s"]) for r in data["legacy_detailed_motion_timeline"] if r["scenario_id"] == "GRID-0119"], "#a7542a"),
        ([(r["time_since_trigger_s"],r["downward_displacement_m"],r["velocity_m_s"]) for r in data["detailed_motion_timeline"] if r["scenario_id"] == "GRID-0119" and r["variant_id"] == "V11B_CORRECTED"], "#216aaa")]
    for values, color in series:
        points=[]
        for (ta,da,va),(tb,db,_) in zip(values, values[1:]):
            if ta > 2: break
            if tb <= ta: continue
            tb2 = min(tb,2)
            acceleration = 2*(db-da-va*(tb-ta))/(tb-ta)**2
            for k in range(21):
                t = ta+(tb2-ta)*k/20
                d = da+va*(t-ta)+0.5*acceleration*(t-ta)**2
                points.append((x0+(x1-x0)*t/2,y1-(y1-y0)*d/max_drop))
        if len(points)>1: draw.line(points,fill=color,width=4)
    text(110, 554, "Orange : V10Y", 21, "#a7542a")
    text(350, 554, "Bleu : V11B", 21, "#216aaa")
    text(180, 946, "Temps depuis le seuil (s) · interpolation mécanique", 19)
    text(785, 510, "Comparaison du même scénario", 25, bold=True)
    rows = [
        ("Départ", "1,829 m et vitesse imposées → repos à 0 m"),
        ("Masse finale", f"{selected['legacy_final_cluster_mass_kg']/1e6:.1f} → {selected['corrected_final_cluster_mass_kg']/1e6:.1f} millions de kg"),
        ("Durée calculée", f"{selected['legacy_duration_excluding_first_drop_s']:.2f} s* → {selected['corrected_duration_from_rest_s']:.2f} s"),
        ("Énergie finale", f"{selected['corrected_final_kinetic_energy_J']/1e9:.1f} GJ — encore en mouvement"),
        ("Vitesse finale", f"{selected['corrected_final_velocity_m_s']:.2f} m/s"),
    ]
    for n,(label,value) in enumerate(rows):
        y=565+67*n
        text(790,y,label,21,bold=True)
        text(790,y+28,value,22)
    text(790,925,"* V10Y omettait le temps de sa chute initiale.",20)
    text(40,995,"Modèle réduit exploratoire : pas de choc au sol, pas de débris stabilisés, pas encore d'impact/incendie calculés indépendamment.",20,"#944c25")
    image.save(path)


def report(cfg: dict, data: dict, checked: dict, cache_audit: list, elapsed: float) -> str:
    counts = counts_by_variant(data)
    count_table = "\n".join(f"| {SHORT_LABELS[key]} | {counts['TIME_ONLY_DIAGNOSTIC'].get(key,0)} | {counts['TIME_AND_RESISTANCE_DIAGNOSTIC'].get(key,0)} | {counts['V11B_CORRECTED'].get(key,0)} |" for key in SHORT_LABELS)
    named = [r for r in data["comparison_cases"] if not r["scenario_id"].startswith("GRID-") or r["scenario_id"] == "GRID-0119"]
    def fmt(value, unit=""):
        return "—" if value is None else f"{value:.3f}{unit}"
    named_table = "\n".join(f"| {r['scenario_id']} | {fmt(r['capacity_trigger_time_s'])} | {SHORT_LABELS[r['corrected_outcome']]} | {fmt(r['corrected_duration_from_rest_s'])} | {r['corrected_final_kinetic_energy_J']/1e9:.3f} |" for r in named)
    selected = next(r for r in named if r["scenario_id"] == "GRID-0119")
    return f"""# WTC 1 — V11B : départ, masse et limite finale du modèle réduit

## Résultat de cette étape

V11B corrige le début du mouvement : départ à déplacement nul et vitesse nulle, résistance active pendant le premier parcours, temps de ce parcours compté. Le demi-étage de masse absent de V10Y est désormais accré­té explicitement. La fin au dernier niveau est appelée **limite inférieure du modèle atteinte avec mouvement résiduel**, et non débris stabilisés ou effondrement complet résolu.

Les 729 scénarios de grille et trois scénarios nommés sont inchangés. Les paramètres, seuils thermiques, températures et dommages de référence ont été comparés au cache V10Y. Aucun ajustement n'a été fait pour obtenir un effondrement, l'empêcher, ou rejoindre la chronologie observée. Les contrôles passent : {checked['tests_passed']}/{checked['test_count']}.

## 1. Faits directement vérifiés

L'inspection du code V10Y montre que son temps de propagation zéro contient déjà un déplacement f·h et une vitesse sqrt(2gfh), sans résistance pendant ce premier parcours. Après accrétion des niveaux inférieurs, sa masse représente 109,5 étages et non 110. Ces constats sont des faits de logiciel, pas des observations sur la tour.

V10Y et V10Z ont été laissées intactes. Leurs empreintes, les entrées utilisées et le master Blender sont vérifiés avant/après. L'ancien calcul de propagation est reproduit par appel de sa fonction pure, sans relancer son programme de publication ni écraser un résultat.

## 2. Résultats de modèles officiels réutilisés

La carte simplifiée de dommages et les enveloppes de température restent celles reprises des modèles NIST dans V10P/V10Q/V10Y. **V11B ne lance pas encore un avion contre une structure détaillée et ne résout pas encore les incendies.** Le calcul actuel explore la réponse à ces entrées. Le polynôme E(T) de V11A n'est pas utilisé ici ; l'ancienne prolongation exploratoire de la loi Fy(T) de V10Y reste inchangée, y compris ses limites de domaine.

Le seuil de capacité de V10Y est également inchangé. Son franchissement ne devient pas une vitesse imposée. Si la résistance dynamique constante reste supérieure au poids du bloc, les deux sous-modèles ne décrivent pas une transition compatible : cette situation reçoit une catégorie explicite, pas une correction cachée.

## 3. Éléments des archives locales

Aucune nouvelle consultation de l'archive source n'a été nécessaire. Les sections, treillis et appuis de V11A restent disponibles mais ne fournissent pas encore la résistance énergétique de toute la tour. Leur somme de forces ou de travaux de ressorts isolés n'est pas injectée dans cette progression 1D.

## 4. Hypothèses et équations conservées ou corrigées

Le modèle reste une pile uniforme de 110 étages de 3,6576 m ; elle ne devient pas la géométrie hétérogène de 416,9664 m par une correction de comptabilité. Au seuil situé au niveau i, M0=(110−i+α)m avec α=0,5, comme en V10Y. La fraction de parcours f reste indépendante de α : lier les deux aurait changé des masses initiales. Cette séparation est une convention de masses concentrées, pas une reconstruction de densité spatiale.

Premier intervalle : d=f·h, résistance F=R_i/h, travail Fd=fR_i. Après ce parcours, capture de (1−α)m, puis capture de m à chaque parcours complet i−1…1. Les R_i, leur gradient vers le bas et leur réduction au temps du seuil ne changent pas.

Pendant un intervalle : a=g−F/M ; v_−²=v0²+2ad ; Δt=2d/(v0+v_−). Si l'énergie s'épuise avant ou exactement à la fin, arrêt avec x=K0/(F−Mg), Δt=−v0/a, sans capture ni perte de choc fictive. À l'arrêt initial, F est une capacité disponible : si F≥Mg, la réaction mobilisée est Mg, l'accélération réalisée est zéro, et il n'y a pas de départ.

À la capture d'une masse immobile μ : v_+=Mv_−/(M+μ), perte=½Mμ/(M+μ)·v_−². L'impulsion et l'énergie sont vérifiées séparément. Le bilan global part de K0=0 : Kfinal=Wg−WR−Σ pertes. Le travail gravitaire initial figure une seule fois.

La masse « du bloc » désigne la masse affectée ou capturée, même à vitesse nulle. La masse non accré­tée reste inscrite. La variante finale a masse du bloc + masse non accré­tée = 110m à chaque événement. Deux variantes de diagnostic gardent délibérément la demi-masse omise dans un compte séparé, uniquement pour isoler les corrections.

Après un arrêt, les températures restent figées au seuil : ni chauffage ultérieur ni redémarrage ne sont résolus. À la dernière frontière, la vitesse et l'énergie demeurent explicitement présentes ; il n'y a ni modèle de fondation ni loi de dépôt des débris.

## 5. Résultats dérivés

### Effet séparé des corrections — 729 cas de grille

La colonne « temps seul » garde exactement les issues V10Y ; elle ajoute seulement le temps de la chute libre supposée. Les colonnes suivantes ajoutent la résistance initiale, puis la masse manquante.

| Issue dans le modèle | Temps seul | + résistance initiale | + masse complète V11B |
|---|---:|---:|---:|
{count_table}

Les nombres décrivent cette grille déterministe, jamais des probabilités de l'événement historique. « Seuil franchi, sans départ » n'est pas un verdict de stabilité réelle : la résistance constante et le critère de capacité sont deux hypothèses encore insuffisamment couplées.

L'ajout de la résistance initiale fait passer 19 anciens cas progressants à l'arrêt ; l'accrétion de la demi-masse manquante leur permet ensuite de progresser à nouveau dans ce modèle. Le total final de 288 arrivées à la frontière basse est donc identique au total ancien, sans que les deux corrections soient individuellement neutres. Les 90 cas sans départ faisaient auparavant partie des cas arrêtés après une vitesse initiale supposée.

### Cas nommés et ancien cas animé

| Scénario | Seuil après impact (s) | Issue V11B | Durée depuis le repos (s) | Énergie finale (GJ) |
|---|---:|---|---:|---:|
{named_table}

GRID-0119 est conservé parce qu'il pilotait déjà le film V10Z, pas parce qu'il serait le meilleur cas après correction. Son seuil reste à {selected['capacity_trigger_time_s']:.0f} s. Sa durée passe de {selected['legacy_duration_excluding_first_drop_s']:.3f} s (temps initial absent) à {selected['corrected_duration_from_rest_s']:.3f} s depuis le repos. Masse finale : {selected['legacy_final_cluster_mass_kg']/1e6:.3f} → {selected['corrected_final_cluster_mass_kg']/1e6:.3f} millions de kg. L'énergie finale de {selected['corrected_final_kinetic_energy_J']/1e9:.3f} GJ et la vitesse de {selected['corrected_final_velocity_m_s']:.3f} m/s ne sont pas annulées artificiellement.

### Vérifications

{checked['test_count']} tests, dont : intervalle accéléré et capture à solution analytique, arrêt à l'intérieur et exactement en frontière, résistance passive au repos, chute libre, vitesse constante, pile indépendante de deux étages, bornes 1/110, conservation de la demi-masse quel que soit f, paramètres inchangés et répétition exacte.

- Résidu relatif maximal d'énergie : {checked['maximum_energy_error']:.3e}.
- Résidu relatif maximal d'impulsion : {checked['maximum_momentum_error']:.3e}.
- Résidu relatif maximal d'inventaire de masse : {checked['maximum_mass_error']:.3e}.
- Erreur max du diagnostic « temps ajouté = temps de chute libre » : {checked['maximum_time_only_comparison_error_s']:.3e} s.
- {cache_audit[0]['thermal_cache_unique_evaluations']} évaluations thermiques distinctes mises en cache pour les 732 scénarios ; répétition numérique exacte. Exécution CPU : {elapsed:.2f} s, Python {platform.python_version()}. Aucun GPU, Blender ou logiciel installé.

Une relecture indépendante a confirmé les équations et ajouté une distinction entre capacité de résistance et résistance réellement mobilisée au repos, ainsi qu'un contrôle analytique à deux étages. Les tests qualifient ces équations et leur exécution, pas le bâtiment réel.

## 6. Limites, avion, incendies et réutilisation pour WTC2

L'objectif demandé reste : tour initialement en équilibre → impact d'un 767 → dommages calculés → incendie et transfert thermique → réponse structurelle, avec arrêt ou progression possibles. « Au point documenté » doit conserver les tolérances de position, d'angle, de vitesse et de masse ; ce ne sont pas des valeurs historiquement connues sans erreur. La dégradation de l'isolation, les ouvertures, le combustible et la ventilation relient impact et incendie : le feu n'est donc pas un effet visuel ajouté à la fin.

Le moteur de calcul pourra être commun aux deux tours. Les configurations devront rester distinctes : noyau orienté E–O pour WTC1, N–S pour WTC2, variations de dimensionnement/modifications, sections et événement d'impact propres à chaque tour. Voir [NIST NCSTAR1-1 p.8](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-1.pdf) et [NCSTAR1-2A tableau2-1 p.13](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2a.pdf). Ce n'est pas une nouvelle configuration WTC2 validée, ni une promesse de durée.

L'estimation vidéo des conditions d'impact doit rester distincte des valeurs choisies dans un cas de calcul : par exemple, 542±24 mph estimés pour UA175 versus 546 mph dans le cas de base du modèle officiel. Voir [présentation NIST sur les impacts](https://www.nist.gov/system/files/documents/2017/05/09/WTC_Symp_ARA_2.pdf) et [NCSTAR1-2B vol.2 tableau9-2 p.198](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2bv2.pdf).

Prochaine V11C : établir un panneau de plancher avec dalle, appuis déformables, liaisons et ruptures explicites à partir de V11A ; le vérifier au froid puis sous température/effets imposés, avant couplage à la structure spatiale. Garder séparés le modèle réduit, le solveur de structure et la visualisation. Aucune issue historique n'est imposée, et V10Z n'est pas remplacée par une animation dont le couplage serait présenté comme déjà complet.

## Fichiers

`comparison_cases.csv` : les 732 comparaisons ; `variant_summaries.csv` : les trois variantes ; `outcome_transitions.csv` : migrations entre issues ; `detailed_energy_mass_momentum_ledger.csv` et `detailed_motion_timeline.csv` : les trois cas nommés et GRID-0119 ; `corrected_driver.json` : interface de visualisation étiquetée, non appliquée à Blender ; `source_manifest.json`, `numerical_audit.json`, `offline_manifest.json` : entrées, contrôles et empreintes.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="wtc1_simulation_v8/output/v11b_initialization_mass")
    args = parser.parse_args()
    cfg = read_json(CONFIG)
    out = (ROOT/args.output_dir).resolve()
    allowed = [(ROOT/cfg[k]).resolve() for k in ("output_directory", "scratch_directory")]
    if not any(out == p or p in out.parents for p in allowed) or out.exists():
        raise ValueError("Use a new directory inside the declared V11B destinations")
    out.mkdir(parents=True, exist_ok=False)
    started_at = datetime.now().astimezone().isoformat()
    start = time.perf_counter()
    files = cfg["source_files"]+cfg["protected_files"]
    before = {r["path"]: sha(ROOT/r["path"]) for r in files}
    if any(before[r["path"]] != r["sha256"] for r in files):
        raise RuntimeError("Frozen source hash mismatch")
    baseline = read_json(ROOT/cfg["baseline_configuration"])
    cached, cache_audit = contexts(cfg, baseline)
    data = calculate(cfg, baseline, cached)
    repeated = digest(calculate(cfg, baseline, cached))
    checked = audit(cfg, baseline, data, repeated, cache_audit)
    write_json(out/"numerical_audit.json", checked)
    if checked["status"] != "PASS":
        print(json.dumps([r for r in checked["tests"] if not r["pass"]], ensure_ascii=False, indent=2))
        raise RuntimeError("Failed numerical audit; incomplete attempt retained")
    for name, rows in data.items():
        write_csv(out/f"{name}.csv", rows)
    write_json(out/"scenario_inputs.json", [r["scenario"] for r in cached])
    write_json(out/"initiation_cache_audit.json", cache_audit)
    write_json(out/"corrected_driver.json", {"iteration": "V11B", "applied_to_blender": False,
        "status": "CORRECTED_REDUCED_MODEL_NOT_VALIDATED_STRUCTURAL_DYNAMICS",
        "labels": ["MODELE REDUIT EXPLORATOIRE", "DEPART AU REPOS; MASSE COMPLETE", "LIMITE BASSE NE SIGNIFIE PAS DEBRIS STABILISES"],
        "tower": baseline["documented_inputs"]["tower"],
        "scenarios": [{"summary": next(s for s in data["variant_summaries"] if s["scenario_id"] == sid and s["variant_id"] == "V11B_CORRECTED"),
                       "events": [r for r in data["detailed_motion_timeline"] if r["scenario_id"] == sid and r["variant_id"] == "V11B_CORRECTED"]}
                      for sid in cfg["detailed_scenario_ids"]]})
    figure(out/"synthese_v11b_depart_masse.png", data)
    after = {r["path"]: sha(ROOT/r["path"]) for r in files}
    if before != after:
        raise RuntimeError("A protected input changed")
    elapsed = time.perf_counter()-start
    manifest = {"iteration": "V11B", "started_at": started_at, "finished_at": datetime.now().astimezone().isoformat(),
        "elapsed_seconds": elapsed, "python_executable": sys.executable, "python_version": platform.python_version(),
        "seed": cfg["random_seed"], "random_draw_used": False, "numerical_passes": 2,
        "thermal_cache_unique_evaluations": cache_audit[0]["thermal_cache_unique_evaluations"],
        "source_and_protected_files_unchanged": True,
        "inputs": [{"path": p, "sha256_before": h, "sha256_after": after[p]} for p,h in before.items()],
        "code": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in (CONFIG, Path(__file__).resolve(), Path(physics.__file__).resolve())]}
    write_json(out/"source_manifest.json", manifest)
    with (out/"rapport_v11b_depart_masse.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(report(cfg, data, checked, cache_audit, elapsed))
    summary = {"iteration": "V11B", "status": "PASS_REDUCED_MODEL_START_MASS_MOMENTUM_ENERGY_NOT_HISTORICAL_VALIDATION",
        "scenario_count": len(cached), "grid_count": 729, "named_count": 3,
        "variant_grid_outcomes": counts_by_variant(data), "tests_passed": checked["tests_passed"], "test_count": checked["test_count"],
        "maximum_energy_error": checked["maximum_energy_error"], "maximum_momentum_error": checked["maximum_momentum_error"],
        "maximum_mass_error": checked["maximum_mass_error"], "numerical_digest_sha256": checked["numerical_digest_sha256"],
        "selected_comparisons": [r for r in data["comparison_cases"] if r["scenario_id"] in cfg["detailed_scenario_ids"]],
        "initial_time_and_resistance_fixed": True, "missing_half_floor_mass_fixed": True,
        "terminal_motion_explicit_but_ground_contact_unsolved": True,
        "scenario_parameters_or_chronology_calibrated": False,
        "aircraft_impact_damage_independently_calculated": False, "fire_independently_solved": False,
        "component_library_globally_coupled": False, "blender_changed": False,
        "wtc2_configuration_created": False, "grid_fractions_are_event_probabilities": False,
        "elapsed_seconds": elapsed, "source_and_protected_files_unchanged": True,
        "next_iteration": "V11C", "next_objective": "Build a cold-stable floor panel with deformable supports and explicit connection/slab coupling from V11A; test load paths and local failures before tower-wide impact/fire coupling."}
    write_json(out/"results_v11b.json", summary)
    write_json(out/"offline_manifest.json", {"iteration": "V11B", "self_hash_excluded": True,
        "files": [{"path": p.relative_to(out).as_posix(), "size_bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(out.rglob("*")) if p.is_file()]})
    print(json.dumps({k:v for k,v in summary.items() if k != "selected_comparisons"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
