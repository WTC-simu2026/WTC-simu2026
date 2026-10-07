"""A10 isolated elastic contact witness; immutable attempts and predeclared gates."""
import argparse, csv, json, re, shutil, subprocess, sys, urllib.request
from pathlib import Path
import numpy as np
from run_aircraft_a02 import ROOT, RUNTIME, read, dump, sha, rel, now, ff, ii, harness, execute, group
from run_aircraft_a06 import env
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records

OUT = ROOT/'wtc1_simulation_v8/output/aircraft_a10'
CFG = ROOT/'wtc1_simulation_v8/data/aircraft_a10_predeclaration.json'
PREV = ROOT/'wtc1_simulation_v8/output/aircraft_a09'
SRC = ROOT/'wtc1_simulation_v8/input/aircraft_a10_sources'
COMMIT = '0168ab344bd743051e996d90c7c8d80728bb04a8'

def declare():
    assert not OUT.exists() and not CFG.exists() and not SRC.exists()
    v=harness(); assert v['CurrentIteration']=='AIRCRAFT-A09'
    OUT.mkdir(); SRC.mkdir(); dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    # Entire JSON is decoded and traversed, including historical evidence and all limitations.
    s=read(ROOT/'harness/state.json'); counts={}
    def leaves(x):
        if isinstance(x,dict): return sum(leaves(q) for q in x.values())
        if isinstance(x,list): return sum(leaves(q) for q in x)
        return 1
    for k,value in s.items(): counts[k]={'leaves_read':leaves(value),'value_sha256':__import__('hashlib').sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
    dump(OUT/'full_state_read_coverage.json',{'source_sha256':sha(ROOT/'harness/state.json'),'all_top_level_fields':counts,'current':s['current_iteration'],'next':s['next_iteration'],'meaning':'Integral JSON read and recursive traversal; historical state is immutable, current route has precedence.'})
    pins={r['path']:r for fn in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/fn)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:
        pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    for r in read(PREV/'source_manifest.json')['new_primary_sources']: pins[r['path']]=r
    dump(OUT/'preservation_before.json',{'files':list(pins.values()),'created_utc':now()})
    requests=[('TH_PART.html','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_part_starter_r.htm'),('PROP_TYPE1.html','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type1_shell_starter_r.htm')]
    for p in ['starter/source/elements/sh3n/coque3n/c3inmas.F','starter/source/elements/shell/coque/cinmas.F','starter/source/elements/beam/pmass.F','engine/source/output/th/hist1.F','engine/source/output/th/hist2.F','engine/source/output/th/hist13.F','starter/source/output/th/th_titles.F90','starter/source/output/th/hm_read_thgrpa.F','hm_cfg_files/config/CFG/radioss2025/LOADS/inivel.cfg']:
        requests.append((Path(p).name,'https://raw.githubusercontent.com/OpenCourant/OpenCourant/'+COMMIT+'/'+p))
    rows=[]
    for name,url in requests:
        p=SRC/name;req=urllib.request.Request(url,headers={'User-Agent':'WTC1-A10 bounded primary-source audit'})
        p.write_bytes(urllib.request.urlopen(req,timeout=60).read())
        rows.append({'path':rel(p),'url':url,'sha256':sha(p),'bytes':p.stat().st_size,'redistribution':'exclude_third_party'})
    dump(SRC/'acquisition.json',{'sources':rows,'commit':COMMIT,'source_binary_equivalence_established':False,'created_utc':now()})
    dump(OUT/'source_access_failures.json',{'retained_failures':[{'url':'https://api.github.com/repos/OpenRadioss/OpenRadioss/git/trees/'+ref+'?recursive=1','status':404} for ref in ['v20260728','main','18707be39cd8b6385a04d698709c540f288ea95c']],'successful_route':'Existing A06 immutable OpenCourant commit; source-to-installed-binary equivalence remains unverified.'})
    cases=[{'id':'FREE','contact':False,'Stfac':1.,'dt_scale':.8}]
    for factor,label in [(1.,'K1'),(.01,'K01'),(.001,'K001')]:
        for dt,dlabel in [(.8,'DT080'),(.4,'DT040')]: cases.append({'id':label+'_'+dlabel,'contact':True,'Stfac':factor,'dt_scale':dt})
    c={'iteration':'AIRCRAFT-A10','created_utc':now(),'seed':1102035,'random_draws':0,'scope':'Elastic LAW1 single quad translating normally into a fixed elastic quad. No aircraft, RBE3, rigid-body mass redistribution, fracture, gravity or fitted event target.',
       'units':{'native':['g','mm','ms'],'mass_g_to_kg':.001,'energy_g_mm2_ms2_to_J':.001,'momentum_g_mm_ms_to_Ns':.001,'force_native_to_N':1.,'velocity_mm_ms_to_m_s':1.},
       'geometry':{'moving_side_mm':20.,'wall_side_mm':40.,'initial_midsurface_x_mm':-1.01,'wall_x_mm':0.,'contact_gap_mm':1.,'thickness_mm':1.},
       'material_hypothesis':{'rho_g_mm3':.00278,'E_MPa':70000.,'nu':.3,'law':'LAW1 linear elasticity','origin':'Synthetic verification values, no Boeing/WTC material qualification'},
       'motion':{'initial_velocity_m_s':1.,'moving_BCS':'   011 111','wall_BCS':'   111 111'},
       'contact':{'type':7,'Istf':4,'Igap':0,'Inacti':2,'friction':0.,'viscous_coefficients':1e-20,'Iform':2,'Irem_gap':0,'stiffness_selection':'Three declared sensitivities, none selected to fit an event'},
       'formulation':{'Ishell':24,'Ismstr':4,'Ish3n':2,'Idrill':2,'N':5,'hm_hf_hr_dm_dn':1e-20},
       'analytical_reference':{'mass_g':1.112,'initial_KE_J':.000556,'initial_Px_Ns':.001112,'frictionless_complete_rebound_impulse_magnitude_Ns':.002224,'first_gap_entry_time_ms':.01,'laws':['Delta P=contact impulse on moving part','Ekin+Eint+Ehourglass+Econtact+Edamping+Efriction-Ework constant','Unstrained complete conservative rebound gives vx=-v0 and |J|=2 M v0'],'no_claim_of_exact_linear_contact_force_law':True},
       'acceptance':{'initial_mass_relative':1e-5,'initial_KE_relative':1e-5,'momentum_residual_relative_to_initial':.01,'maximum_energy_residual_relative_to_initial':.01,'rebound_speed_relative':.01,'half_dt_impulse_relative':.01,'half_dt_energy_residual_change_relative_to_initial':.005,'free_energy_relative':1e-6,'free_velocity_absolute_m_s':1e-6,'zero_rotation_allowance_J':1e-10,'native_binary_csv_relative':6e-7,'native_binary_csv_absolute':1e-12,'support_momentum_relative':.02,'all_criteria_predeclared':True},
       'execution':{'cases':cases,'end_ms':.4,'history_interval_ms':.0001,'animation_interval_ms':.05,'threads':2,'GPU':False,'starter_timeout_s':90,'engine_timeout_s':120,'converter_timeout_s':60,'estimated_campaign_minutes':[2,8]},
       'sources':rows,'inherited_TYPE7_source':rel(ROOT/'wtc1_simulation_v8/input/aircraft_a09_sources/TYPE7.html'),'source_binary_equivalence_established':False,'NIST_outcomes_used_as_target':False,'physical_impact_qualified':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_solver':True});
    dump(OUT/'source_manifest.json',{'sources':rows,'inherited_TYPE7':{'path':c['inherited_TYPE7_source'],'sha256':sha(ROOT/c['inherited_TYPE7_source'])},'archive_rescanned':False,'old_solver_reruns':0})
    print({'declared':len(cases),'old_files_pinned':len(pins),'configuration_sha256':sha(CFG)},flush=True)

def guard(): assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
def preserved():
    rows=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in rows if sha(ROOT/r['path'])!=r['sha256']];assert not bad,bad;return len(rows)

def build(caseid):
    guard();c=read(CFG);case=next(x for x in c['execution']['cases'] if x['id']==caseid)
    d=OUT/'r0'/caseid;assert not d.exists();d.mkdir(parents=True);n='A10_'+caseid
    g=c['geometry'];mat=c['material_hypothesis'];x=[]
    for xx,side in [(g['initial_midsurface_x_mm'],g['moving_side_mm']),(0.,g['wall_side_mm'])]:
        for yy,zz in [(-side/2,-side/2),(side/2,-side/2),(side/2,side/2),(-side/2,side/2)]:x.append([xx,yy,zz])
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0,0,0,0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']
    L.extend(ii(i+1)+ff(*v) for i,v in enumerate(x))
    L+=['/MAT/LAW1/1','SYNTHETIC_ELASTIC',ff(mat['rho_g_mm3']),ff(mat['E_MPa'],mat['nu'])]
    for pid,title,nodes in [(1,'MOVING_QUAD',[1,2,3,4]),(2,'FIXED_QUAD',[5,6,7,8])]:
        L += [f'/PROP/TYPE1/{pid}',title,ii(24,4,2,2),ff(*([1e-20]*5)),ii(5)+' '*10+ff(1.,5/6),f'/PART/{pid}',title,ii(pid,1,0),f'/SHELL/{pid}',ii(pid,*nodes)]
    group(L,1,'MOVING',list(range(1,5)));group(L,2,'FIXED',list(range(5,9)))
    L+=['/BCS/1','MOVING_ONLY_X','   011 111'+ii(0,1),'/BCS/2','FIXED_ALL','   111 111'+ii(0,2),'/INIVEL/TRA/1','INITIAL_TRANSLATION',ff(1,0,0)+ii(1,0),ff(0)+ii(0)]
    if case['contact']:
        L+=['/SURF/PART/3','FIXED_MAIN',ii(2),'/INTER/TYPE7/1','ISOLATED_CONTACT',ii(1,3,4,0,1000)+' '*10+ii(0,2,0,0),ff(1,0,0)+' '*10+ii(0,0),ff(0,0,0)+ii(0,0,0),ff(case['Stfac'],0,1,0,1e30),'   000 000'+ff(1e-20,1e-20,1,0.2),ii(0,0)+ff(0)+ii(0,0,0)+ff(0),'/TH/INTER/3','CONTACT_RAW',f'{"FNX":>10}{"CE_ELAST":>10}',ii(1)]
    L+=['/TH/PART/1','PART_STATE',''.join(f'{s:>10}' for s in ['IE','KE','RKE','HE','PW','XMOM','YMOM','ZMOM','MASS']),ii(1,2),'/TH/NODE/2','NODES',''.join(f'{s:>10}' for s in ['DX','VX','VRX','VRY','VRZ','REACX'])]
    L+=[ii(i,0)+'N'+str(i) for i in range(1,9)];L+=['/END']
    (d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    e=c['execution'];engine=['/ANIM/DT',ff(0,e['animation_interval_ms']),'/ANIM/MASS','/ANIM/VECT/VEL','/ANIM/VECT/DISP','/ANIM/ELEM/ENER','/DT',ff(case['dt_scale'],0),'/MON/ON','/PRINT/100/100',f'/RUN/{n}/1',ff(e['end_ms']),'/TFILE/4',ff(e['history_interval_ms']),'/VERS/2026']
    (d/(n+'_0001.rad')).write_text('\n'.join(engine)+'\n',encoding='utf-8')
    dump(d/'generation.json',{'created_utc':now(),'name':n,'case':case,'nodes_mm':x,'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'history_records_per_frame':5 if case['contact'] else 4,'no_RBE3':True,'no_mass_scaling':True,'no_eroding_elements':True})
    print({'built':caseid},flush=True)

def run(caseid):
    guard();d=OUT/'r0'/caseid;g=read(d/'generation.json');n=g['name'];e=read(CFG)['execution'];assert not (d/'starter.log').exists()
    for exe,args,log,limit in [('starter_win64.exe',['-i',n+'_0000.rad','-np','1'],'starter.log',e['starter_timeout_s']),('engine_win64.exe',['-i',n+'_0001.rad'],'engine.log',e['engine_timeout_s']),('th_to_csv_win64.exe',[n+'T01'],'converter.log',e['converter_timeout_s'])]:
        if not execute(RUNTIME/exe,args,d,log,limit,env()):print({'failed':caseid,'stage':log},flush=True);return
        if log=='starter.log':
            txt=(d/log).read_text(errors='replace');wa=re.findall(r'(\d+) WARNING\(S\)',txt);er=re.findall(r'(\d+) ERROR\(S\)',txt)
            if not wa or not er or int(wa[-1]) or int(er[-1]):print({'starter_rejected':caseid},flush=True);return
    print({'executed':caseid},flush=True)

def review(caseid):
    guard();d=OUT/'r0'/caseid;g=read(d/'generation.json');n=g['name'];assert not (d/'review.json').exists();H=histories(d/(n+'T01.csv'));keys=list(H);T=H['time'];v=np.column_stack(list(H.values()));rr=records(d/(n+'T01'));nr=g['history_records_per_frame'];header=len(rr)-nr*len(T);assert header>0
    frames=[rr[header+i*nr:header+(i+1)*nr] for i in range(len(T))];sizes=[len(q) for q in frames[0]];assert sizes[0]==4 and sizes[1]==88 and all([len(q) for q in f]==sizes for f in frames)
    b=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames]);a=read(CFG)['acceptance'];binary_ok=b.shape==v.shape and np.allclose(b,v,rtol=a['native_binary_csv_relative'],atol=a['native_binary_csv_absolute']);assert binary_ok
    def node(i,channel):
        matches=[k for k in keys if k.startswith('NODES') and re.search(r'\s'+str(i)+r'\s+N'+str(i)+r'\s',k) and k.strip().endswith(channel)]
        assert len(matches)==1,(i,channel,matches);return H[matches[0]]
    def part(i,channel):
        matches=[k for k in keys if k.startswith('PART_STATE') and re.search(r'\s'+str(i)+r'\s',k) and k.strip().endswith(channel)]
        assert len(matches)==1,(i,channel,matches);return H[matches[0]]
    Eterms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    E=sum(H[k] for k in Eterms)*.001;E0=E[0];W=H['EXTERNAL WORK']*.001;res=E-E0-W
    mass=part(1,'MASS')[0]*.001;Px=part(1,'XMOM')*.001;VX=np.column_stack([node(i,'VX') for i in range(1,5)]);DX=np.column_stack([node(i,'DX') for i in range(1,5)])
    initial=read(CFG)['analytical_reference'];P0=initial['initial_Px_Ns'];KE0=initial['initial_KE_J'];J=np.zeros(len(T))
    if g['case']['contact']:
        ck=[k for k in keys if k.startswith('CONTACT_RAW') and k.strip().endswith('FNX')];assert len(ck)==1;J=(H[ck[0]]-H[ck[0]][0])*.001
    # TH/INTER FNX is retained as raw native history; determine which side by residuals, save both signs.
    mom_plus=float(np.max(abs(Px-Px[0]-J)))/P0;mom_minus=float(np.max(abs(Px-Px[0]+J)))/P0
    support=sum(node(i,'REACX') for i in range(5,9));Js=np.r_[0,np.cumsum((support[1:]+support[:-1])*.5*np.diff(T))]*.001
    Pg=H['X-MOMENTUM']*.001;supporterr=float(np.max(abs(Pg-Pg[0]-Js)))/P0
    native_rot=H['ROTATION ENERGY']*.001;prke=part(1,'RKE')*.001
    checks={'binary_all_channels_match_native_converter':bool(binary_ok),'normal_engine_termination':'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace').upper(),'finite_monotone_history':bool(np.all(np.isfinite(v)) and np.all(np.diff(T)>0)),'end_sample_within_2pct':bool(T[-1]>=read(CFG)['execution']['end_ms']*.98),'mass_analytic':bool(abs(mass-.001112)/.001112<=a['initial_mass_relative']),'initial_KE_analytic':bool(abs(E0-KE0)/KE0<=a['initial_KE_relative']),'energy_closure':bool(np.max(abs(res))/KE0<=a['maximum_energy_residual_relative_to_initial']),'momentum_contact':bool(min(mom_plus,mom_minus)<=a['momentum_residual_relative_to_initial']),'support_momentum':bool(supporterr<=a['support_momentum_relative']),'native_rotation_zero':bool(np.max(abs(native_rot))<=a['zero_rotation_allowance_J']),'part_RKE_zero_expected':bool(np.max(abs(prke))<=a['zero_rotation_allowance_J'])}
    if g['case']['contact']:checks['complete_rebound_speed']=bool(np.max(abs(VX[-1]+1))<=a['rebound_speed_relative'])
    else:
        checks.update(free_velocity=bool(np.max(abs(VX-1))<=a['free_velocity_absolute_m_s']),free_energy=bool(np.max(abs(res))/KE0<=a['free_energy_relative']))
    result={'case':g['case'],'created_utc':now(),'checks':checks,'all_checks_pass':all(checks.values()),'failed_checks':[k for k,b in checks.items() if not b],'native_binary_schema':{'header_records':header,'records_per_frame':nr,'sizes_bytes':sizes,'all_channels_verified':binary_ok},'mass_kg':float(mass),'initial_energy_J':float(E0),'last_saved_time_ms':float(T[-1]),'max_energy_residual_fraction':float(np.max(abs(res))/KE0),'final_energy_residual_J':float(res[-1]),'final_velocity_m_s':VX[-1].tolist(),'final_raw_contact_impulse_Ns':float(J[-1]),'momentum_plus_relative':mom_plus,'momentum_minus_relative':mom_minus,'support_momentum_relative':supporterr,'maximum_native_rotation_energy_J':float(np.max(abs(native_rot))),'maximum_part_RKE_J':float(np.max(abs(prke))),'physical_impact_qualified':False}
    np.savez_compressed(d/'balance_history_SI.npz',time_ms=T,energy_residual_J=res,global_energy_J=E,raw_contact_impulse_Ns=J,moving_momentum_Ns=Px,velocity_m_s=VX,displacement_mm=DX,native_rotation_J=native_rot,part_RKE_J=prke,support_impulse_Ns=Js)
    dump(d/'review.json',result);print(result,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','build','run','review']);p.add_argument('--case',default='FREE');a=p.parse_args()
    declare() if a.action=='declare' else globals()[a.action](a.case)
