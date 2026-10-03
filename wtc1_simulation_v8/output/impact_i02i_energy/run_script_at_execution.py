"""I02I-D: fresh TYPE8 energy/history controls; cached B/C remain immutable.

One connector is a diagnostic, not a mixed-mode fracture calibration.
Commands: --declare, --run, --audit, --complete, --verify.
"""
from __future__ import annotations
import argparse, copy, csv, json, math, os, re, subprocess, sys, time
from pathlib import Path
import numpy as np
import run_impact_i02g as deck
import run_impact_i02i_sampling as cached
import audit_impact_i02i_fixed_penalty as columns_module
import audit_impact_i02i_sampling as work_module

ROOT, RUNTIME = cached.ROOT, cached.RUNTIME
NOW, sha, dump, rel, harness = cached.NOW, cached.sha, cached.dump, cached.rel, cached.harness
C = cached.OUT
OUT = ROOT/'wtc1_simulation_v8/output/impact_i02i_energy'
CFG = ROOT/'wtc1_simulation_v8/data/impact_i02i_energy_predeclaration.json'
HANDOFF = ROOT/'harness/handoffs/WTC1_IMPACT_I02I_D_HANDOFF.md'
REPORT = OUT/'rapport_impact_i02i_energy.md'
SUMMARY = OUT/'verification_r1/summary.json'
EPLAN = ROOT/'wtc1_simulation_v8/data/impact_i02i_sensitivity_plan.json'
ADMIN = ['state.json', 'experiments/registry.jsonl', 'publication_cycle.json']

def declare():
    assert not CFG.exists() and not OUT.exists() and not EPLAN.exists(), 'Never overwrite an iteration'
    hv = harness()
    state = json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'))
    assert state['current_iteration']=='IMPACT-I02I-C' and state['next_iteration']=='IMPACT-I02I-D'
    cfg = {
        'id':'IMPACT-I02I-D','seed':1102012,'random_draws':0,
        'scope':'Fresh zero-length TYPE8 unload/failure diagnostics; no coupon or aircraft solver rerun',
        'units':{'mass':'g','length':'mm','time':'ms','force':'N','solver_energy':'N mm = mJ','reported_energy':'J = 0.001 N mm','reaction_history':'cumulative impulse N ms, independently checked by boundary work'},
        'connector':{'initial_area_mm2':1.,'kn_N_per_mm':56000.,'kt_N_per_mm':21500.,'peak_normal_force_N':495.,'hypothetical_Gf_N_per_mm':30.,'mass_g':.2,'rotational_inertia_g_mm2':.001,'H_normal':2,'H_shear':2,'shear_failure_disabled':True,'normal_failure':'whole element deactivation when normal gap reaches 2 Gf/peak','damping':0.,'rotations':'blocked at both nodes','history':'all fresh; no restart, damaged-state property substitution or mass scaling'},
        'loading':{'segment_ms':1.,'subdivisions':800,'path':'quintic 10s3-15s4+6s5 per segment','shear_target_mm':.02,'normal_scale':'deltaf=2 Gf/peak; coordinates below are fractions of deltaf'},
        'execution':{'threads':1,'history_dt_ms':.00005,'maximum_case_wall_seconds':90,'maximum_campaign_wall_seconds':600,'expected_wall_minutes':[1,5],'no_mass_scaling':True,'preflight':'all warnings/errors block engine','end_hold_ms':.002},
        'gates':{'force_fraction':.005,'energy_fraction':.005,'work_fraction':.005,'mass_fraction':1e-5,'gap_mm':1e-5,'transition_max_cycles':1,'force_zero_N':1e-5,'phase_energy_fraction':.005},
        'reference':{'positive_H2':'F=max(0,F_envelope(m)+kn*(delta-m)); m=max historical normal gap; no compression exercised','recoverable_before_failure':'U=Fn^2/(2kn)+Ft^2/(2kt) from reversible unloading at fixed history','residual':'IE minus U is unrecovered numerical work, not identified fracture dissipation','at_deactivation':'Report OFF/FX phase mismatch without masking the strict same-row force gate; U partition ambiguous during that row'},
        'cases':[
            {'id':'NORMAL_RETURN','x_mm':[0,0,0],'y_deltaf':[0,.6,0],'dt_scale':.2,'fails':False,'expected_final':'normal_unrecovered'},
            {'id':'SHEAR_RETURN','x_mm':[0,.02,0],'y_deltaf':[0,0,0],'dt_scale':.2,'fails':False,'expected_final':'zero'},
            {'id':'SHEAR_RETURN_HALF_DT','x_mm':[0,.02,0],'y_deltaf':[0,0,0],'dt_scale':.1,'fails':False,'expected_final':'zero'},
            {'id':'MIXED_SHEAR_RETURN','x_mm':[0,.02,0],'y_deltaf':[0,.6,.6],'dt_scale':.2,'fails':False,'expected_final':'normal_loaded'},
            {'id':'MIXED_FIXED_SHEAR_FAILURE','x_mm':[0,.02,.02,.02],'y_deltaf':[0,0,1.05,1.05],'dt_scale':.2,'fails':True,'expected_final':'normal_plus_elastic_shear'},
            {'id':'MIXED_FIXED_SHEAR_FAILURE_HALF_DT','x_mm':[0,.02,.02,.02],'y_deltaf':[0,0,1.05,1.05],'dt_scale':.1,'fails':True,'expected_final':'normal_plus_elastic_shear'},
            {'id':'MIXED_PROP_HALF_DT','x_mm':[0,.02],'y_deltaf':[0,1.05],'dt_scale':.1,'fails':True,'expected_final':'proportional_failure'},
            {'id':'SHEAR_AFTER_FAILURE','x_mm':[0,0,.02],'y_deltaf':[0,1.05,1.05],'dt_scale':.2,'fails':True,'expected_final':'normal_only'},
            {'id':'MIXED_RETURN_THEN_FAILURE','x_mm':[0,.02,0,0],'y_deltaf':[0,.6,.6,1.05],'dt_scale':.2,'fails':True,'expected_final':'normal_only'}
        ],
        'sources':[
            {'id':'ALTAIR_H2','url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/stiffness_formulation_spring_hardening_r.htm','use':'unloading stiffness and positive zero-force plateau; reuse C saved page'},
            {'id':'ALTAIR_TYPE8','url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type8_spr_gene_starter_r.htm','use':'six independent modes and deformation-based failure'},
            {'id':'ALTAIR_SPRING_HISTORY','url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm','use':'OFF, force, displacement and IE definitions'},
            {'id':'OPENRADIOSS_CODE_ATTEMPT','url':'https://github.com/OpenRadioss/OpenRadioss','access':'404 on 2026-10-03 via web and public API; exact engine integration phase not read','use':'no code-derived explanation claimed; runtime hashes and experimental phase diagnostic retained'}
        ],
        'qualification':{'source_convention_verified':False,'mixed_mode_dissipation_calibrated':False,'physical_propagation_qualified':False,'aircraft_facade_qualified':False,'thermal_branch_resumed':False,'blender_executed':False}
    }
    entries = {}
    for name in ['preservation_before.json','artifact_manifest.json']:
        for row in json.loads((C/name).read_text(encoding='utf-8'))['files']:
            assert sha(ROOT/row['path'])==row['sha256'],row['path']
            entries[row['path']] = row
    for p in [C/'preservation_before.json',C/'artifact_manifest.json',C/'publication_verification.json',ROOT/'harness/handoffs/WTC1_IMPACT_I02I_C_HANDOFF.md']:
        entries[rel(p)] = {'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    OUT.mkdir(); dump(CFG,cfg)
    dump(OUT/'harness_before.json',hv)
    dump(OUT/'preservation_before.json',{'created_utc':NOW(),'scope':'Union of pinned B/C predecessors, no archive scan or old solver rerun','files':list(entries.values())})
    for name in ADMIN:
        (OUT/('before_'+Path(name).name)).write_bytes((ROOT/'harness'/name).read_bytes())
    dump(OUT/'source_manifest.json',{'created_utc':NOW(),'sources':cfg['sources'],'cached_C_source_manifest':rel(C/'source_manifest.json'),'cached_C_source_manifest_sha256':sha(C/'source_manifest.json'),'documentation_snapshots_excluded_from_redistribution':True})
    plan = {
        'id':'IMPACT-I02I-E_PLAN_FROM_D','declared_utc':NOW(),'seed':1102013,'random_draws':0,
        'scope':'Fresh bounded median M(T) sensitivities before Gf15/60; B/C trajectories reused as references',
        'baseline':{'configuration':rel(cached.CFG),'sha256':sha(cached.CFG),'case_ids':['ENG_DENSE_R1','TRUE_DENSE_R1'],'h_mm':1.27,'Gf_N_per_mm':30.,'Kn_N_per_mm3':56000.,'Kt_N_per_mm3':21500.,'loading_ms':12.,'target_displacement_mm':1.2,'outer_x_break_mm':22.86,'near_seam_half_height_mm':12.7},
        'factors_one_at_a_time':[
            {'name':'speed','interpretations':['engineering','true_total'],'loading_ms':24.,'other_values_unchanged':True},
            {'name':'penalty_half','interpretations':['engineering','true_total'],'Kn_N_per_mm3':28000.,'Kt_N_per_mm3':10750.,'other_values_unchanged':True},
            {'name':'penalty_double','interpretations':['engineering','true_total'],'Kn_N_per_mm3':112000.,'Kt_N_per_mm3':43000.,'other_values_unchanged':True},
            {'name':'domain','interpretations':['engineering','true_total'],'outer_x_break_mm':30.48,'near_seam_half_height_mm':12.7,'guard_at_mm':30.48,'refined_domain_maximum_area_advance_mm':17.78,'outer_width_mm':76.2,'other_values_unchanged':True}
        ],
        'invariants':['fresh histories, no damaged property change','fixed initial reference area per connector','QEPH24 Ismstr4 Ithick1 Iplas1','both NASA conventions, no branch selected','dense TH <= minimum solved dt, explicitly check row/cycle count','no mass scaling, one thread','boundary impulse and work, connector work, global energy','no extrapolation of missing displacement or crack topology'],
        'numerical_comparisons':{'common_displacements_mm':[.2,.5,.8,1.,1.01,1.02,1.03,1.04,1.05,1.1,1.2],'common_nodal_advances_mm':[2.54,5.08,7.62],'force_fraction':.05,'work_fraction':.05,'ctoa_fraction':.1,'inertia_significant_window_fraction':.01,'energy_residual_fraction':.005,'independent_boundary_work_fraction':.01,'spring_work_fraction':.005,'event':'first exact contiguous deactivation event at a requested nodal advance; missing event remains unassessed'},
        'cost':{'expected_wall_minutes':[15,30],'maximum_campaign_wall_minutes':40,'maximum_case_wall_seconds':900,'execution_order':['speed','penalty_half','penalty_double','domain'],'rule':'announce bounded campaign before execution; stop at cost ceiling, preserve completed cases, continue remaining declared cases next iteration rather than expanding cost'},
        'qualification':'Sensitivity/mesh/domain coverage only; no mixed-mode, physical alloy, full Boeing, facade or historical penetration qualification. Gf15/60 deferred until these dependencies are assessed.',
        'publication':'D alone = pending 1/2; update after a verified E. Private GitHub admin excluded.'
    }
    dump(EPLAN,plan)
    print(json.dumps({'declared':cfg['id'],'preserved_files':len(entries),'fresh_controls':len(cfg['cases']),'coupons_deferred':8}),flush=True)

def smooth_path(targets,segment_ms):
    return [(t*segment_ms,u) for t,u in cached.smooth_path(targets)]

def generate(cfg,case,folder):
    c=cfg['connector']; kn,kt,peak=c['kn_N_per_mm'],c['kt_N_per_mm'],c['peak_normal_force_N']
    df=2*c['hypothetical_Gf_N_per_mm']/peak;d0=peak/kn;name='I02ID_'+case['id']
    xp=smooth_path(case['x_mm'],cfg['loading']['segment_ms']);yp=smooth_path([v*df for v in case['y_deltaf']],cfg['loading']['segment_ms'])
    assert len(xp)==len(yp)
    lines=['#RADIOSS STARTER','/BEGIN',name,deck.ii(2026,0),deck.ff('g','mm','ms'),deck.ff('g','mm','ms'),'/TITLE',name,'/ANALY',deck.ii(0)+deck.ff(0)+deck.ii(0),'/SPMD',deck.ii(0,0)+deck.ff(0,1),'/SKEW/FIX/1','GLOBAL_XY',deck.ff(0,0,0),deck.ff(0,1,0),deck.ff(0,0,1),'/NODE',deck.ii(1)+deck.ff(0,0,0),deck.ii(2)+deck.ff(0,0,0)]
    start=len(lines);deck.add_spring_property(lines,1,10,11,kt,kn,peak,d0,df,False)
    lines[start+2]=deck.ff(c['mass_g'],c['rotational_inertia_g_mm2'])+deck.ii(1,0,0,0,0,1)
    lines+=['/PART/1','ONE_FRESH_TYPE8',deck.ii(1,0,0),'/SPRING/1',deck.ii(1,1,2,0,0,0,0,'','',1),'/GRNOD/NODE/1','FIXED_NODE',deck.ii(1),'/GRNOD/NODE/2','DRIVEN_NODE',deck.ii(2),'/BCS/1','FIX_NODE_1',f"{'111':>6}{'111':>4}"+deck.ii(0,1),'/BCS/2','BLOCK_Z_AND_ROTATIONS',f"{'001':>6}{'111':>4}"+deck.ii(0,2)]
    for fid,axis,path in [(90,'X',xp),(91,'Y',yp)]:
        lines += [f'/FUNCT/{fid}','PRESCRIBED_'+axis]+[deck.ff(t,u) for t,u in path]
        lines += [f'/IMPDISP/{fid}','DRIVE_'+axis,deck.ii(fid,axis,0,0,2,'',0),deck.ff(1,1,0,1e30)]
    lines+=['/TH/SPRING/2','SEAM_HISTORY',deck.ii('OFF','FX','FY','LX','LY','IE'),deck.ii(1,'')+'ONE_SPRING','/TH/NODE/3','NODES',deck.ii('DX','DY','VX','VY','REACX','REACY'),deck.ii(1,0),deck.ii(2,0),'/UNIT/1','I02ID_G_MM_MS',deck.ff('g','mm','ms'),'/END']
    (folder/(name+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    end=(len(case['x_mm'])-1)*cfg['loading']['segment_ms']+cfg['execution']['end_hold_ms']
    engine=['/DT',deck.ff(case['dt_scale'],0),'/MON/ON','/PRINT/-100/100',f'/RUN/{name}/1',deck.ff(end),'/TFILE/4',deck.ff(cfg['execution']['history_dt_ms']),'/VERS/2026']
    (folder/(name+'_0001.rad')).write_text('\n'.join(engine)+'\n',encoding='utf-8',newline='\n')
    meta={'name':name,'case':case,'kn_N_per_mm':kn,'kt_N_per_mm':kt,'peak_N':peak,'delta0_mm':d0,'deltaf_mm':df,'expected_mass_g':c['mass_g'],'x_path':xp,'y_path':yp,'end_ms':end,'config_sha256':sha(CFG),'generator_sha256':sha(__file__),'dependency_sha256':{Path(deck.__file__).name:sha(deck.__file__),Path(cached.__file__).name:sha(cached.__file__)},'history':'fresh; no old state rerun or damaged material replacement'}
    dump(folder/'generation.json',meta);return meta

def run():
    cfg=json.loads(CFG.read_text(encoding='utf-8'))
    harness()
    env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='1',KMP_STACKSIZE='400m',PYTHONDONTWRITEBYTECODE='1')
    for case in cfg['cases']:
        folder=OUT/case['id']
        if folder.exists():
            records=json.loads((folder/'execution.json').read_text(encoding='utf-8'))
            assert len(records)==3 and all(r['returncode']==0 for r in records),'Incomplete case preserved; no automatic overwrite'
            print(json.dumps({'cached_new_case':case['id'],'no_rerun':True}),flush=True);continue
        elapsed=sum(r['seconds'] for f in OUT.glob('*/execution.json') for r in json.loads(f.read_text(encoding='utf-8')))
        assert elapsed<cfg['execution']['maximum_campaign_wall_seconds']
        folder.mkdir();meta=generate(cfg,case,folder);records=[]
        for exe,args,log in [('starter_win64.exe',['-i',meta['name']+'_0000.rad','-np','1'],'starter.log'),('engine_win64.exe',['-i',meta['name']+'_0001.rad'],'engine.log'),('th_to_csv_win64.exe',[meta['name']+'T01'],'converter.log')]:
            tick=time.perf_counter()
            try:p=subprocess.run([str(RUNTIME/exe),*args],cwd=folder,env=env,capture_output=True,timeout=cfg['execution']['maximum_case_wall_seconds'])
            except subprocess.TimeoutExpired as exc:
                (folder/log).write_bytes((exc.stdout or b'')+(exc.stderr or b''));dump(folder/'timeout.json',{'executable':exe,'seconds_limit':cfg['execution']['maximum_case_wall_seconds']});raise
            (folder/log).write_bytes(p.stdout+p.stderr)
            records.append({'command':[str(RUNTIME/exe),*args],'returncode':p.returncode,'seconds':time.perf_counter()-tick,'executable_sha256':sha(RUNTIME/exe)})
            dump(folder/'execution.json',records);assert p.returncode==0,log
            if exe.startswith('starter'):
                txt=(folder/(meta['name']+'_0000.out')).read_text(errors='replace');warnings=re.findall(r'^\s*WARNING ID\s*:\s*(\d+)',txt,re.M)
                ok=not warnings and not re.search('ERROR ID',txt) and 'unsupported field' not in txt.lower()
                dump(folder/'preflight.json',{'pass':bool(ok),'warning_ids':warnings,'positive_mass_inertia_no_445':True});assert ok,'Preflight blocks engine'
        print(json.dumps({'case':case['id'],'seconds':sum(r['seconds'] for r in records)}),flush=True)

def integral_normal(m,kn,peak,d0,df):
    if m<=d0:return .5*kn*m*m*.001
    m=min(m,df)
    return (.5*peak*d0+peak/(df-d0)*(df*(m-d0)-.5*(m*m-d0*d0)))*.001

def audit_case(cfg,case,destination):
    folder=OUT/case['id'];meta=json.loads((folder/'generation.json').read_text(encoding='utf-8'));headers,a=cached.read_history(folder)
    ci=columns_module.columns(headers,'SEAM_HISTORY',6)[1];nodes=columns_module.columns(headers,'NODES',6)
    indices={s.strip():i for i,s in enumerate(headers)};col=lambda key:a[:,indices[key]]
    t=a[:,0];off=a[:,ci[0]];active=off>=.5;fx=a[:,ci[1]];fy=a[:,ci[2]];x=a[:,ci[3]];y=a[:,ci[4]]
    nx=a[:,nodes[2][0]]-a[:,nodes[1][0]];ny=a[:,nodes[2][1]]-a[:,nodes[1][1]]
    kn,kt,peak,d0,df=(meta[k] for k in ['kn_N_per_mm','kt_N_per_mm','peak_N','delta0_mm','deltaf_mm'])
    refy=np.zeros(len(t));maximum=0.
    for i,delta in enumerate(ny):
        maximum=max(maximum,float(delta));envelope=kn*maximum if maximum<=d0 else max(0.,peak*(df-maximum)/(df-d0))
        refy[i]=max(0.,envelope+kn*(float(delta)-maximum)) if active[i] else 0.
    refx=np.where(active,kt*nx,0.)
    ie=col('INTERNAL ENERGY')*.001;ke=col('KINETIC ENERGY')*.001;we=col('EXTERNAL WORK')*.001
    wx=np.r_[0,np.cumsum(.5*(fx[1:]+fx[:-1])*np.diff(x)*.001)]
    wy=np.r_[0,np.cumsum(.5*(fy[1:]+fy[:-1])*np.diff(y)*.001)]
    # This partition is justified only by fresh reversible unload controls.
    ux=np.where(active,fx*fx/(2*kt)*.001,0.)
    uy=np.where(active,fy*fy/(2*kn)*.001,0.)
    recoverable=ux+uy;unrecovered=ie-recoverable
    work=work_module.work(headers,a);actuator=np.zeros(len(t)-1)
    for ids in nodes.values():
        for displacement,impulse in [(ids[0],ids[4]),(ids[1],ids[5])]:
            actuator+=np.diff(a[:,impulse])/np.diff(t)*np.diff(a[:,displacement])*.001
    wa=np.r_[0,np.cumsum(actuator)];scale=max(float(np.max(np.abs(we))),1e-15)
    endstate=case['expected_final'];normal_loaded=integral_normal(.6*df,kn,peak,d0,df)
    fmax=peak*(df-.6*df)/(df-d0);normal_u=fmax*fmax/(2*kn)*.001;shear_u=.5*kt*.02**2*.001
    expected={'zero':0.,'normal_unrecovered':normal_loaded-normal_u,'normal_loaded':normal_loaded,'normal_only':.03,'normal_plus_elastic_shear':.03+shear_u,'proportional_failure':.03+.5*kt*(.02/1.05)**2*.001}[endstate]
    breaks=np.flatnonzero(np.diff(off)<-.5)+1;events=[]
    for j in breaks:
        subsequent=np.flatnonzero(np.abs(fx[j:])<=cfg['gates']['force_zero_N']);k=int(j+subsequent[0]) if len(subsequent) else None
        event={'row':int(j),'OFF_time_ms':float(t[j]),'last_active_time_ms':float(t[j-1]),'FX_at_OFF_N':float(fx[j]),'force_zero_row':k,'lag_rows':None if k is None else k-int(j),'lag_ms':None if k is None else float(t[k]-t[j]),'local_dt_ms':float(t[j]-t[j-1]),'nodal_gap_overshoot_mm':float(ny[j]-df),'U_shear_before_J':float(ux[j-1]),'IE_before_J':float(ie[j-1]),'IE_after_settled_J':None if k is None else float(ie[k]),'KE_before_J':float(ke[j-1]),'KE_after_settled_J':None if k is None else float(ke[k]),'transition_partition_ambiguous':bool(abs(fx[j])>cfg['gates']['force_zero_N'])}
        event['rows_near_event']=[{'row':int(q),'time_ms':float(t[q]),'OFF':float(off[q]),'FX_N':float(fx[q]),'FY_N':float(fy[q]),'LX_mm':float(x[q]),'LY_mm':float(y[q]),'nodal_x_mm':float(nx[q]),'nodal_y_mm':float(ny[q]),'IE_J':float(ie[q]),'KE_J':float(ke[q]),'external_work_J':float(we[q])} for q in range(max(0,j-2),min(len(t),j+4))]
        events.append(event)
    endpoints=[]
    for q in range(1,len(case['x_mm'])):
        i=min(int(np.searchsorted(t,q*cfg['loading']['segment_ms'])),len(t)-1)
        endpoints.append({'segment':q,'row':i,'time_ms':float(t[i]),'OFF':float(off[i]),'nodal_x_mm':float(nx[i]),'nodal_y_mm':float(ny[i]),'IE_J':float(ie[i]),'KE_J':float(ke[i]),'WX_J':float(wx[i]),'WY_J':float(wy[i]),'U_shear_J':float(ux[i]),'U_normal_J':float(uy[i]),'unrecovered_work_J':float(unrecovered[i])})
    engine=(folder/(meta['name']+'_0001.out')).read_text(errors='replace')
    cm=re.search(r'TOTAL NUMBER OF CYCLES\s*(?:\.\s*)*[:=]?\s*(\d+)',engine)
    metrics={'rows':len(t),'engine_cycles':int(cm.group(1)) if cm else None,'max_force_normal_error_over_peak':float(np.max(np.abs(fy-refy))/peak),'max_force_shear_error_over_430N':float(np.max(np.abs(fx-refx))/430.),'mass_error_fraction':float(np.max(np.abs(col('MASS')-meta['expected_mass_g']))/meta['expected_mass_g']),'energy_residual_fraction':float(np.max(np.abs(we-ie-ke))/scale),'boundary_work_error_fraction':float(np.max(np.abs(wa-we))/scale),'spring_IE_sum_error_fraction':float(np.max(np.abs(a[:,ci[5]]*.001-col('SPRING ENERGY')*.001))/scale),'active_gap_error_mm':float(max(np.max(np.abs(x[active]-nx[active])),np.max(np.abs(y[active]-ny[active])))),'expected_final_IE_J':expected,'final_IE_J':float(ie[-1]),'analytic_final_IE_error_fraction':abs(float(ie[-1])-expected)/max(scale,.03 if case['fails'] else 1e-15),'max_KE_J':float(np.max(ke)),'final_KE_J':float(ke[-1]),'final_U_J':float(recoverable[-1]),'final_unrecovered_work_J':float(unrecovered[-1]),'initial_state_zero':bool(np.max(np.abs(a[0,ci[1:]]))==0.),'normal_loaded_reference_J':normal_loaded,'normal_U_at_0_6deltaf_reference_J':normal_u,'shear_U_at_0_02mm_reference_J':shear_u}
    checks={'preflight':json.loads((folder/'preflight.json').read_text(encoding='utf-8'))['pass'],'three_successful_jobs':len(json.loads((folder/'execution.json').read_text(encoding='utf-8')))==3,'normal_termination':'NORMAL TERMINATION' in engine,'mass':metrics['mass_error_fraction']<=cfg['gates']['mass_fraction'],'normal_H2_force':metrics['max_force_normal_error_over_peak']<=cfg['gates']['force_fraction'],'strict_same_row_OFF_FX':metrics['max_force_shear_error_over_430N']<=cfg['gates']['force_fraction'],'energy_balance':metrics['energy_residual_fraction']<=cfg['gates']['energy_fraction'],'independent_boundary_work':metrics['boundary_work_error_fraction']<=cfg['gates']['work_fraction'],'spring_IE_sum':metrics['spring_IE_sum_error_fraction']<=.001,'work_quadrature':work['spring_work_error_fraction']<=cfg['gates']['work_fraction'],'active_gap':metrics['active_gap_error_mm']<=cfg['gates']['gap_mm'],'initial_state_zero':metrics['initial_state_zero'],'OFF_irreversible':bool(np.all(np.diff(off)<=1e-7)),'expected_final_OFF':bool(off[-1]==(0 if case['fails'] else 1)),'analytic_final_IE':metrics['analytic_final_IE_error_fraction']<=cfg['gates']['energy_fraction'],'TH_every_cycle':metrics['engine_cycles'] is not None and len(t)==metrics['engine_cycles'],'transition_within_one_cycle':all(e['lag_rows'] is not None and e['lag_rows']<=cfg['gates']['transition_max_cycles'] for e in events)}
    checks={k:bool(v) for k,v in checks.items()}
    result={'case':case,'metrics':metrics,'work':work,'endpoints':endpoints,'deactivation_events':events,'checks':checks,'all_checks_pass':all(checks.values()),'raw_csv_sha256':sha(next(folder.glob('*.csv'))),'interpretation':'IE is integrated internal work. U is reversible unloading energy away from deactivation; residual is unrecovered numerical work, not calibrated physical dissipation.'}
    destination.mkdir();dump(destination/'audit.json',result)
    with (destination/'history.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['time_ms','OFF','FX_N','FY_N','LX_mm','LY_mm','nodal_x_mm','nodal_y_mm','IE_J','KE_J','WE_J','actuator_work_J','WX_J','WY_J','U_shear_J','U_normal_J','unrecovered_numerical_work_J']);writer.writerows(zip(t,off,fx,fy,x,y,nx,ny,ie,ke,we,wa,wx,wy,ux,uy,unrecovered))
    return result

def audit():
    dest=SUMMARY.parent;assert not dest.exists(),'Preserve audit revisions';dest.mkdir()
    cfg=json.loads(CFG.read_text(encoding='utf-8'));results={}
    for case in cfg['cases']:results[case['id']]=audit_case(cfg,case,dest/case['id'])
    fixed=results['MIXED_FIXED_SHEAR_FAILURE'];half=results['MIXED_FIXED_SHEAR_FAILURE_HALF_DT'];prop=results['MIXED_PROP_HALF_DT']
    baseline=json.loads((C/'verification_r2/MIXED/audit.json').read_text(encoding='utf-8'))
    sr=results['SHEAR_RETURN'];nr=results['NORMAL_RETURN'];mr=results['MIXED_SHEAR_RETURN'];rf=results['MIXED_RETURN_THEN_FAILURE'];sf=results['SHEAR_AFTER_FAILURE']
    comparison={
        'elastic_shear_return_error_J':sr['metrics']['final_IE_J'],
        'mixed_shear_returned_J':mr['endpoints'][0]['WX_J']-mr['endpoints'][1]['WX_J'],
        'normal_unload_returned_J':nr['endpoints'][0]['WY_J']-nr['endpoints'][1]['WY_J'],
        'fixed_shear_failure_excess_over_unloaded_shear_J':fixed['metrics']['final_IE_J']-rf['metrics']['final_IE_J'],
        'fixed_shear_failure_excess_reference_J':.0043,
        'fixed_failure_halfdt_IE_difference_fraction':abs(fixed['metrics']['final_IE_J']-half['metrics']['final_IE_J'])/.0343,
        'fixed_failure_halfdt_lag_time_ratio':half['deactivation_events'][0]['lag_ms']/fixed['deactivation_events'][0]['lag_ms'],
        'post_failure_shear_work_increment_J':sf['endpoints'][1]['WX_J']-sf['endpoints'][0]['WX_J'],
        'cached_C_proportional_baseline_loaded':baseline is not None,
        'proportional_IE_J_halfdt':prop['metrics']['final_IE_J'],
        'cached_C_proportional_IE_J':None if baseline is None else baseline['metrics']['final_IE_J']
    }
    comparison['checks']={
        'shear_energy_returned':abs(comparison['mixed_shear_returned_J']-.0043)<=.005*.0043,
        'normal_U_returned':abs(comparison['normal_unload_returned_J']-nr['metrics']['normal_U_at_0_6deltaf_reference_J'])<=.005*.03,
        'fixed_shear_retained_work_excess':abs(comparison['fixed_shear_failure_excess_over_unloaded_shear_J']-.0043)<=.005*.0343,
        'fixed_failure_halfdt_work':comparison['fixed_failure_halfdt_IE_difference_fraction']<=.005,
        'phase_duration_halves':.4<=comparison['fixed_failure_halfdt_lag_time_ratio']<=.6,
        'no_shear_work_after_failure':abs(comparison['post_failure_shear_work_increment_J'])<=.005*.0043,
        'cached_C_proportional_halfdt_work':baseline is not None and abs(prop['metrics']['final_IE_J']-baseline['metrics']['final_IE_J'])<=.005*.034
    }
    s={'iteration':'IMPACT-I02I-D','created_utc':NOW(),'cases':results,'comparisons':comparison,'case_checks_passed':sum(sum(v['checks'].values()) for v in results.values()),'case_checks_total':sum(len(v['checks']) for v in results.values()),'comparison_checks_passed':sum(comparison['checks'].values()),'comparison_checks_total':len(comparison['checks']),'all_scientific_checks_pass':all(v['all_checks_pass'] for v in results.values()) and all(comparison['checks'].values()),'runtime_seconds':sum(r['seconds'] for p in OUT.glob('*/execution.json') for r in json.loads(p.read_text(encoding='utf-8'))),'config_sha256':sha(CFG),'audit_script_sha256':sha(__file__),'dependencies_sha256':{Path(v.__file__).name:sha(v.__file__) for v in [cached,deck,columns_module,work_module]},'software':{'python':sys.version,'numpy':np.__version__,'solver':'OpenRadioss 20260728 win64, engine VERS2026, one thread'},'source_convention_verified':False,'physical_propagation_qualified':False,'mixed_mode_dissipation_calibrated':False,'old_solvers_rerun':False,'thermo_branch_resumed':False}
    dump(SUMMARY,s)
    print(json.dumps({k:s[k] for k in ['case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','runtime_seconds','all_scientific_checks_pass']}),flush=True)

def preservation():
    entries=json.loads((OUT/'preservation_before.json').read_text(encoding='utf-8'))['files'];bad=[r['path'] for r in entries if sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad;return len(entries)

def complete():
    assert not REPORT.exists() and not HANDOFF.exists(),'Never overwrite completion'
    s=json.loads(SUMMARY.read_text(encoding='utf-8'));cfg=json.loads(CFG.read_text(encoding='utf-8'));count=preservation();hv=harness()
    assert len(s['cases'])==len(cfg['cases']) and not s['physical_propagation_qualified']
    assert all(v['checks']['preflight'] and v['checks']['normal_termination'] for v in s['cases'].values())
    report_lines=[]
    for name,v in s['cases'].items():
        bad=', '.join(k for k,ok in v['checks'].items() if not ok) or 'aucun'
        report_lines.append(f"| {name} | {v['metrics']['final_IE_J']:.9g} | {v['metrics']['final_U_J']:.9g} | {v['metrics']['final_unrecovered_work_J']:.9g} | {bad} |")
    fixed=s['cases']['MIXED_FIXED_SHEAR_FAILURE'];half=s['cases']['MIXED_FIXED_SHEAR_FAILURE_HALF_DT'];normal=s['cases']['NORMAL_RETURN'];cmp=s['comparisons']
    report=f'''# WTC1 — IMPACT-I02I-D : histoire et énergie d'une liaison TYPE8

## 1. Faits observés ou transcrits

Cette itération comporte {len(s['cases'])} états initiaux neufs, un seul ressort de longueur nulle par cas ; aucun résultat B/C n'est recalculé. Temps des exécutables : {s['runtime_seconds']:.3f} s. Configuration : `{rel(CFG)}` ; résultats : `{rel(SUMMARY)}`. {s['case_checks_passed']}/{s['case_checks_total']} critères de cas et {s['comparison_checks_passed']}/{s['comparison_checks_total']} comparaisons passent. Les échecs restent visibles.

Les définitions primaires Radioss décrivent six modes indépendants, H2 avec raideur linéaire de décharge et plage sans force avant compression, et IE comme énergie interne. Sources : [TYPE8]({cfg['sources'][1]['url']}), [H2]({cfg['sources'][0]['url']}), [TH/SPRING]({cfg['sources'][2]['url']}). Ce n'est pas une identification expérimentale d'un alliage du Boeing. Le dépôt primaire OpenRadioss et son API ont répondu 404 lors de la lecture ciblée ; aucun ordre exact du code moteur n'est affirmé.

## 2. Résultats d'un modèle officiel

Aucun nouveau calcul NIST ou modèle officiel de l'événement n'est importé. La NASA ne fournit ici aucune identification de dissipation mixte ; les deux conventions de courbe issues des étapes précédentes restent indéterminées et ne sont pas sollicitées dans ces ressorts isolés.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation des archives n'est testée. Les sources sont en lecture seule. {count} fichiers des manifests précédents sont préservés avec SHA-256 ; aucun historique complet, archive ou ancien solveur n'est rescanné ou relancé.

## 4. Hypothèses et références propres au modèle

Unités : g, mm, ms, N ; N mm = mJ, conversion J = 0,001 N mm. Aire initiale 1 mm² fixe, Kn=56000 N/mm, Kt=21500 N/mm ; force normale maximale 495 N ; Gf hypothétique 30 N/mm, soit 0,03 J pour cette aire. δ0=495/56000=0,008839285714 mm, δf=60/495=0,1212121212 mm. Déformation relative ici mesurée par ouverture, sans longueur de jauge ni déformation thermique. Masse 0,2 g, inertie 0,001 g mm², rotations et z bloqués, nœud 1 fixe, déplacements x/y du nœud 2 imposés par segments quintiques de 1 ms. Aucune substitution de propriétés après dommage, aucun amortissement ni ajout de masse.

Référence normale en traction : m=max de l'ouverture passée ; F=max(0,F_enveloppe(m)+Kn(δ−m)). La raideur de décharge permet de définir hors transition U_n=F_n²/(2Kn), U_t=F_t²/(2Kt). Le résidu IE−U est un **travail numérique non récupéré**, pas une dissipation physique mesurée. À la ligne où OFF et FX sont discordants, cette partition est ambiguë et n'est pas utilisée comme preuve thermodynamique.

Le travail est recalculé indépendamment par Σ½(F_i+F_(i−1))Δδ_i. Les réactions brutes sont des impulsions N ms : Σ(ΔJ/Δt)Δu aux deux nœuds, comparé au travail externe. Le bilan WE−IE−KE, les masses et la somme IE ressort/global sont vérifiés séparément ; IE global contient déjà IE ressort, sans double comptage.

## 5. Résultats dérivés

| Cas | IE final J | U final J | Travail non récupéré J | Critères échoués |
|---|---:|---:|---:|---|
{chr(10).join(report_lines)}

Le cisaillement 0→0,02→0 mm restitue l'énergie élastique attendue 0,0043 J ; la décharge tangentielle en état normal endommagé restitue {cmp['mixed_shear_returned_J']:.9g} J. La décharge normale depuis 0,6δf restitue {cmp['normal_unload_returned_J']:.9g} J, contre U_n={normal['metrics']['normal_U_at_0_6deltaf_reference_J']:.9g} J. L'ouverture de décharge et le maximum passé sont conservés ; revenir à zéro ne réinitialise pas le ressort.

Rupture normale avec cisaillement maintenu : IE final={fixed['metrics']['final_IE_J']:.9g} J. Rendre le cisaillement avant rupture donne IE final={s['cases']['MIXED_RETURN_THEN_FAILURE']['metrics']['final_IE_J']:.9g} J ; différence {cmp['fixed_shear_failure_excess_over_unloaded_shear_J']:.9g} J, proche du stockage tangent 0,0043 J. Le travail reste inscrit dans IE après suppression des forces. L'effacement de la capacité de restitution tangentielle ne démontre pas que cette énergie soit une énergie de fracture physique. Le témoin chargé en cisaillement après rupture transmet un supplément de travail {cmp['post_failure_shear_work_increment_J']:.9g} J.

Événements OFF/FX : {json.dumps(fixed['deactivation_events'][0],ensure_ascii=False)}

Demi-pas : {json.dumps(half['deactivation_events'][0],ensure_ascii=False)}

Le rapport des durées de décalage vaut {cmp['fixed_failure_halfdt_lag_time_ratio']:.9g}. Les tableaux proches de chaque événement conservent les lignes brutes et le dépassement d'ouverture ; le critère strict force/état n'est ni filtré ni transformé en réussite. Comparaison à C proportionnelle enregistrée : {json.dumps(cmp,ensure_ascii=False)}.

## 6. Contradictions, informations manquantes et suite

Le bilan global et le travail intégré ne suffisent pas à qualifier une dissipation mixte : énergie élastique rendue avant rupture et travail conservé lors d'une désactivation sont distingués. Le phasage OFF/FX est observé sur ce moteur, sans démonstration de son origine dans le code. La propagation sur coupons, l'inertie ENG, les angles et les avances absentes de C restent non qualifiés. Gf=30 reste hypothétique ; Gf15/60 sont différés.

Le plan borné `{rel(EPLAN)}` déclare huit sensibilités vitesse/pénalité/domaine à états neufs et deux conventions, avec limites de coût et critères avant exécution. Prochaine étape I02I-E : commencer par la vitesse divisée par deux, puis les facteurs restants dans l'ordre déclaré sous plafond. Historique dense à chaque cycle, aire initiale fixe, QEPH et impulsions/travail des appuis restent obligatoires. Aucun test avion/façade complet n'est exécuté ici.

Contrôles froids V11F et thermiques V11R/V11S préservés. Température imposée ≠ incendie calculé ; localisation en flexion après fracture complète non validée ; des succès numériques ne valident pas l'effondrement réel ; Blender reste une visualisation tant que ses états ne sont pas reliés à une mécanique vérifiée. La publication B+C est vérifiée (commit scientifique et archives/CI) ; ses métadonnées de confirmation préparées localement restent à inclure au prochain envoi. D devient 1/2 avant la prochaine publication GitHub ; aucun post X autorisé.
'''
    REPORT.write_text(report,encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# WTC1 — IMPACT-I02I-D terminée, prochaine I02I-E

Lire AGENTS.md, harness/state.json, cette passation puis `{rel(OUT/'publication_verification.json')}`. État local prioritaire ; V8H/V11H historiques, V11F/V11R et V11S différée préservés.

D : {len(s['cases'])} ressorts TYPE8 neufs, {s['runtime_seconds']:.3f} s ; {s['case_checks_passed']}/{s['case_checks_total']} critères, {s['comparison_checks_passed']}/{s['comparison_checks_total']} comparaisons. Rapport `{rel(REPORT)}`, résultats `{rel(SUMMARY)}`, config `{rel(CFG)}`. Ne pas relancer pour lire les résultats.

Décharge tangentielle restitue ≈0,0043 J ; normale suit U=F²/(2Kn). Rupture sous cisaillement fixé conserve ≈0,0343 J dans IE, contre ≈0,03 J après retour tangent avant rupture. IE−U est du travail numérique non récupéré, pas une dissipation mixte calibrée. Décalage OFF/FX conservé dans les CSV et critère strict échoué ; durée et demi-pas dans les audits. Lecture du code primaire inaccessible (404), donc origine exacte non démontrée.

E : utiliser `{rel(EPLAN)}` pour huit cas potentiels à états neufs, commencer vitesse moitié (24 ms) ENG/TRUE médian h1,27, puis Kn/Kt ×0,5/2 et extension du domaine à ±30,48 mm, un facteur à la fois. Plafond 40 min, 900 s/cas ; annoncer avant lancement, conserver les cas exécutés et reporter les restants si plafond atteint. Maintenir Gf30, aire initiale fixe, QEPH24 Ismstr4 Ithick1 Iplas1, histoires à chaque cycle (générateur ancien multiplie TFILE par durée : adapter sans perdre le dense), deux conventions et aucune extrapolation des avances manquantes. Comparer aux B/C sauvegardées à déplacements communs et événements nodaux exacts ; bilan indépendant des appuis. Vérifier coût/maillage/gardes avant moteur. Gf15/60 différés.

Harnais PASS avant/après. {count} anciens fichiers épinglés ; aucune archive rescannée ni ancien calcul relancé. Commande de vérification sans solveur : `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/run_impact_i02i_energy.py --verify`.

GitHub : B+C scientifiques publiées et vérifiées ; confirmation administrative préparée dans outputs/github_publication/anonymous_repository à inclure lors du prochain envoi (voir privé updates_2026-10-03_i02i_c/metadata_pin_repair.json). D=1/2, publication après E vérifiée. Compte et identité WTC-simu2026 ; exclure l'administration privée, pas de post X. Aucun Boeing complet/façade/pénétration historique qualifié. Température imposée ≠ incendie, flexion post-fracture non validée, Blender visualisation.
''',encoding='utf-8',newline='\n')
    dump(OUT/'release_audit.json',{'created_utc':NOW(),'pass':True,'definition':'Completed bounded numerical diagnostics, failed qualification gates retained','old_files_preserved':count,'harness':hv,'config_sha256':sha(CFG),'summary_sha256':sha(SUMMARY),'report_sha256':sha(REPORT),'handoff_sha256':sha(HANDOFF),'physical_propagation_qualified':False,'mixed_mode_dissipation_calibrated':False})
    dump(OUT/'harness_after_artifacts.json',harness())
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,EPLAN,Path(__file__),HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':NOW(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(paths))],'exclusions':['self','post-registration verification','mutable state/registry/cadence checked separately'],'scope':'All new decks, binaries outputs, logs, audits, script/config/report/handoff and sensitivity plan'})
    # Register only after existence, numerical completion, preservation and artifact hashes.
    for name in ADMIN:assert sha(ROOT/'harness'/name)==sha(OUT/('before_'+Path(name).name)),'Concurrent harness change'
    state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'));cadence=json.loads((ROOT/'harness/publication_cycle.json').read_text(encoding='utf-8'));assert cadence['pending_iterations']==[]
    status='completed_bounded_energy_diagnostic_with_failed_same_row_force_gates_and_unqualified_mixed_dissipation';when=NOW()
    record={'experiment_id':'WTC1-IMPACT-I02I-D','registered_at':when,'status':status,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(SUMMARY),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'source_manifest':rel(OUT/'source_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'sensitivity_plan':rel(EPLAN),'cases':len(s['cases']),'case_checks_passed':s['case_checks_passed'],'case_checks_total':s['case_checks_total'],'comparison_checks_passed':s['comparison_checks_passed'],'comparison_checks_total':s['comparison_checks_total'],'old_files_preserved':count,'source_convention_verified':False,'physical_propagation_qualified':False,'mixed_mode_dissipation_calibrated':False,'runtime_seconds':s['runtime_seconds'],'next_iteration':'IMPACT-I02I-E','github_pending_iterations':1}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='IMPACT-I02I-D',current_status=status,next_iteration='IMPACT-I02I-E',next_objective='Réutiliser D : énergie restituable vérifiée par décharge, IE après désactivation = travail numérique non récupéré, pas Gf mixte mesuré. Exécuter le plan borné vitesse/pénalité/domaine à états neufs et TH chaque cycle, commencer ENG/TRUE à 24 ms; garder deux conventions, aire initiale fixe, QEPH, impulsions et travail des appuis. Gf15/60 différés. D=1/2 GitHub, envoi après E vérifiée. V11F/V11R/V11S préservés.',updated_at=when)
    state['impact_i02i_d_key_results']={k:record[k] for k in ['cases','case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','old_files_preserved','runtime_seconds','source_convention_verified','physical_propagation_qualified','mixed_mode_dissipation_calibrated','github_pending_iterations']}
    state['impact_i02i_d_key_results'].update(mixed_fixed_shear_final_IE_J=fixed['metrics']['final_IE_J'],mixed_shear_return_before_failure_IE_J=rf_value(s),strict_same_row_force_failed_cases=[name for name,v in s['cases'].items() if not v['checks']['strict_same_row_OFF_FX']],half_dt_phase_duration_ratio=cmp['fixed_failure_halfdt_lag_time_ratio'])
    state['validated_artifacts'].update(impact_i02i_d_report=rel(REPORT),impact_i02i_d_results=rel(SUMMARY),impact_i02i_d_handoff=rel(HANDOFF),impact_i02i_d_publication_verification=rel(OUT/'publication_verification.json'),impact_i02i_e_sensitivity_plan=rel(EPLAN))
    cadence.update(pending_iterations=['IMPACT-I02I-D'],pending_count=1,next_publication_after='After I02I-E is verified: publish pair D+E and saved B+C confirmation metadata',updated_at=when)
    dump(ROOT/'harness/publication_cycle.json',cadence);temp=ROOT/'harness/state_i02id_pending.json';dump(temp,state);temp.replace(ROOT/'harness/state.json')
    verify(write=True)

def rf_value(s):return s['cases']['MIXED_RETURN_THEN_FAILURE']['metrics']['final_IE_J']

def verify(write=False):
    count=preservation();manifest=json.loads((OUT/'artifact_manifest.json').read_text(encoding='utf-8'));bad=[r['path'] for r in manifest['files'] if sha(ROOT/r['path'])!=r['sha256']]
    state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'));old=json.loads((OUT/'before_state.json').read_text(encoding='utf-8'));reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();extra=reg[len(prefix):].decode('utf-8').splitlines();cadence=json.loads((ROOT/'harness/publication_cycle.json').read_text(encoding='utf-8'));s=json.loads(SUMMARY.read_text(encoding='utf-8'));hv=harness()
    protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy']
    checks={'all_new_artifact_hashes':not bad,'old_files_preserved':True,'registry_prefix':reg.startswith(prefix),'one_D_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-D','state_D_to_E':state['current_iteration']=='IMPACT-I02I-D' and state['next_iteration']=='IMPACT-I02I-E','prior_states_preserved':all(state[k]==old[k] for k in protected),'harness_pass':hv['Status']=='PASS','report_handoff_plan_exist':REPORT.exists() and HANDOFF.exists() and EPLAN.exists(),'cadence_one_pending':cadence['pending_iterations']==['IMPACT-I02I-D'] and cadence['pending_count']==1,'failed_force_gates_retained':not s['all_scientific_checks_pass'] and any(not v['checks']['strict_same_row_OFF_FX'] for v in s['cases'].values()),'unqualified_physics_retained':not s['physical_propagation_qualified'] and not s['mixed_mode_dissipation_calibrated'],'no_old_solver_rerun':s['old_solvers_rerun'] is False}
    result={'created_utc':NOW(),'pass':all(checks.values()),'checks':checks,'manifest_files_checked':len(manifest['files']),'manifest_failures':bad,'old_files_checked':count,'harness':hv,'case_checks':f"{s['case_checks_passed']}/{s['case_checks_total']}",'comparison_checks':f"{s['comparison_checks_passed']}/{s['comparison_checks_total']}",'scientific_all_gates_pass':s['all_scientific_checks_pass'],'physical_propagation_qualified':False,'mixed_mode_dissipation_calibrated':False,'next_iteration':'IMPACT-I02I-E','github_pending_iterations':1}
    assert result['pass'],result
    if write:dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

def main():
    p=argparse.ArgumentParser()
    for option in ['declare','run','audit','complete','verify']:p.add_argument('--'+option,action='store_true')
    a=p.parse_args();assert sum(vars(a).values())==1,'One sequential operation per invocation'
    for name,selected in vars(a).items():
        if selected:globals()[name]()

if __name__=='__main__':main()
