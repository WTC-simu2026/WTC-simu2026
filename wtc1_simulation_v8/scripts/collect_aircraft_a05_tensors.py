"""Retain signed composite tensors and verify the nose-only geometry changes."""
import subprocess,re
import numpy as np
from collections import Counter
from run_aircraft_a05 import ROOT,OUT,CFG,RUNTIME,read,dump,sha,rel,now
from audit_aircraft_a04 import vtk

def main():
    paths={k:OUT/v for k,v in read(OUT/'case_selection.json')['case_directories'].items()};proof=[]
    old=read(ROOT/read(CFG)['input_mesh']);xold=np.array(old['nodes_mm']);root=read(CFG)['nose']['root_X_mm']
    for cid,d in paths.items():
        g=read(d/'generation.json');m=read(d/'mesh.json');x=np.array(m['nodes_mm']);r=read(d/'audit.json');name=g['name'];rad=set(m['radome_element_ids']);tris=dict(zip(m['aircraft_triangle_ids'],m['original_triangle_node_ids']))
        outside=xold[:,0]>=root;outside_delta=float(np.max(abs(x[:len(xold)][outside]-xold[outside])));assert outside_delta<1e-7
        ec=Counter(tuple(sorted([el[i],el[(i+1)%3]])) for eid in rad for el in [tris[eid]] for i in range(3));boundary=[e for e,n in ec.items() if n==1]
        assert len(boundary)==24 and max(ec.values())==2 and all(x[a-1,0]==root and x[b-1,0]==root for a,b in boundary)
        area=np.array([np.linalg.norm(np.cross(x[el[1]-1]-x[el[0]-1],x[el[2]-1]-x[el[0]-1]))*.5 for eid in sorted(rad) for el in [tris[eid]]]);assert np.all(area>0)
        items=[];row={'case':cid,'outside_nose_nodes_unchanged_within_1e_minus7_mm':True,'maximum_outside_nose_difference_mm':outside_delta,'root_roundoff_allowance_mm':1e-7,'radome_interior_conforming_and_boundary_shared':True,'minimum_initial_radome_triangle_area_mm2':float(area.min()),'radome_elements':len(rad)}
        if g['case']['composite']:
            tt=[];data={k:[] for k in ['2DELEM_Stress_(upper)','2DELEM_Stress_(lower)','2DELEM_Strain_(upper)','2DELEM_Strain_(lower)','2DELEM_Stress_(layer__2)_','2DELEM_Strain_(layer__2)_']};eid=None
            anim=[p for folder in [d,d/'observer'] for p in folder.glob(name+'A*') if re.fullmatch(re.escape(name)+r'A\d{3}',p.name)]
            for p in anim:
                q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=90).stdout);tm=q['time']
                if tm>r['last_history_time_ms']+1e-5 or (tt and abs(tm-tt[-1])<1e-6):continue
                mask=(q['PART_ID']==21)&(q['ELEMENT_ID']>0);ids=q['ELEMENT_ID'][mask].astype(int);order=np.argsort(ids)
                if eid is None:eid=ids[order];assert set(eid)==rad
                else:assert np.array_equal(eid,ids[order])
                tt.append(tm)
                for k in data:data[k].append(q[k].reshape(-1,3,3)[mask][order].astype(np.float32))
                items.append({'path':rel(p),'sha256':sha(p)})
            dst=d/'composite_signed_tensors.npz';assert not dst.exists();np.savez_compressed(dst,time_s=np.array(tt)*.001,element_ids=eid,**{k:np.array(v) for k,v in data.items()})
            z=np.load(dst);assert all(np.all(np.isfinite(z[k])) for k in z.files)
            row.update(tensor_file=rel(dst),tensor_sha256=sha(dst),states=len(tt),stress_units='MPa',strain_units='dimensionless',basis='native elemental, not orthotropy directions',upper_lower='extreme ply integration stress points; native strain extrapolation; not exterior face measured strain',layer2='mean through core layer; normal crush not represented',no_core_shear_strength_validation=True,native_animations=items)
        proof.append(row)
    dump(OUT/'saved_tensor_and_geometry_review.json',{'created_utc':now(),'pass':True,'cases':proof,'new_solver_jobs':0,'native_sources_unmodified':True,'no_historical_radome_claim':True});print({'geometry_and_signed_tensors_pass':True,'cases':len(proof)})

if __name__=='__main__':main()
