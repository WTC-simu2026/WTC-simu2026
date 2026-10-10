"""Fresh single-factor DKT_S3 whole-impact diagnostic; keep all material budgets fixed."""
import copy,traceback
import numpy as np
from run_aircraft_a19 import *
from run_aircraft_a18 import blocks,recover
from audit_aircraft_a02 import numbers_after

WCFG=ROOT/'wtc1_simulation_v8/data/aircraft_a19_whole_declaration.json'
WCASE='DKT_S3_20';D=OUT/'r0'/WCASE;N='A19_'+WCASE
def whole_guard():
    guard();assert streamsha(WCFG)==read(OUT/'whole_declaration_guard.json')['sha256']

def declare():
    guard();assert not WCFG.exists();assert read(OUT/'triangle_review.json')['pass'];c=copy.deepcopy(read(ROOT/'wtc1_simulation_v8/data/aircraft_a18_predeclaration.json'))
    c.update(iteration='AIRCRAFT-A19',declared_utc=now(),seed=1102044,random_draws=0,
       scope='Fresh single-factor whole impact: Ish3n31 DKT_S3 versus cached A18 Ish3n2 C0 large-rotation. Numerical localization comparison, not identified honeycomb failure.',
       inherited_configuration='wtc1_simulation_v8/data/aircraft_a18_predeclaration.json',
       change={'card':'/PROP/TYPE51/21','field':'Ish3n','old':2,'new':31,'only_mechanical_change':True,
         'reason':'Native negative IE concentrated in root facet174 with failed skins, very large core strain and incompatible directors. Alternative triangle tests a formulation contribution; root cause not assumed solved.',
         'no_mass_modulus_strength_G_or_contact_change':True,'core_fracture_still_absent':True,'alternative_formulation_is_not_a_physical_core_failure_model':True},
       diagnostic={'explicit_ply_outputs':[41,42,43],'integration_point':2,'native_radome_IE_nonnegative_J_allowance':1,
         'preserve_cached_A18_failures':True,'cohesive_part_channels':['IE','KE','HE','PW'],'negative_energy_stop_for_extension':True},
       execution={'cpu_threads':2,'GPU':False,'starter_timeout_s':120,'engine_timeout_s':2700,'converter_timeout_s':120,'estimated_minutes':[17,45],
         'cases':[{'id':WCASE,'end_ms':20,'dt_scale':.5,'transition_fraction':.2}],'stop':'2700s cap, nonpositive step or Engine failure; no mass scaling'},
       goal={'target_physical_s':10,'complete':False,'previous_coverage_s':.0200002613,'requested_new_coverage_s':.02},
       sources=['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_shell_idply_restype_engine_r.htm'])
    c['output_contract']['cohesive']='Native BRICK stress/energy/erosion; four actual part channels IE/KE/HE/PW, corrected coverage contract after A18 diagnosis'
    c['video']['source']=rel(D);dump(WCFG,c);dump(OUT/'whole_declaration_guard.json',{'sha256':streamsha(WCFG),'declared_before_any_A19_whole_solver':True});print({'fresh_whole_declared':WCASE},flush=True)

def build():
    whole_guard();assert not D.exists();D.mkdir(parents=True);g=read(SOURCE/'generation.json');pn=g['name'];orig=blocks((SOURCE/(pn+'_0000.rad')).read_text().splitlines());new=[];changes=[]
    for b0 in orig:
        b=b0.copy()
        if b[0]=='/PROP/TYPE51/21':b[2]=b[2][:20]+ii(31)+b[2][30:];changes.append(b[0])
        if b[0] in ['/BEGIN','/TITLE']:b=[x.replace(pn,N) for x in b]
        new+=b
    newblocks={b[0]:b for b in blocks(new)};assert changes==['/PROP/TYPE51/21'];assert all(newblocks[b[0]]==b for b in orig if b[0] not in ['/BEGIN','/TITLE','/PROP/TYPE51/21'])
    (D/(N+'_0000.rad')).write_text('\n'.join(new)+'\n',encoding='utf-8')
    for job in [1,2]:
        E=(SOURCE/(pn+f'_000{job}.rad')).read_text().replace(pn,N).splitlines();E += [f'/ANIM/SHELL/IDPLY/{kind}/{ply}/2' for kind in ['STRESS','STRAIN'] for ply in [41,42,43]];(D/(N+f'_000{job}.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8')
    shutil.copy2(SOURCE/'mesh.json',D/'mesh.json');shutil.copy2(__file__,D/'generator_snapshot.py');dump(D/'generation.json',{**g,'name':N,'case':read(WCFG)['execution']['cases'][0],'created_utc':now(),'parent':rel(SOURCE),'configuration_sha256':streamsha(WCFG),'generator_sha256':streamsha(Path(__file__)),'changed_cards':changes,'history_records_per_frame':14,'cohesive_part_channels':4,'mechanical_scene_unchanged':False})
    dump(D/'scene_audit.json',{'created_utc':now(),'geometry_before_solve_pass':True,'parent_mesh_sha256':streamsha(SOURCE/'mesh.json'),'new_mesh_sha256':streamsha(D/'mesh.json'),'same_mesh':True,'only_mechanical_card_change':'/PROP/TYPE51/21 Ish3n2 to31','same_material_density_thickness_failure_contact_RBE2_RBE3_BCS_INIVEL_ADMAS':True,'physical_core_failure':False});print({'built':WCASE,'single_mechanical_change':True},flush=True)

def starter():
    whole_guard();assert not (D/'starter.log').exists();ok=execute(RUNTIME/'starter_win64.exe',['-i',N+'_0000.rad','-np','1'],D,'starter.log',120,env());s=(D/'starter.log').read_text(errors='replace');warnings=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(D/'starter_gate.json',{'exit_ok':ok,'warnings':warnings,'errors':errors,'pass':ok and not warnings and not errors})
    listing=(D/(N+'_0000.out')).read_text(errors='replace');parent=(SOURCE/(read(SOURCE/'generation.json')['name']+'_0000.out')).read_text(errors='replace');ids=re.findall(r'WARNING ID\s*:\s*(\d+)',s);sections=re.findall(r'^WARNING ID\s*:\s*\d+.*?(?=^WARNING ID|^ INTERFACE NUMBER)',listing,re.S|re.M)
    mass=[np.array(numbers_after(q,'TOTAL MASS AND MASS CENTER',4)) for q in [parent,listing]];inertia=[np.array(numbers_after(q,'TOTAL INERTIA',6)) for q in [parent,listing]]
    checks={'exit_and_zero_errors':ok and errors==0,'same_two_self_warning_ids':sorted(ids)==['1166','343'],'only_interface2_576_initial_overlaps':len(sections)==2 and all('-- INTERFACE ID: 2' in q and '576 INITIAL PENETRATIONS' in q for q in sections),'mass_exact':mass[0][0]==mass[1][0],'CG_mm':bool(np.max(abs(mass[0][1:]-mass[1][1:]))<.001),'inertia_relative':bool(np.max(abs(inertia[0]-inertia[1]))/np.max(abs(inertia[0]))<1e-6),'native_formulation31_present':bool(re.search(r'3NODE SHELL FORMULATION FLAG.*=\s+31',listing))}
    dump(D/'initial_overlap_diagnostic_gate.json',{'created_utc':now(),'checks':checks,'exploratory_engine_allowed':all(checks.values()),'zero_warning_gate_failed':warnings!=0,'physical_contact_gate_pass':False,'mass_CG_new':mass[1].tolist(),'mass_CG_parent':mass[0].tolist(),'native_inertia_relative_change':float(np.max(abs(inertia[0]-inertia[1]))/np.max(abs(inertia[0]))),'same_declared_initial_pairs':True});assert all(checks.values()),checks;print({'Starter_diagnostic_allowed':True,'strict_zero_warning_gate':False,'checks':checks},flush=True)

def engine():
    whole_guard();assert read(D/'initial_overlap_diagnostic_gate.json')['exploratory_engine_allowed'];assert not (D/'engine.log').exists()
    try:
        assert execute(RUNTIME/'engine_win64.exe',['-i',N+'_0001.rad'],D,'engine.log',2700,env());assert 'NORMAL TERMINATION' in (D/'engine.log').read_text(errors='replace')
        o=D/'observer';o.mkdir();shutil.copy2(D/(N+'_0002.rad'),o/(N+'_0002.rad'))
        for p in D.glob(N+'_0001_*.rst'):shutil.copy2(p,o/p.name)
        pins={p.name:streamsha(p) for p in D.iterdir() if p.is_file()};assert execute(RUNTIME/'engine_win64.exe',['-i',N+'_0002.rad'],o,'observer.log',60,env());assert all(streamsha(D/p)==h for p,h in pins.items());dump(D/'observer_preservation.json',{'main_outputs_unchanged':True,'pass':True})
        assert execute(RUNTIME/'th_to_csv_win64.exe',[N+'T01'],D,'converter.log',120,env());recover(D,N);print({'fresh_whole_finished':WCASE},flush=True)
    except Exception:
        dump(D/('retained_failure_'+now().replace(':','-')+'.json'),{'traceback':traceback.format_exc(),'physical_impact_qualified':False});raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','build','starter','engine']);globals()[p.parse_args().action]()
