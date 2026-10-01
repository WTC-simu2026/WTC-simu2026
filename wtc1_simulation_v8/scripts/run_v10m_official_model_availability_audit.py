from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10m_official_model_availability_audit.json"
SCRIPT_PATH = Path(__file__).resolve()
USER_AGENT = "WTC1-reproducible-research-harness/10.13 (+local evidence audit)"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text.rstrip() + "\n")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def abs_path(relative: str) -> Path:
    return ROOT / Path(relative)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def verify_hash(path: Path, expected: str, role: str) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Missing {role}: {path}")
    actual = sha256_file(path)
    if actual.lower() != expected.lower():
        raise RuntimeError(f"Hash mismatch for {role}: expected {expected}, got {actual}")
    return {"role": role, "path": rel(path), "sha256": actual, "bytes": path.stat().st_size}


def load_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    if config.get("iteration") != "V10M":
        raise RuntimeError("Configuration iteration must be V10M")
    expected = config["expected"]
    checks = {
        "official_source_count": len(config["official_sources"]),
        "pdf_source_count": sum(item["kind"] == "pdf" for item in config["official_sources"]),
        "html_source_count": sum(item["kind"] == "html" for item in config["official_sources"]),
        "regression_file_count": len(config["regression_files"]),
        "protected_file_count": len(config["protected_files"]),
        "local_comparison_count": len(config["local_read_only_comparisons"]),
        "availability_target_count": len(config["availability_targets"]),
    }
    for key, actual in checks.items():
        if actual != expected[key]:
            raise RuntimeError(f"Unexpected {key}: {actual} != {expected[key]}")
    ids = [item["id"] for item in config["official_sources"]]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate official source id")
    allowed_hosts = set(config["source_policy"]["allowed_hosts"])
    for item in config["official_sources"]:
        host = urllib.parse.urlparse(item["url"]).hostname
        if host not in allowed_hosts:
            raise RuntimeError(f"Source host outside allowlist: {host}")
    return config


def regression_audit(config: dict[str, Any]) -> dict[str, Any]:
    regression_rows = [
        verify_hash(abs_path(item["path"]), item["expected_sha256"], item["role"])
        for item in config["regression_files"]
    ]
    protected_rows = [
        verify_hash(abs_path(item["path"]), item["expected_sha256"], item["role"])
        for item in config["protected_files"]
    ]
    local_rows = [
        verify_hash(abs_path(item["path"]), item["expected_sha256"], item["id"])
        for item in config["local_read_only_comparisons"]
    ]
    return {
        "iteration": "V10M",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "regression_file_count": len(regression_rows),
        "protected_file_count": len(protected_rows),
        "local_read_only_comparison_count": len(local_rows),
        "regression_files": regression_rows,
        "protected_files": protected_rows,
        "local_read_only_comparisons": local_rows,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_sources_directory_modified": False,
        "blender_master_unchanged": True,
    }


def pdf_page_count(path: Path) -> int | None:
    executable = shutil.which("pdfinfo")
    if not executable:
        return None
    result = subprocess.run(
        [executable, str(path)], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return None
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def html_title(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()


def existing_source_is_valid(item: dict[str, Any], target: Path) -> bool:
    if not target.is_file() or target.stat().st_size == 0:
        return False
    sample = target.read_bytes()[:2048].lower()
    if item["kind"] == "pdf":
        return sample[:5] == b"%pdf-"
    return b"<html" in sample or b"<!doctype html" in sample


def download_source(item: dict[str, Any], maximum_remaining: int) -> dict[str, Any]:
    target = abs_path(item["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if existing_source_is_valid(item, target):
        row: dict[str, Any] = {
            "id": item["id"],
            "authority": item["authority"],
            "kind": item["kind"],
            "requested_url": item["url"],
            "final_url": item["url"],
            "http_status": None,
            "content_type": "application/pdf" if item["kind"] == "pdf" else "text/html",
            "etag": None,
            "last_modified": None,
            "path": item["path"],
            "sha256": sha256_file(target),
            "bytes": target.stat().st_size,
            "purpose": item["purpose"],
            "acquisition_method": "REUSED_FROM_INTERRUPTED_SAME_ITERATION_ACQUISITION_AFTER_MAGIC_VALIDATION",
            "downloaded_at_utc": datetime.fromtimestamp(
                target.stat().st_mtime, tz=timezone.utc
            ).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        if item["kind"] == "pdf":
            row["pdf_page_count"] = pdf_page_count(target)
        else:
            row["html_title"] = html_title(target)
        return row
    request = urllib.request.Request(
        item["url"],
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.1",
        },
    )
    temporary = target.with_suffix(target.suffix + ".part")
    if temporary.exists():
        temporary.unlink()
    total = 0
    try:
        with urllib.request.urlopen(request, timeout=90) as response, temporary.open("wb") as output:
            final_url = response.geturl()
            status = getattr(response, "status", 200)
            headers = dict(response.headers.items())
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > maximum_remaining:
                    raise RuntimeError(f"Download cap exceeded while acquiring {item['id']}")
                output.write(chunk)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    if total == 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Empty source: {item['id']}")
    if item["kind"] == "pdf":
        with temporary.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                temporary.unlink(missing_ok=True)
                raise RuntimeError(f"Non-PDF payload for {item['id']}")
    else:
        sample = temporary.read_bytes()[:2048].lower()
        if b"<html" not in sample and b"<!doctype html" not in sample:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"Non-HTML payload for {item['id']}")
    temporary.replace(target)
    row: dict[str, Any] = {
        "id": item["id"],
        "authority": item["authority"],
        "kind": item["kind"],
        "requested_url": item["url"],
        "final_url": final_url,
        "http_status": status,
        "content_type": headers.get("Content-Type") or headers.get("content-type"),
        "etag": headers.get("ETag") or headers.get("etag"),
        "last_modified": headers.get("Last-Modified") or headers.get("last-modified"),
        "path": item["path"],
        "sha256": sha256_file(target),
        "bytes": target.stat().st_size,
        "purpose": item["purpose"],
        "acquisition_method": "NETWORK_DOWNLOAD",
        "downloaded_at_utc": utc_now(),
    }
    if item["kind"] == "pdf":
        row["pdf_page_count"] = pdf_page_count(target)
    else:
        row["html_title"] = html_title(target)
    return row


def acquire(config: dict[str, Any]) -> None:
    regression = regression_audit(config)
    rows: list[dict[str, Any]] = []
    total = 0
    cap = config["source_policy"]["maximum_total_download_bytes"]
    for item in config["official_sources"]:
        row = download_source(item, cap - total)
        rows.append(row)
        total += row["bytes"]
    if total > cap:
        raise RuntimeError("Aggregate V10M download cap exceeded")
    source_manifest = {
        "iteration": "V10M",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "network_access_authorized_by_user": True,
        "source_count": len(rows),
        "pdf_source_count": sum(row["kind"] == "pdf" for row in rows),
        "html_source_count": sum(row["kind"] == "html" for row in rows),
        "aggregate_bytes": total,
        "sources": rows,
        "source_archive_read": False,
        "official_sources_directory_modified": False,
    }
    acquisition = {
        "iteration": "V10M",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "download_invocation_count": sum(row["acquisition_method"] == "NETWORK_DOWNLOAD" for row in rows),
        "reused_after_interrupted_acquisition_count": sum(
            row["acquisition_method"].startswith("REUSED_") for row in rows
        ),
        "download_success_count": len(rows),
        "allowed_hosts": config["source_policy"]["allowed_hosts"],
        "aggregate_download_bytes": total,
        "maximum_total_download_bytes": cap,
        "pdf_magic_check_passed": all(
            abs_path(row["path"]).read_bytes()[:5] == b"%PDF-"
            for row in rows if row["kind"] == "pdf"
        ),
        "report_description_promoted_to_solver_input_count": 0,
        "solver_run_count": 0,
        "blender_run_count": 0,
    }
    write_json(abs_path(config["outputs"]["regression_audit"]), regression)
    write_json(abs_path(config["outputs"]["source_manifest"]), source_manifest)
    write_json(abs_path(config["outputs"]["acquisition_audit"]), acquisition)
    print(json.dumps({
        "iteration": "V10M",
        "phase": "acquire",
        "status": "PASS",
        "source_count": len(rows),
        "aggregate_bytes": total,
        "source_manifest": config["outputs"]["source_manifest"],
    }, ensure_ascii=False, indent=2))


def load_and_verify_acquired_sources(config: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest_path = abs_path(config["outputs"]["source_manifest"])
    if not manifest_path.is_file():
        raise RuntimeError("Run --phase acquire first")
    manifest = load_json(manifest_path)
    if manifest.get("validation_status") != "PASS":
        raise RuntimeError("Source manifest is not validated")
    expected_ids = [item["id"] for item in config["official_sources"]]
    rows = manifest.get("sources", [])
    if [row["id"] for row in rows] != expected_ids:
        raise RuntimeError("Acquired source ids differ from configuration")
    for row in rows:
        path = abs_path(row["path"])
        verify_hash(path, row["sha256"], row["id"])
        if path.stat().st_size != row["bytes"]:
            raise RuntimeError(f"Byte-size mismatch for {row['id']}")
    return manifest, rows


def validate_manual_evidence(
    config: dict[str, Any], source_manifest: dict[str, Any]
) -> tuple[
    dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]
]:
    path = abs_path(config["manual_evidence"]["path"])
    if not path.is_file():
        raise RuntimeError(f"Missing manual evidence transcription: {path}")
    evidence = load_json(path)
    if evidence.get("iteration") != "V10M":
        raise RuntimeError("Manual evidence iteration must be V10M")
    if evidence.get("status") != config["manual_evidence"]["required_status"]:
        raise RuntimeError("Manual evidence status is not finalized")
    expected_manifest_hash = sha256_file(abs_path(config["outputs"]["source_manifest"]))
    if evidence.get("source_manifest_sha256") != expected_manifest_hash:
        raise RuntimeError("Manual evidence is not tied to current source manifest")
    claims = evidence.get("claims", [])
    expected_claims = config["manual_evidence"]["required_claim_ids"]
    if [item["claim_id"] for item in claims] != expected_claims:
        raise RuntimeError("Manual claim ids/order differ from predeclaration")
    if len(claims) != config["expected"]["manual_claim_count"]:
        raise RuntimeError("Unexpected manual claim count")
    source_ids = {item["id"] for item in source_manifest["sources"]}
    for claim in claims:
        if claim["source_id"] not in source_ids:
            raise RuntimeError(f"Unknown source id in claim {claim['claim_id']}")
        if claim.get("evidence_class") not in {
            "DIRECT_OFFICIAL_STATEMENT",
            "OFFICIAL_MODEL_DESCRIPTION",
            "OFFICIAL_SCOPE_STATEMENT",
        }:
            raise RuntimeError(f"Unexpected evidence class for {claim['claim_id']}")
        if not claim.get("locator") or not claim.get("observation") or not claim.get("limitation"):
            raise RuntimeError(f"Incomplete manual claim {claim['claim_id']}")
    availability = evidence.get("availability", [])
    if [item["target_id"] for item in availability] != config["availability_targets"]:
        raise RuntimeError("Availability target ids/order differ from predeclaration")
    allowed_statuses = {
        "PUBLIC_REPORT_ONLY_EXACT_INPUT_NOT_LOCATED",
        "PARTIAL_PUBLIC_DRAWINGS_CHAIN_OR_REVISION_OPEN",
        "NOT_CREATED_BY_NIST_FOR_TOWERS",
    }
    for item in availability:
        if item.get("status") not in allowed_statuses:
            raise RuntimeError(f"Unexpected availability status for {item['target_id']}")
        if item.get("exact_solver_ready_file_located") is not False:
            raise RuntimeError(f"No V10M target may be marked solver-ready: {item['target_id']}")
        if not item.get("measure_that_would_change_status"):
            raise RuntimeError(f"Missing status-changing measure for {item['target_id']}")
    visual = evidence.get("pdf_visual_verification", [])
    if len(visual) != config["expected"]["visual_verification_count"]:
        raise RuntimeError("Unexpected PDF visual-verification count")
    for item in visual:
        if item.get("source_id") not in source_ids:
            raise RuntimeError(f"Unknown source id in visual verification: {item}")
        verify_hash(abs_path(item["render_path"]), item["render_sha256"], "pdf_visual_verification")
        if not isinstance(item.get("pdf_page_1_based"), int):
            raise RuntimeError("Visual verification page must be an integer")
    return evidence, claims, availability, visual


def availability_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "target_id": item["target_id"],
            "status": item["status"],
            "documented_as_existing": str(item["documented_as_existing"]).lower(),
            "public_exact_file_located": str(item["public_exact_file_located"]).lower(),
            "local_exact_file_located": str(item["local_exact_file_located"]).lower(),
            "exact_solver_ready_file_located": str(item["exact_solver_ready_file_located"]).lower(),
            "basis": item["basis"],
            "limitation": item["limitation"],
            "measure_that_would_change_status": item["measure_that_would_change_status"],
        }
        for item in items
    ]


def make_feasibility_plan(config: dict[str, Any], evidence: dict[str, Any]) -> str:
    deadline = evidence["deadline_assessment"]
    return f"""# WTC 1 — plan de faisabilité vers le 11 septembre 2026 (V10M)

Date de gel : 2 septembre 2026. Échéance visée : 11 septembre 2026. Fenêtre : {deadline['calendar_days_available']} jours calendaires.

## Verdict de faisabilité

- **Livrable réaliste d’ici le 11 septembre :** une chaîne intégrée et reproductible de modèles réduits, avec scénarios d’incertitude, contrôles dimensionnels, critères explicites d’initiation/propagation et visualisation 3D pilotée par les sorties calculées.
- **Non réaliste dans cette fenêtre :** reconstruire et valider indépendamment un jumeau numérique haute fidélité des 110 niveaux, un Boeing 767 détaillé, les incendies CFD, la thermo-mécanique non linéaire et la propagation explicite complète. Les fichiers de production NIST décrits dans les rapports n’ont pas été localisés comme entrées réutilisables, et le NIST indique lui-même que son modèle des tours s’arrêtait à l’initiation.
- **Nature du verdict final :** le harnais pourra dire ce que produit chaque jeu de paramètres et où se situe la frontière effondrement/non-effondrement. Il ne transformera pas une plage synthétique en probabilité de l’événement réel.

## Chemin critique daté

| Date cible | Itération / livrable | Critère de sortie |
|---|---|---|
| 2 septembre | V10M — provenance et disponibilité | Sources officielles hachées ; modèle exact disponible ou manquant explicitement qualifié. |
| 3 septembre | V10N — ressources et graphe de couplage | CPU/RAM/GPU/solveurs inventoriés ; interfaces et unités gelées. |
| 4–5 septembre | Impact et dommage initial | Enveloppes d’impact bornées ; conservation masse/énergie/impulsion vérifiée ; aucune rupture non calibrée promue. |
| 5–6 septembre | Incendie et transfert thermique | Histoires thermiques bornées et provenance séparée ; tests de sensibilité au feu et au SFRM. |
| 6–7 septembre | Réponse structurelle et initiation | Modèle réduit global + sous-modèles de connexions ; critères d’instabilité et de non-convergence audités. |
| 7–8 septembre | Propagation / arrêt | Modèle de propagation explicitement distinct ; cas d’arrêt, progressif et global ; bilan d’énergie. |
| 8–9 septembre | Ensemble d’incertitude | Graines, plages et résultats complets ; frontière effondrement/non-effondrement, sans fréquence réelle. |
| 9–10 septembre | 3D liée aux résultats | Géométrie et animation lisent les états validés ; Blender reste une visualisation. |
| 11 septembre | Gel reproductible | Harnais PASS, registre, hashes, rapport final, limites et inconnues. |

## Portes qui interdisent une conclusion forte

1. Les 22 exigences mécaniques de source restent ouvertes : aucun texte de rapport ne remplace les tableaux, connexions, révisions et conditions aux limites exactes.
2. Aucun jeu d’entrée de production SAP2000, TrueGrid/LS-DYNA, ANSYS ou FDS du WTC 1 n’a été localisé dans V10M.
3. Une conclusion « effondrement impossible » exige que **toute** la plage crédible échoue à initier et propager ; un seul scénario stable ne suffit pas.
4. Une conclusion « effondrement démontré » exige des résultats robustes aux incertitudes, aux maillages/réductions et aux lois de rupture ; une animation ressemblante ne suffit pas.

## Politique de calcul long

Avant tout calcul estimé à plusieurs heures, annoncer la durée, les ressources, les fichiers d’entrée, le critère d’arrêt et le livrable attendu. V10M ne lance aucun solveur.
"""


def make_report(
    source_manifest: dict[str, Any],
    claims: list[dict[str, Any]],
    availability: list[dict[str, Any]],
) -> str:
    claim_by_id = {item["claim_id"]: item for item in claims}
    not_located = sum(not item["exact_solver_ready_file_located"] for item in availability)
    return f"""# WTC 1 — V10M : provenance officielle et disponibilité des modèles

## Résultat

V10M valide {len(source_manifest['sources'])} sources officielles téléchargées et hachées. Les sources ferment les questions documentaires « Tower A = WTC 1 » et rôle général des Drawing Books 5/6, mais ne ferment **aucune** des 22 exigences mécaniques : {not_located} familles d’entrées ciblées restent sans fichier exact prêt pour solveur.

## 1. Faits directement observés ou transcrits

- {claim_by_id['TOWER_A_IS_WTC1']['observation']}
- {claim_by_id['BOOK5_ROLE']['observation']}
- {claim_by_id['BOOK6_ROLE']['observation']}
- {claim_by_id['ORIGINAL_DRAWINGS_RECEIVED']['observation']}
- {claim_by_id['ORIGINAL_1960S_IMPACT_CALCULATIONS_LOST']['observation']}

## 2. Résultats et descriptions du modèle officiel

- {claim_by_id['STRUCTURAL_DATABASES_EXISTED']['observation']}
- {claim_by_id['SAP2000_REFERENCE_MODELS_EXISTED']['observation']}
- {claim_by_id['LSDYNA_TRUEGRID_IMPACT_MODELS_EXISTED']['observation']}
- {claim_by_id['ANSYS_GLOBAL_MODELS_EXISTED']['observation']}
- {claim_by_id['FDS_FIRE_MODELS_EXISTED']['observation']}
- {claim_by_id['NIST_TOWER_SCOPE_STOPS_AT_INITIATION']['observation']}
- {claim_by_id['HISTORICAL_END_TO_END_RUNTIME']['observation']}

## 3. Affirmations provenant des archives locales

Les PDF et dessins locaux restent des copies candidates hachées. V10M compare trois rapports locaux en lecture seule, mais n’attribue pas aux dessins Archive.org une chaîne NIST, une révision as-built ou une identité de fichier officielle que les preuves ne démontrent pas.

## 4. Hypothèses propres au modèle

La cible du 11 septembre est un modèle intégré réduit avec plages de paramètres. Cette stratégie est une décision d’ingénierie du harnais, pas une affirmation du NIST ni une équivalence avec ses modèles de production.

## 5. Résultats dérivés

- Les descriptions publiées établissent que des bases, modèles et conversions ont existé ; elles ne fournissent pas les fichiers d’entrée exacts.
- La 3D peut être reliée à une chaîne de calcul réduite validée, mais ne devient pas une preuve mécanique autonome.
- Une reconstruction haute fidélité indépendante ne peut pas être honnêtement annoncée comme « complète » en neuf jours avec les entrées actuellement localisées.

## 6. Contradictions et informations manquantes

- Le dépôt NIST actuel annonce des simulations, mais V10M n’y localise pas les bases relationnelles, modèles SAP2000, commandes TrueGrid, decks LS-DYNA, modèles ANSYS ou entrées FDS événementielles exactes.
- L’expression rétrospective « end-to-end » doit être lue avec la FAQ des tours : le NIST indique avoir modélisé la séquence jusqu’à l’initiation, pas la propagation globale des tours.
- Les révisions exactes et l’autorité as-built des Drawing Books 5 et 6 restent ouvertes.

## Conclusion bornée

V10M améliore fortement la provenance, mais ne transforme aucune publication en donnée mécanique manquante. La prochaine étape est V10N : ressources locales, solveurs disponibles et graphe de couplage avec unités, interfaces, validations et coûts estimés.
"""


def finalize(config: dict[str, Any]) -> None:
    regression = regression_audit(config)
    source_manifest, source_rows = load_and_verify_acquired_sources(config)
    evidence, claims, availability, visual = validate_manual_evidence(config, source_manifest)
    rows = availability_rows(availability)
    write_csv(
        abs_path(config["outputs"]["availability_matrix"]),
        [
            "target_id", "status", "documented_as_existing", "public_exact_file_located",
            "local_exact_file_located", "exact_solver_ready_file_located", "basis",
            "limitation", "measure_that_would_change_status",
        ],
        rows,
    )
    evidence_audit = {
        "iteration": "V10M",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "source_manifest_sha256": sha256_file(abs_path(config["outputs"]["source_manifest"])),
        "manual_evidence_path": config["manual_evidence"]["path"],
        "manual_evidence_sha256": sha256_file(abs_path(config["manual_evidence"]["path"])),
        "claim_count": len(claims),
        "claims": claims,
        "availability_target_count": len(availability),
        "pdf_visual_verification_count": len(visual),
        "pdf_visual_verification": visual,
        "report_description_promoted_to_solver_input_count": 0,
        "mechanical_requirements_closed_count": 0,
        "physical_assignment_count": 0,
    }
    gate = {
        "iteration": "V10M",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "official_source_acquisition_gate": "PASS",
        "tower_a_to_wtc1_mapping_gate": "CLOSED_BY_OFFICIAL_SOURCE",
        "book5_general_role_gate": "CLOSED_BY_OFFICIAL_SOURCE",
        "book6_general_role_gate": "CLOSED_BY_OFFICIAL_SOURCE",
        "exact_revision_as_built_authority_gate": "OPEN",
        "wtc1_floor93_99_member_applicability_gate": "OPEN",
        "exact_production_model_input_gate": "OPEN_0_OF_10_TARGETS",
        "mechanical_requirement_closure_gate": "OPEN_0_OF_22",
        "structural_solver_readiness_gate": "CLOSED_22_BLOCKING_REQUIREMENTS",
        "end_to_end_high_fidelity_by_2026_09_11_gate": "NOT_FEASIBLE_WITH_CURRENT_INPUTS_AND_WINDOW",
        "integrated_reduced_order_chain_by_2026_09_11_gate": "FEASIBLE_IF_BOUNDED_AND_CONTINUOUSLY_VALIDATED",
        "physical_assignments": 0,
        "solver_runs": 0,
        "blender_runs": 0,
    }
    plan = make_feasibility_plan(config, evidence)
    report = make_report(source_manifest, claims, availability)
    write_json(abs_path(config["outputs"]["regression_audit"]), regression)
    write_json(abs_path(config["outputs"]["evidence_audit"]), evidence_audit)
    write_json(abs_path(config["outputs"]["source_gate"]), gate)
    write_text(abs_path(config["outputs"]["feasibility_plan"]), plan)
    write_text(abs_path(config["outputs"]["report"]), report)
    results = {
        "iteration": "V10M",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "dataset": config["dataset"],
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "source_manifest": {
            "path": config["outputs"]["source_manifest"],
            "sha256": sha256_file(abs_path(config["outputs"]["source_manifest"])),
            "source_count": len(source_rows),
            "aggregate_bytes": source_manifest["aggregate_bytes"],
        },
        "manual_evidence": {
            "path": config["manual_evidence"]["path"],
            "sha256": sha256_file(abs_path(config["manual_evidence"]["path"])),
            "claim_count": len(claims),
        },
        "availability_summary": {
            "target_count": len(availability),
            "exact_solver_ready_target_count": 0,
            "report_only_or_partial_target_count": len(availability),
        },
        "gates": gate,
        "deadline_assessment": evidence["deadline_assessment"],
        "epistemic_separation": {
            "official_statements": "Recorded as official statements with source locators.",
            "official_model_descriptions": "Recorded as descriptions, not as acquired solver inputs.",
            "local_archive_identity": "Kept separate; no official file-level identity inferred.",
            "model_hypotheses": "Reduced-order deadline strategy explicitly labeled as a harness decision.",
            "derived_results": "Feasibility conclusions are derived from source availability, scope and time.",
            "unknowns": "Exact production inputs, revision authority and 22 mechanical requirements remain open.",
        },
        "next_iteration": config["next_iteration"],
    }
    write_json(abs_path(config["outputs"]["results"]), results)
    artifact_keys = [
        "source_manifest", "acquisition_audit", "regression_audit", "evidence_audit",
        "availability_matrix", "source_gate", "feasibility_plan", "report", "results",
    ]
    artifacts = []
    for key in artifact_keys:
        path = abs_path(config["outputs"][key])
        if not path.is_file():
            raise RuntimeError(f"Missing final artifact {key}: {path}")
        artifacts.append({
            "role": key,
            "path": rel(path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        })
    for index, item in enumerate(visual, start=1):
        path = abs_path(item["render_path"])
        artifacts.append({
            "role": f"pdf_visual_evidence_{index}",
            "path": rel(path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        })
    offline = {
        "iteration": "V10M",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "source_files_reverified_count": len(source_rows),
        "regression_files_reverified_count": len(regression["regression_files"]),
        "protected_blender_master_unchanged": True,
        "source_archive_modified": False,
        "official_sources_directory_modified": False,
        "solver_run_count": 0,
        "blender_run_count": 0,
    }
    write_json(abs_path(config["outputs"]["offline_audit"]), offline)
    print(json.dumps({
        "iteration": "V10M",
        "phase": "finalize",
        "status": "PASS",
        "official_source_count": len(source_rows),
        "manual_claim_count": len(claims),
        "exact_solver_ready_target_count": 0,
        "mechanical_requirements_closed_count": 0,
        "next_iteration": config["next_iteration"]["id"],
    }, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V10M official provenance and model-availability audit")
    parser.add_argument("--phase", required=True, choices=("acquire", "finalize"))
    args = parser.parse_args()
    config = load_config()
    if args.phase == "acquire":
        acquire(config)
    else:
        finalize(config)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"V10M ERROR: {exc}", file=sys.stderr)
        raise
