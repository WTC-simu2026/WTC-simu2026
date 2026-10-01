"""Read-back V11G validation; standard library only, no mechanics-kernel import."""
import argparse
import hashlib
import json
import math
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def read(path):return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()


def audit(directory):
    tests=[]
    def check(name,condition,evidence):tests.append({"test":name,"pass":bool(condition),"evidence":evidence})
    manifest=read(directory/"offline_manifest.json");result=read(directory/"results_v11g.json")
    outputs={p:sha(directory/p)==h for p,h in manifest["output_sha256"].items()}
    inputs={p:sha(ROOT/p)==h for p,h in manifest["input_sha256"].items()}
    check("saved_output_hashes",all(outputs.values()),outputs);check("frozen_input_hashes",all(inputs.values()),inputs)
    data=read(directory/"bar_paths.json");half=read(directory/"bar_half_step_paths.json")
    negative=read(directory/"uniform_damage_controls.json");panels=read(directory/"panel_equilibrium_recovery.json")
    numerical=read(directory/"numerical_audit.json")
    check("saved_counts",len(data)==len(half)==result["bar_case_count"]==16 and len(negative)==8 and len(panels)==42
          and sum(len(d["history"]) for d in data)==result["bar_state_count"],
          {"bar_cases":len(data),"states":result["bar_state_count"],"negative":len(negative),"panels":len(panels)})
    check("saved_numerical_checks_pass",len(numerical["tests"])==result["tests_passed"]==result["test_count"] and all(t["pass"] for t in numerical["tests"]),result["test_count"])
    worst_work=worst_identity=worst_force=worst_displacement=0.
    si=read(directory/"material_input_ledger.json")["SI"]
    for bar in [*data,*half]:
        s=bar["summary"];history=bar["history"];area=s["area_m2"];L=s["length_m"]
        work=0.
        for i,row in enumerate(history):
            if i:
                a=history[i-1]
                work+=(a["force_N"]+row["force_N"])/2*(row["end_displacement_m"]-a["end_displacement_m"])
            worst_work=max(worst_work,abs(work-row["external_work_J"])/(area*si["Gf_J_m2"]))
            worst_identity=max(worst_identity,abs(work-row["stored_J"]-row["dissipated_J"])/(area*si["Gf_J_m2"]))
            if row["phase"]=="elastic":sigma=si["ft_Pa"]*row["phase_parameter"]
            else:
                wm=row["max_opening_m"];w=row["opening_m"]
                sigma=si["ft_Pa"]*max(0.,1-wm/s["critical_opening_m"])*w/wm if wm else si["ft_Pa"]
            worst_force=max(worst_force,abs(row["force_N"]-area*sigma)/(area*si["ft_Pa"]))
            expected_delta=L*sigma/si["E_Pa"]+row["opening_m"]
            worst_displacement=max(worst_displacement,abs(row["end_displacement_m"]-expected_delta)/s["critical_opening_m"])
        check("complete_saved_energy_"+s["id"]+("_half" if bar in half else ""),
              abs(history[-1]["dissipated_J"]-area*si["Gf_J_m2"])<1e-8,history[-1]["dissipated_J"])
    check("entire_saved_external_work_reconstructed",worst_work<1e-10,worst_work)
    check("saved_external_work_equals_stored_plus_dissipated",worst_identity<1e-8,worst_identity)
    check("saved_force_and_displacement_match_analytic_bar",max(worst_force,worst_displacement)<1e-8,{"force":worst_force,"displacement":worst_displacement})
    check("uniform_controls_rejected_as_single_crack",all(r["single_crack_interpretation"]=="REJECTED_MULTIPLE_SIMULTANEOUS_BANDS"
          and abs(r["D_J"]-r["cells"]*r["gauss_per_cell"]*r["one_crack_target_J"])<1e-8 for r in negative),[r["ratio_to_one_crack_energy"] for r in negative])
    worst_N=worst_M=0.
    for panel in panels:
        for p in panel["point_comparisons"]:
            x=p["x_m"];left=[r for r in panel["point_loads_on_slab"] if r["x_m"]<=x]
            N=-math.fsum(r["Fx_N"] for r in left)
            M=math.fsum(r["Fy_N"]*(x-r["x_m"])-r["couple_Nm"] for r in left)+panel["uniform_q_N_m"]*x*x/2
            worst_N=max(worst_N,abs(N-p["N_equilibrated_N"]))
            worst_M=max(worst_M,abs(M-p["M_equilibrated_Nm"]))
    check("saved_pointwise_statics_reconstructed",worst_N<1e-6 and worst_M<1e-6,{"N_error_N":worst_N,"M_error_Nm":worst_M})
    fine=[p["summary"] for p in panels if p["summary"]["subdivisions"]==8]
    failures=[p["case_id"] for p in fine if p["N_max_relative"]>.05 or p["M_max_relative"]>.05]
    check("local_gate_transcribed_honestly",failures==result["panel_sampled_pointwise_gate"]["failing_cases"]
          and 14-len(failures)==result["panel_sampled_pointwise_gate"]["passing_cases"],failures)
    check("no_global_or_thermal_credit",result["global_energy_credit_J"]==0 and not any(result[k] for k in
          ("panel_mechanics_changed","full_panel_fracture_localization_validated","fire_solved","blender_changed","aircraft_impact_computed","as_built_material_known","counts_are_probabilities")),"Local generic benchmark and read-only V11F recovery")
    script=Path(__file__).resolve()
    return {"iteration":"V11G","status":"PASS" if all(t["pass"] for t in tests) else "FAIL",
            "checked_at_utc":datetime.now(timezone.utc).isoformat(),"check_count":len(tests),"checks":tests,
            "output_hash_count":len(outputs),"input_hash_count":len(inputs),"audit_script":script.relative_to(ROOT).as_posix(),
            "audit_script_sha256":sha(script),"scope":"Saved-file checks without importing the mechanics kernel; not external experimental validation",
            "max_external_work_reconstruction_error_relative_AGf":worst_work,
            "max_external_vs_stored_plus_dissipated_relative_AGf":worst_identity,"global_energy_credit_J":0.}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--directory",required=True);parser.add_argument("--write",action="store_true");args=parser.parse_args()
    directory=(ROOT/args.directory).resolve()
    roots=[(ROOT/"tmp/v11g_localization").resolve(),(ROOT/"wtc1_simulation_v8/output/v11g_localization").resolve()]
    if not any(directory==r or r in directory.parents for r in roots):raise ValueError("Outside V11G output roots")
    result=audit(directory)
    if args.write:
        output=directory/"release_audit.json"
        if output.exists():raise FileExistsError("Existing release audit preserved")
        output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in result.items() if k!="checks"},indent=2,ensure_ascii=False))
    if result["status"]!="PASS":
        print(json.dumps([t for t in result["checks"] if not t["pass"]],indent=2));raise SystemExit(1)
