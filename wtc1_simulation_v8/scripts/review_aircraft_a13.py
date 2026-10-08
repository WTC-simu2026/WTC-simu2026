"""A13 independent saved-output audit, cumulative reactions confined to main job."""
import re,subprocess,json
from pathlib import Path
import numpy as np
from run_aircraft_a13 import ROOT,OUT,CFG,REV,allcases,guard,read,dump,sha,rel,now,RUNTIME,triangle,histories,vtk,binary_mass

def nodes(H,title,nvar,nn):
    keys=[k for k in H if k.startswith(title)];assert len(keys)==nvar*nn
    ids=[int(re.search(re.escape(title)+r'\s+(\d+)\s+',k).group(1)) for k in keys[::nvar]]
    assert sorted(ids)==list(range(1,nn+1))
    return np.column_stack([H[k] for k in keys]).reshape(len(H['time']),nn,nvar)[:,np.argsort(ids),:]

def review(c):
    d=OUT/REV/c['id'];g=read(d/'generation.json');name=g['name'];cfg=read(CFG);a=cfg['acceptance'];H=histories(d/(name+'T01.csv'));Ho=histories(d/'observer'/(name+'T02_recovered.csv'))
    T=H['time'];nn=len(g['nodes_mm']);N=nodes(H,'NATIVE_NODES',9,nn);acc=nodes(H,'ACCEL_NATIVE',6,nn)
    rn=np.array(g['radome_nodes'])-1;wn=np.array(g['fixed_nodes'])-1
    sk=[k for k in H if k.startswith('SUPPORT_NATIVE')];assert len(sk)==len(wn)*3
    assert [int(re.search(r'SUPPORT_NATIVE\s+(\d+)\s+',k).group(1)) for k in sk[::3]]==g['fixed_nodes']
    Js=np.column_stack([H[k] for k in sk]).reshape(len(T),len(wn),3).sum(1)*.001;Js-=Js[0]
    J=np.column_stack([H[k] for k in H if k.startswith('CONTACT_RAW')][:3])*.001 if c['contact'] else np.zeros((len(T),3));J-=J[0]
    P=np.column_stack([H[q+'-MOMENTUM'] for q in 'XYZ'])*.001
    terms={k:H[k]*.001 for k in cfg['energy_contract']['ledger']};E=sum(terms.values());res=E-E[0]-H['EXTERNAL WORK']*.001;generated=sum(v for k,v in terms.items() if k!='KINETIC ENERGY')
    final_terms={k:float(Ho[k][0])*.001 for k in terms};finalgen=sum(v for k,v in final_terms.items() if k!='KINETIC ENERGY');finalres=sum(final_terms.values())-E[0]-float(Ho['EXTERNAL WORK'][0])*.001
    fullG=np.r_[generated,finalgen];fullR=np.r_[res,finalres];active=fullG>a['local_generated_min_J']
    animations=sorted([p for p in d.glob(name+'A*') if re.fullmatch(re.escape(name)+r'A\d{3}',p.name)])
    assert animations
    times=[];D=[];V=[];m=None;proofs=[];top=None
    for p in animations:
        q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=60).stdout)
        ix=np.argsort(q['NODE_ID']);assert np.array_equal(q['NODE_ID'][ix],np.arange(1,nn+1));nm,pr=binary_mass(p,q)
        if m is None:m=nm
        else:assert np.array_equal(m,nm)
        snap={k:q[k] for k in ['ELEMENT_ID','PART_ID','cells','types']}
        if top is None:top=snap
        else:assert all(np.array_equal(top[k],snap[k]) for k in top)
        times.append(q['time']);D.append(q['Displacement'].reshape(-1,3)[ix]*.001);V.append(q['Velocity'].reshape(-1,3)[ix]);proofs.append({'path':rel(p),**pr})
    K=.5*np.sum(m[None,:,None]*N[:,:,3:6]**2,axis=(1,2));PN=np.sum(m[None,:,None]*N[:,:,3:6],axis=1)
    Kerr=(K-K[0])-(terms['KINETIC ENERGY']-terms['KINETIC ENERGY'][0]);Perr=(PN-PN[0])-(P-P[0]);ptol=a['momentum_absolute_Ns']+a['momentum_relative']*float(np.max(np.linalg.norm(J,axis=1)))
    supporterr=float(np.max(np.linalg.norm(P-P[0]-Js,axis=1)));contacterr=float(np.max(np.linalg.norm(J+Js,axis=1)))
    contactopposite=float(np.max(np.linalg.norm(J-Js,axis=1)))
    rotI=np.zeros(nn)
    for tr in g['triangles']:
        ix=np.array(tr)-1;ar,w=triangle(np.array(g['nodes_mm'])[ix]);mf=0.;position=-4.5
        for th,rho in [(.5,.00183),(8,.000048),(.5,.00183)]:
            for weight in [5/9,8/9,5/9]:
                dt=th*weight/2;zz=position+dt/2;mf+=rho*dt*(ar/4.5+dt*dt/12+zz*zz);position+=dt
        rotI[ix]+=ar*mf*w*1e-9
    inertia=None
    if not c['witness']:
        cg=(m[rn,None]*np.array(g['nodes_mm'])[rn]*.001).sum(0)/m[rn].sum();rx=np.array(g['nodes_mm'])[rn]*.001-cg
        lever=sum(mass*(float(v@v)*np.eye(3)-np.outer(v,v)) for mass,v in zip(m[rn],rx));pred=lever+np.eye(3)*rotI.sum()
        txt=(d/(name+'_0000.out')).read_text(errors='replace');match=re.search(r'PART\s*:\s*21,.*?\n\s*Mass.*?\n([^\n]+)\n\s*X.*?\n([^\n]+)',txt,re.S);assert match
        ni=np.fromstring(match.group(1),sep=' ');assert len(ni)==7;v=ni[1:]*1e-9;nat=np.array([[v[0],v[3],v[5]],[v[3],v[1],v[4]],[v[5],v[4],v[2]]]);err=float(np.max(abs(nat-pred)))/float(np.max(abs(nat)))
        inertia={'native_tensor_kg_m2':nat.tolist(),'C0_predicted_tensor_kg_m2':pred.tolist(),'C0_algorithm_relative_error':err,'C0_formula_applicable':c['Ish3n']==2,'initial_C0_inertia_consistent':err<=1e-6 if c['Ish3n']==2 else None,'source_binary_equivalence_established':False,'dynamic_RKE_qualified':False}
    timing=[]
    for factor in cfg['timing_diagnostic']['candidates']:
        vel=N[:,:,3:6]+factor*H['TIME STEP'][:,None,None]*acc[:,:,:3]
        omega=(N[:,:,6:9]+factor*H['TIME STEP'][:,None,None]*acc[:,:,3:6])*1000
        kc=.5*np.sum(m[None,:,None]*vel*vel,axis=(1,2));pc=np.sum(m[None,:,None]*vel,axis=1);rc=.5*np.sum(rotI[None,:,None]*omega*omega,axis=(1,2))
        timing.append({'factor':factor,'max_KE_change_difference_J':float(np.max(abs((kc-kc[0])-(terms['KINETIC ENERGY']-terms['KINETIC ENERGY'][0])))),'max_momentum_change_difference_Ns':float(np.max(np.linalg.norm((pc-pc[0])-(P-P[0]),axis=1))),'max_C0_RKE_difference_J':float(np.max(abs(rc-terms['ROTATION ENERGY']))),'no_acceptance_credit':True,'ledger_unchanged':True})
    masserr=abs(float(m[rn].sum())-g['radome_analytic_mass_kg'])/g['radome_analytic_mass_kg']
    checks={'native_CSV_all_channels_verified':read(d/'history_recovery.json')['pass'],'starter_zero_errors_warnings':True,'normal_engine_termination':'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace').upper(),'observer_outputs_preserved':read(d/'observer_preservation.json')['pass'],'finite_monotone_history':bool(np.all(np.isfinite(np.column_stack(list(H.values())))) and np.all(np.diff(T)>0)),'analytic_mass':masserr<=a['mass_relative'],'mass_constant':float(np.max(abs(H['MASS']-H['MASS'][0])))<=a['mass_relative']*float(H['MASS'][0]),'zero_added_mass':float(np.max(abs(H['ADDED MASS'])))<=a['added_mass_fraction']*float(H['MASS'][0]),'supports_fixed':float(np.max(abs(N[:,wn,:])))<=1e-10,'no_external_work':float(np.max(abs(H['EXTERNAL WORK'])))<=1e-8,'no_plastic_work':float(np.max(abs(H['PLASTIC WORK'])))<=1e-8,'zero_spring':float(np.max(abs(terms['SPRING ENERGY'])))<=1e-8,'energy_global':float(np.max(abs(fullR)))<=a['energy_global_fraction_initial']*E[0],'energy_local':bool(np.all(abs(fullR[active])<=a['energy_local_fraction_generated']*abs(fullG[active])+a['energy_precision_J'])),'momentum_support':supporterr<=ptol,'momentum_contact_support':contacterr<=ptol,'independent_translation_KE_change':float(np.max(abs(Kerr)))<=a['independent_KE_change_absolute_J']+a['independent_KE_change_fraction_generated']*float(np.max(abs(generated))),'independent_momentum_change':float(np.max(np.linalg.norm(Perr,axis=1)))<=ptol}
    if c['witness']:
        w=cfg['witness'];wa=cfg['witness_acceptance'];P0=w['initial_P_Ns'];KE0=w['initial_KE_J']
        checks['energy_global']=float(np.max(abs(fullR)))<=wa['energy_fraction_initial']*KE0
        checks['momentum_support']=supporterr<=wa['support_fraction_initial']*P0
        checks['momentum_contact_support']=min(contacterr,contactopposite)<=wa['momentum_fraction_initial']*P0
        checks['initial_KE_analytic']=abs(E[0]-KE0)/KE0<1e-5
        checks['rebound_or_free_velocity']=float(np.max(abs(N[-1,rn,3]-(-200 if c['contact'] else 200))))<=(wa['rebound_velocity_fraction']*200 if c['contact'] else wa['free_velocity_m_s'])
        # Global witness gate (1% initial energy) is authoritative; radome local gate has no active points.
    onset=np.flatnonzero(np.linalg.norm(J,axis=1)>0)
    r={'case':c,'created_utc':now(),'checks':{k:bool(v) for k,v in checks.items()},'all_checks_pass':all(checks.values()),'failed_checks':[k for k,v in checks.items() if not v],'main_last_time_ms':float(T[-1]),'actual_end_ms':float(Ho['time'][0]),'onset_ms':float(T[onset[0]]) if len(onset) else None,'mass_kg':float(m[rn].sum()),'initial_KE_J':float(E[0]),'final_impulse_Ns':J[-1].tolist(),'final_generated_J':finalgen,'final_energy_residual_J':finalres,'max_energy_residual_J':float(np.max(abs(fullR))),'max_local_residual_fraction':float(np.max(abs(fullR[active])/fullG[active])) if np.any(active) else None,'main_support_residual_Ns':supporterr,'main_contact_support_residual_Ns':contacterr,'opposite_contact_support_residual_Ns':contactopposite,'max_dense_KE_change_error_J':float(np.max(abs(Kerr))),'max_dense_momentum_error_Ns':float(np.max(np.linalg.norm(Perr,axis=1))),'final_velocity_m_s':N[-1,rn,3:6].mean(0).tolist(),'timing_candidates':timing,'native_initial_inertia':inertia,'observer_REAC_endpoint_used_for_acceptance':False,'main_native_reactions_not_integrated':True,'physical_impact_qualified':False,'whole_aircraft_extension_allowed':False}
    np.savez_compressed(d/'authoritative_main_history_SI.npz',time_ms=T,residual_J=res,generated_J=generated,impulse_Ns=J,support_Ns=Js,momentum_Ns=P,dense_KE_J=K,native_KE_J=terms['KINETIC ENERGY'],native_RKE_J=terms['ROTATION ENERGY'],native_internal_J=terms['INTERNAL ENERGY'],native_contact_J=terms['ELASTIC CONTACT ENERGY'],timestep_ms=H['TIME STEP'],KE_change_error_J=Kerr,nodal_rotation_inertia_kg_m2=rotI)
    np.savez_compressed(d/'verified_states_SI.npz',time_ms=np.array(times),displacement_m=np.array(D),velocity_m_s=np.array(V),nodal_mass_kg=m,initial_position_m=np.array(g['nodes_mm'])*.001,radome_nodes=rn,fixed_nodes=wn,radome_triangles=np.array(g['triangles'])-1)
    dump(d/'native_mass_reader_proofs.json',{'proofs':proofs});dump(d/'authoritative_review.json',r)
    print({k:r[k] for k in ['case','failed_checks','final_impulse_Ns','final_generated_J','final_energy_residual_J','timing_candidates']},flush=True)
    return r

def main():
    guard();assert not (OUT/'campaign_review.json').exists();rows=[];rejected=[]
    assert all((OUT/REV/c['id']/'history_recovery.json').exists() or list((OUT/REV/c['id']).glob('retained_failure_*.json')) for c in allcases()),'Campaign still running; aggregation forbidden.'
    for c in allcases():
        d=OUT/REV/c['id']
        if not (d/'history_recovery.json').exists():rejected.append({'case':c,'retained_failures':[rel(p) for p in d.glob('retained_failure_*.json')]});continue
        rows.append(read(d/'authoritative_review.json') if (d/'authoritative_review.json').exists() else review(c))
    comparisons=[];a=read(CFG)['acceptance']
    def compare(pa,pb,kind,accept=True):
        if not pa.exists() or not pb.exists():return
        aa=np.load(pa);bb=np.load(pb);tm=min(float(aa['time_ms'][-1]),float(bb['time_ms'][-1]),.4)
        j=[np.array([np.interp(tm,q['time_ms'],q['impulse_Ns'][:,i]) for i in range(3)]) for q in [aa,bb]];e=[float(np.interp(tm,q['time_ms'],q['generated_J'])) for q in [aa,bb]]
        jd=float(np.linalg.norm(j[1]-j[0])/max(np.linalg.norm(j[0]),1e-30));ed=abs(e[1]-e[0])/max(abs(e[0]),1e-30);prefix='half_dt' if kind=='half_dt' else 'mesh'
        comparisons.append({'files':[rel(pa),rel(pb)],'type':kind,'common_time_ms':tm,'impulses_Ns':[v.tolist() for v in j],'generated_J':e,'impulse_difference_fraction':jd,'generated_difference_fraction':ed,'declared_acceptance':accept,'impulse_pass':jd<=a[prefix+'_impulse_relative'] if accept else None,'generated_pass':ed<=a[prefix+'_generated_relative'] if accept else None})
    def p(k):return OUT/REV/k/'authoritative_main_history_SI.npz'
    for typ in ['T25','DKT7']:
        for lev in range(3 if typ=='T25' else 2):compare(p(f'{typ}_L{lev}'),p(f'{typ}_L{lev+1}'),'mesh')
    compare(p('T25_L2'),p('T25_L2_HALF'),'half_dt')
    for typ in [7,25]:
        aa=np.load(p(f'W{typ}_DT050'));bb=np.load(p(f'W{typ}_DT025'));tm=min(float(aa['time_ms'][-1]),float(bb['time_ms'][-1]));j=[float(np.interp(tm,q['time_ms'],q['impulse_Ns'][:,0])) for q in [aa,bb]]
        jd=abs(j[1]-j[0])/abs(j[0]);ed=abs(float(np.max(abs(aa['residual_J'])))-float(np.max(abs(bb['residual_J']))))/read(CFG)['witness']['initial_KE_J'];wa=read(CFG)['witness_acceptance']
        comparisons.append({'cases':[f'W{typ}_DT050',f'W{typ}_DT025'],'type':'witness_half_dt','common_time_ms':tm,'impulse_difference_fraction':jd,'energy_residual_change_fraction_initial':ed,'declared_acceptance':True,'impulse_pass':jd<=wa['half_dt_impulse_relative'],'energy_pass':ed<=wa['half_dt_energy_relative_initial']})
    for old,new in [('SAND_HALF','T25_L0'),('SAND_FINE','T25_L1'),('SAND_FINE2','T25_L2'),('SAND_FINE3','T25_L3'),('SAND_HALF','DKT7_L0'),('SAND_FINE','DKT7_L1'),('SAND_FINE2','DKT7_L2')]:compare(ROOT/'wtc1_simulation_v8/output/aircraft_a12/r1'/old/'authoritative_main_history_SI.npz',p(new),'algorithm_diagnostic',False)
    integrity_keys=['native_CSV_all_channels_verified','starter_zero_errors_warnings','normal_engine_termination','observer_outputs_preserved','finite_monotone_history','analytic_mass','mass_constant','zero_added_mass','supports_fixed','no_external_work','no_plastic_work']
    integrity=all(all(r['checks'][k] for k in integrity_keys) for r in rows);assert integrity
    jobs=[read(p) for p in OUT.rglob('*.execution.json')];eng=[q for q in jobs if q['exe'].endswith('engine_win64.exe')]
    s={'iteration':'AIRCRAFT-A13','created_utc':now(),'cases':rows,'rejected_cases':rejected,'comparisons':comparisons,'integrity_only_pass':integrity,'main_engine_jobs':sum(q['args'][1].endswith('_0001.rad') for q in eng),'observer_jobs':sum(q['args'][1].endswith('_0002.rad') for q in eng),'native_wall_seconds':sum(q['seconds'] for q in jobs),'old_solver_reruns':0,'local_energy_qualified':False,'spatial_convergence_qualified':False,'dynamic_RKE_qualified':False,'physical_impact_qualified':False,'whole_aircraft_extension_allowed':False,'seconds_impact_calculated':False,'parallel_Boeing_module_integrated':False}
    s['earlier_incomplete_aggregate_retained']='authoritative_review.json; produced while solver campaign continued, superseded by campaign_review.json; not used in state or registry'
    dump(OUT/'campaign_review.json',s);print({k:v for k,v in s.items() if k not in ['cases','comparisons']},flush=True);print(json.dumps(comparisons,indent=2),flush=True)
if __name__=='__main__':main()
