from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10n_resource_and_coupling_audit.json"
SCRIPT_PATH = Path(__file__).resolve()


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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content.rstrip() + "\n")


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


def abs_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def verify_hash(item: dict[str, Any]) -> dict[str, Any]:
    path = abs_path(item["path"])
    role = item.get("role", item.get("id", "file"))
    if not path.is_file():
        raise RuntimeError(f"Missing {role}: {path}")
    actual = sha256_file(path)
    if actual.lower() != item["expected_sha256"].lower():
        raise RuntimeError(
            f"Hash mismatch for {role}: expected {item['expected_sha256']}, got {actual}"
        )
    return {
        "role": role,
        "path": rel(path),
        "sha256": actual,
        "bytes": path.stat().st_size,
        "status": "PASS",
    }


def load_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    if config.get("iteration") != "V10N":
        raise RuntimeError("Configuration iteration must be V10N")
    expected = config["expected"]
    counts = {
        "regression_file_count": len(config["regression_files"]),
        "protected_file_count": len(config["protected_files"]),
        "cached_anchor_count": len(config["cached_anchor_files"]),
        "candidate_executable_count": len(config["candidate_executables"]),
        "coupling_module_count": len(config["coupling_module_ids"]),
        "required_interface_count": len(config["required_interface_ids"]),
    }
    for key, actual in counts.items():
        if actual != expected[key]:
            raise RuntimeError(f"Unexpected {key}: {actual} != {expected[key]}")
    for key in ("candidate_executables", "cached_anchor_files"):
        ids = [item["id"] for item in config[key]]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"Duplicate id in {key}")
    for key in ("coupling_module_ids", "required_interface_ids"):
        values = config[key]
        if len(values) != len(set(values)):
            raise RuntimeError(f"Duplicate value in {key}")
    return config


def powershell_executable() -> str:
    executable = shutil.which("powershell.exe") or shutil.which("pwsh.exe") or shutil.which("pwsh")
    if not executable:
        raise RuntimeError("PowerShell executable not found for read-only Windows inventory")
    return executable


def run_powershell_json(script: str) -> Any:
    result = subprocess.run(
        [powershell_executable(), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=45,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Read-only PowerShell inventory failed: {result.stderr.strip()}")
    raw = result.stdout.lstrip("\ufeff").strip()
    if not raw:
        raise RuntimeError("Read-only PowerShell inventory returned no JSON")
    return json.loads(raw)


def hardware_inventory() -> dict[str, Any]:
    script = r"""
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$os = Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture,LastBootUpTime
$cs = Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory
$cpu = @(Get-CimInstance Win32_Processor | Select-Object Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed)
$gpu = @(Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion,VideoProcessor,PNPDeviceID)
$disk = @(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID,VolumeName,FileSystem,Size,FreeSpace)
[ordered]@{os=$os; computer=$cs; cpu=$cpu; gpu=$gpu; logical_disks=$disk} | ConvertTo-Json -Depth 6 -Compress
"""
    raw = run_powershell_json(script)
    computer = raw.get("computer") or {}
    total_memory = int(computer.get("TotalPhysicalMemory") or 0)
    disks = raw.get("logical_disks") or []
    if isinstance(disks, dict):
        disks = [disks]
    for disk in disks:
        disk["size_gib"] = round(int(disk.get("Size") or 0) / 2**30, 3)
        disk["free_gib"] = round(int(disk.get("FreeSpace") or 0) / 2**30, 3)
    gpus = raw.get("gpu") or []
    if isinstance(gpus, dict):
        gpus = [gpus]
    for gpu in gpus:
        adapter_ram = int(gpu.get("AdapterRAM") or 0)
        gpu["adapter_ram_gib_reported_by_wmi"] = round(adapter_ram / 2**30, 3) if adapter_ram else None
    cpus = raw.get("cpu") or []
    if isinstance(cpus, dict):
        cpus = [cpus]
    raw["cpu"] = cpus
    raw["gpu"] = gpus
    raw["logical_disks"] = disks
    raw["computer"]["total_physical_memory_gib"] = round(total_memory / 2**30, 3)
    raw["python_runtime"] = {
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
        "executable": Path(sys.executable).as_posix(),
        "architecture": platform.architecture()[0],
    }
    raw["inventory_method"] = "READ_ONLY_WINDOWS_CIM_AND_STANDARD_LIBRARY"
    return raw


def file_version_metadata(path: Path) -> dict[str, Any]:
    escaped = str(path).replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop'; "
        f"$v=(Get-Item -LiteralPath '{escaped}').VersionInfo; "
        "[ordered]@{FileVersion=$v.FileVersion;ProductVersion=$v.ProductVersion;"
        "CompanyName=$v.CompanyName;ProductName=$v.ProductName;OriginalFilename=$v.OriginalFilename} "
        "| ConvertTo-Json -Compress"
    )
    try:
        value = run_powershell_json(script)
        return {key: value.get(key) for key in (
            "FileVersion", "ProductVersion", "CompanyName", "ProductName", "OriginalFilename"
        )}
    except Exception as exc:
        return {"metadata_error": str(exc)}


def inspect_candidate_path(value: str) -> dict[str, Any]:
    path = abs_path(value)
    row: dict[str, Any] = {
        "declared_path": value,
        "resolved_path": path.resolve().as_posix(),
        "exists": path.exists(),
    }
    if not path.exists():
        row["object_kind"] = "MISSING"
        return row
    if path.is_dir():
        row.update({"object_kind": "DIRECTORY", "sha256": None, "bytes": None, "version_metadata": None})
        return row
    if not path.is_file():
        row["object_kind"] = "OTHER"
        return row
    row.update(
        {
            "object_kind": "FILE",
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "version_metadata": file_version_metadata(path),
        }
    )
    return row


def nvidia_query(path: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                str(path),
                "--query-gpu=index,name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=20,
        )
        rows = []
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                parts = [part.strip() for part in line.split(",")]
                if len(parts) >= 4:
                    rows.append(
                        {
                            "index": int(parts[0]),
                            "name": parts[1],
                            "memory_total_mib": int(parts[2]),
                            "driver_version": parts[3],
                        }
                    )
        return {
            "attempted": True,
            "read_only": True,
            "return_code": result.returncode,
            "gpus": rows,
            "stderr": result.stderr.strip() or None,
        }
    except Exception as exc:
        return {"attempted": True, "read_only": True, "error": str(exc), "gpus": []}


def solver_policy(solver_id: str) -> dict[str, Any]:
    policies = {
        "OPENRADIOSS_STARTER_RUNTIME": {
            "prior_qualification": "V8T_OFFICIAL_TWISBEAM_INSTALLATION_SMOKE_PASS",
            "allowed_credit": "EXECUTABLE_CHAIN_AND_BASIC_SHELL_REGRESSION_ONLY",
            "blocking_for_exact_nist_replay": True,
            "blocking_for_reduced_chain": False,
            "note": "OpenRadioss is not the NIST production LS-DYNA deck and WTC high-rate material, rupture, contact, mesh and energy gates remain open.",
        },
        "OPENRADIOSS_ENGINE_RUNTIME": {
            "prior_qualification": "V8T_OFFICIAL_TWISBEAM_INSTALLATION_SMOKE_PASS",
            "allowed_credit": "EXECUTABLE_CHAIN_AND_BASIC_SHELL_REGRESSION_ONLY",
            "blocking_for_exact_nist_replay": True,
            "blocking_for_reduced_chain": False,
            "note": "Presence does not qualify physical facade impact or aircraft breakup.",
        },
        "CALCULIX_CCX": {
            "prior_qualification": "PRESENCE_PREVIOUSLY_AUDITED_NO_WTC_FORMULATION_QUALIFIED",
            "allowed_credit": "FUTURE_COMPONENT_OR_QUASISTATIC_TESTS_AFTER_CASE_VALIDATION",
            "blocking_for_exact_nist_replay": True,
            "blocking_for_reduced_chain": False,
            "note": "No validated coupled high-rate or full thermomechanical WTC formulation is assigned.",
        },
        "BLENDER": {
            "prior_qualification": "V9O_V9P_LABELLED_STORYBOARD_AND_ANIMATIC_PIPELINE_PASS",
            "allowed_credit": "VISUALIZATION_ONLY_NO_MECHANICAL_FEEDBACK",
            "blocking_for_exact_nist_replay": False,
            "blocking_for_reduced_chain": False,
            "note": "Blender may display only states released by validation gates.",
        },
        "FREECAD_CMD": {
            "prior_qualification": "PRESENCE_PREVIOUSLY_AUDITED",
            "allowed_credit": "GEOMETRY_PREPOST_ONLY",
            "blocking_for_exact_nist_replay": False,
            "blocking_for_reduced_chain": False,
            "note": "Geometry tooling is not a physics qualification.",
        },
        "FDS": {
            "prior_qualification": "NO_LOCAL_WTC_EVENT_MODEL_QUALIFIED",
            "allowed_credit": "NONE_UNTIL_GENERIC_SMOKE_AND_EVENT_INPUT_VALIDATION",
            "blocking_for_exact_nist_replay": True,
            "blocking_for_reduced_chain": False,
            "note": "The exact NIST FDS event inputs and thermal interface histories are unavailable.",
        },
        "SMOKEVIEW": {
            "prior_qualification": "NOT_A_FIRE_SOLVER",
            "allowed_credit": "POSTPROCESSING_ONLY_IF_FDS_OUTPUT_EXISTS",
            "blocking_for_exact_nist_replay": False,
            "blocking_for_reduced_chain": False,
            "note": "Postprocessing presence cannot substitute for an FDS model.",
        },
        "LS_DYNA": {
            "prior_qualification": "NO_LOCAL_PRODUCTION_EXECUTABLE_OR_DECK_QUALIFIED",
            "allowed_credit": "NONE",
            "blocking_for_exact_nist_replay": True,
            "blocking_for_reduced_chain": False,
            "note": "Exact replay also requires the unavailable NIST TrueGrid and LS-DYNA inputs.",
        },
        "ANSYS": {
            "prior_qualification": "NO_LOCAL_PRODUCTION_INPUT_OR_EXECUTABLE_QUALIFIED",
            "allowed_credit": "NONE",
            "blocking_for_exact_nist_replay": True,
            "blocking_for_reduced_chain": False,
            "note": "Exact replay also requires the unavailable translated NIST ANSYS inputs and interfaces.",
        },
        "NVIDIA_SMI": {
            "prior_qualification": "READ_ONLY_INVENTORY_UTILITY",
            "allowed_credit": "GPU_IDENTIFICATION_ONLY",
            "blocking_for_exact_nist_replay": False,
            "blocking_for_reduced_chain": False,
            "note": "No GPU computation is performed in V10N.",
        },
    }
    return policies[solver_id]


def executable_inventory(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    rows: list[dict[str, Any]] = []
    nvidia_result: dict[str, Any] | None = None
    for item in config["candidate_executables"]:
        candidates = [inspect_candidate_path(value) for value in item["candidate_paths"]]
        existing = [candidate for candidate in candidates if candidate["exists"]]
        selected = existing[0] if existing else candidates[0]
        metadata = selected.get("version_metadata") or {}
        policy = solver_policy(item["id"])
        row = {
            "id": item["id"],
            "role": item["role"],
            "presence": "PRESENT" if existing else "NOT_FOUND_AT_DECLARED_PATHS",
            "matching_candidate_count": len(existing),
            "resolved_path": selected["resolved_path"] if existing else "",
            "object_kind": selected.get("object_kind", "MISSING"),
            "sha256": selected.get("sha256") or "",
            "bytes": selected.get("bytes") if selected.get("bytes") is not None else "",
            "file_version": metadata.get("FileVersion") or "",
            "product_version": metadata.get("ProductVersion") or "",
            "prior_qualification": policy["prior_qualification"],
            "allowed_credit": policy["allowed_credit"],
            "blocking_for_exact_nist_replay": policy["blocking_for_exact_nist_replay"],
            "blocking_for_reduced_chain": policy["blocking_for_reduced_chain"],
            "note": policy["note"],
            "candidate_results_json": json.dumps(candidates, ensure_ascii=False, separators=(",", ":")),
        }
        rows.append(row)
        if item["id"] == "NVIDIA_SMI" and existing and selected.get("object_kind") == "FILE":
            nvidia_result = nvidia_query(Path(selected["resolved_path"]))
    return rows, nvidia_result


def workspace_inventory(maximum_count: int) -> dict[str, Any]:
    extension_counts: Counter[str] = Counter()
    solver_deck_extensions = {".rad", ".key", ".k", ".inp", ".fds", ".smv", ".cdb", ".dat"}
    detected_decks: list[str] = []
    total = 0
    capped = False
    skip_names = {".git", "__pycache__", ".mypy_cache", ".pytest_cache"}
    for current, directories, files in os.walk(ROOT, followlinks=False):
        directories[:] = [name for name in directories if name not in skip_names]
        for filename in files:
            total += 1
            if total > maximum_count:
                capped = True
                break
            path = Path(current) / filename
            suffix = path.suffix.lower() or "[no_extension]"
            extension_counts[suffix] += 1
            if suffix in solver_deck_extensions and len(detected_decks) < 200:
                detected_decks.append(rel(path))
        if capped:
            break
    return {
        "method": "FILENAME_ONLY_OS_WALK_NO_FILE_CONTENT_READ",
        "root": ROOT.as_posix(),
        "file_count": min(total, maximum_count),
        "maximum_file_count": maximum_count,
        "inventory_capped": capped,
        "extension_counts": dict(sorted(extension_counts.items(), key=lambda item: (-item[1], item[0]))),
        "solver_deck_like_file_count_within_sample": len(detected_decks),
        "solver_deck_like_paths_max_200": sorted(detected_decks),
        "warning": "Filename extensions indicate possible tool inputs only; they do not establish provenance, completeness, validity or physical applicability.",
    }


def module_definitions() -> list[dict[str, Any]]:
    return [
        {
            "id": "IMPACT_KINEMATICS",
            "purpose": "Freeze aircraft mass, velocity, attitude, trajectory and contact-time envelopes.",
            "implementation": "V8S cached reduced kinematic specification",
            "status": "READY_FOR_REPLAY_AS_KINEMATIC_ENVELOPE_ONLY",
            "solver_or_method": "deterministic SI-unit transformations and geometry checks",
            "inputs": ["source-qualified aircraft mass/velocity/attitude", "tower orientation", "contact reference"],
            "outputs": ["impact_kinematics_v1", "contact_time_s", "kinetic_energy_J", "trajectory_frame"],
            "canonical_units": ["kg", "m", "s", "m/s", "rad", "J"],
            "uncertainties": ["mass", "speed", "yaw", "pitch", "roll", "impact point"],
            "validation_gate": "V8S input hashes and geometric time-scale checks pass; no damage credit.",
            "stop_condition": "Missing provenance, non-SI conversion record, or attempt to infer member damage.",
            "physical_credit": "KINEMATICS_ONLY_NO_FORCE_IMPULSE_DAMAGE_OR_BREAKUP",
            "cached_anchors": ["V8S_IMPACT_KINEMATICS"],
        },
        {
            "id": "IMPACT_DAMAGE_STATE",
            "purpose": "Transform impact conditions into member damage, openings, debris and fuel distributions.",
            "implementation": "schema only; V9M closes the current physical solver branch as unqualified",
            "status": "BLOCKED_FOR_PHYSICAL_PREDICTION_SCHEMA_CAN_BE_IMPLEMENTED",
            "solver_or_method": "future qualified explicit dynamics; OpenRadioss is only installation-smoke qualified",
            "inputs": ["impact_kinematics_v1", "as-built impact-zone mesh", "aircraft and tower high-rate material/joint cards"],
            "outputs": ["impact_damage_state_v1", "opening_map", "debris_distribution", "fuel_distribution"],
            "canonical_units": ["m", "kg", "s", "N", "Pa", "J"],
            "uncertainties": ["fracture surfaces", "regularization length", "mesh", "contact", "projectile breakup", "joint failure"],
            "validation_gate": "All V9M primary-evidence and convergence triggers plus energy/mass balance.",
            "stop_condition": "Any unqualified erosion, mesh dependence, missing CF6-80A2 card, or absent as-built mesh.",
            "physical_credit": "NONE_CURRENTLY",
            "cached_anchors": ["V8T_OPENRADIOSS_SMOKE", "V9M_IMPACT_BRANCH_CLOSURE"],
        },
        {
            "id": "FIRE_GAS_PHASE",
            "purpose": "Compute or bracket gas temperature and heat-flux histories after impact.",
            "implementation": "schema plus bounded surrogate inputs; exact NIST FDS event inputs unavailable",
            "status": "REDUCED_SURROGATE_ONLY_NOT_EVENT_VALIDATED",
            "solver_or_method": "future FDS or explicitly labelled reduced fire envelope",
            "inputs": ["opening_map", "fuel_distribution", "combustibles", "ventilation", "sprinkler and fireproofing state"],
            "outputs": ["fire_gas_history_v1", "gas_temperature_K", "incident_heat_flux_W_m2"],
            "canonical_units": ["m", "s", "K", "W/m2", "kg", "kg/s"],
            "uncertainties": ["fuel placement", "ventilation", "fuel load", "burn rate", "compartment connectivity"],
            "validation_gate": "Mass/energy conservation, mesh/time sensitivity and comparison to bounded observations or published official-model envelopes.",
            "stop_condition": "Damage/fire interface lacks provenance or a surrogate is mislabeled as an FDS event reconstruction.",
            "physical_credit": "NONE_AS_EVENT_RECONSTRUCTION",
            "cached_anchors": [],
        },
        {
            "id": "THERMAL_SOLIDS",
            "purpose": "Map gas exposure through protection and conduction to member temperature histories.",
            "implementation": "V8E synthetic fields preserve official extrema but are not member-resolved NIST temperatures",
            "status": "CACHED_SYNTHETIC_FIELDS_READY_FOR_SOFTWARE_CONTROL_ONLY",
            "solver_or_method": "reduced thermal map; future validated solid heat-transfer solver",
            "inputs": ["fire_gas_history_v1", "member geometry", "insulation thickness/damage", "thermal properties"],
            "outputs": ["thermal_member_history_v1", "member_temperature_K_by_time"],
            "canonical_units": ["m", "s", "K", "W/m2", "W/(m K)", "J/(kg K)"],
            "uncertainties": ["SFRM loss", "thermal properties", "section factors", "boundary convection/radiation"],
            "validation_gate": "Temperature extrema, conservation, time-step convergence and member/source mapping.",
            "stop_condition": "Synthetic spatial field is treated as measured or as an event probability.",
            "physical_credit": "SENSITIVITY_ONLY",
            "cached_anchors": ["V8E_THERMAL_FIELDS"],
        },
        {
            "id": "COLD_GRAVITY_REDISTRIBUTION",
            "purpose": "Establish the post-impact gravity state before heating.",
            "implementation": "V8H/V8J/V8L/V8R reduced graph and capacity diagnostics",
            "status": "DIAGNOSTIC_AVAILABLE_SOURCE_GATE_FAILED",
            "solver_or_method": "reduced nonlinear spring/network calculations",
            "inputs": ["impact_damage_state_v1", "gravity loads", "topology", "member/connection laws", "boundary conditions"],
            "outputs": ["cold_structural_state_v1", "residual_loads_N", "displacements_m", "failed_component_flags"],
            "canonical_units": ["m", "N", "Pa", "rad"],
            "uncertainties": ["Book 5 sections", "Book 6 connections", "office/perimeter transfer", "boundaries", "damage state"],
            "validation_gate": "All 22 V10A source requirements plus equilibrium and displacement compatibility.",
            "stop_condition": "Disconnected loaded component, failed equilibrium, or proxy capacity presented as as-built.",
            "physical_credit": "NONE_CURRENTLY; REDUCED DIAGNOSTIC ONLY",
            "cached_anchors": ["V8H_MECHANICAL_TRANSFER", "V8J_COLD_GATE", "V8L_MULTISTORY_COLD", "V8R_NETWORK_BOUNDS", "V10A_SOLVER_NEUTRAL_SCHEMA"],
        },
        {
            "id": "THERMOMECHANICAL_INITIATION",
            "purpose": "Combine prestress and temperature-dependent response to test initiation or survival.",
            "implementation": "interface schema only",
            "status": "BLOCKED_PENDING_COLD_AND_THERMAL_PHYSICAL_GATES",
            "solver_or_method": "future coupled or sequential structural solver with validated material/connection laws",
            "inputs": ["cold_structural_state_v1", "thermal_member_history_v1", "temperature-dependent material and connection laws"],
            "outputs": ["initiation_state_v1", "instability_time_s_or_null", "failure_sequence", "survival_margin"],
            "canonical_units": ["m", "s", "K", "N", "Pa", "rad", "J"],
            "uncertainties": ["creep", "strength/stiffness reduction", "connection response", "initial imperfections", "load path"],
            "validation_gate": "Cold equilibrium, thermal mapping, numerical convergence and component benchmarks all pass.",
            "stop_condition": "Any upstream physical gate is closed or instability depends on an unbounded proxy.",
            "physical_credit": "NONE_CURRENTLY",
            "cached_anchors": [],
        },
        {
            "id": "PROPAGATION_OR_ARREST",
            "purpose": "Test whether an initiated local descent propagates, arrests, or remains indeterminate.",
            "implementation": "not yet implemented; deliberately separate from initiation",
            "status": "SCHEMA_ONLY_SEPARATE_MODEL_REQUIRED",
            "solver_or_method": "future energy-momentum/member-removal bracket with optional explicit verification",
            "inputs": ["initiation_state_v1", "upper/lower mass distribution", "story capacities", "dissipation and debris interaction laws"],
            "outputs": ["propagation_outcome_v1", "outcome_label", "arrest_story_or_null", "energy_momentum_ledger"],
            "canonical_units": ["kg", "m", "s", "N", "J", "kg m/s"],
            "uncertainties": ["participating mass", "impact velocity", "dynamic amplification", "connection fracture", "debris compaction"],
            "validation_gate": "Energy and momentum close, time-step/element sensitivity passes, and arrest control cases reproduce.",
            "stop_condition": "Initiation is assumed to imply global propagation, or conservation residual exceeds the declared tolerance.",
            "physical_credit": "NONE_CURRENTLY",
            "cached_anchors": [],
        },
        {
            "id": "UNCERTAINTY_ENSEMBLE",
            "purpose": "Run declared parameter envelopes and preserve outcome classifications without converting them to real-event probabilities.",
            "implementation": "orchestration schema ready for V10O",
            "status": "READY_FOR_SYNTHETIC_SOFTWARE_CONTROLS_ONLY",
            "solver_or_method": "deterministic case grid and seeded sampling",
            "inputs": ["module configurations", "parameter provenance classes", "validation flags", "outcome records"],
            "outputs": ["ensemble_manifest_v1", "case_results", "sensitivity_metrics", "epistemic_class"],
            "canonical_units": ["module-native SI units", "dimensionless normalized sensitivity"],
            "uncertainties": ["aleatory variables only where justified", "epistemic intervals kept separate"],
            "validation_gate": "Fixed seeds, complete manifests, unit checks, replay equality and explicit probability prohibition.",
            "stop_condition": "Synthetic fraction is reported as probability of the historical event.",
            "physical_credit": "ORCHESTRATION_ONLY",
            "cached_anchors": ["V8E_THERMAL_FIELDS"],
        },
        {
            "id": "BLENDER_VISUALIZATION",
            "purpose": "Render only released states and uncertainty labels for human inspection.",
            "implementation": "V9O/V9P labelled storyboard/animatic pipeline",
            "status": "READY_FOR_VALIDATED_STATE_VISUALIZATION_ONLY",
            "solver_or_method": "Blender; no rigid-body, fracture, fluid or structural feedback credit",
            "inputs": ["released state records", "time mapping", "camera/storyboard", "mandatory evidence labels"],
            "outputs": ["blend derivative", "frames/video", "visual audit manifest"],
            "canonical_units": ["m", "s", "rad"],
            "uncertainties": ["displayed as separate scenarios or envelopes, never hidden interpolation"],
            "validation_gate": "Source-state hashes, transform reproduction, mandatory banner and no post-contact invention.",
            "stop_condition": "A blocked state is animated as prediction or Blender output feeds a mechanical result.",
            "physical_credit": "VISUALIZATION_ONLY",
            "cached_anchors": ["V9P_ANIMATIC"],
        },
    ]


def interface_definitions() -> list[dict[str, Any]]:
    return [
        {
            "id": "I01_KINEMATICS_TO_DAMAGE",
            "producer": "IMPACT_KINEMATICS",
            "consumer": "IMPACT_DAMAGE_STATE",
            "schema": "impact_kinematics_v1",
            "required_fields": "scenario_id,mass_kg,velocity_vector_m_s,attitude_rad,trajectory_frame,contact_time_s,provenance",
            "spatial_mapping": "aircraft frame to tower impact coordinate frame",
            "temporal_mapping": "absolute event time; contact reference t=0 s",
            "uncertainty_transfer": "preserve mass/speed/attitude intervals and source class without averaging",
            "status": "SCHEMA_FREEZABLE_PHYSICAL_DAMAGE_BLOCKED",
            "adapter_ready_for_v10o": True,
            "physical_ready": False,
            "validation_gate": "SI units, transform round trip, source hashes and V9M physical triggers",
            "stop_condition": "adapter may serialize the envelope but must emit PHYSICS_BLOCKED instead of damage",
        },
        {
            "id": "I02_DAMAGE_TO_FIRE",
            "producer": "IMPACT_DAMAGE_STATE",
            "consumer": "FIRE_GAS_PHASE",
            "schema": "impact_damage_state_v1",
            "required_fields": "member_states,opening_polygons_m,debris_occupancy,fuel_mass_kg_and_distribution,damage_uncertainty,provenance",
            "spatial_mapping": "structural member/opening IDs to fire mesh compartments/cells",
            "temporal_mapping": "post-impact state at declared handoff time",
            "uncertainty_transfer": "retain correlated damage/opening/fuel scenarios",
            "status": "SCHEMA_FREEZABLE_EVENT_INPUT_BLOCKED",
            "adapter_ready_for_v10o": True,
            "physical_ready": False,
            "validation_gate": "mass conservation, geometry containment and physical impact qualification",
            "stop_condition": "no exact damage state may be fabricated from a kinematic envelope",
        },
        {
            "id": "I03_DAMAGE_TO_COLD_STRUCTURE",
            "producer": "IMPACT_DAMAGE_STATE",
            "consumer": "COLD_GRAVITY_REDISTRIBUTION",
            "schema": "impact_damage_state_v1",
            "required_fields": "member_id,state,remaining_section_fraction,connection_state,residual_loads,provenance",
            "spatial_mapping": "damage IDs must resolve one-to-one to the structural catalogue",
            "temporal_mapping": "equilibrated cold state before thermal continuation",
            "uncertainty_transfer": "damage alternatives stay separate cases",
            "status": "SCHEMA_FREEZABLE_PHYSICAL_COLD_GATE_BLOCKED",
            "adapter_ready_for_v10o": True,
            "physical_ready": False,
            "validation_gate": "identifier coverage, equilibrium, displacement compatibility and 22/22 source closure",
            "stop_condition": "unresolved member IDs or disconnected loaded components",
        },
        {
            "id": "I04_FIRE_TO_THERMAL_SOLIDS",
            "producer": "FIRE_GAS_PHASE",
            "consumer": "THERMAL_SOLIDS",
            "schema": "fire_gas_history_v1",
            "required_fields": "cell_or_surface_id,time_s,gas_temperature_K,incident_heat_flux_W_m2,convection_coefficient_W_m2K,provenance",
            "spatial_mapping": "conservative cell/surface to member-face exposure map",
            "temporal_mapping": "monotone time interpolation with no extrapolation beyond declared bounds",
            "uncertainty_transfer": "fire scenario ID and correlated time history preserved",
            "status": "SCHEMA_FREEZABLE_SURROGATE_CONTROL_AVAILABLE",
            "adapter_ready_for_v10o": True,
            "physical_ready": False,
            "validation_gate": "unit/range checks, conservative mapping and heat-flux/time integral audit",
            "stop_condition": "temperature-only surrogate may not be relabeled as measured heat flux",
        },
        {
            "id": "I05_THERMAL_TO_INITIATION",
            "producer": "THERMAL_SOLIDS",
            "consumer": "THERMOMECHANICAL_INITIATION",
            "schema": "thermal_member_history_v1",
            "required_fields": "member_id,time_s,temperature_K,section_temperature_distribution,thermal_model_class,provenance",
            "spatial_mapping": "every thermal member ID resolves to one structural element/section",
            "temporal_mapping": "shared monotone time grid or declared energy-preserving resampling",
            "uncertainty_transfer": "SFRM/material/fire scenario IDs retained",
            "status": "SCHEMA_FREEZABLE_PHYSICAL_INITIATION_BLOCKED",
            "adapter_ready_for_v10o": True,
            "physical_ready": False,
            "validation_gate": "ID coverage, Kelvin bounds, time-grid audit and temperature-dependent law provenance",
            "stop_condition": "missing member map or use of synthetic fields as exact member temperatures",
        },
        {
            "id": "I06_COLD_STATE_TO_INITIATION",
            "producer": "COLD_GRAVITY_REDISTRIBUTION",
            "consumer": "THERMOMECHANICAL_INITIATION",
            "schema": "cold_structural_state_v1",
            "required_fields": "node_displacements_m,element_forces_N,connection_state,boundary_state,equilibrium_residual_N,provenance",
            "spatial_mapping": "identical structural IDs and coordinate frame",
            "temporal_mapping": "cold equilibrium is initial state at thermal time zero",
            "uncertainty_transfer": "topology/connection/boundary alternatives retained",
            "status": "SCHEMA_FREEZABLE_COLD_GATE_BLOCKED",
            "adapter_ready_for_v10o": True,
            "physical_ready": False,
            "validation_gate": "equilibrium tolerance, displacement compatibility and 22/22 source closure",
            "stop_condition": "failed or indeterminate cold gate cannot seed a physical thermal run",
        },
        {
            "id": "I07_INITIATION_TO_PROPAGATION",
            "producer": "THERMOMECHANICAL_INITIATION",
            "consumer": "PROPAGATION_OR_ARREST",
            "schema": "initiation_state_v1",
            "required_fields": "time_s,failed_members,displacements_m,velocities_m_s,participating_mass_kg,energy_J,boundary_state,provenance",
            "spatial_mapping": "full state projection onto the separately validated propagation model",
            "temporal_mapping": "handoff at a declared instability event with conserved state",
            "uncertainty_transfer": "initiation alternatives remain separate propagation cases",
            "status": "SCHEMA_FREEZABLE_BOTH_PHYSICS_MODULES_BLOCKED",
            "adapter_ready_for_v10o": True,
            "physical_ready": False,
            "validation_gate": "mass/momentum/energy ledger and state-projection error tolerances",
            "stop_condition": "initiation alone must never be reported as proof of global propagation",
        },
        {
            "id": "I08_PROPAGATION_TO_ENSEMBLE",
            "producer": "PROPAGATION_OR_ARREST",
            "consumer": "UNCERTAINTY_ENSEMBLE",
            "schema": "propagation_outcome_v1",
            "required_fields": "case_id,outcome_label,arrest_story_or_null,conservation_residuals,validation_flags,parameter_provenance",
            "spatial_mapping": "story/member outcome IDs retained without aggregation loss",
            "temporal_mapping": "complete history or declared terminal event",
            "uncertainty_transfer": "epistemic and aleatory variables stored in separate fields",
            "status": "SCHEMA_FREEZABLE_SOFTWARE_CONTROL_READY",
            "adapter_ready_for_v10o": True,
            "physical_ready": False,
            "validation_gate": "manifest completeness, deterministic replay and probability-language audit",
            "stop_condition": "fraction of synthetic cases must not be called real-event probability",
        },
        {
            "id": "I09_ALL_VALIDATED_STATES_TO_BLENDER",
            "producer": "VALIDATION_RELEASE_BUS",
            "consumer": "BLENDER_VISUALIZATION",
            "schema": "visualization_state_v1",
            "required_fields": "source_module,state_id,time_s,object_transforms,display_class,validation_status,uncertainty_label,source_hashes",
            "spatial_mapping": "solver/reduced coordinates to Blender coordinates with reversible transform",
            "temporal_mapping": "explicit time/frame mapping; blocked intervals may use cards only",
            "uncertainty_transfer": "show separate envelopes/scenarios and permanent labels",
            "status": "READY_FOR_RELEASED_STATES_ONLY",
            "adapter_ready_for_v10o": True,
            "physical_ready": False,
            "validation_gate": "hashes, transform round trip, mandatory banner, no physics feedback",
            "stop_condition": "blocked state or post-contact invention must freeze or render as a data card",
        },
    ]


def compute_budget(hardware: dict[str, Any], solver_rows: list[dict[str, Any]]) -> dict[str, Any]:
    logical = sum(int(cpu.get("NumberOfLogicalProcessors") or 0) for cpu in hardware.get("cpu", []))
    physical = sum(int(cpu.get("NumberOfCores") or 0) for cpu in hardware.get("cpu", []))
    ram_gib = float((hardware.get("computer") or {}).get("total_physical_memory_gib") or 0.0)
    fixed_disks = hardware.get("logical_disks") or []
    workspace_drive = ROOT.drive.upper()
    workspace_disk = next(
        (disk for disk in fixed_disks if str(disk.get("DeviceID", "")).upper() == workspace_drive),
        None,
    )
    present = {row["id"]: row["presence"] == "PRESENT" for row in solver_rows}
    return {
        "iteration": "V10N",
        "generated_at_utc": utc_now(),
        "host_summary": {
            "physical_core_count": physical,
            "logical_processor_count": logical,
            "ram_gib": ram_gib,
            "workspace_drive": workspace_drive,
            "workspace_drive_free_gib": workspace_disk.get("free_gib") if workspace_disk else None,
            "openradioss_present": present.get("OPENRADIOSS_STARTER_RUNTIME", False) and present.get("OPENRADIOSS_ENGINE_RUNTIME", False),
            "calculix_present": present.get("CALCULIX_CCX", False),
            "fds_present": present.get("FDS", False),
            "blender_present": present.get("BLENDER", False),
        },
        "runtime_classes": [
            {
                "class": "SHORT",
                "wall_clock_bound": "<=15 minutes",
                "authorized_next_use": "V10O schema adapters, unit checks and cached no-propagation control",
                "recommended_cpu_threads": min(max(logical, 1), 4),
                "recommended_ram_gib_max": min(max(round(ram_gib * 0.125, 1), 1), 4) if ram_gib else 4,
                "gpu": "not required",
                "announcement_required": False,
            },
            {
                "class": "MEDIUM",
                "wall_clock_bound": ">15 minutes and <=2 hours",
                "authorized_next_use": "only after V10O controls pass; bounded reduced ensembles",
                "recommended_cpu_threads": min(max(logical // 2, 1), 16),
                "recommended_ram_gib_max": round(ram_gib * 0.5, 1) if ram_gib else None,
                "gpu": "optional only for a separately validated renderer; not needed for reduced calculations",
                "announcement_required": False,
            },
            {
                "class": "LONG",
                "wall_clock_bound": ">2 hours or otherwise described as several hours",
                "authorized_next_use": "not authorized by V10N; estimate resources and deliverable to Jeremy before launch",
                "recommended_cpu_threads": "case-specific",
                "recommended_ram_gib_max": "case-specific with safety reserve",
                "gpu": "case-specific",
                "announcement_required": True,
            },
        ],
        "excluded_from_current_schedule": [
            {
                "job": "full high-rate aircraft/tower impact",
                "reason": "physical inputs and convergence gates are open; executable presence is insufficient",
            },
            {
                "job": "event-scale FDS plus member-resolved heat transfer",
                "reason": "exact damage, fuel, furnishings, ventilation and interface inputs are unavailable",
            },
            {
                "job": "full-building thermomechanical collapse propagation",
                "reason": "22 mechanical requirements and both initiation/propagation validation chains are open",
            },
        ],
        "deadline_policy": "Use cached verified calculations and short adapters first. A Sep 11 package can be a reproducible reduced-order uncertainty chain and labelled 3D, not a validated full-fidelity historical reconstruction.",
    }


def make_report(
    config: dict[str, Any],
    resource_inventory: dict[str, Any],
    solver_rows: list[dict[str, Any]],
    modules: list[dict[str, Any]],
    interfaces: list[dict[str, Any]],
    budget: dict[str, Any],
) -> str:
    host = budget["host_summary"]
    present = [row["id"] for row in solver_rows if row["presence"] == "PRESENT"]
    absent = [row["id"] for row in solver_rows if row["presence"] != "PRESENT"]
    lines = [
        "# WTC 1 — V10N : ressources locales et gel du couplage",
        "",
        f"Généré le {utc_now()}. Cette itération n’exécute aucun solveur, aucun calcul GPU et aucun lancement Blender.",
        "",
        "## Résultat principal",
        "",
        "Le poste permet de poursuivre immédiatement la chaîne réduite : les adaptateurs, contrôles d’unités, relectures de sorties en cache et tests d’orchestration sont compatibles avec des exécutions courtes. En revanche, la présence d’un exécutable ne ferme aucun verrou physique. Le modèle d’impact WTC, les entrées FDS de l’événement, les entrées thermomécaniques et les 22 exigences mécaniques restent indisponibles ou non qualifiés.",
        "",
        "La chaîne est désormais découpée en neuf modules et neuf interfaces explicites. V10O peut implémenter ces contrats et produire un premier contrôle intégré « aucune propagation », mais ce contrôle vérifiera le logiciel et les transferts de données — pas la réalité historique.",
        "",
        "## Ressources observées",
        "",
        f"- Processeurs physiques/logiques : {host['physical_core_count']} cœurs / {host['logical_processor_count']} fils.",
        f"- Mémoire physique : {host['ram_gib']} Gio.",
        f"- Espace libre sur le volume de travail {host['workspace_drive']} : {host['workspace_drive_free_gib']} Gio.",
        f"- Candidats présents : {', '.join(present) if present else 'aucun'}.",
        f"- Candidats absents des chemins pré-déclarés : {', '.join(absent) if absent else 'aucun'}.",
        "",
        "Ces observations proviennent de l’inventaire Windows, des métadonnées de fichiers et des empreintes SHA-256. Les exécutables de calcul n’ont pas été lancés. Seul l’outil de diagnostic NVIDIA peut avoir été interrogé en lecture seule.",
        "",
        "## Qualification réelle des outils",
        "",
        "| Outil | Présence | Crédit autorisé | Limite déterminante |",
        "|---|---|---|---|",
    ]
    for row in solver_rows:
        lines.append(
            f"| {row['id']} | {row['presence']} | {row['allowed_credit']} | {row['note']} |"
        )
    lines.extend(
        [
            "",
            "## Chaîne gelée",
            "",
            "| Module | État | Crédit physique actuel |",
            "|---|---|---|",
        ]
    )
    for module in modules:
        lines.append(f"| {module['id']} | {module['status']} | {module['physical_credit']} |")
    lines.extend(
        [
            "",
            "| Interface | Transfert | État | Implémentable en V10O |",
            "|---|---|---|---|",
        ]
    )
    for interface in interfaces:
        lines.append(
            f"| {interface['id']} | {interface['producer']} → {interface['consumer']} | {interface['status']} | {'oui' if interface['adapter_ready_for_v10o'] else 'non'} |"
        )
    lines.extend(
        [
            "",
            "## Séparation des preuves",
            "",
            "1. **Faits observés ici** : présence, taille, version déclarée et empreinte des fichiers exécutables ; caractéristiques CIM du poste ; empreintes inchangées des résultats en cache.",
            "2. **Résultats de modèles officiels** : ils restent des entrées dépendantes lorsqu’ils sont repris par les anciens sous-modèles ; V10N ne les rend pas indépendants.",
            "3. **Affirmations d’archives** : aucune nouvelle archive source n’est lue ou promue dans V10N.",
            "4. **Hypothèses du modèle** : les champs thermiques synthétiques, topologies reconstruites, lois proxy et futurs scénarios d’interface restent explicitement hypothétiques.",
            "5. **Résultats dérivés** : disponibilité de la chaîne logicielle courte, graphe de couplage et budget de calcul.",
            "6. **Contradictions et inconnues** : modèle de dommage physique non qualifié, entrées événementielles feu/thermique absentes, 0/22 exigences mécaniques fermées, propagation non implémentée.",
            "",
            "## Décision",
            "",
            "- **V10O autorisée** : adaptateurs validés par schéma, contrôles d’unités/provenance, relecture des cas en cache et contrôle intégré sans propagation, pour une durée visée inférieure à 15 minutes.",
            "- **Conclusion physique non autorisée** : V10O ne pourra pas conclure que le WTC1 devait s’effondrer ou ne pouvait pas s’effondrer.",
            "- **Calcul long non autorisé sans annonce préalable** : aucun calcul de plusieurs heures ne sera lancé sans estimation, ressources et livrable attendus.",
            "- **3D** : Blender reste en sortie uniquement ; aucune animation ne peut créer ou valider une dynamique absente des modules amont.",
            "",
            "## Prochaine étape",
            "",
            config["next_iteration"]["objective"],
        ]
    )
    return "\n".join(lines)


def main() -> int:
    started = time.perf_counter()
    config = load_config()

    regression_rows = [verify_hash(item) for item in config["regression_files"]]
    protected_rows = [verify_hash(item) for item in config["protected_files"]]
    cached_rows = [verify_hash(item) for item in config["cached_anchor_files"]]

    regression = {
        "iteration": "V10N",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "regression_file_count": len(regression_rows),
        "protected_file_count": len(protected_rows),
        "regression_files": regression_rows,
        "protected_files": protected_rows,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_sources_directory_modified": False,
        "blender_master_unchanged": True,
    }
    cached_audit = {
        "iteration": "V10N",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "cached_anchor_count": len(cached_rows),
        "cached_anchors": cached_rows,
        "reuse_policy": "Hashes establish identity only. Each anchor retains its original scope, failure gates and epistemic limits.",
    }

    hardware = hardware_inventory()
    solver_rows, nvidia_result = executable_inventory(config)
    workspace = workspace_inventory(config["resource_policy"]["maximum_workspace_inventory_file_count"])
    resource_inventory = {
        "iteration": "V10N",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "inventory_scope": "read-only host, declared candidate paths and workspace filenames",
        "hardware": hardware,
        "nvidia_smi_query": nvidia_result,
        "workspace_filename_inventory": workspace,
        "policy_checks": {
            "software_installed_or_modified": False,
            "solver_executed": False,
            "solver_version_execution_probe_used": False,
            "gpu_compute_executed": False,
            "blender_executed": False,
            "source_archive_read": False,
            "source_archive_modified": False,
            "official_sources_directory_modified": False,
        },
    }

    modules = module_definitions()
    interfaces = interface_definitions()
    if [module["id"] for module in modules] != config["coupling_module_ids"]:
        raise RuntimeError("Module definitions do not match the predeclared order")
    if [interface["id"] for interface in interfaces] != config["required_interface_ids"]:
        raise RuntimeError("Interface definitions do not match the predeclared order")
    coupling_graph = {
        "iteration": "V10N",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "graph_version": "solver-neutral-coupling-v1",
        "canonical_unit_system": {
            "system": "SI",
            "base": {"length": "m", "mass": "kg", "time": "s", "temperature": "K"},
            "derived": {"force": "N", "stress": "Pa", "energy": "J", "power": "W", "heat_flux": "W/m2"},
            "conversion_policy": "Preserve source units and exact conversion in every adapter record; reject implicit units.",
        },
        "modules": modules,
        "interfaces": interfaces,
        "release_bus_rule": "Only records with an explicit validation_status, epistemic_class and source hashes can reach the ensemble or Blender. Blocked records may be carried only as labelled null/control states.",
        "causal_scope_rule": "Passing one interface validates only its serialization and declared mapping. It does not validate upstream physics, downstream physics or the whole historical chain.",
    }
    coupling_rows = [
        {
            "interface_id": item["id"],
            "producer": item["producer"],
            "consumer": item["consumer"],
            "schema": item["schema"],
            "required_fields": item["required_fields"],
            "spatial_mapping": item["spatial_mapping"],
            "temporal_mapping": item["temporal_mapping"],
            "uncertainty_transfer": item["uncertainty_transfer"],
            "status": item["status"],
            "adapter_ready_for_v10o": item["adapter_ready_for_v10o"],
            "physical_ready": item["physical_ready"],
            "validation_gate": item["validation_gate"],
            "stop_condition": item["stop_condition"],
        }
        for item in interfaces
    ]
    budget = compute_budget(hardware, solver_rows)

    present_count = sum(row["presence"] == "PRESENT" for row in solver_rows)
    source_gate = {
        "iteration": "V10N",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "regression_gate": "PASS",
        "protected_blender_master_gate": "PASS_UNCHANGED",
        "cached_anchor_identity_gate": "PASS_10_OF_10",
        "host_inventory_gate": "PASS_READ_ONLY",
        "candidate_presence_count": present_count,
        "candidate_declared_count": len(solver_rows),
        "openradioss_installation_smoke_gate": "PASS_CACHED_V8T",
        "openradioss_wtc_impact_physics_gate": "CLOSED",
        "exact_nist_production_input_gate": "OPEN_0_OF_10_TARGETS_FROM_V10M",
        "mechanical_source_gate": "OPEN_0_OF_22_REQUIREMENTS",
        "coupling_module_definition_gate": "PASS_9_OF_9",
        "coupling_interface_definition_gate": "PASS_9_OF_9",
        "all_interfaces_adapter_specified": all(item["adapter_ready_for_v10o"] for item in interfaces),
        "physically_ready_interface_count": sum(item["physical_ready"] for item in interfaces),
        "visualization_release_interface_ready": any(
            item["id"] == "I09_ALL_VALIDATED_STATES_TO_BLENDER"
            and item["status"] == "READY_FOR_RELEASED_STATES_ONLY"
            for item in interfaces
        ),
        "v10o_short_adapter_and_cached_control_authorized": True,
        "v10o_physical_historical_conclusion_authorized": False,
        "high_fidelity_end_to_end_solver_run_authorized": False,
        "blender_physical_feedback_authorized": False,
        "physical_assignment_count": 0,
        "solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
        "gate_interpretation": "Software availability is sufficient for the next bounded integration step, but no unavailable input or failed physical gate is closed by executable presence.",
    }

    outputs = config["outputs"]
    write_json(abs_path(outputs["regression_audit"]), regression)
    write_json(abs_path(outputs["cached_anchor_audit"]), cached_audit)
    write_json(abs_path(outputs["resource_inventory"]), resource_inventory)
    write_csv(
        abs_path(outputs["solver_inventory"]),
        [
            "id", "role", "presence", "matching_candidate_count", "resolved_path", "object_kind",
            "sha256", "bytes", "file_version", "product_version", "prior_qualification",
            "allowed_credit", "blocking_for_exact_nist_replay", "blocking_for_reduced_chain",
            "note", "candidate_results_json",
        ],
        solver_rows,
    )
    write_json(abs_path(outputs["coupling_graph"]), coupling_graph)
    write_csv(
        abs_path(outputs["coupling_matrix"]),
        list(coupling_rows[0].keys()),
        coupling_rows,
    )
    write_json(abs_path(outputs["compute_budget"]), budget)
    write_json(abs_path(outputs["source_gate"]), source_gate)
    write_text(
        abs_path(outputs["report"]),
        make_report(config, resource_inventory, solver_rows, modules, interfaces, budget),
    )

    results = {
        "iteration": "V10N",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "dataset": config["dataset"],
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "regression_summary": {"files": len(regression_rows), "protected_files": len(protected_rows), "passed": True},
        "cached_anchor_summary": {"count": len(cached_rows), "all_hashes_passed": True},
        "resource_summary": budget["host_summary"],
        "solver_summary": {
            "declared_candidate_count": len(solver_rows),
            "present_candidate_count": present_count,
            "exact_nist_replay_ready": False,
            "reduced_chain_software_ready_for_short_controls": True,
            "physical_solver_readiness": False,
        },
        "coupling_summary": {
            "module_count": len(modules),
            "interface_count": len(interfaces),
            "adapter_ready_interface_count": sum(item["adapter_ready_for_v10o"] for item in interfaces),
            "physically_ready_interface_count": sum(item["physical_ready"] for item in interfaces),
            "initiation_and_propagation_separate": True,
            "blender_feedback_to_physics": False,
        },
        "gates": source_gate,
        "epistemic_separation": {
            "observed_facts": "Hardware, declared-path presence, executable metadata/hashes and cached artifact identities.",
            "official_model_results": "Preserved as dependent inputs only when referenced by cached modules.",
            "archive_claims": "No source archive read or promoted in V10N.",
            "model_hypotheses": "Reduced fields, reconstructed topology and future interface scenarios remain labelled hypotheses.",
            "derived_results": "Resource sufficiency for short controls and the frozen coupling contracts.",
            "unknowns": "Physical impact damage, exact fire/thermal interfaces, 22 mechanical requirements, initiation and propagation validation.",
        },
        "next_iteration": config["next_iteration"],
        "runtime_seconds": round(time.perf_counter() - started, 6),
    }
    write_json(abs_path(outputs["results"]), results)

    artifact_roles = [
        "regression_audit", "cached_anchor_audit", "resource_inventory", "solver_inventory",
        "coupling_graph", "coupling_matrix", "compute_budget", "source_gate", "report", "results",
    ]
    artifacts = []
    for role in artifact_roles:
        path = abs_path(outputs[role])
        if not path.is_file():
            raise RuntimeError(f"Missing final artifact {role}: {path}")
        artifacts.append({"role": role, "path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    offline = {
        "iteration": "V10N",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "regression_files_reverified_count": len(regression_rows),
        "cached_anchor_files_reverified_count": len(cached_rows),
        "protected_blender_master_unchanged": True,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_sources_directory_modified": False,
        "software_installation_count": 0,
        "solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    write_json(abs_path(outputs["offline_audit"]), offline)

    print(
        json.dumps(
            {
                "iteration": "V10N",
                "status": "PASS",
                "regression_files": len(regression_rows),
                "cached_anchors": len(cached_rows),
                "candidate_tools_present": present_count,
                "modules": len(modules),
                "interfaces": len(interfaces),
                "physical_interfaces_ready": sum(item["physical_ready"] for item in interfaces),
                "solver_runs": 0,
                "next_iteration": config["next_iteration"]["id"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"V10N ERROR: {exc}", file=sys.stderr)
        raise
