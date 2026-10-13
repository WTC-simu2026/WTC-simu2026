"""Fresh isolated transverse-free fixtures; preserve fully prescribed failed A55 controls."""
from probe_aircraft_a55 import ROOT,OUT,CFG,read,dump,sha,now,rel,engine,cards,run_case
from pathlib import Path
import argparse,subprocess,time,re,json

DEC=OUT/'active_dof_predeclaration_r1.json'
RUNTIME=ROOT/'wtc1_simulation_v8/openradioss_runtime/v20260728-win64'


def declare():
    engine();assert not DEC.exists()
    baseline=read(CFG);cases=[]
    for row in baseline['cohesive_cases']:
        old=ROOT/row['initial_state']['path'];source=old.with_name(row['cached_generation']['name']+'_0000.rad')
        assert source.exists()
        cases.append({'case':row['case'],'source_input':rel(source),'source_sha256':sha(source),
            'reference_generation':row['cached_generation'],'new_name':'A55_ACTIVE_'+row['case']['id']})
    dump(DEC,{'created_utc':now(),'iteration':'AIRCRAFT-A55','seed':1102080,'random_draws':0,
        'hypothesis':'Fully prescribed witness may have no free translational equations; invalid-pointer abort does not by itself identify a material failure or prove this cause.',
        'cases':cases,'change':'Release TOP transverse translations only: BCS2 mask110111 or011111 becomes000111. Bottom support and actual imposed opening direction/motion stay identical. Fresh Starter required.',
        'expected_reference':'LAW117 uncoupled pure-mode loading should leave unforced transverse response zero. Check actual transverse fields before comparing the original analytic traction/work/energy reference.',
        'masses_material_law_geometry_motion_unchanged':True,'support_change_explicit':True,
        'acceptance':baseline['acceptance'],'maximum_transverse_displacement_mm':baseline['acceptance']['prescribed_motion_mm'],
        'CPU_threads':1,'GPU':False,'Starter_cap_s':180,'Engine_cap_s':180,'new_software_patch':False,
        'no_whole_model_modification':True,'old_failures_preserved':True,'new_whole_duration_credit_s':0})
    print(json.dumps({'active_dof_cases_declared':len(cases),'physical_support_change_explicit':True}),flush=True)


def run():
    engine();config=read(DEC);root=OUT/'active_dof_controls_r1';assert not root.exists();root.mkdir()
    rows=[]
    for row in config['cases']:
        case=row['case'];name=row['new_name'];d=root/'w0'/case['id'];d.mkdir(parents=True)
        source=ROOT/row['source_input'];assert sha(source)==row['source_sha256'];text=source.read_text()
        oldname=row['reference_generation']['name'];text=text.replace(oldname,name)
        oldmask='   110 111' if case['mode']=='Z' else '   011 111'
        pattern=r'(/BCS/2\nTOP_TRANSVERSE_FIXED\n)'+re.escape(oldmask)
        text,count=re.subn(pattern,r'\g<1>   000 111',text);assert count==1
        (d/(name+'_0000.rad')).write_text(text,encoding='utf8')
        (d/(name+'_0001.rad')).write_text(cards(name,case['dt_cap_ms']),encoding='utf8')
        dump(d/'generation.json',{**row['reference_generation'],'name':name,'created_utc':now(),
            'new_implicit_cards':True,'transverse_translations_released':True,'A55_configuration_sha256':sha(CFG)})
        argv=[str(RUNTIME/'starter_win64.exe'),'-i',name+'_0000.rad','-np','1']
        start=time.perf_counter()
        with (d/'starter.log').open('xb') as stream:
            result=subprocess.run(argv,cwd=d,stdout=stream,stderr=subprocess.STDOUT,timeout=180,
                env=__import__('run_aircraft_a17').env()|{'OMP_NUM_THREADS':'1','RAD_HMPP_DOMAINS':'1'})
        log=(d/'starter.log').read_text(errors='replace');warnings=re.findall(r'(\d+) WARNING\(S\)',log);errors=re.findall(r'(\d+) ERROR\(S\)',log)
        review={'created_utc':now(),'exit_code':result.returncode,'wall_s':time.perf_counter()-start,'CPU_threads':1,'GPU':False,'cap_s':180,
            'warnings':int(warnings[-1]) if warnings else None,'errors':int(errors[-1]) if errors else None}
        dump(d/'starter.execution.json',review)
        ok=result.returncode==0 and review['warnings']==0 and review['errors']==0
        if ok:
            native=run_case(d,name);ok=native['parent_exit_code']==0 and native['normal_termination']
            if ok:
                started=time.perf_counter();converted=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,timeout=60)
                (d/'converter.log').write_bytes(converted.stdout+converted.stderr)
                dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':converted.returncode,'wall_s':time.perf_counter()-started,'cap_s':60})
                ok=converted.returncode==0 and (d/(name+'T01.csv')).exists()
        rows.append({'case':case,'native_completed_and_converted':ok,'Starter':review})
        print(json.dumps(rows[-1]),flush=True)
    dump(root/'execution_review.json',{'created_utc':now(),'cases':rows,'all_native_completed':all(row['native_completed_and_converted'] for row in rows)})


def review():
    engine();root=OUT/'active_dof_controls_r1';result=read(root/'execution_review.json')
    if not result['all_native_completed']:
        print('Active-DOF campaign incomplete; no loaded cohesive qualification inferred.',flush=True);return
    import review_aircraft_a17 as auditor
    auditor.OUT=root;auditor.CFG=CFG;auditor.guard=lambda:engine();auditor.main()
    from audit_aircraft_a05 import histories,vtk
    import numpy as np
    fields=[]
    for row in read(DEC)['cases']:
        case=row['case'];d=root/'w0'/case['id'];name=row['new_name'];axis=2 if case['mode']=='Z' else 0
        others=[index for index in range(3) if index!=axis]
        for path in sorted(d.glob(name+'A[0-9][0-9][0-9]')):
            converted=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(path)],capture_output=True,check=True,timeout=60)
            field=vtk(converted.stdout.decode());displacement=field['Displacement'].reshape(-1,3)
            value=float(abs(displacement[:,others]).max())
            fields.append({'path':rel(path),'maximum_unforced_transverse_displacement_mm':value,
                'tolerance_mm':read(DEC)['maximum_transverse_displacement_mm'],'pass':value<=read(DEC)['maximum_transverse_displacement_mm']})
    dump(root/'transverse_response_review.json',{'created_utc':now(),'fields':fields,'pass':bool(fields) and all(row['pass'] for row in fields),
        'different_boundary_conditions_from_initial_fully_prescribed_witness':True,'no_whole_support_change':True})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run','review']);globals()[p.parse_args().action]()
