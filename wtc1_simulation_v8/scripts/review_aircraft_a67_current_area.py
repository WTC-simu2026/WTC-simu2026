"""Independent all-step physical/free and scoped variable-area Newmark control analysis."""
from control_aircraft_a67_current_area import ROOT,OUT,CONTROL,read,dump,sha,now,engine
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records
from assess_aircraft_a23_reader_precision import printed_bound
from surface_iteration_aircraft_a61_r1 import iteration_matrix,shape
import numpy as np,re,json,time

def areas_and_force(nodes,U,p):
    mid=((nodes[None,:4,:]+U[:,:4,:])+(nodes[None,4:,:]+U[:,4:,:]))/2
    r=mid[:,1]+mid[:,2]-mid[:,0]-mid[:,3];s=mid[:,2]+mid[:,3]-mid[:,0]-mid[:,1]
    n=np.cross(r,s);length=np.linalg.norm(n,axis=1);assert np.all(length>0);n/=length[:,None]
    weights=[];g=1/np.sqrt(3)
    for a,b in [(-g,-g),(g,-g),(g,g),(-g,g)]:
        dr=np.array([-(1-b),1-b,1+b,-(1+b)])/4;ds=np.array([-(1-a),-(1+a),1+a,1-a])/4
        tr=np.einsum('a,taj->tj',dr,mid);ts=np.einsum('a,taj->tj',ds,mid);weights.append(np.einsum('tj,tj->t',n,np.cross(tr,ts)))
    weights=np.array(weights).T
    gap=np.einsum('pa,taj->tpj',shape(),U[:,4:,:]-U[:,:4,:]);projected=np.einsum('tpj,tj->tp',gap,n)
    traction=p['ET_N_mm3']*gap+(p['EN_N_mm3']-p['ET_N_mm3'])*projected[:,:,None]*n[:,None,:]
    force=np.einsum('tp,tpj->tj',weights,traction)
    return weights,force

def reference(case,p,count):
    dt=case['dt_cap_ms'];t=np.arange(count)*dt;Q=np.zeros((count,8,3));V=np.zeros_like(Q)
    if case['reference']=='current_area_evolution_free_Y':
        q=0.;v=case['initial_free_velocity_mm_ms'][1];a=0.;Q[0,4:,1]=q;V[0,4:,1]=v
        for j in range(1,count):
            lam=100*p['ET_N_mm3']*(1+.1*np.sin(np.pi*t[j])**2)/4
            predict=q+dt*v+.25*dt*dt*a;anew=-lam*predict/(1+.25*dt*dt*lam)
            q=predict+.25*dt*dt*anew;v=v+.5*dt*(a+anew);a=anew;Q[j,4:,1]=q;V[j,4:,1]=v
        return Q,V
    nodes=np.asarray(case['nodes_mm']);K=iteration_matrix(nodes,case['initial_current_GP_area_mm2'],p)[12:,12:]
    lam,eigen=np.linalg.eigh(K);assert np.all(lam>0);omega=np.sqrt(lam)
    v0=np.tile(case['initial_free_velocity_mm_ms'],4);coeff=eigen.T@v0;phase=np.arange(count)[:,None]*2*np.arctan(omega*dt/2)[None,:]
    Q[:,4:,:]=((np.sin(phase)*(coeff/omega)[None,:])@eigen.T).reshape(count,4,3)
    V[:,4:,:]=((np.cos(phase)*coeff[None,:])@eigen.T).reshape(count,4,3)
    return Q,V

def case_review(case,cfg):
    d=OUT/'native'/case['id'];name=read(d/'generation.json')['name'];completion=read(d/'completion_review.json')
    assert completion['parent_exit_code']==0 and completion['normal_termination']
    H=histories(d/(name+'T01.csv'));T=H['time'];CSV=np.column_stack(list(H.values()));rr=records(d/(name+'T01'))
    nr=next(n for n in range(3,10) if sum(map(len,rr[-n:]))==CSV.shape[1]*4 and len(rr[-n])==4);header=len(rr)-len(T)*nr
    native=np.asarray([np.concatenate([np.frombuffer(v,dtype='>f4').astype(float) for v in rr[header+j*nr:header+(j+1)*nr]]) for j in range(len(T))])
    binary_ok=native.shape==CSV.shape and np.allclose(native,CSV,rtol=6e-7,atol=1e-12)
    F=np.stack([np.column_stack([v for k,v in H.items() if k.startswith('REACTION_'+a)]).reshape(len(T),8,3) for a in 'XYZ'],axis=-1)
    U=F[:,:,0,:];sec=F[:,:,1,:];imp=F[:,:,2,:];dt=case['dt_cap_ms'];nominal=np.arange(len(T))*dt
    V0=np.zeros((8,3));V0[4:]=case['initial_free_velocity_mm_ms'];V=np.empty_like(sec);V[0]=V0
    for j in range(1,len(T)):V[j]=2*sec[j]-V[j-1]
    Qref,Vref=reference(case,cfg['cohesive'],len(T));variable=case['reference']=='current_area_evolution_free_Y'
    nodes=np.asarray(case['nodes_mm']);areas,expected_force=areas_and_force(nodes,U,cfg['cohesive']);_,ref_force=areas_and_force(nodes,Qref,cfg['cohesive'])
    I=imp[:,:4,:].sum(axis=1);force=np.zeros_like(I)
    for j in range(1,len(T)):force[j]=-2*(I[j]-I[j-1])/dt-force[j-1]
    scope=[1] if variable else [0,1,2];top_scope=V[:,4:,:][:,:,scope]
    K=.5*np.sum(top_scope**2,axis=(1,2))*.001;P=V[:,:,scope].sum(axis=1)*.001;P0=V0[:,scope].sum(axis=0)*.001
    K0=.5*np.sum(V0[:,scope]**2)*.001;lim=cfg['acceptance'];et=lim['energy_relative']*K0+lim['energy_absolute_J'];pt=lim['momentum_relative']*np.sum(abs(V0[:,scope]))*.001+lim['momentum_absolute_Ns']
    nativeP=np.column_stack([H[a+'-MOMENTUM'] for a in 'XYZ'])*.001;nativeK=H['KINETIC ENERGY']*.001
    support=I[:,scope]*.001;momentum=P-P0-support
    other=sum(H[k] for k in ['ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '])*.001
    energy=K+other-K0-(0 if variable else H['EXTERNAL WORK']*.001)
    relative=U[:,4:,:]-U[:,:4,:]
    q=relative.mean(axis=1)
    delta=np.diff(q,axis=0);work=np.r_[0,np.cumsum(np.sum(.5*(expected_force[1:]+expected_force[:-1])*delta,axis=1))]*.001
    fscale=max(float(np.linalg.norm(ref_force[:,scope],axis=1).max()),1e-20)
    ferr=float(np.linalg.norm((force-expected_force)[:,scope],axis=1).max()/fscale)
    log=(d/'engine.log').read_text(encoding='utf8',errors='replace');cycles=int(re.search(r'TOTAL NUMBER OF CYCLES\s*:\s*(\d+)',log).group(1))
    steps=[float(x) for x in re.findall(r' NC=.*? DT=\s*([\d.E+\-]+)',log)]
    identity=np.diff(U[:,:,scope],axis=0)/dt-sec[1:,:,scope]
    precision=(printed_bound(U[1:,:,scope])+printed_bound(U[:-1,:,scope]))/dt+printed_bound(sec[1:,:,scope])+1e-6
    errq=float(abs((U-Qref)[:,4:,:][:,:,scope]).max());errv=float(abs((V-Vref)[:,4:,:][:,:,scope]).max())
    checks={'native_normal_no_STOP_or_abort':not bool(re.search(r'STOP\s*:|STOP\s+66|USER\s*BREAK|MPI_ABORT',log,re.I)),
        'complete_native_binary_CSV':binary_ok,'fixed_native_time_grid':bool(np.all(abs(T-nominal)<=printed_bound(T)+4*np.finfo(np.float32).eps*abs(T)+1e-12)),
        'native_cycles_match_rows':abs(cycles-len(T))<=1,'actual_printed_step_matches':bool(steps and all(abs(h-dt)<=dt*1e-5 for h in steps)),
        'complete_TH_nodes_reach_target':float(T[-1])>=1-1e-6,'overshoot_within_one_step':float(T[-1])<=1+dt+1e-6,
        'free_scope_secant_displacement_identity':bool(np.all(abs(identity)<=precision)),
        'physical_P_scope_vs_native':float(abs(P-nativeP[:,scope]).max())<=pt,
        'physical_support_scope_momentum_balance':float(abs(momentum).max())<=pt,
        'source_scope_energy_balance':float(abs(energy).max())<=et,
        'mass_8g':bool(np.allclose(H['MASS'],8,rtol=lim['mass_relative'],atol=1e-6)),
        'no_added_mass':bool(np.all(H['ADDED MASS']==0)),'actual_current_projected_GP_areas_positive':bool(np.all(np.isfinite(areas)) and np.all(areas>0)),
        'reference_Newmark_free_displacement':errq<=cfg['extra_analytical_displacement_tolerance_mm'],
        'reference_Newmark_free_velocity':errv<=cfg['extra_analytical_velocity_tolerance_mm_ms'],
        'elastic_gap_domain':float(np.linalg.norm(relative,axis=2).max())<cfg['cohesive']['TT_MPa']/cfg['cohesive']['ET_N_mm3'],
        'current_area_traction_vs_support_impulse':ferr<=.02,
        'native_IE_vs_independent_uniform_gap_work':float(abs(H['INTERNAL ENERGY']*.001-work).max())<=et}
    if not variable:
        checks.update(physical_KE_vs_native=float(abs(K-nativeK).max())<=et,zero_external_work=bool(np.all(H['EXTERNAL WORK']==0)),fixed_bottom=bool(np.all(U[:,:4,:]==0)))
        if case['uniform_top_motion_required']:checks['uniform_top_motion']=float(abs(U[:,4:,:]-U[:,4:,:].mean(axis=1)[:,None,:]).max())<=lim['free_displacement_mm']
    else:
        expected_X=.1*10*np.sin(np.pi*nominal)**2
        mask=np.array([0,1,1,0,0,1,1,0])
        checks.update(common_X_matches_declared_stretch=float(abs(U[:,:,0]-expected_X[:,None]*mask).max())<=lim['free_displacement_mm'],
            fixed_bottom_Y_Z=bool(np.all(U[:,:4,1:]==0)),
            current_area_matches_predeclared_scale=float(abs(areas.sum(axis=1)-100*(1+.1*np.sin(np.pi*nominal)**2)).max())<=1e-5*100,
            uniform_top_free_Y=float(abs(U[:,4:,1]-U[:,4:,1].mean(axis=1)[:,None]).max())<=lim['free_displacement_mm'])
    row={'case':case['id'],'pass':bool(all(checks.values())),'checks':{k:bool(v) for k,v in checks.items()},'failed_checks':[k for k,v in checks.items() if not v],
        'full_global_free_energy_momentum_qualification':bool(not variable and all(checks.values())),
        'scope':'free_Y_current_area_control_only' if variable else 'all_free_top_translations',
        'reference':'time-varying Newmark scalar from predeclared area scale' if variable else 'constant initial stiffness exact discrete eigenmodes, small-amplitude limit for nonuniform case',
        'maximum_reference_gap_error_mm':errq,'maximum_reference_velocity_error_mm_ms':errv,
        'maximum_scope_energy_residual_J':float(abs(energy).max()),'maximum_scope_momentum_residual_Ns':float(abs(momentum).max()),
        'maximum_native_IE_independent_work_difference_J':float(abs(H['INTERNAL ENERGY']*.001-work).max()),
        'traction_relative_error':ferr,'energy_tolerance_J':et,'momentum_tolerance_Ns':float(pt),
        'last_TH_ms':float(T[-1]),'native_cycles':cycles,'native_rows':len(T),
        'initial_energy_J':float(K0),'current_area_min_mm2':float(areas.min()),'current_total_area_range_mm2':[float(areas.sum(axis=1).min()),float(areas.sum(axis=1).max())],
        'prescribed_X_global_KE_P_not_qualified':variable,'inherited_generic_all_top_free_flag_not_applicable_to_case6':variable,
        'new_whole_credit_s':0,'native_whole_insertion_qualified':False}
    np.savez_compressed(d/'mechanical_diagnostics.npz',time_ms=T,nominal_cycle_time_ms=nominal,displacement_mm=U,source_endpoint_velocity_scope=V[:,:,scope],
        reference_displacement_mm=Qref,reference_velocity_mm_ms=Vref,scope_KE_J=K,scope_P_Ns=P,scope_energy_residual_J=energy,
        scope_momentum_residual_Ns=momentum,current_GP_area_mm2=areas,source_support_force_N=force,elastic_current_area_force_N=expected_force,
        independent_uniform_gap_work_J=work,native_IE_J=H['INTERNAL ENERGY']*.001,native_global_KE_J=nativeK,native_global_P_Ns=nativeP)
    dump(d/'mechanical_review.json',row);print(json.dumps({'case':case['id'],'pass':row['pass'],'scope':row['scope'],'failed':row['failed_checks']}),flush=True)
    return row,(T,K,H['INTERNAL ENERGY']*.001)

def main():
    engine();cfg=read(CONTROL);rows=[];diag=[]
    dump(OUT/'scope_clarification.json',{'created_utc':now(),'case6_source_inputs_explicitly_prescribe_all_X_only':True,
        'case6_Y_Z_top_are_free':True,'inherited_all_top_translations_free_metadata_is_not_applicable_to_case6':True,
        'original_control_json_and_native_inputs_preserved':True,'no_global_prescribed_X_counter_qualification_inferred':True,
        'new_native_or_source_modification':False})
    for c in cfg['cases']:
        try:r,d=case_review(c,cfg);rows.append(r);diag.append(d)
        except Exception as e:
            r={'case':c['id'],'pass':False,'analysis_error':repr(e),'failed_checks':['analysis_or_native_completion'],'whole_insertion_qualified':False}
            dump(OUT/('analysis_failure_'+c['id']+'.json'),r);rows.append(r);diag.append(None);print(json.dumps(r),flush=True)
    compare=[]
    if diag[0] is not None and diag[1] is not None:
        threshold=cfg['acceptance']['half_dt_energy_relative']*rows[0]['initial_energy_J']+cfg['acceptance']['comparison_energy_absolute_J']
        for idx,label in [(1,'physical_KE'),(2,'native_IE')]:
            error=float(abs(diag[0][idx]-np.interp(diag[0][0],diag[1][0],diag[1][idx])).max());compare.append({'channel':label,'maximum_difference_J':error,'unchanged_tolerance_J':threshold,'pass':error<=threshold})
    dump(OUT/'current_area_mechanical_review.json',{'created_utc':now(),'cases':rows,'half_dt_energy_comparisons':compare,
        'pass':bool(all(r['pass'] for r in rows) and len(compare)==2 and all(r['pass'] for r in compare)),
        'five_fully_free_cases_pass':bool(all(r['pass'] for r in rows[:5])),
        'variable_area_case_is_scoped_Y_control_not_full_global_physical_qualification':True,
        'exact_geometric_Jacobian_native_rollback_damage_large_rotation_or_whole_not_qualified':True,
        'maximum_authorized_native':8,'new_native_replays':0,'whole_credit_s':0})

if __name__=='__main__':main()
