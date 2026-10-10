"""Keep a capped attempt incomplete; verify its available native history without rerun."""
import csv,struct,subprocess
import numpy as np
from run_aircraft_a15 import ROOT,OUT,CFG,RUNTIME,read,dump,rel,now,guard,execute,env,streamsha
from review_aircraft_a15 import segments
from audit_aircraft_a05 import histories,vtk
from recover_aircraft_a05_history import records
from review_aircraft_a08 import binary_mass

def main():
    guard();d=OUT/'r0/IMPACT_10_DT25';assert list(d.glob('retained_failure_*.json'))
    assert not (d/'partial_review.json').exists();g=read(d/'generation.json');n=g['name'];cfg=read(CFG)
    assert read(d/'engine.log.execution.json')['exit_code']=='TIMEOUT'
    assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'partial_converter.log',120,env())
    H=histories(d/(n+'T01.csv'));v=np.column_stack(list(H.values()));rr=records(d/(n+'T01'))
    schema=read(OUT/'r0/IMPACT_10_DT50/history_recovery.json');nr=schema['records_per_frame'];sizes=schema['sizes'];header=len(rr)-len(v)*nr;assert header>0
    frames=[rr[header+i*nr:header+(i+1)*nr] for i in range(len(v))]
    assert all([len(q) for q in f]==sizes for f in frames)
    raw=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames]);assert raw.shape==v.shape and np.allclose(raw,v,rtol=6e-7,atol=1e-12)
    assert np.isfinite(v).all();T=H['time'];S=segments(H);J=sum(S.values());J-=J[0]
    terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    E=sum(H[k] for k in terms)*.001;G=sum(H[k] for k in terms if k!='KINETIC ENERGY')*.001;R=E-E[0]-H['EXTERNAL WORK']*.001
    P=np.column_stack([H[z+'-MOMENTUM'] for z in 'XYZ'])*.001
    Pf=np.column_stack([sum((H[k] for k in H if k.startswith('FACADE_') and k.strip().endswith(z+'MOM')),np.zeros(len(T))) for z in 'XYZ'])*.001
    Js=np.column_stack([sum((H[k] for k in H if k.startswith('SUPPORT_IMPULSE_'+z)),np.zeros(len(T))) for z in 'XYZ'])*.001;Js-=Js[0]
    np.savez_compressed(d/'balance_history_SI.npz',time_s=T*.001,contact_impulse_Ns=J,facade_momentum_Ns=Pf,global_momentum_Ns=P,support_Ns=Js,energy_residual_J=R,generated_energy_J=G,plastic_work_J=H['PLASTIC WORK']*.001)
    files=sorted(p for p in d.glob(n+'A*') if p.name[len(n)+1:].isdigit());file=files[-1]
    q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(file)],capture_output=True,text=True,check=True,timeout=120).stdout)
    with file.open('rb') as f:magic,tm=struct.unpack('>if',f.read(8))
    assert magic==0x542c and abs(q['time']-tm)<=max(1e-6,abs(tm)*5e-6);q['time']=tm
    nm,pf=binary_mass(file,q);order=np.argsort(q['NODE_ID']);u=q['Displacement'].reshape(-1,3)[order];fa=np.array(g['facade_translated_node_ids'])-1
    assert np.isfinite(u).all() and np.all(q['EROSION_STATUS']==1)
    nominal=np.load(OUT/'r0/IMPACT_10_DT50/balance_history_SI.npz');tc=min(T[-1]*.001,nominal['time_s'][-1]);ja=np.array([np.interp(tc,nominal['time_s'],nominal['contact_impulse_Ns'][:,i]) for i in range(3)]);jb=J[-1];ga=float(np.interp(tc,nominal['time_s'],nominal['generated_energy_J']));gb=float(G[-1]);jd=float(np.linalg.norm(jb-ja)/max(np.linalg.norm(ja),1e-30));ed=abs(gb-ga)/max(abs(ga),1e-30)
    comparison={'cases':['IMPACT_10_DT50','IMPACT_10_DT25'],'common_time_ms':float(tc*1000),'partial_window_only':True,'both_requested_horizons_reached':False,'impulse_difference_fraction':jd,'generated_energy_difference_fraction':ed,'impulse_pass':jd<=cfg['acceptance']['half_dt_impulse_difference_fraction'],'generated_energy_pass':ed<=cfg['acceptance']['half_dt_generated_energy_difference_fraction']}
    r={'created_utc':now(),'case':g['case'],'status':'incomplete_cost_cap_retained','native_binary_CSV_verified':True,'native_history_rows':len(T),'last_available_main_history_ms':float(T[-1]),'actual_end_ms':None,'requested_horizon_reached':False,'normal_termination':False,'engine_exit_code':'TIMEOUT','no_solver_rerun':True,'last_available_animation_ms':tm,'last_available_animation':rel(file),'last_sample_facade_displacement_mm':float(np.max(np.linalg.norm(u[fa],axis=1))),'last_main_contact_impulse_Ns':jb.tolist(),'last_generated_energy_J':gb,'last_energy_residual_J':float(R[-1]),'maximum_available_energy_residual_J':float(np.max(abs(R))),'native_mass_reader_proof':pf,'native_total_mass_kg':float(nm.sum()),'comparison':comparison,'physical_impact_qualified':False,'spatial_convergence_qualified':False,'available_main_history_only':True,'no_observer_or_final_timestamp':True}
    dump(d/'partial_review.json',r);dump(d/'partial_history_recovery.json',{'created_utc':now(),'pass':True,'all_available_CSV_channels_binary_verified':True,'frames':len(T),'records_per_frame':nr,'payload_sizes':sizes,'raw_binary_sha256':streamsha(d/(n+'T01')),'incomplete_run_remains_incomplete':True})
    print(r,flush=True)

if __name__=='__main__':main()
