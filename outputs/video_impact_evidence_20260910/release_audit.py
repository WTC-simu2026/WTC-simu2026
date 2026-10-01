"""Validate saved delivery without rerunning video extraction or mechanics."""
import json, subprocess, time
from pathlib import Path
from PIL import Image
from audit_video import ROOT, CFG, digest, save
t0=time.perf_counter()
intake=json.loads((ROOT/'intake.json').read_text(encoding='utf-8'))
checks={}
for k,v in intake['sources'].items(): checks['original_'+k]=digest(v['path'])==v['sha256_before']
for key,folder,n in [('Evidence1','Evidence1_0_359',360),('Evidence2','Evidence2_2790_2940',151)]:
    paths=sorted((ROOT/folder).glob('*.png'))
    checks[key+'_frame_count']=len(paths)==n
    checks[key+'_dimensions']=all(Image.open(p).size==tuple(CFG['dimensions'][key]) for p in paths)
    # Basic PNG validity including compressed image data.
    for p in paths:
        with Image.open(p) as im: im.verify()
    checks[key+'_png_integrity']=True
state=json.loads((ROOT.parents[1]/'harness/state.json').read_text(encoding='utf-8-sig'))
checks['structural_state_preserved']=state['current_iteration']=='V11R' and state['next_iteration']=='V11S'
for name in ['rapport.md','aile_comparaison_finale.png','moving_crop_manifest.json','presentation_timing.json','pixel_diagnostics.json','integrity_after.json']:
    checks['exists_'+name]=(ROOT/name).is_file()
checks['handoff_exists']=(ROOT.parents[1]/'harness/handoffs/WTC1_VIDEO_EVIDENCE_20260910_HANDOFF.md').is_file()
result=subprocess.run(['C:/Program Files/PowerShell/7/pwsh.exe','-NoProfile','-File',str(ROOT.parents[1]/'harness/tools/Test-WtcHarness.ps1')],capture_output=True,text=True,encoding='utf-8')
(ROOT/'harness_after.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
checks['harness_pass']=result.returncode==0 and 'PASS' in result.stdout
files={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['release_audit.json','manifest.json']}
save('manifest.json',files)
save('release_audit.json',{'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'seconds':time.perf_counter()-t0,'manifest_files':len(files),'manifest_sha256':digest(ROOT/'manifest.json'),'scope':'Integrity, files, state and harness only; not video authenticity or physical wing/impact validation'})
assert all(checks.values()),checks
print('PASS',len(checks),'checks;',len(files),'manifest files')
