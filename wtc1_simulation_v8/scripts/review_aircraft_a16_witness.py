"""Check native maximum-history damage, repeated equal peaks and work balance."""
import re,struct,subprocess
import numpy as np
from run_aircraft_a16 import OUT,CFG,RUNTIME,read,dump,now,guard,rel,streamsha
from audit_aircraft_a05 import histories,vtk
from recover_aircraft_a05_history import records

def path(T):
    w=read(CFG)['witness'];ep=np.zeros_like(T)
    for ta,tb,ea,eb in zip(w['path_time_ms'][:-1],w['path_time_ms'][1:],w['path_log_strain'][:-1],w['path_log_strain'][1:]):
        ix=(T>=ta)&(T<=tb);u=(T[ix]-ta)/(tb-ta);ep[ix]=ea+(eb-ea)*(3*u*u-2*u*u*u)
    return ep

def main():
    guard();assert not (OUT/'witness_review.json').exists();cfg=read(CFG);a=cfg['witness_acceptance'];rows=[]
    for c in cfg['witness']['cases']:
        d=OUT/'w0'/c['id'];n=read(d/'generation.json')['name'];H=histories(d/(n+'T01.csv'));T=H['time'];rr=records(d/(n+'T01'));v=np.column_stack(list(H.values()));nr=4;header=len(rr)-len(v)*nr;assert header>0
        fs=[rr[header+i*nr:header+(i+1)*nr] for i in range(len(v))];sizes=[len(q) for q in fs[0]];assert sizes[:2]==[4,88] and all([len(q) for q in f]==sizes for f in fs)
        raw=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in fs]);assert raw.shape==v.shape and np.allclose(raw,v,rtol=6e-7,atol=1e-12)
        N=np.column_stack([H[k] for k in H if k.startswith('AFFINE_NODES')]).reshape(len(T),4,6);ep=path(T);L=c['L_mm'];aff=float(max(np.max(abs(N[:,1,0]-L*np.expm1(ep))),np.max(abs(N[:,2,1]-L*np.expm1(-.25*ep)))))
        K=H['KINETIC ENERGY']*.001;IE=H['INTERNAL ENERGY']*.001;EW=H['EXTERNAL WORK']*.001;res=K+IE+H['ROTATION ENERGY']*.001+H['HOURGLASS ENERGY']*.001-EW;res-=res[0];norm=max(float(np.max(abs(EW))),.001)
        rw=float(np.sum((N[1:,:,2:4]+N[:-1,:,2:4])*.5*np.diff(N[:,:,4:6],axis=0))*.001)
        ts=[];dam=[];strain=[]
        files=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name))
        for file in files:
            q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(file)],capture_output=True,text=True,check=True,timeout=60).stdout)
            with file.open('rb') as f:magic,tm=struct.unpack('>if',f.read(8))
            assert magic==0x542c and np.all(q['EROSION_STATUS']==1)
            keys=[k for k in q if 'DAMAGE' in k];assert len(keys)==3;z=np.stack([q[k] for k in keys]);assert np.isfinite(z).all();ts.append(tm);dam.append(z);strain.append(q['2DELEM_Strain_(upper)'].reshape(2,3,3)[:,0,0])
        ts=np.array(ts);dam=np.array(dam);e=path(ts);peak=np.maximum.accumulate(e);ed=cfg['damage']['tensile_onset'];ef=ed*(1+c['transition_fraction']);expect=np.clip(ef*(peak-ed)/(np.maximum(peak,1e-30)*(ef-ed)),0,1);faces=dam[:,[0,2],:];derr=float(np.max(abs(faces-expect[:,None,None])));i1=int(np.argmin(abs(ts-.25)));i2=int(np.argmin(abs(ts-.75)));same=float(np.max(abs(faces[i2]-faces[i1])));cyc=abs(float(np.interp(.75,T,IE)-np.interp(.25,T,IE)))/norm
        checks={'binary_CSV_all_channels':True,'normal_termination':True,'no_erosion':True,'core_damage_zero':bool(np.all(dam[:,1,:]==0)),'damage_bounds':bool(np.min(dam)>=-1e-6 and np.max(dam)<=1.000001),'affine_positions':aff<=a['affine_displacement_error_mm'],'native_maximum_history_damage':derr<=a['native_vs_maximum_history_damage_absolute'],'no_new_damage_at_equal_peak':same<=a['no_damage_at_equal_peak_absolute'],'closed_equal_peak_energy':cyc<=a['closed_equal_peak_energy_fraction'],'global_energy':np.max(abs(res))<=a['global_work_balance_fraction']*norm+a['energy_absolute_J'],'reaction_impulse_work':abs(rw-EW[-1])<=a['global_work_balance_fraction']*norm+a['energy_absolute_J']}
        r={'case':c,'checks':{k:bool(v) for k,v in checks.items()},'failed_checks':[k for k,v in checks.items() if not v],'native_history_rows':len(T),'last_history_ms':float(T[-1]),'native_damage_error':derr,'damage_growth_equal_peak':same,'equal_peak_energy_difference_fraction':cyc,'maximum_work_balance_residual_J':float(np.max(abs(res))),'reaction_impulse_work_error_J':float(abs(rw-EW[-1])),'affine_error_mm':aff,'final_IE_J':float(IE[-1]),'final_EW_J':float(EW[-1]),'face_damage_at_peaks':[faces[i1].tolist(),faces[i2].tolist()],'actual_fracture_energy_qualified':False}
        np.savez_compressed(d/'witness_diagnostics.npz',history_time_s=T*.001,kinetic_J=K,internal_J=IE,external_J=EW,residual_J=res,animation_time_s=ts*.001,damage=dam,expected_damage=expect,log_strain=e)
        dump(d/'witness_review.json',r);rows.append(r);print(r,flush=True)
    pair=rows[:2];delta=abs(pair[0]['final_IE_J']-pair[1]['final_IE_J'])/max(abs(pair[0]['final_IE_J']),.001);half=delta<=a['half_dt_final_IE_difference_fraction']
    s={'created_utc':now(),'cases':rows,'mechanical_gate_pass':all(all(r['checks'].values()) for r in rows) and half,'half_dt_final_IE_difference_fraction':delta,'half_dt_pass':half,'physical_fracture_energy_qualified':False,'physical_aircraft_qualified':False,'only_implementation_history_gate':True,'old_ORTHENERG_failure_retained':True};dump(OUT/'witness_review.json',s);print(s['mechanical_gate_pass'],flush=True)

if __name__=='__main__':main()
