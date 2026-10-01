"""Independent saved-history checks; do not confuse integrated REAC with force."""
import argparse,csv,json,re,sys
from pathlib import Path
import numpy as np
from run_impact_i02c import ROOT,dump
CFG=json.loads((ROOT/'wtc1_simulation_v8/data/impact_i02d_lap_joint.json').read_text())
OUT=ROOT/CFG['output_root']

def ref_patch(delta):
    j=CFG['joint'];K=np.array([j['tangent_Fp_N'],j['tangent_Fp_N'],j['normal_Fp_N']])/j['d0_mm']
    d0=j['d0_mm'];Gn=.5*j['normal_Fp_N']*j['df_mm'];Gt=.5*j['tangent_Fp_N']*j['df_mm']
    history=[];damage=0.;kappa=0.;energies=[];dfhist=[]
    for q in delta:
        opening=q.copy();opening[2]=max(q[2],0);r=np.linalg.norm(opening)
        kappa=max(kappa,r)
        if r>1e-12:
            s2=float(np.dot(opening[:2],opening[:2]));n2=opening[2]**2
            mix=K[0]*s2/(K[0]*s2+K[2]*n2);Gc=Gn+(Gt-Gn)*mix
            kmix=float(np.dot(K,opening**2))/r**2;df=2*Gc/(d0*kmix)
            damage=max(damage,float(np.clip(df*(kappa-d0)/(kappa*(df-d0)),0,1)))
        else:df=j['df_mm']
        force=(1-damage)*K*opening;force[2]+=K[2]*min(q[2],0) if damage<1 else 0
        history.append(force);energies.append(.5*(1-damage)*float(np.dot(K,opening**2))*.001);dfhist.append(df)
    return np.array(history),np.array(energies),np.array(dfhist)

def audit(name):
    d=OUT/name;meta=json.loads((d/'generation.json').read_text());c=meta['case'];gate=CFG['gates'];patch=c['geometry']=='patch'
    with (d/(meta['name']+'T01.csv')).open() as f:
        headers=next(csv.reader(f));a=np.loadtxt(f,delimiter=',')
    t=a[:,0];nn=len(meta['nodes_mm']);nb=len(meta['bricks']);start=35+8*nb
    assert a.shape[1]==start+15*nn
    raw=a[:,start:].reshape(len(t),nn,15)
    ids=[int(re.search(r'NODE_HISTORY\s+(\d+)',headers[start+15*k]).group(1)) for k in range(nn)]
    node=raw[:,[ids.index(k) for k in range(1,nn+1)],:]
    brick=a[:,35:start].reshape(len(t),nb,8);off=brick[:,:,0]
    x=np.array(meta['nodes_mm'])[None,:,:]+node[:,:,:3];v=node[:,:,3:6];vr=node[:,:,6:9];imp=node[:,:,9:12];momentimp=node[:,:,12:15]
    mass=np.array(meta['nodal_mass_g']);R=np.array(meta['rotation']);areas=np.array(meta['areas_mm2'])
    right=np.array(meta['right'])-1;left=np.array(meta['left'])-1
    P=(v*mass[None,:,None]).sum(axis=1);L=np.cross(x,v*mass[None,:,None]).sum(axis=1)
    J=imp.sum(axis=1);dJ=np.diff(imp,axis=0);xm=(x[1:]+x[:-1])*.5
    torque_increment=(np.cross(xm,dJ)+np.diff(momentimp,axis=0)).sum(axis=1)
    angular=np.vstack([np.zeros(3),np.cumsum(torque_increment,axis=0)])
    force=np.gradient(imp,t,axis=0);couple=np.gradient(momentimp,t,axis=0)
    grip_right=force[:,right].sum(axis=1);grip_left=force[:,left].sum(axis=1)
    externalW=np.r_[0,np.cumsum(((v[1:]+v[:-1])*.5*dJ).sum(axis=(1,2))+((vr[1:]+vr[:-1])*.5*np.diff(momentimp,axis=0)).sum(axis=(1,2)))]*.001
    # Global KE is translational; rotational and contact energies are separate columns.
    total=(a[:,1]+a[:,2]+a[:,8]+a[:,11])*.001
    residual=total-total[0]-a[:,9]*.001
    scale=max(float(np.max(abs(a[:,9]))*.001),float(np.max(abs(total))),1e-9)
    pscale=max(float(np.max(np.linalg.norm(J,axis=1))),float(np.max(np.linalg.norm(P,axis=1))),1e-6)
    rscale=max(float(np.max(np.linalg.norm(np.cumsum(np.cross(xm[:,right],dJ[:,right]).sum(axis=1)+np.diff(momentimp[:,right],axis=0).sum(axis=1),axis=0),axis=1))),1e-6)
    nodalKE=(v*v*mass[None,:,None]).sum(axis=(1,2))*.0005
    localx=x@R;localv=v@R
    delta=localx[:,np.array(meta['top'])-1].mean(axis=1)-localx[0,np.array(meta['top'])-1].mean(axis=0)
    IE=a[:,31]*.001
    # Pure patch: subtract the momentum derivative of the uniformly driven top plate.
    top=np.array(meta['top'])-1;Ptop=(localv[:,top]*mass[None,top,None]).sum(axis=1)
    Fboundary=grip_right@R-np.gradient(Ptop,t,axis=0)
    Fpatch=np.stack([brick[:,:,7]@areas,brick[:,:,6]@areas,brick[:,:,4]@areas],axis=1)
    uref=None;force_error=None;ref_error=None;D=None
    if patch:
        Fref,uref,df=ref_patch(delta)
        Uactual=.5*np.sum(Fpatch*delta,axis=1)*.001
        D=IE-Uactual
        mask=np.ones(len(t),bool)
        if c.get('contact'):mask=delta[:,2]>=-1e-8
        force_error=float(np.max(abs(Fpatch[mask]-Fref[mask]))/max(CFG['joint']['normal_Fp_N'],CFG['joint']['tangent_Fp_N']))
        Wref=np.r_[0,np.cumsum(np.sum((Fref[1:]+Fref[:-1])*.5*np.diff(delta,axis=0),axis=1))]*.001
        ref_error=float(np.max(abs(Wref-IE))/max(float(IE.max()),1e-9))
    starter=(d/(meta['name']+'_0000.out')).read_text(errors='replace');warnings=re.findall(r'^WARNING ID\s*:\s*(\d+)',starter,re.M)
    normal='NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace')
    fixed_window=t>c['path'][-2][0]+.5*(t[-1]-c['path'][-2][0])
    griptorque=np.cross(x,force)+couple
    Mleft=griptorque[:,left].sum(axis=1);Mright=griptorque[:,right].sum(axis=1)
    # Mean terminal grip wrench is checked as quasi-static only if stored KE is small.
    meanF=grip_right[fixed_window].mean(axis=0);meanM=Mright[fixed_window].mean(axis=0)
    stats={'case':name,'time_end_ms':float(t[-1]),'shells':len(meta['quads']),'nodes':nn,'cohesive_elements':nb,'normal_termination':normal,'warning_ids':warnings,
        'mass_initial_g':float(a[0,6]),'cohesive_mass_reported_g':float(a[0,33]),'cohesive_mass_geometry_g':meta['cohesive_mass_g'],
        'mass_relative_error':float(abs(a[0,6]-meta['initial_mass_g'])/meta['initial_mass_g']),
        'mass_variation_fraction':float(np.max(abs(a[:,6]-a[0,6]))/a[0,6]),'added_mass_fraction':float(np.max(abs(a[:,17]))/a[0,6]),
        'energy_residual_fraction':float(np.max(abs(residual))/scale),'boundary_work_error_fraction':float(np.max(abs(externalW-a[:,9]*.001))/scale),
        'linear_impulse_error_fraction':float(np.max(np.linalg.norm(J-(P-P[0]),axis=1))/pscale),
        'orbital_angular_impulse_residual_fraction':float(np.max(np.linalg.norm(angular-(L-L[0]),axis=1))/rscale),
        'spin_angular_momentum_included':False,'nodal_global_KE_error_fraction':float(np.max(abs(nodalKE-a[:,2]*.001))/scale),
        'final_joint_work_J':float(IE[-1]),'final_plate_energy_J':float((a[-1,23]+a[-1,27])*.001),'final_KE_J':float((a[-1,2]+a[-1,8])*.001),'final_contact_energy_J':float(a[-1,11]*.001),
        'peak_right_force_N':float(np.max(np.linalg.norm(grip_right,axis=1))),
        'final_mean_right_force_N':meanF.tolist(),'final_mean_right_moment_about_origin_Nmm':meanM.tolist(),
        'terminal_mean_force_imbalance_N':float(np.linalg.norm((grip_left+grip_right)[fixed_window].mean(axis=0))),
        'terminal_mean_moment_imbalance_Nmm':float(np.linalg.norm((Mleft+Mright)[fixed_window].mean(axis=0))),
        'max_nodal_rotation_rate_rad_ms':float(np.max(abs(vr))),'max_z_motion_mm':float(np.max(abs(node[:,:,2]))),
        'all_separated':bool((off[-1]==0).all()),'any_separated':bool((off==0).any()),
        'max_contact_energy_J':float(np.max(abs(a[:,11]))*.001),'max_contact_elastic_J':float(np.max(abs(a[:,13]))*.001),
        'coupon_force_error_fraction':force_error,'coupon_work_error_fraction':ref_error,
        'min_coupon_dissipation_J':float(D.min()) if D is not None else None,
        'min_coupon_dissipation_increment_J':float(np.diff(D).min()) if D is not None else None,
        'seconds':sum(r['seconds'] for r in json.loads((d/'execution.json').read_text()))}
    lower=set(np.array(meta['quads'])[np.array(meta['parts'])==1].flatten());upper=set(meta['top'])
    checks={'normal_termination':normal,'only_declared_gap_warning':(not warnings) or (set(warnings)=={'94'} and not lower.intersection(upper)),
        'cohesive_mass_matches_reference':abs(a[0,33]-meta['cohesive_mass_g'])<1e-6*max(a[0,33],1e-15),
        'mass_from_geometry':stats['mass_relative_error']<gate['mass_relative'],
        'mass_preserved':stats['mass_variation_fraction']<gate['mass_relative'],'no_mass_scaling':stats['added_mass_fraction']<gate['mass_relative'],
        'global_energy':stats['energy_residual_fraction']<gate['global_energy_relative'],'boundary_work':stats['boundary_work_error_fraction']<gate['boundary_work_relative'],
        'linear_impulse_balance':stats['linear_impulse_error_fraction']<gate['momentum_relative'],
        'nodal_global_KE':stats['nodal_global_KE_error_fraction']<gate['global_energy_relative'],
        'no_healing':all(not (off[:,k]==0).any() or (off[np.argmax(off[:,k]==0):,k]==0).all() for k in range(nb)),
        'part_element_work_agreement':float(np.max(abs(brick[:,:,1].sum(axis=1)*.001-IE)))<1e-5*max(1,float(IE.max())),
        'complete_history':meta['end_ms']-t[-1]<2.1*meta['history_dt_ms']}
    if patch:
        checks.update(coupon_force_law=force_error<gate['coupon_force_relative'],coupon_work=ref_error<gate['coupon_energy_relative'],
            dissipation_nonnegative=stats['min_coupon_dissipation_J']>=-gate['dissipation_floor_J'],
            dissipation_non_decreasing=stats['min_coupon_dissipation_increment_J']>=-gate['dissipation_floor_J'],
            moment_balance=stats['orbital_angular_impulse_residual_fraction']<gate['coupon_moment_relative'],full_separation=stats['all_separated'])
    if 'ELASTIC' in name:
        checks['no_deletion']=not stats['any_separated']
        checks['quasistatic_force_balance']=stats['terminal_mean_force_imbalance_N']/max(np.linalg.norm(meanF),1e-9)<gate['momentum_relative']
        checks['quasistatic_moment_balance']=stats['terminal_mean_moment_imbalance_Nmm']/max(np.linalg.norm(meanM),1e-9)<gate['coupon_moment_relative']
        checks['quasistatic_kinetic_small']=stats['final_KE_J']/max(scale,1e-9)<gate['global_energy_relative']
    if patch:
        failed=off[:,0]==0
        checks['zero_cohesive_force_after_failure']=not failed.any() or np.max(np.linalg.norm(Fpatch[failed],axis=1))<gate['postfailure_force_N']
    checks={k:bool(v) for k,v in checks.items()}
    stats.update(checks=checks,status='PASS' if all(checks.values()) else 'FAIL')
    hist={'time_ms':t.tolist(),'grip_right_force_N':(grip_right@R).tolist(),'grip_left_force_N':(grip_left@R).tolist(),
        'grip_right_moment_origin_Nmm':(Mright@R).tolist(),'grip_left_moment_origin_Nmm':(Mleft@R).tolist(),
        'joint_work_J':IE.tolist(),'kinetic_J':((a[:,2]+a[:,8])*.001).tolist(),'plate_energy_J':((a[:,23]+a[:,27])*.001).tolist(),'contact_energy_J':(a[:,11]*.001).tolist(),
        'external_work_J':(a[:,9]*.001).tolist(),'energy_residual_J':residual.tolist(),'active_fraction':(off@areas/sum(areas)).tolist()}
    if patch:hist.update(coupon_delta_mm=delta.tolist(),coupon_force_N=Fpatch.tolist(),coupon_boundary_force_N=Fboundary.tolist(),coupon_reference_force_N=Fref.tolist(),coupon_reference_U_J=uref.tolist(),coupon_U_J=Uactual.tolist(),coupon_D_J=D.tolist())
    sel=np.linspace(0,len(t)-1,31,dtype=int)
    np.savez_compressed(d/'computed_frames.npz',points_mm=x[sel],times_ms=t[sel],quads=np.array(meta['quads'])-1,parts=np.array(meta['parts']),bricks=np.array(meta['bricks'])-1,active=off[sel])
    dump(d/'column_map.json',{'global':headers[:23],'part_start':23,'part_variables':['IE','KE','MASS','HE'],'brick_start':35,'brick_variables':['OFF','IE','LSX','LSY','LSZ','LSXY','LSYZ','LSXZ'],'node_start':start,'node_variables':['DX','DY','DZ','VX','VY','VZ','VRX','VRY','VRZ','REACX','REACY','REACZ','REACXX','REACYY','REACZZ'],'REAC_units':'cumulative Nms and Nmmms, independently checked against momentum/work','raw_node_ids':ids})
    dump(d/'history.json',hist);dump(d/'results.json',stats)
    return stats
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();r=audit(a.case)
    print(json.dumps(r,indent=2));sys.exit(0 if r['status']=='PASS' else 1)
