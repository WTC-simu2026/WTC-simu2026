"""Native cohesive work, equal-peak reload and area/time discretization audit."""
import re,struct,subprocess
import numpy as np
from run_aircraft_a17 import ROOT,OUT,CFG,RUNTIME,read,dump,now,guard,opening
from audit_aircraft_a05 import histories,vtk
from recover_aircraft_a05_history import records

def reference(q,K,T,G):
    d0=T/K;df=2*G/T;p=np.maximum.accumulate(np.maximum(q,0));D=np.where(p<=d0,0,np.where(p>=df,1,df*(p-d0)/(np.maximum(p,1e-30)*(df-d0))))
    a=np.clip(p,d0,df);W=np.where(p<=d0,.5*K*p*p,.5*T*d0+T/(df-d0)*(df*(a-d0)-.5*(a*a-d0*d0)))
    stored_at_peak=.5*(1-D)*K*p*p;diss=W-stored_at_peak;stored=.5*(1-D)*K*q*q;tr=(1-D)*K*q
    return D,tr,stored,diss

def main():
    guard();assert not (OUT/'cohesive_review.json').exists();cfg=read(CFG);c=cfg['cohesive'];lim=cfg['acceptance'];rows=[]
    for case in cfg['witness']['cases']:
        d=OUT/'w0'/case['id'];n=read(d/'generation.json')['name'];H=histories(d/(n+'T01.csv'));T=H['time'];N=np.column_stack([v for k,v in H.items() if k.startswith('REACTION_NODES')]).reshape(len(T),8,3)
        rr=records(d/(n+'T01'));V=np.column_stack(list(H.values()));nr=4;hd=len(rr)-len(V)*nr;assert hd>0;frames=[rr[hd+i*nr:hd+(i+1)*nr] for i in range(len(T))];sz=[len(b) for b in frames[0]];assert sz[:2]==[4,88] and all([len(b) for b in f]==sz for f in frames)
        binary=np.array([np.concatenate([np.frombuffer(b,dtype='>f4').astype(float) for b in f]) for f in frames]);assert binary.shape==V.shape and np.allclose(binary,V,rtol=6e-7,atol=1e-12)
        area=case['L_mm']**2;K,traction,G=(c['EN_N_mm3'],c['TN_MPa'],c['GI_N_mm']) if case['mode']=='Z' else (c['ET_N_mm3'],c['TT_MPa'],c['GII_N_mm']);q=N[:,4:,0].mean(axis=1);D,tr,S,Q=reference(q,K,traction,G);IE=H['INTERNAL ENERGY']*.001;KE=H['KINETIC ENERGY']*.001;EW=H['EXTERNAL WORK']*.001
        referenceIE=(S+Q)*area*.001;res=IE+KE+H['ROTATION ENERGY']*.001+H['HOURGLASS ENERGY']*.001-EW;res-=res[0];target=G*area*.001;work=float(np.sum((N[1:,:,1]+N[:-1,:,1])*.5*np.diff(N[:,:,2],axis=0))*.001);force=-np.gradient(N[:,:4,2].sum(axis=1),T);ferr=float(np.max(abs(force-tr*area))/(traction*area));pos=float(np.max(abs(q-opening(T,case['mode']))));cyc=abs(float(np.interp(.75,T,IE)-np.interp(.25,T,IE)))/target;last=float(IE[-1]);endwork=last/area*1000
        checks={'native_binary_CSV_all_channels':True,'normal_termination':'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace'),'mass_matches_instrument':bool(np.allclose(H['MASS'],8,rtol=1e-6,atol=1e-6)),'no_added_mass':bool(np.all(H['ADDED MASS']==0)),'motion_exact':pos<=lim['prescribed_motion_mm'],'global_work_energy':np.max(abs(res))<=lim['work_energy_fraction']*target+lim['absolute_energy_J'],'reaction_impulse_work':abs(work-EW[-1])<=lim['work_energy_fraction']*target+lim['absolute_energy_J'],'surface_work_matches_entered_G':abs(endwork-G)/G<=lim['work_per_area_G_fraction'],'native_IE_matches_stored_plus_dissipated_reference':np.max(abs(IE-referenceIE))<=lim['work_energy_fraction']*target+lim['absolute_energy_J'],'same_peak_reload_no_new_work':cyc<=lim['equal_peak_energy_fraction'],'reference_dissipation_monotone':bool(np.all(np.diff(Q)>=-1e-9)),'native_traction_matches_reference':ferr<=lim['traction_maximum_relative']}
        fn=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name))[-1];raw=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(fn)],capture_output=True,text=True,check=True,timeout=60).stdout;z=vtk(raw);status=np.asarray(z['EROSION_STATUS']);checks['native_cohesive_element_deleted']=bool(np.all(status==0));checks['opening_beyond_complete_failure']=float(q[-1])>=2*G/traction
        np.savez_compressed(d/'cohesive_diagnostics.npz',time_s=T*.001,opening_mm=q,native_internal_J=IE,reference_stored_J=S*area*.001,reference_dissipated_J=Q*area*.001,native_external_J=EW,residual_J=res,reference_damage=D,native_reaction_force_N=force,reference_force_N=tr*area)
        row={'case':case,'checks':{k:bool(v) for k,v in checks.items()},'failed_checks':[k for k,v in checks.items() if not v],'native_history_rows':len(T),'native_binary_record_sizes':sz,'final_surface_work_N_mm':endwork,'entered_G_N_mm':G,'final_IE_J':last,'maximum_work_energy_residual_J':float(np.max(abs(res))),'reaction_work_error_J':float(abs(work-EW[-1])),'maximum_reference_IE_error_J':float(np.max(abs(IE-referenceIE))),'equal_peak_IE_difference_fraction':cyc,'maximum_traction_relative_error':ferr,'maximum_motion_error_mm':pos,'native_erosion_status_final':status.tolist(),'physical_G_measured':False,'whole_aircraft_transfer_qualified':False};dump(d/'review.json',row);rows.append(row);print({k:row[k] for k in ['case','failed_checks','final_surface_work_N_mm','maximum_traction_relative_error','equal_peak_IE_difference_fraction']},flush=True)
    dt=abs(rows[1]['final_IE_J']-rows[0]['final_IE_J'])/rows[0]['final_IE_J'];area=abs(rows[2]['final_surface_work_N_mm']-rows[0]['final_surface_work_N_mm'])/rows[0]['final_surface_work_N_mm'];checks={'all_cases_pass':all(not r['failed_checks'] for r in rows),'half_dt_work_pass':dt<=lim['half_dt_work_fraction'],'area_normalized_work_pass':area<=lim['area_normalized_work_fraction']}
    dump(OUT/'cohesive_review.json',{'created_utc':now(),'cases':rows,'checks':checks,'mechanical_implementation_gate_pass':all(checks.values()),'half_dt_final_work_difference_fraction':dt,'area_normalized_work_difference_fraction':area,'physical_fracture_energy_measured':False,'whole_aircraft_transfer_qualified':False,'old_ORTHENERG_failure_retained':True,'objective1_complete':False})

if __name__=='__main__':main()
