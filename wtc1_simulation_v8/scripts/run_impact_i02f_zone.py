"""Run one immutable I02E local zone with the I02F central crack-band hypothesis."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from run_impact_i02e import generate, load_config
from run_impact_i02f import failure_lines, ff


ROOT = Path(__file__).resolve().parents[2]
BASE_CFG = ROOT / "wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone_r9.json"
COUPON_CFG = ROOT / "wtc1_simulation_v8/data/impact_i02f_tear_coupon.json"
OUT = ROOT / "wtc1_simulation_v8/output/impact_i02f_tear_coupon"
RUNTIME = ROOT / "wtc1_simulation_v8/openradioss_runtime/v20260728-win64"
CASE_ID = "ZONE_AA2024_G30_H0635_R0"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def execute(executable: Path, arguments: list[str], directory: Path, environment: dict, log_name: str, timeout: int) -> dict:
    start = time.perf_counter()
    process = subprocess.run([str(executable), *arguments], cwd=directory, env=environment, capture_output=True, timeout=timeout)
    (directory / log_name).write_bytes(process.stdout + process.stderr)
    record = {
        "command": [str(executable), *arguments],
        "returncode": process.returncode,
        "seconds": time.perf_counter() - start,
        "executable_sha256": sha(executable),
    }
    if process.returncode:
        raise RuntimeError(f"{log_name} failed in {directory}")
    return record


def main() -> None:
    cfg, chain = load_config(BASE_CFG)
    base_case = next(case for case in cfg["cases"] if case["id"] == "CONTACT_RUPTURABLE_H0635_R9")
    case = json.loads(json.dumps(base_case))
    case["id"] = CASE_ID
    case["role"] = "single local I02E zone with central I02F crack-band sensitivity; not a physical Boeing prediction"
    directory = OUT / CASE_ID
    if directory.exists():
        raise RuntimeError("Existing local-zone case preserved: " + str(directory))
    directory.mkdir(parents=True)
    meta = generate(cfg, case, directory, BASE_CFG, chain)
    old_name = meta["name"]
    new_name = "I02F_" + CASE_ID
    old_starter = directory / f"{old_name}_0000.rad"
    old_engine = directory / f"{old_name}_0001.rad"
    starter = directory / f"{new_name}_0000.rad"
    engine = directory / f"{new_name}_0001.rad"
    coupon_cfg = json.loads(COUPON_CFG.read_text(encoding="utf-8"))
    gf = 30.0
    nominal_h = float(base_case["mesh_mm"])
    inherited_yield = float(cfg["materials"]["skin_2024_t3_reference"]["yield_strength_mpa"])
    failure_plastic_strain = gf / (inherited_yield * nominal_h)
    starter_text = old_starter.read_text(encoding="utf-8").replace(old_name, new_name)
    block = "\n".join(failure_lines(2, 1002, failure_plastic_strain)) + "\n"
    if "/NODE\n" not in starter_text:
        raise RuntimeError("Cannot locate I02E /NODE insertion point")
    starter_text = starter_text.replace("/NODE\n", block + "/NODE\n", 1)
    starter_text = starter_text.replace("/END\n", "/UNIT/1\nI02F_G_MM_MS\n" + ff("g", "mm", "ms") + "\n/END\n", 1)
    starter.write_text(starter_text, encoding="utf-8", newline="\n")
    engine.write_text(old_engine.read_text(encoding="utf-8").replace(old_name, new_name), encoding="utf-8", newline="\n")
    meta.update(
        name=new_name,
        base_i02e_case_id=base_case["id"],
        case=case,
        i02f_metal_tearing={
            "material_id": 2,
            "affected_part": "WING_SKINS",
            "Gf_N_per_mm": gf,
            "nominal_h_mm": nominal_h,
            "inherited_yield_strength_mpa": inherited_yield,
            "failure_plastic_strain": failure_plastic_strain,
            "equation": "eps_p_failure = Gf / (sigma_y * nominal_h)",
            "status": "constant-triaxiality-independent numerical sensitivity transferred from unit-cell central case",
        },
        base_generator_sha256=meta["generator_sha256"],
        generator_sha256=sha(Path(__file__)),
        coupon_config_sha256=sha(COUPON_CFG),
        starter_sha256=sha(starter),
        engine_sha256=sha(engine),
        unmodified_i02e_base_decks_preserved=[old_starter.name, old_engine.name],
    )
    meta["source_sha256"].update({source["path"]: source["sha256"] for source in coupon_cfg["sources"] if "path" in source})
    dump(directory / "generation.json", meta)
    environment = os.environ.copy()
    environment.update(
        RAD_CFG_PATH="C:/OpenRadioss/hm_cfg_files",
        RAD_H3D_PATH="C:/OpenRadioss/extlib/h3d/lib/win64",
        OPENRADIOSS_PATH="C:/OpenRadioss",
        OMP_NUM_THREADS="1",
        KMP_STACKSIZE="400m",
    )
    records = []
    for executable, arguments, log_name in [
        ("starter_win64.exe", ["-i", starter.name, "-np", "1"], "starter.log"),
        ("engine_win64.exe", ["-i", engine.name], "engine.log"),
        ("th_to_csv_win64.exe", [new_name + "T01"], "converter.log"),
    ]:
        records.append(execute(RUNTIME / executable, arguments, directory, environment, log_name, 180))
        dump(directory / "execution.json", records)
    print(json.dumps({"case": CASE_ID, "seconds": sum(record["seconds"] for record in records), "failure_plastic_strain": failure_plastic_strain, "skin_shells": meta["element_ranges"]["2"][1] - meta["element_ranges"]["2"][0] + 1}))


if __name__ == "__main__":
    main()
