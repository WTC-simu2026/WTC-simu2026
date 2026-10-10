"""Native A18 coupled histories, retained gates and actual fragment connectivity."""
import struct,subprocess
import numpy as np
from run_aircraft_a18 import *
from audit_aircraft_a05 import vtk,vm_tensor
from audit_aircraft_a03 import topology
from review_aircraft_a08 import binary_mass
from audit_aircraft_a02 import numbers_after
from review_aircraft_a15 import segments

def binary_coordinates(p):
    b=p.read_bytes();assert struct.unpack_from('>i',b,0)[0]==0x542c;flags=np.frombuffer(b,dtype='>i4',count=10,offset=251);nn,nf,npart,nfun,nefun,nvec,nten,nsk=np.frombuffer(b,dtype='>i4',count=8,offset=291).astype(int)
    assert flags[0]==1 and flags[1]==1
    return np.frombuffer(b,dtype='>f4',count=nn*3,offset=323+nsk*12).astype(float).reshape(nn,3)

def fragment_counts(m,status):
    E=m['radome_element_ids'];parent={e:e for e in E}
    def root(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    def link(a,b):parent[root(a)]=root(b)
    for seam,alive in zip(m['cohesive_seams'],status):
        if alive:link(*seam['facet_ids'])
    incident=defaultdict(list)
    for eid,t in zip(m['aircraft_triangle_ids'],m['original_triangle_node_ids']):
        if eid in parent:
            for ni in t:incident[ni].append(eid)
    for es in incident.values():
        for b in es[1:]:link(es[0],b)
    groups=defaultdict(list)
    for e in E:groups[root(e)].append(e)
    nodes=np.array(m['nodes_mm']);rooted={e for ni,es in incident.items() if nodes[ni-1,0]==2000 for e in es}
    detached=[es for es in groups.values() if not set(es)&rooted]
    return {'connected_components':len(groups),'detached_components':len(detached),'detached_facets':sum(map(len,detached)),'largest_component_facets':max(map(len,groups.values()))}

def early():
    guard();d=OUT/'r0'/CASE;g=read(d/'generation.json');m=read(d/'mesh.json');n=g['name'];p=d/(n+'A001');q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120).stdout);order=np.argsort(q['NODE_ID']);nm,proof=binary_mass(p,q);x=binary_coordinates(p)[order];v=q['Velocity'].reshape(-1,3)[order];air=np.array(m['aircraft_node_ids'])-1
    assert np.array_equal(q['NODE_ID'][order],np.arange(1,len(m['nodes_mm'])+1));assert np.allclose(x,q['points'].reshape(-1,3)[order],rtol=5e-6,atol=1e-6)
    pl=np.load(SOURCE/'verified_states_SI.npz');pm=pl['native_nodal_mass_kg'];px=pl['initial_positions_m']*1000
    masserr=float(nm.sum()-pm.sum());cg=np.sum(nm[:,None]*x,axis=0)/nm.sum();pcg=np.sum(pm[:,None]*px,axis=0)/pm.sum()
    def I(x,m):r=x-np.sum(m[:,None]*x,axis=0)/m.sum();return np.eye(3)*np.sum(m*np.sum(r*r,axis=1))-np.einsum('n,ni,nj->ij',m,r,r)
    irel=float(np.max(abs(I(x,nm)-I(px,pm)))/np.max(abs(I(px,pm))))
    mask=(q['types']==12);assert sum(mask)==len(m['cohesive_connectivity']);stress=q['3DELEM_Stress'].reshape(-1,3,3)[mask];ie=q['3DELEM_Specific_Energy'][mask];cohoff=np.array(m['cohesive_offset_map']);err=float(np.max(abs(np.linalg.norm(x[cohoff[:,1].astype(int)-1]-x[cohoff[:,0].astype(int)-1],axis=1)-cohoff[:,2])))
    r={'created_utc':now(),'native_time_ms':q['time'],'mass_kg':float(nm.sum()),'mass_difference_parent_kg':masserr,'CG_difference_parent_mm':(cg-pcg).tolist(),'inertia_relative_difference_parent':irel,'maximum_offset_distance_error_mm':err,'maximum_initial_cohesive_stress_MPa':float(np.max(abs(stress))),'maximum_initial_cohesive_specific_energy':float(np.max(abs(ie))),'initial_aircraft_velocity_max_error_m_s':float(np.max(abs(v[air]-[-200,5,2]))),'native_mass_reader_proof':proof,'checks':{'mass_relative':abs(masserr)/pm.sum()<1e-6,'CG_mm':bool(np.max(abs(cg-pcg))<.001),'inertia_relative':irel<1e-6,'zero_initial_cohesive_stress':bool(np.max(abs(stress))==0),'zero_initial_cohesive_energy':bool(np.max(abs(ie))==0),'initial_offset_distance':err<.001,'initial_velocity':bool(np.max(abs(v[air]-[-200,5,2]))<1e-5)}}
    r['checks']={k:bool(v) for k,v in r['checks'].items()};dump(d/'initial_native_review.json',r);print({k:r[k] for k in ['mass_difference_parent_kg','CG_difference_parent_mm','inertia_relative_difference_parent','checks']},flush=True)

def main():
    guard();d=OUT/'r0'/CASE;g=read(d/'generation.json');m=read(d/'mesh.json');n=g['name'];cfg=read(CFG);assert not (d/'review.json').exists();assert read(d/'history_recovery.json')['pass'];a=cfg['acceptance']
    H=histories(d/(n+'T01.csv'));Ho=histories(d/'observer'/(n+'T02_recovered.csv'));T=H['time'];S=segments(H);J=sum(S.values());J-=J[0]
    P=np.column_stack([H[z+'-MOMENTUM'] for z in 'XYZ'])*.001
    Pf=np.column_stack([sum((H[k] for k in H if k.startswith('FACADE_') and k.strip().endswith(z+'MOM')),np.zeros(len(T))) for z in 'XYZ'])*.001
    Js=np.column_stack([sum((H[k] for k in H if k.startswith('SUPPORT_IMPULSE_'+z)),np.zeros(len(T))) for z in 'XYZ'])*.001;Js-=Js[0]
    terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    E=sum(H[k] for k in terms)*.001;E0=float(E[0]);R=E-E0-H['EXTERNAL WORK']*.001;G=sum(H[k] for k in terms if k!='KINETIC ENERGY')*.001
    finalE=sum(float(Ho[k][0]) for k in terms)*.001;finalR=finalE-E0-float(Ho['EXTERNAL WORK'][0])*.001;finalG=sum(float(Ho[k][0]) for k in terms if k!='KINETIC ENERGY')*.001
    RR=np.r_[R,finalR];GG=np.r_[G,finalG];window=GG>a['local_energy_comparison_minimum_J'];mass=numbers_after((d/(n+'_0000.out')).read_text(errors='replace'),'TOTAL MASS AND MASS CENTER',4)[0]*.001
    jmax=float(np.max(np.linalg.norm(J,axis=1)));mtol=a['momentum_absolute_allowance_Ns']+a['momentum_relative_allowance']*jmax;ge=float(np.max(np.linalg.norm(P-P[0]-Js,axis=1)));fe=float(np.max(np.linalg.norm(Pf-Pf[0]-J-Js,axis=1)))
    end=float(Ho['time'][0]);step=float(Ho['TIME STEP'][0]);x0=np.array(m['nodes_mm']);air=np.array(m['aircraft_node_ids'])-1;fa=np.array(g['facade_translated_node_ids'])-1;fix=np.array(m['fixed_node_ids'])-1
    times=[];D=[];V=[];EPS=[];VM=[];STATUS=[];DM=[];rows=[];proofs=[];KE=[];PP=[];nm0=None;cellinfo=None;fixederr=0.;coorderr=0.;unchanged=True;maxeps=0.;maxratio=0.;topcheck=True;offerr=0.;shell_alive=True
    available=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name));files=[p for i,p in enumerate(available) if i%cfg['output_contract']['geometry_review_stride']==0 or i==len(available)-1]+sorted(p for p in (d/'observer').glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name))
    mp=np.array(m['cohesive_offset_map']);cnids=[s['element_id'] for s in m['cohesive_seams']]
    for p in files:
        q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120).stdout);tm=struct.unpack_from('>f',p.read_bytes(),4)[0]
        if times and abs(tm-times[-1])<1e-6:continue
        if tm>end+1e-5:continue
        assert not times or tm>times[-1];order=np.argsort(q['NODE_ID']);assert np.array_equal(q['NODE_ID'][order],np.arange(1,len(x0)+1));q['time']=tm
        u=q['Displacement'].reshape(-1,3)[order];v=q['Velocity'].reshape(-1,3)[order];nm,proof=binary_mass(p,q);bx=binary_coordinates(p)[order];assert np.allclose(bx,q['points'].reshape(-1,3)[order],rtol=5e-6,atol=1e-6);proofs.append({'time_ms':tm,'file':rel(p),**proof})
        if nm0 is None:
            nm0=nm;cells=topology(q);cellinfo={k:q[qk].astype(int) for k,qk in [('element_ids','ELEMENT_ID'),('part_ids','PART_ID'),('cell_types','types')]};index={int(e):i for i,e in enumerate(q['ELEMENT_ID']) if e>0}
            for i,t in enumerate(q['types']):
                if t==5:assert cells[i][-1]==cells[i][-2];cells[i]=cells[i][:3]
            topcheck=all(cells[index[eid]]==el for k,ei in [('original_triangle_node_ids',m['aircraft_triangle_ids']),('original_beam_node_ids',m['aircraft_beam_ids']),('facade_quads_node_ids',range(20001,20001+len(m['facade_quads_node_ids'])))] for eid,el in zip(ei,m[k])) and all(cells[index[row[0]]]==row[1:] for row in m['cohesive_connectivity'])
        else:unchanged=unchanged and np.array_equal(nm0,nm);assert np.array_equal(q['ELEMENT_ID'].astype(int),cellinfo['element_ids'])
        ci=[index[e] for e in cnids];status=q['EROSION_STATUS'][ci].astype(int);shell=(cellinfo['cell_types']==5)|(cellinfo['cell_types']==9);shell_alive=shell_alive and bool(np.all(q['EROSION_STATUS'][shell]==1))
        epkeys=[k for k in q if 'Plast_Strn_Layer_' in k];eps=np.max(np.vstack([q[k] for k in epkeys]),axis=0);rm=(cellinfo['part_ids']==21)&(cellinfo['cell_types']==5);steel=cellinfo['cell_types']==9;metal=(cellinfo['cell_types']==5)&~rm
        tensors=[q[k].reshape(-1,3,3)[rm] for k in ['2DELEM_Stress_(upper)','2DELEM_Stress_(lower)']];ev=np.concatenate([np.linalg.eigvalsh(t[:,:2,:2]).ravel() for t in tensors]);ratio=max(float(ev.max(initial=0))/cfg['sandwich']['face']['diagnostic_tension_MPa'],float((-ev).max(initial=0))/cfg['sandwich']['face']['diagnostic_compression_MPa']);maxratio=max(maxratio,ratio);maxeps=max(maxeps,float(eps.max()))
        fixederr=max(fixederr,float(np.max(abs(u[fix]))));coorderr=max(coorderr,float(np.max(abs(q['points'].reshape(-1,3)[order]-x0-u))));off=float(np.max(abs(np.linalg.norm(bx[mp[:,1].astype(int)-1]-bx[mp[:,0].astype(int)-1],axis=1)-mp[:,2])));offerr=max(offerr,off)
        assert all(np.isfinite(z).all() for z in [u,v,eps,q['2DELEM_Von_Mises'],bx]);KE.append(float(.5*np.sum(nm[:,None]*v*v)));PP.append(np.sum(nm[:,None]*v,axis=0));fc=fragment_counts(m,status)
        rows.append({'time_ms':tm,'maximum_metal_plastic_strain':float(eps[metal].max(initial=0)),'maximum_facade_plastic_strain':float(eps[steel].max(initial=0)),'radome_face_reference_strength_ratio':ratio,'maximum_facade_displacement_mm':float(np.max(np.linalg.norm(u[fa],axis=1))),'deleted_cohesive_strips':int(np.sum(status==0)),'offset_RBE2_distance_error_mm':off,**fc})
        times.append(tm);D.append(u.astype(np.float32)*.001);V.append(v.astype(np.float32));EPS.append(eps.astype(np.float32));VM.append(q['2DELEM_Von_Mises'].astype(np.float32));STATUS.append(status);DM.append(np.stack([q[k][[index[e] for e in m['radome_element_ids']]] for k in list(q) if 'DAMAGE' in k])[:3]);print({'review_state_ms':round(tm,5),'deleted_strips':int(np.sum(status==0)),'detached_components':fc['detached_components']},flush=True)
    assert len(times)>1 and abs(times[-1]-end)<1e-5;times=np.array(times);KE=np.array(KE);PP=np.array(PP);kg=np.interp(times,T,H['KINETIC ENERGY']*.001);pg=np.column_stack([np.interp(times,T,P[:,i]) for i in range(3)]);kg[-1]=float(Ho['KINETIC ENERGY'][0])*.001;pg[-1]=[float(Ho[z+'-MOMENTUM'][0])*.001 for z in 'XYZ'];dk=(KE-KE[0])-(kg-kg[0]);dp=(PP-PP[0])-(pg-pg[0])
    bk=[k for k in H if k.startswith('FORWARD_BEAM_DIAGNOSTIC')];beam=np.column_stack([H[k] for k in bk]).reshape(len(T),len(g['beam_history_ids']),9);beps=float(beam[:,:,8].max());cohkeys=[k for k in H if k.startswith('RADOME_EDGE_COHESIVE ')];assert len(cohkeys)==4;cohh={k.strip().split()[-1]:H[k] for k in cohkeys};cohIE=cohh['IE']*.001
    checks={'native_binary_CSV':True,'normal_termination':'NORMAL TERMINATION' in (d/'engine.log').read_text(),'requested_horizon_reached':end>=20 and end-20<=a['final_timestamp_overshoot_native_step_factor']*step,'declared_connectivity':topcheck,'finite_states':True,'all_supports_fixed':fixederr<1e-8,'native_mass_expected':abs(mass-m['expected_total_mass_kg'])/mass<a['mass_relative_error'],'independent_native_mass_matches':abs(nm0.sum()-mass)/mass<a['mass_relative_error'],'native_nodal_mass_unchanged':unchanged,'no_added_mass':float(np.max(abs(H['ADDED MASS'])))/(mass*1000)<a['added_mass_fraction'],'mass_bearing_shells_not_deleted':shell_alive,'no_external_work':bool(np.all(H['EXTERNAL WORK']==0)),'global_energy':np.max(abs(RR))/E0<a['global_energy_residual_initial_KE_fraction'],'local_energy':bool(np.all(abs(RR[window])<=a['local_energy_residual_generated_energy_fraction']*GG[window]+a['CSV_KE_precision_allowance_J'])),'global_support_momentum':ge<=mtol,'contact_facade_momentum':fe<=mtol,'metal_material_domain':maxeps<=a['metal_plastic_strain_diagnostic_limit'],'beam_material_domain':beps<=a['metal_plastic_strain_diagnostic_limit'],'radome_face_reference_domain':maxratio<=1,'independent_translation_delta_KE':np.max(abs(dk))<=cfg['acceptance_extra']['independent_nodal_translation_KE_fraction_of_initial']*E0,'independent_momentum':np.max(np.linalg.norm(dp,axis=1))<=cfg['acceptance_extra']['independent_nodal_momentum_absolute_Ns']+cfg['acceptance_extra']['independent_nodal_momentum_relative']*jmax,'initial_native_gate':all(read(d/'initial_native_review.json')['checks'].values()),'offset_rotation_distance_tolerance':offerr<cfg['insertion_acceptance']['offset_RBE2_distance_error_mm'],'zero_warning_gate':read(d/'starter_gate.json')['pass'],'cohesive_part_history_present':True,'zero_initial_cohesive_IE':abs(cohIE[0])<.001,'cohesive_IE_nonnegative':bool(cohIE.min()>-.001)}
    checks['cohesive_expected_nine_channels']=len(cohkeys)==9
    contact_active=np.linalg.norm(J,axis=1)>0;first=int(np.flatnonzero(contact_active)[0]);precontact_G=float(np.max(abs(G[:first]-G[0])));checks['no_generated_energy_before_external_contact']=precontact_G<cfg['insertion_acceptance']['no_initial_contact_work_J']
    r={'created_utc':now(),'iteration':'AIRCRAFT-A18','case':g['case'],'checks':{k:bool(v) for k,v in checks.items()},'failed_checks':[k for k,v in checks.items() if not v],'all_declared_checks_pass':all(checks.values()),'end_ms':end,'total_mass_kg':mass,'initial_KE_J':E0,'final_generated_energy_J':finalG,'final_energy_residual_J':finalR,'maximum_energy_residual_J':float(np.max(abs(RR))),'maximum_local_residual_fraction':float(np.max(abs(RR[window])/GG[window])),'final_cohesive_part_IE_J':float(Ho[next(k for k in cohkeys if k.strip().endswith(' IE'))][0])*.001,'maximum_facade_displacement_mm':max(z['maximum_facade_displacement_mm'] for z in rows),'maximum_metal_plastic_strain':maxeps,'maximum_beam_plastic_strain':beps,'maximum_radome_strength_ratio':maxratio,'maximum_RBE2_offset_distance_error_mm':offerr,'global_support_momentum_error_Ns':ge,'facade_contact_momentum_error_Ns':fe,'native_coordinate_rounding_error_mm':coorderr,'final_contact_impulse_main_Ns':J[-1].tolist(),'final_fragment_connectivity':{k:rows[-1][k] for k in ['deleted_cohesive_strips','connected_components','detached_components','detached_facets','largest_component_facets']},'native_history_rows':len(T),'verified_geometry_states':len(times),'precontact_maximum_generated_energy_J':precontact_G,'first_external_contact_history_ms':float(T[first]),'state_diagnostics':rows,'physical_impact_qualified':False,'physical_G_measured':False,'spatial_convergence_qualified':False,'objective1_complete':False,'NIST_outcomes_used_as_target':False,'observer_impulses_excluded':True,'cohesive_IE_included_once_in_native_global_IE':True}
    np.savez_compressed(d/'verified_states_SI.npz',time_s=times*.001,node_ids=np.arange(1,len(x0)+1),initial_positions_m=x0*.001,displacement_m=np.array(D),velocity_m_s=np.array(V),shell_max_layer_plastic_strain=np.array(EPS),shell_von_mises_mean_MPa=np.array(VM),native_nodal_mass_kg=nm0,cohesive_element_ids=cnids,cohesive_alive=np.array(STATUS),**cellinfo)
    np.savez_compressed(d/'native_radome_damage.npz',time_s=times*.001,element_ids=m['radome_element_ids'],skin_core_skin_damage=np.array(DM))
    np.savez_compressed(d/'balance_history_SI.npz',time_s=T*.001,contact_impulse_Ns=J,global_momentum_Ns=P,facade_momentum_Ns=Pf,support_Ns=Js,energy_residual_J=R,generated_energy_J=G,cohesive_part_IE_J=cohIE)
    dump(d/'native_mass_reader_proofs.json',{'samples':proofs});dump(d/'review.json',r);dump(OUT/'campaign_review.json',{'created_utc':now(),'cases':[r],'all_declared_checks_pass':r['all_declared_checks_pass'],'physical_impact_qualified':False,'objective1_complete':False,'old_failed_gates_retained':True,'old_solver_reruns':0})
    print({k:r[k] for k in ['end_ms','failed_checks','final_fragment_connectivity','final_energy_residual_J']},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['early','main']);globals()[p.parse_args().action]()
