"""Saved A14 plate outputs: independent mass, native ledgers, analytic rebound."""
import json,re,subprocess,math
import numpy as np
from run_aircraft_a14 import ROOT,OUT,CFG,REV,read,dump,now,guard,allcases,RUNTIME,histories,rel
from review_aircraft_a08 import binary_mass
from audit_aircraft_a05 import vtk

def array(H,title,nvar,ids):
    keys=[k for k in H if k.startswith(title)];assert len(keys)==nvar*len(ids)
    actual=[int(re.search(re.escape(title)+r'\s+(\d+)\s+',k).group(1)) for k in keys[::nvar]];assert actual==ids
    return np.column_stack([H[k] for k in keys]).reshape(len(H['time']),len(ids),nvar)

def review(c):
    cfg=read(CFG);a=cfg['acceptance'];d=OUT/REV/c['id'];g=read(d/'generation.json');name=g['name'];assert not (d/'review.json').exists();H=histories(d/(name+'T01.csv'));Ho=histories(d/'observer'/(name+'T02_recovered.csv'));T=H['time'];nn=len(g['nodes_mm']);N=array(H,'NATIVE_NODES',9,list(range(1,nn+1)));A=array(H,'ACCEL_NATIVE',6,list(range(1,nn+1)));rn=np.array(g['moving_nodes'])-1;wn=np.array(g['fixed_nodes'])-1
    S=array(H,'SUPPORT_NATIVE',3,g['fixed_nodes']);Js=S.sum(1)*.001;Js-=Js[0]
    ck=[k for k in H if k.startswith('CONTACT_RAW')];nc=len(g['contact_groups']);assert len(ck)==4*nc
    C=np.column_stack([H[k] for k in ck]).reshape(len(T),nc,4) if nc else np.zeros((len(T),0,4));J=C[:,:,:3].sum(1)*.001;J-=J[0];P=np.column_stack([H[z+'-MOMENTUM'] for z in 'XYZ'])*.001
    terms={k:H[k]*.001 for k in cfg['energy_contract']['ledger']};E=sum(terms.values());res=E-E[0]-H['EXTERNAL WORK']*.001;finalE=sum(float(Ho[k][0])*.001 for k in terms);fullres=np.r_[res,finalE-E[0]-float(Ho['EXTERNAL WORK'][0])*.001];contact=terms['ELASTIC CONTACT ENERGY'];KE0=22.24;P0=.2224
    p=d/(name+'A001');q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=60).stdout);ix=np.argsort(q['NODE_ID']);assert np.array_equal(q['NODE_ID'][ix],np.arange(1,nn+1));m,proof=binary_mass(p,q)
    masserr=abs(float(m[rn].sum())-.001112)/.001112;expected=np.array(g['nodal_tributary_area_mm2'])*.00278*.001;nodalmasserr=float(np.max(abs(m[rn]-expected[rn])))/float(np.max(expected[rn]))
    step=H['TIME STEP'];phases=[]
    for f in [0,-.5,.5]:
        V=N[:,:,3:6]+f*step[:,None,None]*A[:,:,:3];K=.5*np.sum(m[None,:,None]*V*V,axis=(1,2));PN=np.sum(m[None,:,None]*V,axis=1);phases.append({'factor':f,'max_KE_change_error_J':float(np.max(abs((K-K[0])-(terms['KINETIC ENERGY']-terms['KINETIC ENERGY'][0])))),'max_momentum_change_error_Ns':float(np.max(np.linalg.norm((PN-PN[0])-(P-P[0]),axis=1))),'ledger_unchanged':True,'binary_source_equivalence_established':False})
    flags=[int(x) for x in re.findall(r'CONTACT TYPES.*?\s(\d+)\s*$',(d/(name+'_0000.out')).read_text(errors='replace'),re.M)];assert not c['contact'] or flags and all(v==g['contact_surface_flag_expected'] for v in flags)
    checks={'native_binary_CSV':read(d/'history_recovery.json')['pass'],'normal_engine_termination':'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace').upper(),'starter_zero_errors_warnings':True,'native_contact_mode_matches_declaration':not c['contact'] or all(v==g['contact_surface_flag_expected'] for v in flags),'finite_monotone':bool(np.isfinite(np.column_stack(list(H.values()))).all() and (np.diff(T)>0).all()),'analytic_mass':masserr<=a['mass_relative'],'nodal_mass_matches_area':nodalmasserr<=a['mass_relative'],'mass_constant':float(np.max(abs(H['MASS']-H['MASS'][0])))<=a['mass_relative']*float(H['MASS'][0]),'zero_added_mass':float(np.max(abs(H['ADDED MASS'])))<=a['added_mass_fraction']*float(H['MASS'][0]),'supports_fixed':float(np.max(abs(N[:,wn,:])))<=1e-10,'no_external_work':float(np.max(abs(H['EXTERNAL WORK'])))<=1e-8,'no_plastic_work':float(np.max(abs(H['PLASTIC WORK'])))<=1e-8,'energy_global':float(np.max(abs(fullres)))<=a['energy_fraction_initial']*KE0,'momentum_support':float(np.max(np.linalg.norm(P-P[0]-Js,axis=1)))<=a['support_fraction_initial']*P0,'momentum_contact':float(np.max(np.linalg.norm(P-P[0]+J,axis=1)))<=a['momentum_fraction_initial']*P0,'contact_support':float(np.max(np.linalg.norm(J+Js,axis=1)))<=a['support_fraction_initial']*P0,'native_rotation_zero':float(np.max(abs(terms['ROTATION ENERGY'])))<=1e-10}
    active=np.flatnonzero(contact>1e-6);duration=None;pred_duration=None;penetration=None;refpen=None;curve_err=None;law_err=None;effective_plane=None;measuredK=None
    if c['contact']:
        checks['complete_rebound_impulse']=abs(float(J[-1,0])-.4448)/.4448<=a['momentum_fraction_initial'];checks['rebound_velocity']=float(np.max(abs(N[-1,rn,3]+200)))/200<=a['rebound_velocity_fraction']
        t0=(abs(c.get('start_x_mm',-5))-(.5 if c.get('legacy_surface_mode') else 1))/200
        if len(active):duration=float(T[active[-1]]-T[active[0]]+np.median(step[active]));pred_duration=math.pi*math.sqrt(1.112/g['K_total_expected_N_mm'])
        if c['weighting']=='area' or c['n']==1:
            # Closed reference of uniform plate motion. Coarse finite-step differences stay failed.
            Ktotal=g['K_total_expected_N_mm'];omega=math.sqrt(Ktotal/1.112);refpen=200/omega;dx=np.average(N[:,rn,0],axis=1,weights=m[rn]);entry=abs(c.get('start_x_mm',-5))-(.5 if c.get('legacy_surface_mode') else 1);penetration=float(np.max(dx-entry))
            tau=T-t0;ref=np.where((tau>=0)&(tau<=math.pi/omega),KE0*np.sin(omega*tau)**2,0);curve_err=float(np.max(abs(contact-ref)))/KE0
            delta=np.maximum(N[:,rn,0]-entry,0);kv=np.zeros(nn)
            for row in g['contact_groups']:kv[np.array(row['nodes'])-1]=35000*row['Stfac']
            reconstructed=.5*np.sum(kv[rn][None,:]*delta**2,axis=1)*.001;law_err=float(np.max(abs(reconstructed-contact)))/KE0
            checks['analytic_contact_duration']=duration is not None and abs(duration-pred_duration)/pred_duration<=a['contact_duration_fraction'];checks['analytic_peak_penetration']=abs(penetration-refpen)/refpen<=a['peak_penetration_fraction'];checks['contact_energy_law']=law_err<=a['contact_energy_law_fraction_initial']
            peak=int(np.argmax(contact));sample=(contact>1)&(np.arange(len(T))<peak)
            if np.sum(sample)>3:
                slope,intercept=np.polyfit(dx[sample],np.sqrt(contact[sample]),1);effective_plane=float(c.get('start_x_mm',-5)-intercept/slope);measuredK=float(2*slope*slope/.001)
        if c['weighting']=='area':checks['weighted_velocity_uniformity']=float(np.max(np.ptp(N[:,rn,3],axis=1)))/200<=a['area_weighted_velocity_uniformity_fraction']
    else:checks['free_velocity']=float(np.max(abs(N[:,rn,3:6]-[200,0,0])))<=a['free_velocity_m_s']
    r={'case':c,'created_utc':now(),'checks':{k:bool(v) for k,v in checks.items()},'all_checks_pass':all(checks.values()),'failed_checks':[k for k,v in checks.items() if not v],'mass_kg':float(m[rn].sum()),'analytic_mass_error_fraction':masserr,'nodal_mass_error_fraction':nodalmasserr,'actual_end_ms':float(Ho['time'][0]),'final_impulse_Ns':J[-1].tolist(),'initial_KE_J':float(E[0]),'maximum_energy_residual_J':float(np.max(abs(fullres))),'final_energy_residual_J':float(fullres[-1]),'onset_ms':float(T[active[0]]) if len(active) else None,'contact_duration_ms':duration,'analytic_uniform_contact_duration_ms':pred_duration,'peak_penetration_mm':penetration,'analytic_peak_penetration_mm':refpen,'maximum_analytic_contact_curve_error_fraction_initial':curve_err,'maximum_contact_energy_law_error_fraction_initial':law_err,'effective_contact_plane_from_saved_energy_fit_mm_diagnostic':effective_plane,'aggregate_stiffness_from_energy_fit_N_mm_diagnostic':measuredK,'aggregate_stiffness_expected_N_mm':g['K_total_expected_N_mm'],'phase_candidates':phases,'observed_native_contact_modes':sorted(set(flags)),'raw_velocities_not_reclassified':True,'observer_REAC_used_for_acceptance':False,'physical_impact_qualified':False}
    np.savez_compressed(d/'balance_history_SI.npz',time_ms=T,residual_J=res,impulse_Ns=J,momentum_Ns=P,support_Ns=Js,contact_J=contact,native_KE_J=terms['KINETIC ENERGY'],native_IE_J=terms['INTERNAL ENERGY'],mean_DX_mm=np.average(N[:,rn,0],axis=1,weights=m[rn]),velocity_spread_m_s=np.ptp(N[:,rn,3],axis=1),timestep_ms=step)
    dump(d/'native_mass_reader_proof.json',proof);dump(d/'review.json',r);print({'case':c['id'],'failed':r['failed_checks'],'duration_ms':duration,'K_total':g['K_total_expected_N_mm'],'residual_J':r['maximum_energy_residual_J']},flush=True);return r

def main():
    guard();assert not (OUT/'plate_review.json').exists();assert all((OUT/REV/c['id']/'history_recovery.json').exists() or list((OUT/REV/c['id']).glob('retained_failure_*.json')) for c in allcases())
    rows=[];rejected=[]
    for c in allcases():
        d=OUT/REV/c['id']
        if not (d/'history_recovery.json').exists():rejected.append(c);continue
        rows.append(read(d/'review.json') if (d/'review.json').exists() else review(c))
    comp=[];a=read(CFG)['acceptance']
    def compare(aa,bb,kind):
        x=np.load(OUT/REV/aa/'balance_history_SI.npz');y=np.load(OUT/REV/bb/'balance_history_SI.npz');tm=min(float(x['time_ms'][-1]),float(y['time_ms'][-1]));t=x['time_ms'][x['time_ms']<=tm];ex=x['contact_J'][:len(t)];ey=np.interp(t,y['time_ms'],y['contact_J']);j=[float(np.interp(tm,z['time_ms'],z['impulse_Ns'][:,0])) for z in [x,y]];jd=abs(j[1]-j[0])/max(abs(j[0]),1e-30);ed=float(np.max(abs(ex-ey)))/22.24;ra=next(r for r in rows if r['case']['id']==aa);rb=next(r for r in rows if r['case']['id']==bb);dd=abs(rb['contact_duration_ms']-ra['contact_duration_ms'])/ra['contact_duration_ms']
        comp.append({'cases':[aa,bb],'kind':kind,'time_ms':tm,'impulse_difference_fraction':jd,'contact_duration_difference_fraction':dd,'contact_energy_curve_difference_fraction_initial':ed,'impulse_pass':jd<=a['half_dt_impulse_fraction' if kind=='half_dt' else 'mesh_impulse_fraction'],'duration_pass':dd<=a['mesh_duration_fraction'],'energy_curve_pass':ed<=a['mesh_contact_energy_curve_fraction_initial']})
    for label in ['RAW','AREA']:
        for n1,n2 in [(1,2),(2,4),(4,8)]:compare(f'{label}_N{n1}',f'{label}_N{n2}','secondary_mesh')
    for b,k in [('AREA_N8_HALF','half_dt')]:compare('AREA_N8',b,k)
    for b in ['AREA_N4_MAIN3','AREA_N4_MAIN4']:compare('AREA_N4',b,'main_mesh')
    for lab in ['SOFT','STIFF']:compare(f'AREA_{lab}_N4',f'AREA_{lab}_N8','secondary_mesh_sensitivity')
    required=['native_binary_CSV','normal_engine_termination','starter_zero_errors_warnings','native_contact_mode_matches_declaration','finite_monotone','analytic_mass','nodal_mass_matches_area','mass_constant','zero_added_mass','supports_fixed','no_external_work','no_plastic_work'];integrity=not rejected and all(all(r['checks'][k] for k in required) for r in rows);assert integrity
    selected=[r for r in rows if r['case']['weighting']=='area'];core=['energy_global','momentum_contact','momentum_support','contact_support','complete_rebound_impulse','rebound_velocity','weighted_velocity_uniformity'];numerical_plate_ready=all(all(r['checks'][k] for k in core) for r in selected) and all(q['impulse_pass'] and q['duration_pass'] and q['energy_curve_pass'] for q in comp if not q['cases'][0].startswith('RAW'))
    s={'iteration':'AIRCRAFT-A14','created_utc':now(),'cases':rows,'comparisons':comp,'rejected_cases':rejected,'integrity_only_pass':integrity,'area_weighted_core_and_mesh_plate_pass':numerical_plate_ready,'all_declared_case_checks_pass':all(r['all_checks_pass'] for r in rows),'conditional_radome_diagnostic_allowed':numerical_plate_ready,'whole_aircraft_extension_allowed':False,'physical_impact_qualified':False,'no_stiffness_fitted_to_historical_result':True,'old_solver_reruns':0}
    dump(OUT/'plate_review.json',s);print({k:v for k,v in s.items() if k not in ['cases','comparisons']},flush=True);print(json.dumps(comp,indent=2),flush=True)
if __name__=='__main__':main()
