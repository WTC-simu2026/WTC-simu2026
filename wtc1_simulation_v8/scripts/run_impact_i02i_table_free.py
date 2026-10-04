"""I02I-G: fresh table-resolution controls and a free elastic oscillator.

Preserve all previous trajectories; no restart or damaged property change.
Actions declare / run. Six fresh cases, 90 s/case and 600 s total.
"""
from __future__ import annotations
import argparse, copy, json, math, urllib.request
from pathlib import Path
import run_impact_i02i_dtcap as f

ROOT,RUNTIME,NOW,sha,dump,rel,harness=f.ROOT,f.RUNTIME,f.NOW,f.sha,f.dump,f.rel,f.harness
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02i_table_free'
CFG=ROOT/'wtc1_simulation_v8/data/impact_i02i_table_free_predeclaration.json'
SOURCES=[
 ('ALTAIR_INIVEL','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inivel_starter_r.htm','Initial translational velocity, node group, zero start time and optional units'),
 ('ALTAIR_TH_NODE','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm','VX/DX and constrained-node REACX; documentation calls REACX force whereas cached runtime checks identify cumulative impulse: discrepancy retained'),
 ('ALTAIR_DYNAMIC_THEORY_2017','https://2017.help.altair.com/2017/hwsolvers/theory_dynamic_analysis.pdf','Central difference half-step velocities and second-order accuracy; does not establish 2026 time-history centering')]

def declare():
    assert not OUT.exists() and not CFG.exists(),'Never overwrite iterations'
    hv=harness();state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'))
    assert state['current_iteration']=='IMPACT-I02I-F' and state['next_iteration']=='IMPACT-I02I-G'
    cfg=copy.deepcopy(json.loads(f.CFG.read_text(encoding='utf-8')))
    cfg.update(id='IMPACT-I02I-G',declared_utc=NOW(),seed=1102015,random_draws=0,
      scope='Four refined imposed AFTER histories and two fresh free elastic oscillators; no free fracture')
    base=next(c for c in cfg['cases'] if c['id']=='AFTER_CAP100NS');cases=[]
    for n in [1600,3200]:
        for cap,label in [(.0001,'100NS'),(.00005,'050NS')]:
            c=copy.deepcopy(base);c.update(id=f'AFTER_N{n}_{label}',subdivisions=n,maximum_dt_ms=cap,stage='table')
            cases.append(c)
    m=.1;k=21500.;omega=math.sqrt(k/m);period=2*math.pi/omega
    for cap,label in [(.0001,'100NS'),(.00005,'050NS')]:
        cases.append({'id':'FREE_ELASTIC_'+label,'stage':'free','maximum_dt_ms':cap,'dt_scale':.2,'fails':False,'end_ms':8*period})
    cfg['cases']=cases;cfg['comparison_pairs']=[]
    cfg['free_reference']={'moving_mass_g':m,'fixed_mass_g':m,'k_N_per_mm':k,'u0_mm':0.,'v0_mm_per_ms':1.,
        'omega_rad_per_ms':omega,'period_ms':period,'duration_periods':8,
        'amplitude_mm':1/omega,'force_amplitude_N':k/omega,'initial_momentum_N_ms':m,'initial_energy_J':.5*m*.001,
        'formulas':'u=v0/omega*sin(omega*t); v=v0*cos(omega*t); F=k*u; U=k*u^2/2; K=m*v^2/2; P=m*v; J_support=P-P0',
        'normal_mode':'non-failing linear, Y blocked; X symmetric linear H2 with no fracture',
        'time_centering':'Exact 2026 TH output centering not documented; raw common times audited without shift or extrapolation'}
    cfg['gates'].update(table_residual_ratio_relative_tolerance=.10,table_energy_difference_fraction=.005,
        free_displacement_fraction=.01,free_nodal_velocity_fraction=.03,free_force_fraction=.03,
        free_global_momentum_fraction=.01,free_impulse_fraction=.03,free_nodal_global_momentum_fraction=.03,
        free_energy_fraction=.005,free_recoverable_energy_fraction=.005,free_period_fraction=.005,
        free_fixed_displacement_mm=1e-10,free_initial_velocity_fraction=1e-6)
    cfg['predeclared_tolerance_rationale']={
        'free_staggered_fields':'3% of analytic amplitude for raw force, nodal velocity and reaction impulse. At 100 ns omega*h/2=0.023184 rad; 8-period central-difference dispersion adds about 0.004505 rad; conservative sum below 0.03. No fitted time shift.',
        'centered_fields':'1% displacement and global momentum; 0.5% energy and period.',
        'table_ratio':'Residual expected to scale linearly with 1/N; compare G/F to 800/N within 10%, with both step caps independently. Hypothesis tested, not guaranteed.',
        'stricter_raw_1pct':'Also save 1% diagnostics for all staggered channels. A failed stricter diagnostic remains visible and does not become a successful 1% qualification.'}
    cfg['qualification'].update(free_fracture_qualified=False,free_elastic_control_only=True,
        exact_time_history_centering_verified=False,post_deactivation_free_inertia_qualified=False)
    cfg['sources'] += [{'id':n,'url':u,'use':use} for n,u,use in SOURCES]
    cfg['saved_F_baseline']={'path':rel(f.OUT/'verification_r1/summary.json'),'sha256':sha(f.OUT/'verification_r1/summary.json'),'cases':['AFTER_CAP100NS','AFTER_CAP050NS']}
    rows={}
    for p in [f.OUT/'preservation_before.json',f.OUT/'artifact_manifest.json']:
        for r in json.loads(p.read_text(encoding='utf-8'))['files']:
            assert sha(ROOT/r['path'])==r['sha256'],r['path'];rows[r['path']]=r
    for p in [f.OUT/'preservation_before.json',f.OUT/'artifact_manifest.json',f.OUT/'publication_verification.json',ROOT/'harness/handoffs/WTC1_IMPACT_I02I_F_HANDOFF.md']:
        rows[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    OUT.mkdir();dump(CFG,cfg);dump(OUT/'harness_before.json',hv)
    dump(OUT/'preservation_before.json',{'created_utc':NOW(),'files':list(rows.values()),'scope':'Saved F/predecessor inventories only; no source archive scan'})
    for name in f.ADMIN:(OUT/('before_'+Path(name).name)).write_bytes((ROOT/'harness'/name).read_bytes())
    (OUT/'sources').mkdir();snapshots=[]
    for n,u,use in SOURCES:
        req=urllib.request.Request(u,headers={'User-Agent':'WTC-simu2026-primary-source-audit'})
        with urllib.request.urlopen(req,timeout=40) as response:data=response.read()
        p=OUT/'sources'/(n.lower()+('.pdf' if u.endswith('.pdf') else '.html'));p.write_bytes(data)
        snapshots.append({'id':n,'url':u,'path':rel(p),'sha256':sha(p),'bytes':len(data),'use':use})
    dump(OUT/'source_manifest.json',{'created_utc':NOW(),'sources':cfg['sources'],'new_primary_snapshots':snapshots,
        'cached_F_manifest':rel(f.OUT/'source_manifest.json'),'cached_F_sha256':sha(f.OUT/'source_manifest.json'),
        'documentation_excluded_from_redistribution':True,'REACX_documentation_runtime_discrepancy_retained':True})
    print(json.dumps({'declared':cfg['id'],'cases':len(cases),'old_files_pinned':len(rows),'period_ms':period}),flush=True)

def smooth_path(targets,segment_ms,n):
    path=[]
    for s,(left,right) in enumerate(zip(targets[:-1],targets[1:])):
        for j in range(n):
            q=j/n;w=10*q**3-15*q**4+6*q**5
            path.append(((s+q)*segment_ms,left+(right-left)*w))
    path.append(((len(targets)-1)*segment_ms,targets[-1]));return path

def generate(cfg,case,folder):
    d=f.inherited;oldcfg,oldpath=d.CFG,d.smooth_path
    temp=copy.deepcopy(case)
    if case['stage']=='free':temp.update(x_mm=[0,0],y_deltaf=[0,0],expected_final='zero')
    n=case.get('subdivisions',800)
    try:
        d.CFG=CFG;d.smooth_path=lambda targets,segment:smooth_path(targets,segment,n)
        meta=d.generate(cfg,temp,folder)
    finally:d.CFG,d.smooth_path=oldcfg,oldpath
    dump(folder/'generation_inherited.json',meta)
    oldname=meta['name'];name='I02IG_'+case['id'];deck=d.deck
    for suffix in ['_0000.rad','_0001.rad']:
        p=folder/(oldname+suffix);lines=p.read_text(encoding='utf-8').replace(oldname,name).splitlines()
        if suffix=='_0000.rad' and case['stage']=='free':
            # Replace only the fresh generated property by a non-failing elastic one.
            start=lines.index('/PROP/TYPE8/1');end=lines.index('/PART/1')
            prop=[];c=cfg['connector'];deck.add_spring_property(prop,1,10,11,c['kt_N_per_mm'],c['kn_N_per_mm'],c['peak_normal_force_N'],meta['delta0_mm'],meta['deltaf_mm'],True)
            prop[2]=deck.ff(c['mass_g'],c['rotational_inertia_g_mm2'])+deck.ii(1,0,0,0,0,1)
            lines[start:end]=prop
            j=lines.index('/BCS/2');lines[j+1]='FREE_X_BLOCK_YZ_ROT';lines[j+2]=f"{'011':>6}{'111':>4}"+deck.ii(0,2)
            start=lines.index('/FUNCT/90');end=lines.index('/TH/SPRING/2');del lines[start:end]
            j=lines.index('/TH/SPRING/2');lines[j:j]=['/INIVEL/TRA/90/1','INITIAL_FREE_X',deck.ff(1,0,0)+deck.ii(2,0),deck.ff(0)+deck.ii(0)]
            assert not any('/IMPDISP' in line for line in lines)
        if suffix=='_0001.rad':
            j=lines.index('/MON/ON');lines[j:j]=['/DTIX',deck.ff(case['maximum_dt_ms'],case['maximum_dt_ms'])]
            if case['stage']=='free':lines[lines.index('/RUN/'+name+'/1')+1]=deck.ff(case['end_ms'])
        new=folder/(name+suffix);assert not new.exists();new.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n');p.unlink()
    if case['stage']=='table':
        text=(folder/(name+'_0000.rad')).read_text().splitlines()
        counts={};spacing={}
        for fid in [90,91]:
            j=text.index('/FUNCT/'+str(fid))+2;rows=[]
            while j<len(text) and not text[j].startswith('/'):
                rows.append([float(text[j][:20]),float(text[j][20:40])]);j+=1
            counts[str(fid)]=len(rows);spacing[str(fid)]=max(b[0]-a[0] for a,b in zip(rows[:-1],rows[1:]))
            assert len(rows)==(len(case['x_mm'])-1)*n+1
            assert spacing[str(fid)]<=cfg['loading']['segment_ms']/n+1e-10
        meta.update(serialized_function_points=counts,maximum_function_interval_ms=spacing,subdivisions=n)
    else:
        meta.update(x_path=[],y_path=[],end_ms=case['end_ms'],free_reference=cfg['free_reference'],no_imposed_moving_X=True,fracture_disabled=True)
    meta.update(name=name,case=case,config_sha256=sha(CFG),generator_sha256=sha(__file__),inherited_generator_sha256=sha(d.__file__),maximum_dt_ms=case['maximum_dt_ms'],fresh_state=True)
    dump(folder/'generation.json',meta);return meta

def run():
    # Reuse the bounded execution protocol, changing bindings only in this process.
    previous=f.OUT,f.CFG,f.generate
    try:f.OUT,f.CFG,f.generate=OUT,CFG,generate;f.run()
    finally:f.OUT,f.CFG,f.generate=previous

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);a=p.parse_args();globals()[a.action]()
