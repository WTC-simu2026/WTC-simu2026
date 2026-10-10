"""Read explicit ply fields from a copied A18 end checkpoint, without rerunning impact."""
import shutil
from diagnose_aircraft_a19_cached import fast
from run_aircraft_a19 import *

def main():
    guard();cfg=ROOT/'wtc1_simulation_v8/data/aircraft_a19_ply_observer.json';d=OUT/'ply_observer';assert not cfg.exists() and not d.exists()
    n=read(SOURCE/'generation.json')['name'];checkpoint=SOURCE/(n+'_0001_0001.rst');pin=streamsha(checkpoint)
    c={'iteration':'AIRCRAFT-A19','declared_utc':now(),'seed':1102044,'random_draws':0,'source_checkpoint':rel(checkpoint),'source_sha256':pin,
       'scope':'Isolated first observer state at A18 end, only explicit three integration points of plies41/42/43. End state is unphysical; no predictive continuation.',
       'mechanics_changed':False,'old_impact_reruns':0,'maximum_seconds':60,'record':'first animation only; exclude observer work and impulses',
       'requests':[f'/ANIM/SHELL/IDPLY/{kind}/{ply}/{ip}' for kind in ['STRESS','STRAIN'] for ply in [41,42,43] for ip in [1,2,3]],
       'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_shell_idply_restype_engine_r.htm'],'physical_impact_qualified':False}
    dump(cfg,c);d.mkdir();dump(d/'declaration_guard.json',{'sha256':streamsha(cfg),'declared_before_execution':True});shutil.copy2(checkpoint,d/checkpoint.name)
    E=['/ANIM/DT',ff(0,.2),'/PRINT/-1/100',f'/RUN/{n}/2',ff(20.000001),'/TFILE/4',ff(1),'/VERS/2026','/ANIM/MASS','/ANIM/ELEM/ENER','/ANIM/SHELL/DAMA/ALL','/ANIM/VECT/VEL']+c['requests'];(d/(n+'_0002.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8')
    ok=execute(RUNTIME/'engine_win64.exe',['-i',n+'_0002.rad'],d,'observer.log',60,env());assert ok and 'NORMAL TERMINATION' in (d/'observer.log').read_text(errors='replace');assert streamsha(checkpoint)==pin
    p=sorted(d.glob(n+'A*'))[0];q=fast(p);sel={int(e):j for j,e in enumerate(q['eid'])};rad=read(SOURCE/'mesh.json')['radome_element_ids'];out=[]
    for eid in [174,150,168,180]:
        j=sel[eid];out.append({'element_id':eid,'IE_J':float(q['scalar']['Specific Energy'][j]*q['element_mass_g'][j]*.001),'tensor_fields':{k:v[j].tolist() for k,v in q['tensor'].items()},'damage':{k:float(v[j]) for k,v in q['scalar'].items() if k.startswith('DAMAGE')}})
    dump(d/'explicit_ply_diagnostic.json',{'created_utc':now(),'time_ms':q['time_ms'],'source_checkpoint_unchanged':True,'tensors':list(q['tensor']),'selected_elements':out,'all_core_field_maxima':{k:float(abs(v[[sel[e] for e in rad]]).max()) for k,v in q['tensor'].items() if '42' in k},'old_solver_reruns':0,'physical_impact_qualified':False})
    print({'time_ms':q['time_ms'],'tensors':list(q['tensor']),'selected':out[0]},flush=True)

if __name__=='__main__':main()
