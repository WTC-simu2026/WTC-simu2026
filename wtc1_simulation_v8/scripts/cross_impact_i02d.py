"""Compare native animations with separately stored complete nodal histories."""
import json,re,subprocess
from pathlib import Path
import numpy as np
from export_impact_i02a import parse_vtk
from run_impact_i02c import ROOT,sha,dump,RUNTIME
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02d_lap_joint';d=OUT/'LAP_SEPARATE_H025_R5';VIEW=ROOT/'wtc1_3d_v4/output/impact_i02d';raw=VIEW/'native_cross';raw.mkdir(parents=True,exist_ok=True)
m=json.loads((d/'generation.json').read_text());column=json.loads((d/'column_map.json').read_text());a=np.loadtxt(d/(m['name']+'T01.csv'),delimiter=',',skiprows=1)
ids=column['raw_node_ids'];node=a[:,column['node_start']:].reshape(len(a),len(ids),15)[:,[ids.index(i) for i in range(1,len(ids)+1)]]
initial=np.array(m['nodes_mm']);records=[];vmax=float(abs(node[:,:,3:6]).max())
files=sorted(p for p in d.glob(m['name']+'A*') if re.fullmatch(r'.*A\d{3}',p.name))
for k,path in enumerate(files):
    proc=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(path)],capture_output=True,text=True,timeout=30);assert proc.returncode==0
    mesh=parse_vtk(proc.stdout);nids=mesh['NODE_ID'].astype(int);xyz=mesh['points'].reshape(-1,3);displ=mesh['Displacement'].reshape(-1,3);t=mesh['time']
    expected=initial[nids-1]+np.array([[np.interp(t,a[:,0],node[:,n-1,j]) for j in range(3)] for n in nids])
    extra=max(a[0,0]-t,t-a[-1,0],0);tol=.0001+vmax*(m['history_dt_ms']*.5+extra)
    quant=lambda v:.500001*10.**(np.floor(np.log10(np.maximum(abs(v),1e-30)))-5)
    identity=abs(xyz-initial[nids-1]-displ);bound=quant(xyz)+quant(displ)+np.finfo(np.float32).eps*abs(initial[nids-1])+1e-10
    offset=0;count=0;topology=True;ci=0;cells=mesh['cells'].astype(int)
    while offset<len(cells):
        n=cells[offset];indices=cells[offset+1:offset+1+n];eid=int(mesh['ELEMENT_ID'][ci]);offset+=n+1;ci+=1
        if n==4:
            topology &= set(nids[indices])==set(m['quads'][eid-1]);count+=1
    target=raw/f'state_{k:03d}.vtk';target.write_text(proc.stdout)
    checks={'coordinate_history':bool(abs(xyz-expected).max()<tol),'displacement_identity':bool((identity<=bound).all()),'shell_connectivity':bool(topology and count==len(m['quads']))}
    records.append({'state':k,'time_ms':t,'cross_error_mm':float(abs(xyz-expected).max()),'cross_bound_mm':tol,'identity_error_mm':float(identity.max()),'checks':checks,'source':str(path.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(path),'vtk_sha256':sha(target)})
result={'status':'PASS' if len(records)==31 and all(all(r['checks'].values()) for r in records) else 'FAIL','states':records,'converter_sha256':sha(RUNTIME/'anim_to_vtk_win64.exe'),'nodal_frames_sha256':sha(d/'computed_frames.npz'),'meaning':'Independent native-animation versus TH coordinate and shell topology check. PVD/movie use exact saved TH times, not native animation times. Interpolation here is solely a bounded cross-check, not generated mechanical states.'}
dump(VIEW/'animation_cross_audit.json',result);print(json.dumps({'status':result['status'],'states':len(records),'max_cross_mm':max(r['cross_error_mm'] for r in records),'max_identity_mm':max(r['identity_error_mm'] for r in records)}))
