"""Cross-check independently saved animation and nodal history outputs."""
import csv,json,re,subprocess,hashlib
from pathlib import Path
import numpy as np
from export_impact_i02a import parse_vtk
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02c_deformable_joint'
CASE='DYN_BASE_H025_R2';directory=OUT/CASE
VIEW=ROOT/'wtc1_3d_v4/output/impact_i02c';VIEW.mkdir(parents=True,exist_ok=True)
raw=VIEW/'vtk_raw';raw.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((directory/'generation.json').read_text());column=json.loads((directory/'column_map.json').read_text())
with (directory/(m['name']+'T01.csv')).open() as stream:
    next(stream);a=np.loadtxt(stream,delimiter=',')
ids=column['node_ids_raw_order'];nodes=a[:,column['node_start']:].reshape(len(a),len(ids),3)
nodes=nodes[:,[ids.index(i) for i in range(1,len(ids)+1)],:]
initial=np.array(m['nodes_mm']);records=[]
converter=ROOT/'wtc1_simulation_v8/openradioss_runtime/v20260728-win64/anim_to_vtk_win64.exe'
files=sorted(p for p in directory.glob(m['name']+'A*') if re.fullmatch(r'.*A\d{3}',p.name))
for index,source in enumerate(files):
    proc=subprocess.run([str(converter),str(source)],capture_output=True,text=True,timeout=30)
    if proc.returncode:raise RuntimeError(source.name)
    d=parse_vtk(proc.stdout);nids=d['NODE_ID'].astype(int);points=d['points'].reshape(-1,3);displ=d['Displacement'].reshape(-1,3)
    t=d['time'];expected=initial[nids-1].copy()
    expected[:,m['axis']]+=[np.interp(t,a[:,0],nodes[:,nid-1,0]) for nid in nids]
    cross=float(np.max(abs(points-expected)));identity=float(np.max(abs(points-initial[nids-1]-displ)))
    def quantization(values):
        return .500001*10.0**(np.floor(np.log10(np.maximum(abs(values),1e-30)))-5)
    identity_bound=quantization(points)+quantization(displ)+np.finfo(np.float32).eps*abs(initial[nids-1])+1e-10
    time_extrap=max(a[0,0]-t,t-a[-1,0],0)
    # Bound source history sampling plus conversion coordinate quantization.
    tolerance=.00005+float(abs(nodes[:,:,1]).max())*(m['history_dt_ms']*.5+time_extrap)
    cells=d['cells'].astype(int);offset=0;quad_count=0;topology=True;ci=0
    while offset<len(cells):
        count=cells[offset];indices=cells[offset+1:offset+1+count];eid=int(d['ELEMENT_ID'][ci]);offset+=count+1;ci+=1
        if count==4:
            topology &= set(nids[indices])==set(m['quads'][eid-1]);quad_count+=1
    target=raw/f'state_{index:03d}.vtk';target.write_text(proc.stdout,encoding='utf-8')
    checks={'coordinates_vs_nodal_history':bool(cross<tolerance),'coordinate_displacement_identity':bool(np.all(abs(points-initial[nids-1]-displ)<=identity_bound)),'shell_connectivity':bool(topology and quad_count==len(m['quads']))}
    records.append({'state':index,'time_ms':t,'history_cross_error_mm':cross,'cross_tolerance_mm':tolerance,'displacement_identity_error_mm':identity,'max_coordinate_quantization_bound_mm':float(identity_bound.max()),'checks':checks,'source':str(source.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(source),'vtk_sha256':sha(target)})
result={'status':'PASS' if all(all(r['checks'].values()) for r in records) else 'FAIL','case':CASE,'states':records,'converter_sha256':sha(converter),
        'nodal_frames_npz_sha256':sha(directory/'computed_frames.npz'),'scope':'Animation cross-check only; video uses exactly sampled nodal frames. Fixed axes, no displacement amplification, no aircraft prediction.',
        'coordinate_quantization_rule':'Six-significant-digit ASCII output half-unit bounds for position AND displacement, plus single-precision coordinate rounding. Initial audit incorrectly budgeted the position rounding alone at 5e-5 mm; retained separately.'}
(VIEW/'animation_cross_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'states':len(records),'max_cross_error_mm':max(r['history_cross_error_mm'] for r in records),'max_identity_error_mm':max(r['displacement_identity_error_mm'] for r in records)},indent=2))
