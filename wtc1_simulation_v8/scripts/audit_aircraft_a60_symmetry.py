"""Read the pinned source cache; publish hashes/anchors, not third-party source."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
import tarfile,hashlib,re,json

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a60'
ARCH=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'

def main():
    assert sha(ARCH)=='d64b773e899c174f5d59aadc4d2b73a101a083581e611d67215aaa50037cf9f8'
    selected=['engine/source/implicit/imp_mumps.F','engine/source/mpi/implicit/imp_spmd.F','engine/source/implicit/imp_glob_k.F']
    rows=[];calls=[]
    with tarfile.open(ARCH) as t:
        for entry in t.getmembers():
            if not entry.isfile() or not entry.name.lower().endswith(('.f','.f90')):continue
            path=entry.name.split('/',1)[1]
            if not(path.startswith('engine/source/implicit/') or path.startswith('engine/source/mpi/implicit/')):continue
            raw=t.extractfile(entry).read();lines=raw.decode('utf8').splitlines()
            for j,line in enumerate(lines):
                if re.search(r'CALL\s+SPMD_MUMPS_INI\s*\(',line,re.I):calls.append({'path':path,'line':j+1,'call':line.strip(),'source_sha256':hashlib.sha256(raw).hexdigest()})
            if path in selected:
                anchors=[{'line':j+1,'keyword':word} for j,line in enumerate(lines) for word in ['SUBROUTINE ASSEMC_KIJ','SUBROUTINE SPMD_MUMPS_INI','MUMPS_PAR%SYM=SYM','CALL SPMD_MUMPS_INI','KIJD(I,J)=KIJ(I,J)+KIJ(J,I)','ID=MIN(IDI,IDJ)'] if word in line]
                rows.append({'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'lines':len(lines),'anchors':anchors})
    result={'created_utc':now(),'archive':rel(ARCH),'archive_sha256':sha(ARCH),'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','sources':rows,'MUMPS_initialization_calls_in_scanned_implicit_directories':calls,
      'scan_scope':['engine/source/implicit/','engine/source/mpi/implicit/'],
      'observations':['IMP_MUMPS1 initializes SPMD_MUMPS_INI with SYM=1. SPMD_MUMPS_INI assigns its SYM argument to MUMPS_PAR%SYM.',
        'ASSEMC_KIJ adds the transposed block for a degenerate node pair and stores only one triangular global block for distinct pairs. Full nonsymmetric material Jacobians cannot be preserved by this symmetric assembly.'],
      'full_tree_or_all_solver_paths_not_claimed':True,
      'mixed_exact_Jacobian_cannot_be_inserted_unchanged':True,
      'candidate_direction':'Symmetric elastic/quasi-Newton iteration matrix with unchanged native traction residual, convergence gates and correctly staged internal state. Native implementation not yet qualified.',
      'new_software_patch_applied':False,'raw_AGPL_source_not_copied_to_public_MIT_artifact':True}
    assert len(rows)==3 and calls
    dump(OUT/'native_symmetry_compatibility_review.json',result)
    print(json.dumps({'source_files':len(rows),'MUMPS_initialization_calls':calls,'direct_exact_mixed_Jacobian_compatible':False}))

if __name__=='__main__':main()
