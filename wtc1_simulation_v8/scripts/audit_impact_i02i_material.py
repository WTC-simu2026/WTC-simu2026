"""Independent 1D return reference, kinematic power and differentiated support impulse."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/'wtc1_simulation_v8/data/impact_i02i_material_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02i_material'

def dump(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False,default=lambda v:v.item())+'\n',encoding='utf-8',newline='\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def grouped(headers,title,n):
    cols={}
    for j,h in enumerate(headers):
        m=re.match(re.escape(title)+r'\s+(\d+)\s+.*var\s+(\d+)$',h)
        if m: cols.setdefault(int(m[1]),[]).append((int(m[2]),j))
    if any(len(v)!=n for v in cols.values()): raise ValueError('Invalid CSV group width')
    return {k:[j for _,j in sorted(v)] for k,v in cols.items()}
def reference(strains,curve,E):
    """Closed piecewise-linear positive-tension return, path dependent unloading."""
    cr=np.array(curve); ep=0.; stresses=[]; plastics=[]
    for e in strains:
        trial=E*(e-ep); y=np.interp(ep,cr[:,0],cr[:,1])
        if trial>y:
            for (p0,s0),(p1,s1) in zip(cr[:-1],cr[1:]):
                H=(s1-s0)/(p1-p0); root=(E*e-s0+H*p0)/(E+H)
                if p0-1e-12<=root<=p1+1e-12:
                    ep=max(ep,root); break
            else: raise ValueError('Beyond reference domain')
        stresses.append(E*(e-ep)); plastics.append(ep)
    return np.array(stresses),np.array(plastics)
def cumulative(x): return np.r_[0.,np.cumsum(x)]
def relative_curve(a,b,scale): return float(np.max(np.abs(a-b))/scale)

def audit_case(folder,cfg,dest):
    dest.mkdir(parents=True,exist_ok=False)
    meta=json.loads((folder/'generation.json').read_text()); name=meta['name']
    with (folder/(name+'T01.csv')).open(newline='') as f:
        reader=csv.reader(f); headers=next(reader); data=np.array(list(reader),float)
    if not np.isfinite(data).all(): raise ValueError('Nonfinite history')
    ncols=grouped(headers,'NODES',6); scols=grouped(headers,'SHELL',9)
    # This untitled T01 format orders output IDs canonically, not in request order.
    # Validate mapping against initial thickness/activation and independent geometry.
    shell=data[:,scols[1]]
    sx,sy,sxy,IEM,off,th,p,e1,e2=shell.T
    t=data[:,0]; g=cfg['geometry']; E=cfg['material']['young_modulus_mpa']; nu=cfg['material']['poisson_ratio']; V0=g['length_mm']*g['width_mm']*g['thickness_mm']
    coords=np.tile(np.array([[0,0],[g['length_mm'],0],[g['length_mm'],g['width_mm']],[0,g['width_mm']]]),(len(t),1,1)).astype(float)
    velocities=np.zeros_like(coords); impulses=np.zeros_like(coords)
    for nid,cols in ncols.items():
        coords[:,nid-1,:]+=data[:,cols[:2]]; velocities[:,nid-1,:]=data[:,cols[2:4]]; impulses[:,nid-1,:]=data[:,cols[4:6]]
    dx1=.5*(coords[:,1]+coords[:,2]-coords[:,0]-coords[:,3]); dx2=.5*(coords[:,2]+coords[:,3]-coords[:,0]-coords[:,1])
    J=np.stack([dx1,dx2],axis=2); length=np.linalg.norm(dx1,axis=1); width=np.linalg.norm(dx2,axis=1)
    small=meta['case']['shell']=='small'; strain=(length/g['length_mm']-1) if small else np.log(length/g['length_mm'])
    sigma_ref,p_ref=reference(strain,meta['curve'],E)
    axial_scale=max(float(np.max(np.abs(sigma_ref))),meta['curve'][0][1] if meta['case']['path']!='elastic' else 0.)
    mapping_checks={'initial_thickness':abs(th[0]-g['thickness_mm'])<1e-9,'initial_activation':off[0]==(2. if small else 1.),'E1_kinematics':np.max(np.abs(e1-strain))<1e-5,'IEM_internal_energy':np.max(np.abs(IEM-data[:,1]))<.01}
    if not all(mapping_checks.values()): raise ValueError('Canonical CSV variable mapping failed independent checks')
    ie=data[:,headers.index('INTERNAL ENERGY')]*.001; ke=data[:,headers.index('KINETIC ENERGY')]*.001; we=data[:,headers.index('EXTERNAL WORK')]*.001; dp=data[:,headers.index('PLASTIC WORK')]*.001
    energy_scale=max(float(np.max(np.abs(ie))),float(np.max(np.abs(we))))
    # Actual area and corotated stresses are used; small formulation uses initial Jacobian/volume.
    area=np.abs(np.linalg.det(J)); volume=area*th
    unit=dx1/length[:,None]; Q=np.stack([unit,np.stack([-unit[:,1],unit[:,0]],axis=1)],axis=2)
    slocal=np.zeros((len(t),2,2)); slocal[:,0,0]=sx; slocal[:,1,1]=sy; slocal[:,0,1]=slocal[:,1,0]=sxy
    S=Q@slocal@np.swapaxes(Q,1,2)
    Jmid=.5*(J[1:]+J[:-1]); strain_increment=(J[1:]-J[:-1])@np.linalg.inv(np.tile(J[0],(len(t)-1,1,1)) if small else Jmid)
    dwork=np.einsum('nij,nij->n',.5*(S[1:]+S[:-1]),strain_increment)*(V0 if small else .5*(volume[1:]+volume[:-1]))*.001
    stress_work=cumulative(dwork)
    # Independently reconstruct actuator work from reaction impulses, no stress channel involved.
    reaction_interval=np.diff(impulses,axis=0)/np.diff(t)[:,None,None]
    displacement_increment=np.diff(coords,axis=0)
    boundary_work=cumulative(np.sum(reaction_interval*displacement_increment,axis=(1,2))*.001)
    raw_right=impulses[:,1,0]+impulses[:,2,0]
    support_left_interval=reaction_interval[:,0,0]+reaction_interval[:,3,0]
    support_right_interval=reaction_interval[:,1,0]+reaction_interval[:,2,0]
    expected_force=sx*(g['thickness_mm']*g['width_mm'] if small else th*width)
    # 1D reference plastic work including elastic volume change; small strain has fixed initial volume.
    pmax=np.maximum.accumulate(p_ref)
    pgrid=np.unique(np.r_[np.linspace(0,max(float(pmax[-1]),1e-16),20001),np.array(meta['curve'])[:,0]])
    pgrid=pgrid[pgrid<=max(float(pmax[-1]),1e-16)]
    sgrid=np.interp(pgrid,np.array(meta['curve'])[:,0],np.array(meta['curve'])[:,1])
    vgrid=V0 if small else V0*np.exp((1-2*nu)*sgrid/E)
    integrand=sgrid*vgrid
    Dgrid=cumulative(.5*(integrand[1:]+integrand[:-1])*np.diff(pgrid))*.001
    Dref=np.interp(pmax,pgrid,Dgrid)
    sigwindow=ie>.01*np.max(ie)
    stats={
        'stress_reference_error_fraction':relative_curve(sx,sigma_ref,axial_scale),
        'plastic_strain_reference_error_absolute':float(np.max(np.abs(p-p_ref))),
        'transverse_stress_over_axial_scale':float(np.max(np.abs(sy))/axial_scale),
        'mass_error_fraction':float(np.max(np.abs(data[:,6]-meta['expected_mass_g']))/meta['expected_mass_g']),
        'global_energy_residual_fraction':relative_curve(we,ie+ke,energy_scale),
        'internal_stress_work_error_fraction':relative_curve(stress_work,ie,energy_scale),
        'independent_boundary_work_error_fraction':relative_curve(boundary_work,we,energy_scale),
        'plastic_work_reference_error_fraction':relative_curve(dp,Dref,energy_scale),
        'negative_plastic_increment':float(max(0.,-np.min(np.diff(p)))),
        'maximum_kinetic_to_internal_significant_window':float(np.max(ke[sigwindow]/ie[sigwindow])),
        'final_stress_MPa':float(sx[-1]),'final_plastic_strain':float(p[-1]),'final_thickness_mm':float(th[-1]),
        'final_internal_energy_J':float(ie[-1]),'final_plastic_work_J':float(dp[-1]),'final_elastic_energy_by_difference_J':float(ie[-1]-dp[-1]),'final_reference_plastic_work_J':float(Dref[-1]),
        'final_external_work_J':float(we[-1]),'final_boundary_work_J':float(boundary_work[-1]),'final_stress_work_J':float(stress_work[-1]),
        'raw_right_REAC_end_N_ms':float(raw_right[-1]),
        'force_impulse_derivative_vs_stress_fraction':relative_curve(support_right_interval,.5*(expected_force[1:]+expected_force[:-1]),float(np.max(np.abs(expected_force)))),
        'sampled_end_ms':float(t[-1]),'requested_end_ms':meta['end_ms'],'minimum_saved_dt_ms':float(np.min(np.diff(t))),'maximum_saved_dt_ms':float(np.max(np.diff(t))),
        'last_source_point_plastic_strain':meta['curve'][-2][0],'maximum_plastic_strain':float(np.max(p))
    }
    if meta['case']['interpretation']=='engineering' and not small:
        # The conventional engineering->true formula assumes approximately conserved volume.
        # Compare boundary stress from current area against sigma_true / lambda, quantify approximation.
        stats['nominal_stress_conversion_error_fraction']=relative_curve(expected_force/(g['width_mm']*g['thickness_mm']),sigma_ref/(length/g['length_mm']),axial_scale)
    starter=(folder/(name+'_0000.out')).read_text(errors='replace'); engine=(folder/(name+'_0001.out')).read_text(errors='replace'); execution=json.loads((folder/'execution.json').read_text())
    flags=re.search(r'Ishell\s+Ismstr\s+Idril\s+NPT\s+ITHK\s+IPLAS\s+IPOS\s*\n\s*([\d\s-]+)\n',starter)
    resolved=[int(v) for v in flags[1].split()] if flags else []
    checks={'normal_termination':'NORMAL TERMINATION' in engine and 'ERROR TERMINATION' not in engine,'zero_starter_warnings':not re.search(r'WARNING ID',starter),'zero_engine_warnings':not re.search(r'WARNING ID',engine),'all_jobs_success':len(execution)==3 and all(v['returncode']==0 for v in execution),'no_deletion':bool(np.all(off>=1.)),'config_matches':meta['config_sha256']==sha(CFG),'resolved_flags_present':len(resolved)==7,'last_output_covers_end':meta['end_ms']-t[-1]<max(1.01*cfg['execution']['history_dt_ms']*meta['case'].get('time_factor',1.),.002)}
    if meta['case']['shell']=='finite': checks['explicit_finite_flags']=resolved[:2]==[24,4] and resolved[4:6]==[1,1]
    for key,value in stats.items():
        gate='maximum_'+key
        if gate in cfg['gates']: checks[key]=value<=cfg['gates'][gate]
    checks['kinetic_significant_window']=stats['maximum_kinetic_to_internal_significant_window']<=cfg['gates']['maximum_kinetic_to_internal_significant_window']
    checks['no_extrapolated_plastic_strain']=stats['maximum_plastic_strain']<=stats['last_source_point_plastic_strain']+1e-6
    result=dict(case=meta['case'],metrics=stats,checks=checks,pass_all_checks=all(checks.values()),resolved_shell_flags=dict(zip(['Ishell','Ismstr','Idril','NPT','ITHK','IPLAS','IPOS'],resolved)),mapping_checks=mapping_checks,states=len(t),execution_seconds=sum(v['seconds'] for v in execution),note='Inherited/small controls retain failed gates; only finite variants are candidates for forward numerical qualification.')
    hrows=[{'time_ms':float(t[j]),'engineering_strain':float(length[j]/g['length_mm']-1),'solver_strain':float(strain[j]),'stress_MPa':float(sx[j]),'reference_stress_MPa':float(sigma_ref[j]),'plastic_strain':float(p[j]),'reference_plastic_strain':float(p_ref[j]),'thickness_mm':float(th[j]),'internal_energy_J':float(ie[j]),'plastic_work_J':float(dp[j]),'reference_plastic_work_J':float(Dref[j]),'external_work_J':float(we[j]),'boundary_work_J':float(boundary_work[j]),'stress_work_J':float(stress_work[j]),'right_impulse_N_ms':float(raw_right[j])} for j in range(len(t))]
    with (dest/'verified_history.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(hrows[0])); w.writeheader(); w.writerows(hrows)
    # Keep intervals explicitly: differentiated impulses are interval average reactions.
    with (dest/'support_intervals.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['start_ms','end_ms','right_reaction_N','left_reaction_N','stress_force_average_N'])
        w.writerows(zip(t[:-1],t[1:],support_right_interval,support_left_interval,.5*(expected_force[1:]+expected_force[:-1])))
    dump(dest/'audit.json',result)
    return result,hrows

def figure(paths,out):
    im=Image.new('RGB',(1450,960),'#f4f6fa'); d=ImageDraw.Draw(im)
    fontpath='C:/Windows/Fonts/arial.ttf'
    f=ImageFont.truetype(fontpath,21); title=ImageFont.truetype(fontpath,30); small=ImageFont.truetype(fontpath,17)
    d.text((45,24),'WTC1 - I02I-A : traction elementaire LAW36',font=title,fill='#172b4d')
    d.text((45,68),'Cas generiques neufs | Aucun impact physique ou effondrement valide',font=f,fill='#784400')
    panels=[(70,160,675,505,'Contrainte vraie (MPa)',.18,600),(805,160,1400,505,'Epaisseur (mm)',.18,2.4),(70,610,675,915,'Travail des appuis (J) : charge et cycle',.18,18),(805,610,1400,915,'Erreur de contrainte / pic de reference (%)',.18,6.5)]
    colors={'ENG_FINITE_R3':'#146c94','TRUE_FINITE_R3':'#6b4fc6','ENG_LEGACY_R3':'#c54e30','TRUE_LEGACY_R3':'#99724c'}
    for left,top,right,bottom,label,xmax,ymax in panels:
        d.rectangle((left,top,right,bottom),fill='white',outline='#a6b5c9'); d.text((left,top-35),label,font=f,fill='#243b53')
        for q in range(5):
            y=bottom-q/4*(bottom-top); d.line((left,y,right,y),fill='#e2e8f0'); d.text((left-57,y-11),f'{ymax*q/4:g}',font=small,fill='#526477')
        for q in range(4):
            x=left+q/3*(right-left); d.text((x-16,bottom+8),f'{xmax*q/3:.2f}',font=small,fill='#526477')
        d.text((left+150,bottom+26),'Deformation nominale : allongement / L0',font=small,fill='#526477')
    for idx,(l,t,r,b,label,xmax,ymax) in enumerate(panels):
        selected=colors if idx!=2 else {'ENG_FINITE_R3':'#146c94','ENG_FINITE_CYCLE_R3':'#239b56'}
        for name,color in selected.items():
            rows=paths[name]; pts=[]
            for row in rows:
                x=row['engineering_strain']; y=row['stress_MPa'] if idx==0 else row['thickness_mm'] if idx==1 else row['boundary_work_J'] if idx==2 else 100*abs(row['stress_MPa']-row['reference_stress_MPa'])/max(v['reference_stress_MPa'] for v in rows)
                pts.append((l+x/xmax*(r-l),b-y/ymax*(b-t)))
            d.line(pts,fill=color,width=3)
        if idx in [0,1]:
            for j,(name,color) in enumerate(colors.items()): d.text((l+10,t+12+24*j),name.replace('_R3',''),font=small,fill=color)
    im.save(out)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default=str(OUT/'verification_r1')); args=parser.parse_args(); dest=Path(args.output)
    if not dest.is_absolute(): dest=ROOT/dest
    dest.mkdir(parents=True,exist_ok=False); start=time.perf_counter(); cfg=json.loads(CFG.read_text())
    results={}; paths={}
    for case in cfg['cases']:
        r,p=audit_case(OUT/case['id'],cfg,dest/case['id']); results[case['id']]=r; paths[case['id']]=p
    finite=[r for r in results.values() if r['case']['shell']=='finite']
    comparisons={}
    base=paths['ENG_FINITE_R3']; xx=np.array([v['engineering_strain'] for v in base]); ss=np.array([v['stress_MPa'] for v in base]); scale=max(ss)
    # Monotone common engineering strain, no arbitrary time alignment.
    for name in ['ENG_FINITE_DT45_R3','ENG_FINITE_SLOW_R3']:
        other=paths[name]; x2=np.array([v['engineering_strain'] for v in other]); s2=np.array([v['stress_MPa'] for v in other]); ux,ids=np.unique(x2,return_index=True)
        comparisons[name]={'stress_difference_fraction':float(np.max(np.abs(ss-np.interp(xx,ux,s2[ids])))/scale),'final_plastic_work_difference_fraction':abs(results[name]['metrics']['final_plastic_work_J']-results['ENG_FINITE_R3']['metrics']['final_plastic_work_J'])/results['ENG_FINITE_R3']['metrics']['final_plastic_work_J']}
    # Both curves at same displacement are an interpretation sensitivity, not experiments.
    true=paths['TRUE_FINITE_R3']; tx=np.array([r['engineering_strain'] for r in true]); ts=np.array([r['stress_MPa'] for r in true]); comparisons['interpretations_at_engineering_strain_0p10']={name:float(np.interp(.10,xx if name=='engineering' else tx,ss if name=='engineering' else ts)) for name in ['engineering','true_total']}
    # Raw reaction impulse grows with loading duration; differentiated work closes independently.
    comparisons['raw_reaction_duration_ratio']=results['ENG_FINITE_SLOW_R3']['metrics']['raw_right_REAC_end_N_ms']/results['ENG_FINITE_R3']['metrics']['raw_right_REAC_end_N_ms']
    preservation=json.loads((OUT/'preservation_before.json').read_text()); failures=[e['path'] for e in preservation['files'] if sha(ROOT/e['path'])!=e['sha256']]
    checks={'finite_cases_all_gates_pass':all(r['pass_all_checks'] for r in finite),'all_ten_cases_normal_termination':all(r['checks']['normal_termination'] for r in results.values()),'all_ten_cases_warning_free':all(r['checks']['zero_starter_warnings'] and r['checks']['zero_engine_warnings'] for r in results.values()),'half_dt_stress':comparisons['ENG_FINITE_DT45_R3']['stress_difference_fraction']<=cfg['gates']['maximum_half_dt_stress_difference_fraction'],'slow_stress':comparisons['ENG_FINITE_SLOW_R3']['stress_difference_fraction']<=cfg['gates']['maximum_slow_stress_difference_fraction'],'old_files_preserved':not failures,'interpretations_separate':len(comparisons['interpretations_at_engineering_strain_0p10'])==2,'no_material_convention_promotion':cfg['qualification']['source_convention_verified']==False}
    allcheck=[v for r in results.values() for v in r['checks'].values()]
    finitecheck=[v for r in finite for v in r['checks'].values()]
    summary=dict(id=cfg['id'],created_utc=datetime.now(timezone.utc).isoformat(),cases=results,comparisons=comparisons,campaign_checks=checks,campaign_pass=all(checks.values()),case_checks_passed=sum(allcheck),case_checks_total=len(allcheck),finite_checks_passed=sum(finitecheck),finite_checks_total=len(finitecheck),finite_cases=len(finite),preservation={'files_checked':len(preservation['files']),'failures':failures},accepted_solver_execution_seconds=sum(r['execution_seconds'] for r in results.values()),audit_seconds=time.perf_counter()-start,software={'python':sys.version,'numpy':np.__version__},source_convention_verified=False,physical_propagation_qualified=False,remaining_I02I_work=cfg['deferred_I02I_work'])
    dump(dest/'summary_i02i_material.json',summary); figure(paths,dest/'synthese_i02i_material.png')
    print(json.dumps({k:summary[k] for k in ['campaign_pass','case_checks_passed','case_checks_total','finite_checks_passed','finite_checks_total','finite_cases','accepted_solver_execution_seconds']},default=lambda v:v.item()))
    print(json.dumps({name:{'pass':r['pass_all_checks'],'failed':[k for k,v in r['checks'].items() if not v],'metrics':r['metrics']} for name,r in results.items()},indent=2,default=lambda v:v.item()))

if __name__=='__main__': main()
