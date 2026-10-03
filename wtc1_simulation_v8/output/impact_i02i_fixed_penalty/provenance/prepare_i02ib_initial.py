"""Create a separate bounded I02I-B campaign; never edit predecessor files."""
import hashlib, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root/'wtc1_simulation_v8'
def dump(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
h=json.loads((base/'data/impact_i02h_local_cohesive.json').read_text())
a=json.loads((base/'data/impact_i02i_material_predeclaration.json').read_text())
cases=[]
def add(id,mode,interpretation='engineering',h=1.27,**kw):
    cases.append(dict(id=id+'_R1',mode=mode,interpretation=interpretation,local_step_mm=h,material_variant='nasa_law36',**kw))
add('ELASTIC','elastic',loading_end_ms=6.,target_displacement_mm=.02)
add('ELASTIC_SLOW','elastic',loading_end_ms=12.,target_displacement_mm=.02)
for branch,interpretation in [('ENG','engineering'),('TRUE','true_total')]:
    add(branch+'_NOPROP','no_propagation',interpretation,loading_end_ms=12.,target_displacement_mm=1.2)
    for label,step in [('L254',2.54),('L127',1.27),('L0635',.635)]:
        add(branch+'_'+label,'fracture',interpretation,step,Gf_N_per_mm=30.,loading_end_ms=12.,target_displacement_mm=1.2)
add('ENG_L127_DT45','fracture',Gf_N_per_mm=30.,loading_end_ms=12.,target_displacement_mm=1.2,dt_scale=.45)
add('ENG_L127_SLOW','fracture',Gf_N_per_mm=30.,loading_end_ms=24.,target_displacement_mm=1.2)
cfg=dict(id='IMPACT-I02I-B-R1',scope='Fresh generic M(T) numerical coupon, fixed initial-area cohesive penalty, two unresolved source interpretations; no aircraft/facade/global-collapse qualification.',seed=1102010,random_draws=0,geometry=h['geometry'],mesh=h['mesh'],material=a['material'],material_baseline_applied=h['material_baseline_applied'],material_tabulated_radioss={},identified_material_curve_not_applied={'note':'Two fresh interpretations from I02I-A; neither selected as measured truth.'},seam={'peak_normal_traction_mpa':495.,'normal_penalty_N_per_mm3':56000.,'tangent_penalty_N_per_mm3':21500.,'area_rule':'initial thickness times clipped reference tributary width, fixed throughout each fresh history','penalty_status':'numerical choices, not measured stiffness','fracture_status':'Gf=30 N/mm is hypothetical; 15/60 deferred to I02I-C or later; TYPE8 hysteretic spring is not a calibrated mixed-mode cohesive material','domain_stop_gap_fraction_of_deltaf':.8},units={'mass':'g','length':'mm','time':'ms','force':'N','stress':'MPa = N/mm2','penalty':'N/mm3','solver_energy':'N mm = mJ','report_energy':'J = 0.001 N mm','reaction_history':'raw untitled REACY expected cumulative impulse N ms, verify by controls'},shell_options=a['shell_variants']['finite'],execution={'threads':1,'dt_scale':.9,'elastic_end_ms':6.,'elastic_target_displacement_mm':.02,'fracture_end_ms':12.,'fracture_target_displacement_mm':1.2,'history_dt_ms':.004,'animation_states':0,'maximum_case_wall_seconds':1800,'maximum_campaign_wall_seconds':5400,'preflight_before_engine':True,'no_mass_scaling':True,'loading_path':'quintic 10s3-15s4+6s5, 800 subdivisions; slow cases same path with doubled time','expected_wall_minutes':[30,60],'absolute_cost_ceiling_minutes':90},gates={'maximum_mass_error_fraction':1e-5,'maximum_global_energy_residual_fraction':.005,'maximum_independent_boundary_work_error_fraction':.01,'maximum_momentum_residual_fraction':.01,'maximum_spring_energy_sum_error_fraction':.001,'maximum_spring_geometry_gap_error_mm':1e-5,'maximum_kinetic_to_internal_significant_window':.01,'maximum_elastic_duration_work_difference_fraction':.01,'maximum_elastic_duration_impulse_ratio_error_fraction':.01,'maximum_mesh_force_difference_fraction':.1,'maximum_mesh_work_difference_fraction':.05,'maximum_mesh_ctoa_difference_fraction':.1,'maximum_time_force_difference_fraction':.05,'maximum_time_ctoa_difference_fraction':.1},comparison={'common_displacements_mm':[.2,.5,.8,1.,1.2],'common_nodal_advances_mm':[2.54,5.08,7.62],'no_extrapolation':True,'advance_area_definition':'sum reference tributary widths of contiguous deactivated springs, first cell h/2','advance_nodal_definition':'last contiguous deactivated seam-node distance from original tip; exact nodal targets only, absent targets unassessed','ctoa_definition':'2 atan(opening/(2B)) and 2 atan(opening/(4B)), mean of two sides; reference opening offsets B/2B behind area-equivalent tip','refined_domain_maximum_area_advance_mm':10.16,'guard_definition':'stop engine when Euclidean distance between duplicated seam nodes at x=+-22.86 reaches 0.8 deltaf; not cropped history','significant_energy_window':'IE >= 1 percent of its own peak; no exclusion of fracture spikes'},cases=cases,sources=a['sources']+[{'id':'ALTAIR_SENSOR_DIST','url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/sensor_dist_starter_r.htm','use':'distance trigger for refined-domain guard'},{'id':'ALTAIR_STOP_SENSOR','url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/stop_lsensor_engine_r.htm','use':'engine stop with ended time history'},{'id':'ALTAIR_SPRING_HISTORY','url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm','use':'OFF, forces, elongations and IE'}],qualification={'source_convention_verified':False,'physical_material_calibrated':False,'fracture_propagation_qualified':False,'aircraft_facade_qualified':False,'thermal_branch_resumed':False,'blender_executed':False},publication={'repository':'https://github.com/WTC-simu2026/WTC-simu2026','every_verified_iterations':2,'baseline_iteration':'IMPACT-I02I-A','this_iteration_count_since_baseline':1})
dump(base/'data/impact_i02i_fixed_penalty_predeclaration.json',cfg)
old=base/'scripts/run_impact_i02h.py'
code=old.read_text()
def replace(a,b):
    global code
    assert a in code,a[:100]
    code=code.replace(a,b)
replace('import run_impact_i02g as i02g','import run_impact_i02g as i02g\nimport run_impact_i02i_material as unit\nimport re\nfrom datetime import datetime, timezone')
replace('impact_i02h_local_cohesive','impact_i02i_fixed_penalty_predeclaration',1) if False else None
replace('data/impact_i02h_local_cohesive.json','data/impact_i02i_fixed_penalty_predeclaration.json')
replace('output/impact_i02h_local_cohesive','output/impact_i02i_fixed_penalty')
replace('    material = cfg["material_tabulated_radioss"] if material_variant == "nasa_law36" else cfg["material_baseline_applied"]','    points, ledger = unit.curve(cfg, case["interpretation"])\n    material = dict(cfg["material"], law36_plastic_true_strain=[p[0] for p in points], law36_true_stress_mpa=[p[1] for p in points])')
replace('name = "I02H_"','name = "I02IB_"')
replace('    lines += i02g.shell_property_lines(thickness)','    lines += ["/PROP/SHELL/1", "QEPH_EXPLICIT_FINITE_FRESH", f\'{24:10d}{4:10d}{0:10d}{0:10d}{0:10d}{"":10s}{0:20g}\', i02g.ff(0,0,0,0,0), i02g.ii(5,"")+i02g.ff(thickness,0)+i02g.ii("",1,1,0)]')
replace('normal_stiffness = material["young_modulus_mpa"] / local_step * area','normal_stiffness = seam["normal_penalty_N_per_mm3"] * area')
replace('tangent_stiffness = shear_modulus / local_step * area','tangent_stiffness = seam["tangent_penalty_N_per_mm3"] * area')
replace('range(401)','range(801)')
replace('index / 400.0','index / 800.0')
replace('smooth = 3.0 * u * u - 2.0 * u * u * u','smooth = u*u*u*(10+u*(-15+6*u))')
replace('    lines += ["/UNIT/1", "I02H_G_MM_MS", i02g.ff("g", "mm", "ms"), "/END"]','''    lines += ["/TH/NODE/5", "LOWER_GRIP_HISTORY", i02g.ii("DY", "VY", "REACY")]
    lines += [i02g.ii(node_id, 0) for node_id in lower_grip]
    plastic_ids=[]
    for eid,quad in enumerate(shells,1):
        cx=sum(nodes[n-1][0] for n in quad)/4; cy=sum(nodes[n-1][1] for n in quad)/4
        if crack_half-local_step <= abs(cx) <= outer_break and abs(cy) <= 2*local_step:
            plastic_ids.append(eid)
    lines += ["/TH/SHEL/7", "TIP_PLASTIC_HISTORY", i02g.ii("EMAX")]
    lines += [i02g.ii(eid,0) for eid in plastic_ids]
    guards=[]
    if mode == "fracture":
        for sid,x in [(501,-outer_break),(502,outer_break)]:
            j=min(range(len(xs)),key=lambda k:abs(xs[k]-x))
            assert abs(xs[j]-x)<1e-9
            guards.append(dict(sensor_id=sid,x_mm=x,lower_node=lower_seam[j],upper_node=upper_seam[j],threshold_mm=seam["domain_stop_gap_fraction_of_deltaf"]*deltaf))
            lines += [f"/SENSOR/DIST/{sid}/1", "REFINED_DOMAIN_GUARD", i02g.ff(0), i02g.ii(lower_seam[j],upper_seam[j])+i02g.ff(-1e30,guards[-1]["threshold_mm"],0)+i02g.ii(0)]
        lines += ["/TH/SENSOR/6", "DOMAIN_STOP_STATUS", i02g.ii("STATUS"), i02g.ii(501,502)]
    lines += ["/UNIT/1", "I02IB_G_MM_MS", i02g.ff("g", "mm", "ms"), "/END"]''')
replace('    animation_dt = run_end_ms / (int(execution["animation_states"]) - 1)','    history_dt = execution["history_dt_ms"] * loading_end_ms / (6. if mode=="elastic" else 12.)')
replace('        "/ANIM/DT", i02g.ff(0, animation_dt), "/ANIM/VECT/DISP", "/ANIM/VECT/VEL", "/ANIM/ELEM/ENER",\n','')
replace('i02g.ff(execution["history_dt_ms"])','i02g.ff(history_dt)')
replace('    engine_file = directory / f"{name}_0001.rad"','    if guards: engine += ["/STOP/LSENSOR",i02g.ii(501,502),i02g.ii(0,1,0,0,0,0,0)]\n    engine_file = directory / f"{name}_0001.rad"')
replace('        "generator_sha256": sha(Path(__file__)),','        "generator_sha256": sha(Path(__file__)),\n        "shell_options": cfg["shell_options"], "conversion_ledger": ledger, "guards":guards, "plastic_history_shell_ids":plastic_ids,\n        "dependency_sha256":{Path(mod.__file__).name:sha(Path(mod.__file__)) for mod in [i02g,unit]},')
code=code[:code.index('\ndef execute(')]
code=code.replace('"""Generate and run immutable IMPACT-I02H locally refined M(T) coupons."""','"""Fresh I02I-B coupon generator, derived from preserved I02H geometry; explicit finite shell and fixed initial-area penalty."""')
p=base/'scripts/run_impact_i02i_fixed_penalty.py'; assert not p.exists(); p.write_text(code,encoding='utf-8',newline='\n')
dump(base/'data/impact_i02i_fixed_penalty_generator_origin.json',{'previous_generator':str(old.relative_to(root).as_posix()),'sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'changes':'fresh finite shell, two source interpretations, fixed Kn/Kt, reference area, quintic path, lower reactions, tip plastic histories, distance sensor stop, no animation','bootstrap':'tmp/prepare_i02ib.py'})
print(json.dumps({'cases':len(cases),'config':str(cfg['id'])}))
