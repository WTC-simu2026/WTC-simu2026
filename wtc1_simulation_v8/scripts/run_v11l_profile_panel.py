"""Reproducible V11L calculations and saved verification artifacts."""
import argparse
import copy
import hashlib
import json
import platform
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import run_v11i_thermoelastic_panel as inherited
import v11l_profile_panel as physics

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'wtc1_simulation_v8/data/v11l_profile_panel.json'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v): Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,allow_nan=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args()
    cfg=read(CONFIG); out=(ROOT/args.output).resolve()
    if not any(out==r or r in out.parents for r in [(ROOT/cfg[k]).resolve() for k in ('scratch_directory','output_directory')]):
        raise ValueError('Output outside authorized V11L roots')
    if out.exists(): raise FileExistsError(out)
    icfg=read(ROOT/cfg['panel_configuration'])
    ccfg=read(ROOT/icfg['cold_panel_configuration']); hcfg=read(ROOT/icfg['thermomechanical_configuration'])
    ecfg=read(ROOT/icfg['section_configuration']); inputs,input_paths=inherited.load_inputs(ccfg)
    before={}; controls={}
    for path in cfg['sources']:
        m=read(ROOT/path); directory=(ROOT/path).parent
        expected=dict(m['input_sha256'])
        expected.update({(directory/name).relative_to(ROOT).as_posix():h for name,h in m['output_sha256'].items()})
        failed=[name for name,h in expected.items() if sha(ROOT/name)!=h]
        release=read(directory/'release_audit.json')
        if failed or release['status']!='PASS': raise ValueError((path,failed))
        controls[m['iteration']]={'status':'PASS','verified_hash_count':len(expected),'driver_rerun':False}
        before.update(expected)
        for name in ('offline_manifest.json','release_audit.json'):
            p=directory/name; before[p.relative_to(ROOT).as_posix()]=sha(p)
    for path in [CONFIG.relative_to(ROOT).as_posix(),cfg['panel_configuration'],*input_paths.values(),
                 'wtc1_simulation_v8/scripts/v11l_profile_panel.py',
                 'wtc1_simulation_v8/scripts/run_v11l_profile_panel.py',
                 'wtc1_simulation_v8/scripts/audit_v11l_profile_panel.py']:
        before[path]=sha(ROOT/path)
    source_case=next(v for v in read(ROOT/cfg['thermal_cases']) if v['summary']['id']==cfg['source_case'])
    source=physics.SavedProfile(source_case,cfg)
    assert abs(source.length-0.11049)<1e-12
    clock=time.perf_counter(); started=datetime.now(timezone.utc).isoformat()
    out.mkdir(parents=True)
    def model(mode,sub=None,fibers=None):
        active=copy.deepcopy(icfg)
        active['discretization']['concrete_depth_fibers']=fibers or cfg['reference_fibers']
        return physics.ProfilePanel(active,ccfg,hcfg,ecfg,inputs,source,mode,sub or cfg['reference_subdivisions'])
    tests=[]
    def check(name,condition,evidence): tests.append({'name':name,'pass':bool(condition),'evidence':evidence})
    # Cold and affine references use the new adapter, with stored V11I as comparator.
    runs=[]
    for mode in ('cold','uniform_control','linear_control','profile','uniform'):
        run=physics.trace(model(mode),cfg,cfg['interpolation_substeps'],reverse=(mode=='profile'))
        runs.append(run)
        print(mode,run['terminal']['profile_time_coordinate_s'],run['terminal']['max_DCR'],flush=True)
    by={r['mode']:r for r in runs}
    cached=read(ROOT/'wtc1_simulation_v8/output/v11i_thermoelastic_panel/panel_paths.json')
    for mode,cached_id in [('cold','COLD_DELTA_T_ZERO'),('uniform_control','SLAB_UNIFORM_100K')]:
        old=next(r for r in cached if r['summary']['id']==cached_id)['summary']['final']
        err={k:abs(by[mode]['terminal'][k]-old[k])/max(1,abs(old[k])) for k in
             ('stored_J','sensible_enthalpy_J','max_DCR','seat_vertical_reaction_N')}
        check('cached_V11I_'+mode,max(err.values())<cfg['acceptance']['cached_response_relative'],err)
    coldrow=inherited.cached_cold_row(icfg)
    error=abs(by['cold']['terminal']['stored_J']-float(coldrow['stored_J']))
    check('cached_V11F_energy',error<1e-7,error)
    check('cached_V11F_displacement',abs(by['cold']['terminal']['max_slab_down_m']-float(coldrow['max_slab_down_m']))<1e-10,
          by['cold']['terminal']['max_slab_down_m'])
    # Full-section free/restrained identities plus V11H affine constitutive checks.
    section_controls=[]
    for mode in ('uniform_control','linear_control','profile'):
        m=model(mode); sec=m.section
        t=by[mode]['terminal']['profile_time_coordinate_s']
        dt,meta=m.mapped(t); eps=sec.alpha*dt; f=sec.B.T@(sec.EA*eps)
        q=np.linalg.solve(sec.K,f); stress=sec.E*(sec.B@q-eps)
        free=sec.B.T@(sec.area*stress)
        restrained=-sec.E*eps
        record={'mode':mode,'q_free':q.tolist(),'free_resultant':free.tolist(),
                'reaction_fully_restrained':f.tolist(),
                'free_energy_J_per_m':float(.5*np.sum(sec.area*stress**2/sec.E)),
                'restrained_energy_J_per_m':float(.5*np.sum(sec.area*restrained**2/sec.E))}
        section_controls.append(record)
        check('free_resultants_'+mode,float(np.max(abs(free)))/max(1,float(np.max(abs(f))))<1e-10,record)
        if mode!='profile':
            expected=(100 if mode=='uniform_control' else 5*(sec.y/sec.h+.5))*t/source.times[-1]
            check('affine_mapping_'+mode,float(np.max(abs(dt-expected)))<1e-10,float(np.max(abs(dt-expected))))
            # Inherited H solve with matching temperatures, no history mutation.
            sc={'id':'V11L_REFERENCE','rho_total':.002,'layout':'symmetric','mode':'FREE',
                'delta_t_bottom_c':100 if mode=='uniform_control' else 0,
                'delta_t_top_c':100 if mode=='uniform_control' else 5,'alpha_mode':'differential'}
            hs=physics.panel.thermo.ElasticThermoSection(ecfg,hcfg,sc,160).solve(t/source.times[-1])
            check('V11H_free_'+mode,float(np.max(abs(q-hs['q'])))<1e-12,q.tolist())
            check('V11H_restrained_'+mode,float(np.max(abs(f-hs['thermal_resultant'])))/max(1,float(np.max(abs(f))))<1e-10,f.tolist())
    comparisons=[]
    reference=by['profile']
    for label,sub,fibers,steps in [('half_step',4,160,4),('mesh',8,160,2),('fibers',4,320,2)]:
        other=physics.trace(model('profile',sub,fibers),cfg,steps,reverse=False)
        t=reference['terminal']['profile_time_coordinate_s']; ot=other['terminal']['profile_time_coordinate_s']
        relative=abs(t-ot)/max(t,1e-9)
        comparisons.append({'kind':label,'terminal_time_s':ot,'reference_time_s':t,'relative_time_change':relative,
                            'run':other})
        limit=(abs(t-ot)<cfg['acceptance']['half_step_time_absolute_s'] if label=='half_step'
               else relative<cfg['acceptance']['mesh_guard_relative' if label=='mesh' else 'fiber_guard_relative'])
        check(label+'_guard',limit,{'reference_s':t,'other_s':ot,'relative':relative})
        common=min(t,ot)
        refstate=model('profile').solve(.25,common)
        altstate=model('profile',sub,fibers).solve(.25,common)
        responses={k:abs(refstate[k]-altstate[k])/max(floor,abs(refstate[k])) for k,floor in
                   [('max_slab_down_m',1e-6),('seat_vertical_reaction_N',1.),('stored_J',1.)]}
        comparisons[-1]['common_time_s']=common
        comparisons[-1]['common_response_relative']=responses
        check(label+'_common_response',max(responses.values())<.05,responses)
        print('comparison',label,ot,flush=True)
    replay=physics.trace(model('profile'),cfg,cfg['interpolation_substeps'],reverse=True)
    check('deterministic_profile_replay',digest(replay)==digest(reference),{'reference':digest(reference),'replay':digest(replay)})
    all_runs=runs+[r['run'] for r in comparisons]
    histories=[r for run in all_runs for r in run['history']]
    maxima={
        'equilibrium':max(r['equilibrium_residual'] for r in histories),
        'energy_relative':max(r['energy_residual_relative'] for r in histories),
        'energy_absolute_J':max(abs(r['energy_residual_J']) for r in histories),
        'increment_energy_relative':max(r['increment_residual_relative'] for r in histories),
        'accepted_DCR':max(r['max_DCR'] for r in histories),
        'mapping_mean_error_K':max(abs(r['mapping']['mean_delta_k']-r['mapping']['mapped_mean_delta_k']) for r in histories),
        'mapping_gradient_error_K':max(abs(r['mapping']['reference_equivalent_gradient_k']-r['mapping']['mapped_equivalent_gradient_k']) for r in histories),
        'fiber_correction_K':max(r['mapping']['maximum_fiber_correction_k'] for r in histories)}
    for metric,limit in [('equilibrium',1e-8),('energy_relative',2e-8),('increment_energy_relative',2e-8),
                         ('mapping_mean_error_K',1e-10),('mapping_gradient_error_K',1e-10),('accepted_DCR',.900001)]:
        check(metric,maxima[metric]<=limit,{'value':maxima[metric],'limit':limit})
    check('profile_cycle_displacements',reference['cycle_displacement_error']<1e-9,reference['cycle_displacement_error'])
    check('profile_cycle_energy',reference['cycle_stored_error_J']<1e-5,reference['cycle_stored_error_J'])
    bracket=reference['guard_bracket']
    check('guard_brackets_uncommitted',all(r['guard_bracket'] is None or (r['guard_bracket']['accepted_DCR']<.9<=r['guard_bracket']['rejected_DCR'] and not r['guard_bracket']['rejected_committed']) for r in all_runs),bracket)
    check('zero_initial_thermal_profile',float(np.max(abs(model('profile').delta_temperature(0))))==0.,0.)
    lowest=min(min(r['fiber_delta_temperature_k']) for r in histories)
    check('heating_mapping_no_cold_undershoot',lowest>=-1e-10,lowest)
    # Source gross heat and projected temperature mean share the V11K rho*cp.
    source_errors=[]
    for t in source.times:
        _,_,meta=source.at(t)
        source_errors.append(abs(2160000*source.length*meta['mean_delta_k']-meta['source_heat_j_m2']))
    check('source_enthalpy_vs_saved_flux',max(source_errors)<1e-5,max(source_errors))
    after={p:sha(ROOT/p) for p in before}
    check('protected_inputs_unchanged',before==after,{'count':len(before)})
    seconds=time.perf_counter()-clock
    passed=all(c['pass'] for c in tests)
    result={'iteration':'V11L','status':'PASS' if passed else 'FAIL','test_count':len(tests),
        'tests_passed':sum(c['pass'] for c in tests),'case_count':len(runs),
        'state_count':sum(len(r['history']) for r in runs),'maxima':maxima,'controls':controls,
        'profile_terminal':reference['terminal'],'profile_guard':bracket,
        'cycle_return_error_m':reference['cycle_displacement_error'],
        'thermal_history_computed_this_iteration':False,'one_way_profile_transfer':True,
        'coupled_first_law_closed':False,'fire_solved':False,'heated_fracture_solved':False,
        'blender_changed':False,'global_energy_credit_J':0.,
        'runtime':{'seconds':seconds,'started_utc':started,'python':platform.python_version(),'numpy':np.__version__},
        'numerical_digest_sha256':digest({'runs':runs,'comparisons':comparisons,'sections':section_controls}),
        'next_iteration':'V11M',
        'next_objective':'Résoudre et sauvegarder finement les premières minutes thermiques, notamment entre 45 et 90 s, pour mesurer la sensibilité du premier garde-fou au pas thermique, au maillage en profondeur et à la reconstruction de surface ; conserver le couplage unidirectionnel élastique et expliciter l’écart de capacité thermique du matériau composite.'}
    write(out/'results_v11l.json',result); write(out/'panel_runs.json',runs)
    write(out/'comparisons.json',comparisons); write(out/'section_controls.json',section_controls)
    write(out/'numerical_audit.json',tests); write(out/'source_manifest.json',{'source_label':cfg['source_label'],'controls':controls,'input_sha256':before})
    # Report values are generated directly from verified records.
    lines=['# V11L — transfert de profils thermiques vers le panneau élastique','',
        f"Résultat : {result['status']}, {result['tests_passed']}/{len(tests)} contrôles.",'',
        '## 1. Faits observés dans les fichiers','',
        'V11K fournit 41 profils espacés de 45 s sur 1800 s. Les contrôles sauvegardés V11F, V11H, V11I et V11K sont vérifiés par empreintes. Le palier est synthétique_non_WTC.','',
        '## 2. Résultats de modèles officiels','',
        'Aucun nouveau résultat officiel importé. Les hypothèses héritées restent celles des configurations V11H/V11I/V11K.','',
        '## 3. Archives locales','',
        'Aucune nouvelle analyse d’archive, de vidéo ou de photographie.','',
        '## 4. Hypothèses et unités','',cfg['mapping'],'',cfg['energy'],'',
        'Le panneau est préchargé à 0,25 gravité. La dalle utilise eps=eps0-y*kappa et eps_th=alpha*DeltaT. E, alpha, rho, cp restent constants : béton alpha=1e-5/K, rho=2400 kg/m³, cp=900 J/kg/K ; armatures alpha=1,2e-5/K, rho=7850 kg/m³, cp=600 J/kg/K. Le treillis et les assemblages restent au contrôle froid.','',
        'Les contraintes sont évaluées dans les fibres, aux nœuds du profil reconstruit, aux extrémités des éléments et aux points de Gauss. Les propriétés E, aires, y, alpha, rho et cp effectivement utilisées sont conservées pour chaque calcul dans panel_runs.json.','',
        '## 5. Résultats dérivés','',
        '| Cas | Coordonnée du profil (s) | DCR | Énergie élastique (J) | Réaction verticale (N) |',
        '|---|---:|---:|---:|---:|']
    for r in runs:
        v=r['terminal']; lines.append(f"| {r['mode']} | {v['profile_time_coordinate_s']:.9f} | {v['max_DCR']:.8f} | {v['stored_J']:.8f} | {v['seat_vertical_reaction_N']:.6f} |")
    v=reference['terminal']
    lines += ['',f"Profil courbe : arrêt au garde-fou à la coordonnée interpolée {v['profile_time_coordinate_s']:.9f} s, dans l’intervalle sauvegardé {v['mapping']['source_interval_s']}. Ce nombre ne constitue pas un temps d’échauffement résolu ni un temps de rupture.",'',
        f"Travail extérieur cumulé {v['external_work_J']:.9f} J ; travail thermoélastique {v['thermal_work_J']:.9f} J ; énergie stockée {v['stored_J']:.9f} J. Résidu maximal relatif {maxima['energy_relative']:.3e}. Retour mécanique : écart de déplacement {reference['cycle_displacement_error']:.3e} m.",'',
        f"Enthalpie brute du coupon étendu au panneau : {v['gross_coupon_sensible_J']:.6f} J ; enthalpie composite : {v['sensible_enthalpy_J']:.6f} J ; écart déclaré : {v['composite_minus_gross_sensible_J']:.6f} J. Cette différence n’est pas corrigée par une énergie fictive.",'',
        '| Comparaison | Coordonnée au garde-fou (s) | Écart relatif |','|---|---:|---:|']
    for c in comparisons: lines.append(f"| {c['kind']} | {c['terminal_time_s']:.9f} | {c['relative_time_change']:.6g} |")
    lines += ['','## 6. Limites et informations manquantes','',cfg['time_caveat'],'',
        'La reconstruction des températures de face utilise les cellules et n’impose pas les températures des surfaces sans masse de V11K. Leur différence est sauvegardée. Le transfert conserve la moyenne et le gradient linéaire équivalent ; le moment absolu conserve l’erreur de quadrature de V11H. La différence d’enthalpie due aux armatures empêche de déclarer un bilan thermodynamique couplé fermé.','',
        f"Correction maximale des fibres : {maxima['fiber_correction_K']:.6g} K. La première tentative utilisait une correction additive créant un sous-dépassement froid de 0,02 K : elle est conservée mais écartée de la publication. La correction multiplicative vérifiée préserve les zones froides. Les numéros de tentatives et les changements d’audit sont consignés dans la passation.",'',
        'Une température imposée n’est pas un incendie calculé. Le garde-fou DCR=0,9 fondé sur des propriétés froides génériques ne constitue pas une température critique réelle. Pas de dégradation, fissuration chaude, dynamique, flambement géométrique, effondrement calculé ni preuve de survie. La localisation en flexion après fracture complète reste non validée. Blender reste une visualisation inchangée. Crédit énergétique global nul.','',
        '## Suite','',result['next_objective'],'',f'Calcul CPU : {seconds:.2f} s. Graine 11012 sans tirage.','']
    (out/'rapport_v11l.md').write_text('\n'.join(lines),encoding='utf-8')
    write(out/'offline_manifest.json',{'iteration':'V11L','implementation_status':result['status'],
         'input_sha256':before,'input_and_protected_unchanged':before==after,
         'output_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    print(json.dumps({'status':result['status'],'tests':len(tests),'seconds':seconds,'maxima':maxima,'failed':[t for t in tests if not t['pass']]}),flush=True)
    if not passed: raise SystemExit(1)

if __name__=='__main__': main()
