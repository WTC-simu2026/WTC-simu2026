"""Read-back force/history, nodal kinematics, strip compliance and energy audit."""
from __future__ import annotations
import argparse,csv,hashlib,json,re,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'wtc1_simulation_v8/data/impact_i02c_deformable_joint.json').read_text())
OUT=ROOT/CFG['output_root']
def dump(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False,default=lambda v:v.item())+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def reference(x,peak,d0,df):
    slip=np.zeros(x.shape[1]);failed=np.zeros(x.shape[1],bool);forces=[]
    for d in x:
        failed|=d>=df
        env=np.where(d<=d0,peak*d/d0,peak*(df-d)/(df-d0))
        force=np.minimum(np.maximum(peak/d0*(d-slip),0),np.maximum(env,0));force[failed]=0
        slip=np.maximum(slip,d-force/(peak/d0));forces.append(force.copy())
    return np.array(forces)

def audit(name):
    directory=OUT/name;m=json.loads((directory/'generation.json').read_text());c=m['case'];g=CFG['geometry'];material=CFG['material'];gate=CFG['gates']
    with (directory/(m['name']+'T01.csv')).open() as stream:
        headers=next(csv.reader(stream));a=np.loadtxt(stream,delimiter=',')
    nn=len(m['nodes_mm']);ns=len(m['links']);assert a.shape[1]==31+8*ns+3*nn
    part=a[:,23:31].reshape(len(a),2,4);spring=a[:,31:31+8*ns].reshape(len(a),ns,8)
    nodes=a[:,31+8*ns:].reshape(len(a),nn,3)
    ids=[int(re.search(r'NODE_HISTORY\s+(\d+)',headers[31+8*ns+3*j]).group(1)) for j in range(nn)]
    nodes=nodes[:,[ids.index(n) for n in range(1,nn+1)],:]
    off=spring[:,:,0];F=spring[:,:,1+m['local_axis']];delta=spring[:,:,4+m['local_axis']]
    IE=spring[:,:,-1].sum(axis=1)*.001;weight=np.array(m['weights']);K=m['peak_N']/m['d0_mm']*weight*c.get('stiffness_pad',1)
    ref=reference(delta,m['peak_N']*weight,m['d0_mm'],m['df_mm'])
    U=(F*F/(2*K)).sum(axis=1)*.001;D=IE-U
    W=np.r_[0,np.cumsum(np.sum((F[1:]+F[:-1])*.5*np.diff(delta,axis=0),axis=1))]*.001
    displacement=nodes[:,:,0];v=nodes[:,:,1];impulse=nodes[:,:,2].sum(axis=1)*.001
    links=np.array(m['links'])-1
    opening=displacement[:,links[:,1]]-displacement[:,links[:,0]]
    masses=np.array(m['nodal_mass_g']);P=(v*masses).sum(axis=1)*.001;dP=P-P[0]
    KE_node=(v*v*masses).sum(axis=1)*.0005
    energy=(a[:,1]+a[:,2]+a[:,8]-a[0,1]-a[0,2]-a[0,8]-a[:,9])*.001
    energy_scale=max(float(np.max(abs(a[:,9]))*.001),float(np.max(a[:,1]+a[:,2])*.001),1e-9)
    momentum_scale=max(float(np.max(abs(dP))),float(np.max(abs(impulse))),float(abs(P[0])),1e-9)
    globalP=a[:,3+m['axis']]*.001
    starter=(directory/(m['name']+'_0000.out')).read_text(errors='replace');warnings=re.findall(r'^WARNING ID\s*:\s*(\d+)',starter,re.M)
    normal='NORMAL TERMINATION' in (directory/'engine.log').read_text(errors='replace')
    force=F.sum(axis=1);failed=off==0
    unwanted=np.delete(spring[:,:,1:4],m['local_axis'],axis=2)
    q=np.array(m['quads'])-1;p0=np.array(m['nodes_mm']);R=np.array(m['rotation']);local=p0@R
    # Longitudinal engineering strain of each shell's two x-directed edges.
    du=.5*(displacement[:,q[:,1]]-displacement[:,q[:,0]]+displacement[:,q[:,2]]-displacement[:,q[:,3]])
    lengths=local[q[:,1],0]-local[q[:,0],0]
    strain=du/lengths if c['mode']=='shear' else np.zeros_like(du)
    stats={'case':name,'normal_termination':normal,'warning_ids':warnings,'nodes':nn,'shells':len(q),'connectors':ns,
        'time_end_ms':float(a[-1,0]),'initial_energy_J':float(a[0,2]*.001),'final_kinetic_J':float(a[-1,2]*.001),
        'joint_energy_J':float(IE[-1]),'joint_dissipation_J':float(D[-1]),'expected_full_joint_energy_J':m['full_joint_energy_J'],
        'final_plate_energy_J':float(part[-1,:,0].sum()*.001),'peak_force_N':float(force.max()),
        'max_force_law_error_fraction':float(np.max(abs(F-ref)/(m['peak_N']*weight))),
        'joint_work_error_fraction':float(np.max(abs(W-IE))/max(float(np.max(abs(IE))),1e-9)),
        'energy_residual_fraction':float(np.max(abs(energy))/energy_scale),'energy_scale_J':energy_scale,
        'momentum_error_fraction':float(np.max(abs(impulse-dP))/momentum_scale),
        'nodal_global_momentum_error_fraction':float(np.max(abs(P-globalP))/momentum_scale),
        'nodal_global_kinetic_error_fraction':float(np.max(abs(KE_node-a[:,2]*.001))/energy_scale),
        'opening_identity_error_mm':float(np.max(abs(opening-delta))),
        'min_dissipation_J':float(D.min()),'min_dissipation_increment_J':float(np.diff(D).min()),
        'any_separated':bool(failed.any()),'all_separated':bool(failed[-1].all()),
        'final_active_fraction':float(np.sum(off[-1]*weight)/sum(weight)),
        'max_parasitic_force_N':float(np.max(abs(unwanted))),
        'mass_initial_g':float(a[0,6]),'mass_final_g':float(a[-1,6]),'max_added_mass_g':float(abs(a[:,17]).max()),
        'max_longitudinal_strain':float(abs(strain).max()) if c['mode']=='shear' else None,
        'max_longitudinal_stress_proxy_MPa':float(abs(strain).max()*material['E_MPa']/(1-material['nu']**2)) if c['mode']=='shear' else None,
        'min_signed_slip_mm':float(delta.min()),'max_signed_slip_mm':float(delta.max()),
        'first_negative_slip_time_ms':float(a[np.argmax(np.min(delta,axis=1)<-1e-5),0]) if (delta<-1e-5).any() else None,
        'max_relative_motion_mm':float(abs(delta).max()),
        'seconds':sum(r['seconds'] for r in json.loads((directory/'execution.json').read_text()))}
    checks={'normal_termination':normal,'only_declared_null_inertia_warnings':len(warnings)==ns and set(warnings)=={'445'} and starter.count('NULL INERTIA')==ns,
        'force_law':stats['max_force_law_error_fraction']<gate['force_law_relative'],
        'joint_force_work':stats['joint_work_error_fraction']<gate['work_relative'],
        'global_energy':stats['energy_residual_fraction']<gate['global_energy_relative'],
        'momentum_balance':stats['momentum_error_fraction']<gate['momentum_relative'],
        'independent_nodal_momentum':stats['nodal_global_momentum_error_fraction']<gate['momentum_relative'],
        'joint_kinematic_identity':stats['opening_identity_error_mm']<1e-5,
        'dissipation_nonnegative':stats['min_dissipation_J']>=-gate['dissipation_floor_J'],
        'dissipation_non_decreasing':stats['min_dissipation_increment_J']>=-gate['dissipation_floor_J'],
        'no_parasitic_force':stats['max_parasitic_force_N']<.001,
        'mass_from_geometry':abs(a[0,6]-m['initial_mass_g'])/m['initial_mass_g']<gate['mass_relative'],
        'mass_preserved':abs(a[-1,6]-a[0,6])/a[0,6]<gate['mass_relative'],
        'no_mass_scaling':stats['max_added_mass_g']/m['initial_mass_g']<gate['mass_relative'],
        'complete_sampling':m['end_ms']-a[-1,0]<2.1*m['history_dt_ms'],
        'one_sided_law_domain':float(delta.min())>=-1e-5,
        'independent_nodal_kinetic_energy':c['mode']=='normal' or stats['nodal_global_kinetic_error_fraction']<gate['global_energy_relative']}
    if failed.any():
        checks['no_healing']=all(not failed[:,j].any() or failed[np.argmax(failed[:,j]):,j].all() for j in range(ns))
        checks['no_force_after_separation']=bool(np.max(abs(F[failed]))<gate['no_healing_force_N'])
    if c['loading'] in ('mono','cycle'):
        checks['full_joint_separation']=stats['all_separated']
        checks['full_separation_energy']=abs(IE[-1]-m['full_joint_energy_J'])/m['full_joint_energy_J']<gate['work_relative']
    if c['loading']=='elastic':
        E=material['E_MPa']/(1-material['nu']**2);L=g['strip_length_mm'];b=g['width_mm'];t1=g['skin_thickness_mm'];t2=g['flange_thickness_mm']
        if c['mode']=='shear':compliance=L/(E*b)*(1/t1+1/t2)
        else:
            compliance=4*L**3/(E*b)*(1/t1**3+1/t2**3)+L/((5/6)*material['E_MPa']/(2*(1+material['nu']))*b)*(1/t1+1/t2)
        compliance+=1/sum(K);expected=.01/compliance
        window=a[:,0]>.95*m['end_ms']; measured=float(np.mean(force[window]))
        stats.update(elastic_reference_force_N=expected,elastic_measured_force_N=measured,elastic_compliance_error_fraction=abs(measured-expected)/expected)
        checks['elastic_closed_form_compliance']=stats['elastic_compliance_error_fraction']<gate['elastic_compliance_relative']
        checks['elastic_no_damage']=stats['max_relative_motion_mm']<m['d0_mm'] and not stats['any_separated']
    if c['loading']=='free':
        checks['free_translation_no_force']=stats['peak_force_N']<.001
        checks['free_translation_no_strain']=stats['max_longitudinal_strain']<1e-8
    stats['checks']=checks;stats['status']='PASS' if all(checks.values()) else 'FAIL'
    history={'time_ms':a[:,0].tolist(),'joint_force_N':force.tolist(),'mean_slip_mm':(delta@weight/sum(weight)).tolist(),'grip_displacement_mm':displacement[:,np.array(m['moving_nodes'])-1].mean(axis=1).tolist(),
        'joint_work_J':IE.tolist(),'recoverable_joint_J':U.tolist(),'dissipation_J':D.tolist(),'plate_energy_J':(part[:,:,0].sum(axis=1)*.001).tolist(),'kinetic_J':(a[:,2]*.001).tolist(),
        'external_work_J':(a[:,9]*.001).tolist(),'energy_residual_J':energy.tolist(),'active_fraction':(off@weight/sum(weight)).tolist(),'boundary_impulse_Ns':impulse.tolist(),'delta_momentum_Ns':dP.tolist()}
    indices=np.linspace(0,len(a)-1,31,dtype=int);points=np.repeat(p0[None,:,:],len(indices),axis=0);points[:,:,m['axis']]+=displacement[indices]
    np.savez_compressed(directory/'computed_frames.npz',points_mm=points,times_ms=a[indices,0],quads=q,parts=np.array(m['parts']),links=links,active=off[indices],strain=strain[indices])
    dump(directory/'history.json',history);dump(directory/'results.json',stats)
    dump(directory/'column_map.json',{'headers':headers,'global_columns':23,'part_start':23,'part_order':['IE','KE','MASS','HE'],'spring_start':31,'spring_order':['OFF','FX','FY','FZ','LX','LY','LZ','IE'],'node_start':31+8*ns,'node_order':['D','V','cumulative_REAC_impulse_Nms'],'node_ids_raw_order':ids})
    return stats

def main():
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();r=audit(a.case)
    print(json.dumps({k:v for k,v in r.items() if k not in ('checks','warning_ids') } | {'failed':[k for k,v in r['checks'].items() if not v]},indent=2))
    return 0 if r['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
