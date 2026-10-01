"""Read-back audit of saved files; does not import the V11E mechanics kernel."""
import argparse
import csv
import hashlib
import json
import math
import platform
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import PIL

ROOT=Path(__file__).resolve().parents[2]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def rows(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))


def audit(directory):
    manifest=read(directory/"offline_manifest.json");result=read(directory/"results_v11e.json")
    inv={v["case"]["id"]:v for v in read(directory/"section_inventory.json")}
    checks=[]
    def check(name,ok,evidence): checks.append({"test":name,"pass":bool(ok),"evidence":evidence})
    outputs={p:sha(directory/p)==h for p,h in manifest["output_sha256"].items()}
    inputs={p:sha(ROOT/p)==h for p,h in manifest["input_sha256"].items()}
    check("published_output_hashes",all(outputs.values()),outputs)
    check("input_and_protected_hashes",all(inputs.values()),inputs)
    previous=ROOT/"wtc1_simulation_v8/output/v11d_slab_contact"
    oldoutputs={r["path"]:sha(previous/r["path"])==r["sha256"] for r in read(previous/"offline_manifest.json")["files"]}
    oldinputs={r["path"]:sha(ROOT/r["path"])==r["sha256_after"] for r in read(previous/"source_manifest.json")["input_and_protected_files"]}
    check("all_previous_V11D_output_hashes",all(oldoutputs.values()),oldoutputs)
    check("all_previous_V11D_input_hashes",all(oldinputs.values()),oldinputs)
    history=rows(directory/"section_history.csv");fibers=rows(directory/"section_fibers.csv")
    bycase=defaultdict(list);byfiber=defaultdict(list)
    for r in history: bycase[r["case_id"]].append(r)
    for r in fibers: byfiber[r["case_id"]].append(r)
    check("saved_case_and_state_counts",len(bycase)==result["case_count"]==14 and len(history)==result["state_count"],
          {"cases":len(bycase),"states":len(history),"fiber_rows":len(fibers)})
    numerical=read(directory/"numerical_audit.json")
    check("saved_tests_all_pass",numerical["tests_passed"]==numerical["test_count"]==result["tests_passed"]==result["test_count"] and all(r["pass"] for r in numerical["tests"]),result["test_count"])
    errors=[]
    for name,fr in byfiber.items():
        last=bycase[name][-1]
        N=math.fsum(float(r["stress_Pa"])*float(r["area_m2"]) for r in fr)
        M=math.fsum(-float(r["stress_Pa"])*float(r["area_m2"])*float(r["y_m"]) for r in fr)
        U=math.fsum(float(r["stored_J_m3"])*float(r["area_m2"]) for r in fr)
        D=math.fsum(float(r["dissipated_J_m3"])*float(r["area_m2"]) for r in fr)
        errors.append({"case_id":name,"force_N_error":abs(N-float(last["N_N"])),"moment_Nm_error":abs(M-float(last["M_Nm"])),
                       "stored_J_per_m_error":abs(U-float(last["stored_J_per_m"])),
                       "work_J_per_m_error":abs(U+D-float(last["exact_material_work_J_per_m"]))})
    check("saved_fibers_recover_forces_moments_energy",all(max(v for k,v in r.items() if k!="case_id")<1e-6 for r in errors),errors)
    face_error=0.;domain_error=0.;max_face_ratio=0.
    for name,hr in bycase.items():
        geometry=inv[name]
        for r in hr:
            face=max(0.,-geometry["E_concrete_Pa"]*(float(r["eps0"])-abs(float(r["kappa_per_m"]))*geometry["equivalent_thickness_m"]/2))
            face_error=max(face_error,abs(face-float(r["compression_face_stress_Pa"])) / max(1.,face))
            domain_error=max(domain_error,abs(face/geometry["fc_Pa"]-float(r["compression_ratio"])))
            max_face_ratio=max(max_face_ratio,face/geometry["fc_Pa"])
    check("saved_outer_face_compression_screen",face_error<1e-12 and domain_error<1e-12 and max_face_ratio<1+1e-8,
          {"relative_face_error":face_error,"ratio_error":domain_error,"maximum_face_ratio":max_face_ratio})
    # Independently reconstruct the entire generalized external-work ledger from the saved endpoints.
    max_work_error=0.
    for hr in bycase.values():
        work=0.
        for a,b in zip(hr[:-1],hr[1:],strict=True):
            work+=(float(a["N_N"])+float(b["N_N"]))/2*(float(b["eps0"])-float(a["eps0"]))
            work+=(float(a["M_Nm"])+float(b["M_Nm"]))/2*(float(b["kappa_per_m"])-float(a["kappa_per_m"]))
            max_work_error=max(max_work_error,abs(work-float(b["external_trapezoid_work_J_per_m"])))
    check("saved_external_work_ledger_reproduced",max_work_error<1e-7,max_work_error)
    bycoupon=defaultdict(list)
    for r in rows(directory/"material_coupons.csv"): bycoupon[r["coupon_id"]].append(r)
    gf_errors={name:abs(float(rr[-1]["dissipated_J_m3"])*float(rr[-1]["Lch_m"])-100.) for name,rr in bycoupon.items() if name.startswith("CONCRETE")}
    check("saved_coupon_Gf_per_declared_band",len(gf_errors)==3 and max(gf_errors.values())<1e-8,gf_errors)
    codepath=Path(__file__).resolve()
    return {"iteration":"V11E","status":"PASS" if all(c["pass"] for c in checks) else "FAIL","checked_at_utc":datetime.now(timezone.utc).isoformat(),
            "audit_scope":"Read-back validation of saved artifacts, not independent experimental or multi-agent review",
            "checks":checks,"check_count":len(checks),"output_hash_count":len(outputs),"input_hash_count":len(inputs),
            "old_V11D_output_hash_count":len(oldoutputs),"old_V11D_input_hash_count":len(oldinputs),
            "audit_script":codepath.relative_to(ROOT).as_posix(),"audit_script_sha256":sha(codepath),
            "software":{"python":platform.python_version(),"Pillow":PIL.__version__},
            "attempt_policy":"attempt02 is the final outer-face compression criterion; attempt01 retained as superseded midpoint-screen diagnostic, never promoted. Current kernel/configuration hashes reproduce attempt02 only.",
            "global_energy_credit_J":0.,"blender_changed":False}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--directory",required=True);parser.add_argument("--write",action="store_true");args=parser.parse_args()
    directory=(ROOT/args.directory).resolve()
    allowed=[(ROOT/"tmp/v11e_cracked_section").resolve(),(ROOT/"wtc1_simulation_v8/output/v11e_cracked_section").resolve()]
    if not any(directory==p or p in directory.parents for p in allowed): raise ValueError("Outside V11E output roots")
    result=audit(directory)
    if args.write:
        output=directory/"release_audit.json"
        if output.exists(): raise FileExistsError("Existing release audit is preserved")
        output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in result.items() if k!="checks"},indent=2,ensure_ascii=False))
    if result["status"]!="PASS":
        print(json.dumps([r for r in result["checks"] if not r["pass"]],indent=2));raise SystemExit(1)
