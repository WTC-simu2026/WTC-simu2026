import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wtc1_simulation_v8" / "scripts"))
import run_v8h_mechanical_core_transfer as h
import run_v8f_vertical_load_path as f

transfer = json.loads(h.TRANSFER.read_text(encoding="utf-8"))
prior_b = json.loads(h.V8B_RESULT.read_text(encoding="utf-8"))
parameters = json.loads(h.PARAMETERS.read_text(encoding="utf-8"))
aisc = json.loads(h.AISC.read_text(encoding="utf-8"))
coords = {int(r["id"]): (float(r["x_m"]), float(r["y_m"])) for r in parameters["core_layout_reconstruction"]["columns"]}
prepared = {}
for floor in h.FLOORS_DESC:
    fd = prior_b["floor_inputs"][str(floor)]
    prepared[floor] = {"sections": {int(k): v for k, v in fd["sections"].items()}, "removed": set(fd["initial_removed"])}
for seed in range(100):
    state = h.simulate_path(
        float(transfer["nist_global_core_loads_floor_98_kip"]["case_b_time_history"]["100"]),
        f.smooth_score(coords, seed),
        1.0,
        4,
        prepared,
        transfer["fire_case_b"]["core_column_temperature_ranges_c"],
        coords,
        h.nearest_four_edges(coords),
        aisc["shapes"]["14WF136"],
        1.0,
        2,
        "cold_20c_upper_transfer_bound",
        transfer["steel_temperature_model"]["yield_ratio_parameters"],
        transfer["steel_temperature_model"]["young_modulus_parameters"],
    )
    if state["first_failed_floor"] and state["floors"][str(state["first_failed_floor"])]["reason"] == "force_residual":
        print(seed, state["floors"][str(state["first_failed_floor"])])
        break
