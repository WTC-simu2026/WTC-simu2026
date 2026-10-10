"""Locate A20's negative saved skin element without changing or repeating the simulation."""
from run_aircraft_a21 import *

def main():
    guard();dst=OUT/'cached_skin_negative_localization.json';assert not dst.exists();m=read(SOURCE/'mesh.json');n='A20_CORE3D_TIED_20';skin={r['id']:r for r in m['radome_skin_quads']};files=sorted(p for p in SOURCE.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name))+sorted(p for p in (SOURCE/'observer').glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name));worst=None;rows=[]
    for p in files:
        z=fast(p);ix={int(e):i for i,e in enumerate(z['eid'])};ids=np.array(list(skin));js=np.array([ix[i] for i in ids]);IE=z['scalar']['Specific Energy'][js]*z['element_mass_g'][js]*.001;negative=IE<-.001
        if negative.any():
            j=int(np.argmin(IE));eid=int(ids[j]);cell=skin[eid];nodes=np.array(cell['nodes'])-1;order=np.argsort(z['nid']);X=z['x'][order][nodes];ref=np.array(m['nodes_mm'])[nodes];area=lambda q:float((np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))+np.linalg.norm(np.cross(q[2]-q[0],q[3]-q[0])))*.5)
            record={'native_path':rel(p),'time_ms':z['time_ms'],'element_id':eid,'IE_J':float(IE[j]),'mass_g':float(z['element_mass_g'][js[j]]),'facet':cell['facet'],'side':cell['side'],'part':cell['part'],'alive':int(z['alive'][js[j]]),'nodes':cell['nodes'],'native_damage_layers':{k:float(v[js[j]]) for k,v in z['scalar'].items() if k.startswith('DAMAGE')},'initial_area_mm2':area(ref),'deformed_area_mm2':area(X),'native_node_positions_mm':X.tolist(),'negative_skin_elements_at_frame':int(negative.sum())};rows.append(record)
            if worst is None or record['IE_J']<worst['IE_J']:worst=record
    r={'created_utc':now(),'native_frames_read':len(files),'negative_frames':len(rows),'minimum_record':worst,'negative_frame_records':rows,'native_negative_IE_preserved':True,'specific_cause_proven':False,'geometry_is_diagnostic_not_proof_of_failure_mechanism':True,'native_old_solver_reruns':0,'physical_acceptance_of_negative_IE':False};dump(dst,r);print({'frames':len(files),'negative_frames':len(rows),'worst':worst},flush=True)

if __name__=='__main__':main()
