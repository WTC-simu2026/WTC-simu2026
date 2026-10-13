"""Compilation-only explicit interface repair within approved A61 work and original cap."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,linux,harness
from build_aircraft_a62_surface import OUT,CFG,CAND,guard
from pathlib import Path
import time,subprocess,shlex,json,difflib

INTERFACE='''C     Explicit interface required for the helper TARGET dummy argument.
      INTERFACE
        SUBROUTINE WTC_A61_S43_K(ELBUF_STR,NEL,IXS,X,IPM,BUFMAT,
     .                IDDL,IADK,JDIK,K_DIAG,K_LT,ETAG)
          IMPORT :: ELBUF_STRUCT_,NIXS,NPROPMI,WP
          TYPE(ELBUF_STRUCT_), TARGET :: ELBUF_STR
          INTEGER NEL,IXS(NIXS,*),IPM(NPROPMI,*),IDDL(*),IADK(*)
          INTEGER JDIK(*),ETAG(*)
          REAL(KIND=WP) X(*),BUFMAT(*),K_DIAG(*),K_LT(*)
        END SUBROUTINE WTC_A61_S43_K
      END INTERFACE
'''

def main():
    cfg=guard();deadline=read(OUT/'build_clock.json')['deadline_epoch'];assert time.time()<deadline
    attempt=OUT/'build_attempt_R1_interface';assert not attempt.exists();attempt.mkdir();logs=attempt/'build_logs';scripts=attempt/'build_scripts';logs.mkdir();scripts.mkdir()
    original=ROOT/cfg['surface_patch']['proposed_source_path'];s=original.read_text(encoding='utf8');anchor='      GBUF => ELBUF_STR%GBUF\n';assert s.count(anchor)==1
    repaired=s.replace(anchor,INTERFACE+anchor);assert repaired.replace(INTERFACE,'')==s
    src=CAND/'s8zke3_R1_interface.proposed.F';src.write_text(repaired,encoding='utf8',newline='\n')
    patch=CAND/'type43_surface_interface_R1.patch';target=cfg['surface_patch']['target'];patch.write_text(''.join(difflib.unified_diff(s.splitlines(True),repaired.splitlines(True),fromfile='a/'+target,tofile='b/'+target)),encoding='utf8',newline='\n')
    assert all(len(l)<=72 for l in INTERFACE.splitlines() if not l.startswith('C'))
    dump(attempt/'attempt_predeclaration.json',{'created_utc':now(),'iteration':'AIRCRAFT-A62','attempt':'R1_interface','seed':1102087,'random_draws':0,
      'authorization':'Existing explicit A61 surface correction and compilation approval; this is solely the compiler-required declaration of the same helper interface, with no mechanical/software scope extension.',
      'reason':'GNU explicit interface required for TARGET dummy; R0 exact approved source applied and compile failure retained.',
      'original_source_sha256':sha(original),'interface_source_sha256':sha(src),'interface_patch_sha256':sha(patch),'removing_interface_recovers_approved_source_exactly':True,
      'helper_body_and_all_executable_equations_unchanged':True,'same_sixth_candidate_and_original_deadline':True,'deadline_epoch':deadline,'cap_original_s':3600,'CPU':6,'GPU':False,'installation':False})
    dump(attempt/'harness_before.json',harness())
    q=lambda p:shlex.quote(linux(p));mount=CAND/'native_workspace';image=CAND/'build_workspace.ext4';mounted=False
    def shell(name,body,cleanup=False):
        remaining=int(deadline-time.time());assert cleanup or remaining>0
        cap=45 if cleanup else remaining;p=scripts/(name+'.sh');p.write_text('set -eu\n'+body+'\n',encoding='utf8',newline='\n')
        start=time.perf_counter();print(json.dumps({'attempt':'R1_interface','build_step':name,'remaining_original_s':remaining}),flush=True)
        r=subprocess.run(['wsl.exe','-d','Ubuntu','-u','root','--','timeout','--signal=TERM','--kill-after=5',str(cap),'bash',linux(p)],capture_output=True,timeout=cap+15)
        (logs/(name+'.log')).write_bytes(r.stdout+r.stderr);dump(logs/(name+'.execution.json'),{'created_utc':now(),'exit_code':r.returncode,'wall_s':time.perf_counter()-start,'cap_s':cap});assert r.returncode==0,name
    try:
        shell('01_remount',f'test -f {q(image)}\nmount -o loop {q(image)} {q(mount)}');mounted=True
        t=mount/'source'/target
        shell('02_interface_only',f'test "$(sha256sum {q(t)} | cut -d " " -f 1)" = {sha(original)}\ncd {q(mount)}/source\npatch --batch --fuzz=0 -p1 < {q(patch)}\ntest "$(sha256sum {q(t)} | cut -d " " -f 1)" = {sha(src)}\ncmp {q(t)} {q(src)}')
        dump(OUT/'exact_interface_declaration_application.json',{'created_utc':now(),'pass':True,'same_helper_code_and_mechanical_equations':True,'source_sha256':sha(src),'interface_patch_sha256':sha(patch),'source_path':rel(src),'patch_path':rel(patch),'original_approved_source_sha256':sha(original),'initial_exact_patch_and_compile_failure_preserved':True})
        shell('03_compile_resume',f'cmake --build {q(mount)}/engine_build --parallel 6')
        dest=CAND/'isolated_exec';shell('04_export',f'test ! -e {q(dest)}\nmkdir {q(dest)}\ncp {q(mount)}/source/exec/engine_linux64_gf_ompi {q(dest)}/\ncp -a {q(mount)}/source/hm_cfg_files {q(CAND)}/hm_cfg_files\ncp {q(mount)}/engine_build/CMakeCache.txt {q(OUT)}/engine_CMakeCache.txt\nldd {q(dest)}/engine_linux64_gf_ompi\nnm -n {q(dest)}/engine_linux64_gf_ompi > {q(OUT)}/engine_symbols.txt')
        protected=[r for r in read(OUT/'preservation_before_metadata.json')['files'] if r['path'].endswith('/isolated_exec/engine_linux64_gf_ompi')]
        for row in protected:assert sha(ROOT/row['path'])==row['sha256']
        binary=dest/'engine_linux64_gf_ompi';assert time.time()<=deadline
        dump(OUT/'build_finished.json',{'created_utc':now(),'build_success':True,'attempt':'R1_interface','candidate_directory':rel(CAND),'source_pin':cfg['source_pin'],'binary_sha256':sha(binary),'bytes':binary.stat().st_size,'wall_s_from_original_start':time.time()-read(OUT/'build_clock.json')['started_epoch'],'within_original_hour':True,'CPU_threads':6,'GPU':False,'old_Engines_hash_verified':len(protected),'no_installation':True,'Starter_not_built':True,'exact_A53_graph_patch_applied':True,'exact_A55_scratch_patch_applied':True,'exact_A56_original_scratch_patch_applied':True,'exact_A61_surface_patch_initially_applied':True,'required_interface_declaration_added_only':True,'native_or_physical_qualification':False,'source_license':'AGPL-3.0-or-later','R0_compile_failure_preserved':True})
        print(json.dumps({'build_success':True,'attempt':'R1_interface','binary_sha256':sha(binary)}),flush=True)
    except BaseException as exc:
        dump(attempt/'build_failure.json',{'created_utc':now(),'error':str(exc),'partial_outputs_preserved':True});raise
    finally:
        if mounted:shell('05_unmount',f'sync\numount {q(mount)}',cleanup=True)

if __name__=='__main__':main()
