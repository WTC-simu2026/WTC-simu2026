"""Supplement cached native histories with full four-point gap work, including nonuniform motion."""
from control_aircraft_a67_current_area import ROOT,OUT,CONTROL,read,dump,now
from surface_iteration_aircraft_a61_r1 import shape
import numpy as np,json

def main():
    assert not (OUT/'quadrature_work_review.json').exists()
    cfg=read(CONTROL);base=read(OUT/'current_area_mechanical_review.json');rows=[]
    for c,r in zip(cfg['cases'],base['cases']):
        assert c['id']==r['case']
        z=np.load(OUT/'native'/c['id']/'mechanical_diagnostics.npz')
        U=z['displacement_mm'];nodes=np.asarray(c['nodes_mm']);mid=(nodes[None,:4]+U[:,:4]+nodes[None,4:]+U[:,4:])/2
        normal=np.cross(mid[:,1]+mid[:,2]-mid[:,0]-mid[:,3],mid[:,2]+mid[:,3]-mid[:,0]-mid[:,1]);normal/=np.linalg.norm(normal,axis=1)[:,None]
        gap=np.einsum('pa,taj->tpj',shape(),U[:,4:]-U[:,:4]);normal_gap=np.einsum('tpj,tj->tp',gap,normal)
        p=cfg['cohesive'];traction=p['ET_N_mm3']*gap+(p['EN_N_mm3']-p['ET_N_mm3'])*normal_gap[:,:,None]*normal[:,None,:]
        weighted=traction*z['current_GP_area_mm2'][:,:,None]
        increment=np.einsum('tpj,tpj->t',.5*(weighted[1:]+weighted[:-1]),np.diff(gap,axis=0))*.001
        work=np.r_[0,np.cumsum(increment)];error=float(abs(work-z['native_IE_J']).max())
        rows.append({'case':c['id'],'full_GP_gap_work_difference_J':error,'unchanged_energy_tolerance_J':r['energy_tolerance_J'],
            'pass':error<=r['energy_tolerance_J'],'earlier_mean_gap_diagnostic_preserved':True,
            'nonuniform_motion_quadrature_not_replaced_by_mean_gap':True,'source_scope':r['scope']})
        np.savez_compressed(OUT/'native'/c['id']/'quadrature_work.npz',work_J=work,native_IE_J=z['native_IE_J'])
    dump(OUT/'quadrature_work_review.json',{'created_utc':now(),'cases':rows,'pass':all(r['pass'] for r in rows),
        'read_only_cached_native_analysis':True,'new_native':0,'whole_credit_s':0,
        'large_rotation_damage_or_exact_Jacobian_not_qualified':True})
    print(json.dumps({'full_quadrature_work':rows}),flush=True)

if __name__=='__main__':main()
