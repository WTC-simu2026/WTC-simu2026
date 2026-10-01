"""Read saved Radioss animations, verify identity and export exact computed nodes."""
import json,re,subprocess,hashlib,time
from pathlib import Path
import numpy as np
from run_impact_i01 import ROOT,CFG,sha,write_json
cfg=json.loads(CFG.read_text(encoding='utf-8')); out=ROOT/cfg['output_root']; start=time.perf_counter()
exe=ROOT/'wtc1_simulation_v8/openradioss_runtime/v20260728-win64/anim_to_vtk_win64.exe'
def vtk(text):
    a={}; lines=text.splitlines(); i=0; n=0
    while i<len(lines):
        q=lines[i].split(); i+=1
        if not q: continue
        if q[0]=='TIME':
            while not lines[i].strip(): i+=1
            a['time']=float(lines[i]); i+=1
        elif q[0] in ['POINT_DATA','CELL_DATA']: n=int(q[1])
        elif q[0] in ['POINTS','CELLS','SCALARS','VECTORS','CELL_TYPES']:
            kind=q[0]
            if kind=='POINTS': key='points'; count=int(q[1])*3
            elif kind=='CELLS': key='cells'; count=int(q[2])
            elif kind=='CELL_TYPES': key='types'; count=int(q[1])
            elif kind=='SCALARS':
                key=q[1]; count=n*(int(q[3]) if len(q)>3 else 1)
                while not lines[i].strip(): i+=1
                assert lines[i].startswith('LOOKUP_TABLE'); i+=1
            else: key=q[1]; count=n*3
            j=i; total=0
            while total<count:
                total+=len(lines[i].split()); i+=1
            vals=np.fromstring(' '.join(lines[j:i]),sep=' ')
            assert len(vals)==count,(key,len(vals),count)
            a[key]=vals
    return a
summaries={}
for case in cfg['cases']:
    d=out/case['id']; fs=sorted(p for p in d.glob('I01_*A*') if re.match(r'.*A\d{3}$',p.name))
    # Full animation of nominal pilot; endpoints/early strain inspection of other cases.
    if case['id']!='M050': fs=[fs[0],fs[-1]]
    original=json.loads((d/'mesh.json').read_text()); gen=json.loads((d/'generation.json').read_text())
    coords=[]; eps=[]; ts=[]; refs=[]; ids0=None; quads0=None; parts0=None; diag=[]
    for p in fs:
        r=subprocess.run([str(exe),str(p)],capture_output=True,text=True,encoding='utf-8',errors='strict'); assert r.returncode==0
        a=vtk(r.stdout); nodeid=a['NODE_ID'].astype(int); xyz=a['points'].reshape(-1,3); cells=a['cells'].astype(int).reshape(-1,5); assert np.all(cells[:,0]==4)
        parts=a['PART_ID'].astype(int); quads=cells[:,1:]; elid=a['ELEMENT_ID'].astype(int)
        if ids0 is None: ids0=nodeid; quads0=quads; parts0=parts
        assert np.array_equal(nodeid,ids0) and np.array_equal(quads,quads0) and np.array_equal(parts,parts0)
        initial=np.asarray(original['nodes_mm'])[nodeid-1]
        # Converter writes limited decimal precision; 0.05 mm bounds output quantization.
        consistency=float(np.max(np.abs(xyz-initial-a['Displacement'].reshape(-1,3))))
        assert consistency<0.05,consistency
        for j,e in enumerate(elid):
            assert set(nodeid[quads[j]])==set(np.asarray(original['quads'][e-1])+1)
            assert parts[j]==original['parts'][e-1]
        layer=[v for k,v in a.items() if 'Plast' in k]; ep=np.maximum.reduce(layer)
        for part in [1,2,3]: assert np.all(np.isfinite(ep[parts==part]))
        coords.append(xyz.astype('float32')); eps.append(ep.astype('float32')); ts.append(a['time']); refs.append({'file':str(p.relative_to(ROOT)),'sha256':sha(p)})
        diag.append({'time_ms':a['time'],'max_epsp_by_part':{str(part):float(ep[parts==part].max()) for part in [1,2,3]},'displacement_identity_error_mm':consistency,'min_erosion_status':float(a['EROSION_STATUS'].min()),'max_erosion_status':float(a['EROSION_STATUS'].max())})
    np.savez_compressed(d/'computed_frames.npz',points_mm=np.asarray(coords),epsp=np.asarray(eps),times_ms=ts,quads=quads0,parts=parts0,node_ids=ids0)
    summaries[case['id']]={'converted_frames':len(fs),'states':diag,'animation_sources':refs,'output':str((d/'computed_frames.npz').relative_to(ROOT))}
write_json(out/'animation_export_audit.json',{'seconds':time.perf_counter()-start,'converter':str(exe),'converter_sha256':sha(exe),'position_quantization_tolerance_mm':0.05,'cases':summaries,'physical_validation':False})
print('EXPORTED', {k:(v['converted_frames'],v['states'][-1]['max_epsp_by_part']) for k,v in summaries.items()})
