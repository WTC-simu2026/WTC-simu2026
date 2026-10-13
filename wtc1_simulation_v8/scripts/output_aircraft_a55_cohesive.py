"""Isolate nodal reaction output request from cohesive mechanics, with fresh native states."""
from probe_aircraft_a55 import ROOT,OUT,CFG,read,dump,sha,now,rel,engine,cards,run_case
from pathlib import Path
from run_aircraft_a17 import env
import subprocess,json,time,re


def main():
    engine();target=OUT/'nodal_output_control_predeclaration.json';assert not target.exists()
    root=OUT/'nodal_output_controls';assert not root.exists()
    config=read(CFG);selected=config['cohesive_cases'][0]
    source=ROOT/selected['initial_state']['path'];source=source.with_name(selected['cached_generation']['name']+'_0000.rad')
    cases=[{'id':'DISP_VEL_WITHOUT_REACTION','variables':['DZ','VZ']},
        {'id':'NO_NODAL_OUTPUT','variables':None}]
    dump(target,{'created_utc':now(),'iteration':'AIRCRAFT-A55','seed':1102080,'random_draws':0,
        'source_input':rel(source),'source_sha256':sha(source),'cases':cases,
        'changes':'TH/NODE variables only; remove REACZ while retaining DZ/VZ, or remove the complete TH/NODE block. Original fully prescribed BCS, geometry, mass, LAW117 and imposed motion unchanged.',
        'purpose':'Separate nodal-output descriptor initialization/cleanup failure from actual cohesive mechanics. Native SIGABRT stack identifies RESOL freeing NODREAC; root cause not assumed proved.',
        'CPU_threads':1,'GPU':False,'Starter_cap_s':180,'Engine_cap_s':180,'new_software_patch':False,
        'physical_inputs_unchanged':True,'diagnostic_output_request_change_explicit':True,
        'loaded_fracture_qualification_requires_actual_completed_time_and_original_physical_gates':True,
        'new_whole_duration_credit_s':0})
    root.mkdir();results=[]
    for case in cases:
        d=root/case['id'];d.mkdir();name='A55_'+case['id'];text=source.read_text().replace(selected['cached_generation']['name'],name)
        pattern=r'/TH/NODE/2\nREACTION_NODES\n[^\n]*\n(?:[^/\n]*\n)*'
        match=re.search(pattern,text);assert match
        old=match.group(0)
        if case['variables'] is None:new=''
        else:
            lines=old.splitlines();lines[2]=''.join(f'{value:>10}' for value in case['variables']);new='\n'.join(lines)+'\n'
        text=text[:match.start()]+new+text[match.end():]
        (d/(name+'_0000.rad')).write_text(text,encoding='utf8')
        (d/(name+'_0001.rad')).write_text(cards(name,selected['case']['dt_cap_ms']),encoding='utf8')
        dump(d/'generation.json',{**selected['cached_generation'],'created_utc':now(),'name':name,'TH_NODE_change':case['variables'],'physical_BCS_unchanged':True})
        runtime=ROOT/'wtc1_simulation_v8/openradioss_runtime/v20260728-win64'
        start=time.perf_counter()
        with (d/'starter.log').open('xb') as stream:
            result=subprocess.run([str(runtime/'starter_win64.exe'),'-i',name+'_0000.rad','-np','1'],cwd=d,stdout=stream,stderr=subprocess.STDOUT,timeout=180,env=env()|{'OMP_NUM_THREADS':'1','RAD_HMPP_DOMAINS':'1'})
        log=(d/'starter.log').read_text(errors='replace');warnings=int(re.findall(r'(\d+) WARNING\(S\)',log)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',log)[-1])
        dump(d/'starter.execution.json',{'created_utc':now(),'exit_code':result.returncode,'wall_s':time.perf_counter()-start,'CPU_threads':1,'GPU':False,'cap_s':180,'warnings':warnings,'errors':errors})
        assert result.returncode==0 and warnings==0 and errors==0
        native=run_case(d,name);results.append({'case':case['id'],'native':native})
        print(json.dumps(results[-1]),flush=True)
    dump(root/'output_control_execution_review.json',{'created_utc':now(),'cases':results,'no_physical_qualification_inferred_from_exit_code_only':True})


if __name__=='__main__':main()
