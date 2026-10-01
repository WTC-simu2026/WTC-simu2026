"""V11Q: saved nodal conduction -> guarded pristine elastic sections only."""
import argparse, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import v11h_thermomechanical_model as fiber
import v11o_startup_bridge as section

ROOT=Path(__file__).resolve().parents[2]
CONFIG='wtc1_simulation_v8/data/v11q_nodal_section.json'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj): Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args()
    cfg=read(ROOT/CONFIG); out=(ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/cfg['scratch_directory']): raise ValueError('Use new Q scratch attempt')
    out.mkdir(parents=True,exist_ok=False); clock=time.perf_counter(); started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    manifest=read(ROOT/cfg['protected_manifest']); parent=Path(cfg['protected_manifest']).parent
    before=dict(manifest['input_sha256']); before.update({(parent/p).as_posix():h for p,h in manifest['output_sha256'].items()})
    for p in [CONFIG,cfg['protected_manifest'],(parent/'release_audit.json').as_posix(),'harness/handoffs/WTC1_V11P_HANDOFF.md',
              'wtc1_simulation_v8/scripts/run_v11q_nodal_section.py','wtc1_simulation_v8/scripts/audit_v11q_nodal_section.py']:
        before[p]=sha(ROOT/p)
    if any(sha(ROOT/p)!=h for p,h in before.items()): raise ValueError('Protected source changed')
    if read(ROOT/parent/'release_audit.json')['status']!='PASS': raise ValueError('Unqualified P source')
    write(out/'source_manifest.json',{'input_sha256':before,'sources':cfg['sources']})
    hc=read(ROOT/cfg['thermo_configuration']); ec=read(ROOT/hc['section_configuration'])
    base={'id':'V11Q_SECTION','rho_total':cfg['reinforcement_ratio'],'layout':'symmetric','mode':'FREE','alpha_mode':'differential','delta_t_bottom_c':0.,'delta_t_top_c':0.}
    sec=section.ContinuousSection(fiber.ElasticThermoSection(ec,hc,base,640)); inv=sec.inventory()
    tests=[]
    def check(name,value,limit): tests.append({'name':name,'value':float(value),'limit':float(limit),'pass':bool(np.isfinite(value) and value<=limit)})
    check('same_V11O_section_inventory',int(digest(inv)!=digest(read(ROOT/'wtc1_simulation_v8/output/v11o_startup_bridge/section_inventory.json'))),0)
    midpoint=fiber.ElasticThermoSection(ec,hc,base,cfg['cold_midpoint_fibers']); difference=sec.K-midpoint.K
    expected=sec.Ec*sec.Ac*sec.h**2/(12*cfg['cold_midpoint_fibers']**2)
    check('cold_inertia_correction',abs(difference[1,1]-expected)/sec.K[1,1],1e-10)
    cold={'midpoint_fibers':cfg['cold_midpoint_fibers'],'midpoint_K':midpoint.K.tolist(),'continuous_K':sec.K.tolist(),
          'expected_bending_correction_Nm2':expected,'relative_bending_change':float(difference[1,1]/sec.K[1,1]),
          'V11F_rerun':False,'old_K_replaced':False}
    controls=[]
    # Plain concrete analytical references, both free and restrained; no old driver rerun.
    plain=section.ContinuousSection(fiber.ElasticThermoSection(ec,hc,{**base,'rho_total':0.},640))
    for c in cfg['controls']:
        a,b=c['bottom_delta_k'],c['top_delta_k']; x=np.array([0.,plain.h]); t=np.array([a,b])
        for mode in cfg['restraints']:
            state=plain.solve(x,t,t,mode); mean=(a+b)/2; square=(a*a+a*b+b*b)/3
            f=plain.Ec*plain.Ac*plain.alphac*np.array([mean,-plain.h*(b-a)/12])
            q=plain.alphac*np.array([mean,-(b-a)/plain.h]) if mode=='FREE' else np.zeros(2)
            U=0. if mode=='FREE' else .5*plain.Ec*plain.Ac*plain.alphac**2*square
            check(c['id']+mode+':q',np.max(np.abs(np.array(state['q'])-q)),1e-12)
            check(c['id']+mode+':U',abs(state['stored_J_per_m']-U),1e-9)
            check(c['id']+mode+':force',np.max(np.abs(np.array(state['thermal_force_N_Nm'])-f))/max(1,np.max(np.abs(f))),1e-10)
            controls.append({'id':c['id'],'mode':mode,'bottom_delta_k':a,'top_delta_k':b,'state':state,'inventory':plain.inventory()})
    paths=[]; maxima={'mean_error_k':0.,'square_error_k2':0.,'heat_error_j_m2':0.,'energy_relative':0.,'free_resultant_relative':0.,'maximum_committed_strength_ratio':0.}
    for job in cfg['source_jobs']:
        saved=read(ROOT/cfg['source_directory']/(job+'.json')); x=np.array(saved['x_m'])
        check(job+':thickness',abs(x[-1]-sec.h),1e-14)
        for mode in cfg['restraints']:
            history=[]; rejected=None; previous=None; Wth=Wext=0.
            for p,h in zip(saved['profiles'],saved['history']):
                t=np.array(p['temperature_c'])-cfg['reference_temperature_c']; state=sec.solve(x,t,t[[0,-1]],mode)
                row={'step':p['step'],'time_s':p['time_s'],**state,
                     'source_enthalpy_j_m2':h['enthalpy_j_m2'],'gross_coupon_heat_J_per_m':sec.width*h['enthalpy_j_m2'],
                     'concrete_thermal_strain_at_knots':(sec.alphac*t).tolist(),
                     'steel_thermal_strain':(sec.alphas*np.array(state['steel_delta_k'])).tolist(),
                     'top_temperature_c':p['temperature_c'][-1]}
                if state['maximum_cold_strength_ratio']>cfg['cold_strength_guard']:
                    rejected={**row,'status':'REJECTED_ELASTIC_GUARD','committed':False}; break
                q=np.array(state['q']); f=np.array(state['thermal_force_N_Nm']); R=np.array(state['resultant_N_Nm']); S=state['thermal_square_energy_S_J_per_m']
                if previous is not None:
                    oq,of,oR,oS=previous; Wth+=float(-.5*(oq+q)@(f-of)+.5*(S-oS)); Wext+=float(.5*(oR+R)@(q-oq))
                residual=abs(state['stored_J_per_m']-Wth-Wext)/max(1,abs(state['stored_J_per_m']),abs(Wth),abs(Wext))
                row.update({'committed':True,'thermal_work_J_per_m':Wth,'external_work_J_per_m':Wext,'energy_residual_relative':residual})
                history.append(row); previous=q,f,R,S
                maxima['mean_error_k']=max(maxima['mean_error_k'],abs(state['mean_delta_k']-h['mean_delta_k']))
                maxima['square_error_k2']=max(maxima['square_error_k2'],abs(state['mean_square_delta_k2']-h['mean_square_delta_k2']))
                maxima['heat_error_j_m2']=max(maxima['heat_error_j_m2'],abs(sec.h*2160000*state['mean_delta_k']-h['enthalpy_j_m2']))
                maxima['energy_relative']=max(maxima['energy_relative'],residual)
                maxima['maximum_committed_strength_ratio']=max(maxima['maximum_committed_strength_ratio'],state['maximum_cold_strength_ratio'])
                if mode=='FREE': maxima['free_resultant_relative']=max(maxima['free_resultant_relative'],float(np.max(np.abs(R)))/max(1,float(np.max(np.abs(f)))))
                check(job+mode+':nonnegative_U_step'+str(p['step']),-state['stored_J_per_m'],1e-9)
            check(job+mode+':cold',max(abs(history[0]['stored_J_per_m']),float(np.max(np.abs(history[0]['q']))),float(np.max(np.abs(history[0]['support_reaction_N_Nm'])))),1e-12)
            paths.append({'job':job,'mode':mode,'history':history,'rejected_trial':rejected,
                          'source_states_available':len(saved['profiles']),'completed_to_source_end':rejected is None,
                          'last_committed_time_s':history[-1]['time_s'],
                          'first_rejected_time_s':None if rejected is None else rejected['time_s']})
        print(job+' direct section transfer complete',flush=True)
    for key,tol in [('mean_error_k',1e-10),('square_error_k2',1e-8),('heat_error_j_m2',1e-4),('energy_relative',1e-10),('free_resultant_relative',1e-10),('maximum_committed_strength_ratio',cfg['cold_strength_guard'])]: check(key,maxima[key],tol)
    # Common saved times only; no interpolation or mechanical crossing-time fit.
    comparisons=[]
    for mode in cfg['restraints']:
        group=[p for p in paths if p['mode']==mode]; common=set(r['time_s'] for r in group[0]['history'])
        for p in group[1:]: common &= set(r['time_s'] for r in p['history'])
        time_common=max(common); states={p['job']:next(r for r in p['history'] if r['time_s']==time_common) for p in group}
        for axis,names in [('space',['N64_S640','N128_S640','N256_S640','N512_S640']),('time',['N256_S160','N256_S320','N256_S640','N256_S1280'])]:
            for old,new in zip(names,names[1:]):
                a,b=states[old],states[new]
                comparisons.append({'mode':mode,'axis':axis,'time_s':time_common,'coarse':old,'fine':new,
                    'q_difference':(np.array(b['q'])-a['q']).tolist(),
                    'reaction_difference_N_Nm':(np.array(b['support_reaction_N_Nm'])-a['support_reaction_N_Nm']).tolist(),
                    'stored_relative_difference':(b['stored_J_per_m']-a['stored_J_per_m'])/max(1e-30,abs(b['stored_J_per_m'])),
                    'square_relative_difference':(b['mean_square_delta_k2']-a['mean_square_delta_k2'])/max(1e-30,b['mean_square_delta_k2']),
                    'cold_ratio_difference':b['maximum_cold_strength_ratio']-a['maximum_cold_strength_ratio']})
    replay_x=np.array(read(ROOT/cfg['source_directory']/(cfg['source_jobs'][0]+'.json'))['x_m'])
    replay=sec.solve(replay_x,np.zeros(len(replay_x)),np.zeros(2),'FREE')
    check('cold_replay_exact',int(digest(replay)!=digest({k:paths[0]['history'][0][k] for k in replay})),0)
    check('sources_unchanged',sum(sha(ROOT/p)!=h for p,h in before.items()),0)
    payload={'paths':paths,'controls':controls,'cold':cold,'comparisons':comparisons,'inventory':inv}
    result={'iteration':'V11Q','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL','test_count':len(tests),'tests_passed':sum(t['pass'] for t in tests),
        'path_count':len(paths),'committed_states':sum(len(p['history']) for p in paths),'rejected_trials':sum(p['rejected_trial'] is not None for p in paths),
        'path_summary':[{k:p[k] for k in ['job','mode','last_committed_time_s','first_rejected_time_s','completed_to_source_end']} for p in paths],
        'maxima':maxima,'numerical_digest_sha256':digest(payload),'runtime':{'seconds':time.perf_counter()-clock,'started_utc':started,'python':platform.python_version(),'numpy':np.__version__},
        'direct_nodal_section_transfer_qualified':True,'temporal_interpolation_qualified':False,'cold_V11F_preserved':True,
        'conduction_rerun':False,'panel_history_solved':False,'heated_fracture_solved':False,'coupled_first_law_closed':False,'fire_solved':False,'blender_changed':False,'global_energy_credit_j':0.,
        'next_iteration':'V11R','next_objective':'Préparer une intégration bornée des profils nodaux V11P dans le panneau élastique, avec intégrales exactes de section, contrôle froid comparé et garde-fou local avant engagement. Pré-déclarer une fenêtre thermique commune sous le garde-fou, vérifier charges mécaniques et conventions de travail/réactions, conserver séparément chaleur sensible et travail thermoélastique. Aucun prolongement au-delà du garde-fou ni dommage chaud sans formulation et validation nouvelles.'}
    for name,obj in [('results_v11q.json',result),('section_paths.json',paths),('section_inventory.json',inv),('closed_form_controls.json',controls),('cold_comparison.json',cold),('comparisons.json',comparisons),('numerical_audit.json',tests)]: write(out/name,obj)
    lines=['# V11Q — transfert nodal direct vers une section élastique','',f"{result['tests_passed']}/{result['test_count']} contrôles ; {len(paths)} chemins ; {result['committed_states']} états engagés ; {result['rejected_trials']} premiers essais refusés.",'',
       '## 1. Faits observés dans les fichiers','', 'V11P fournit les profils nodaux et la chaleur sensible sauvegardés. V11Q les lit sans relancer la conduction. Les anciens résultats, le contrôle froid V11F et le master Blender sont protégés par empreintes.','',
       '## 2. Modèles officiels','', 'Aucun nouveau résultat officiel importé.','',
       '## 3. Archives locales','', 'Aucune nouvelle analyse d’archive.','',
       '## 4. Hypothèses et équations','',
       'Section de largeur 80 in × 0,0254=2,032 m, épaisseur 4,35 in × 0,0254=0,11049 m ; béton E=2500 ksi × 6,894757293168361e6 Pa/ksi, alpha=1e-5/K, ft20=1 MPa, fc20=3 ksi ; armatures E=200 GPa, alpha=1,2e-5/K, fy=400 MPa, fraction totale 0,002, deux couches symétriques à 25 mm des faces. Propriétés constantes héritées, pas une loi validée à chaud.','',
       'Sections planes : eps(y)=eps0−y*kappa, déformation thermique alpha*DeltaT, contrainte E*(eps−alpha*DeltaT). q=(eps0 sans unité,kappa en 1/m), R=Kq−f en N et N·m ; réaction conventionnelle aux blocages −R. Libre : q=K^-1*f ; entièrement empêchée : q=0. Les signes des réactions suivent cette convention de section et ne sont pas encore des forces nodales de panneau.','',
       'Le béton est intégré exactement sur chaque segment linéaire du profil : m0=mean(DeltaT), m1=mean((y/h)*DeltaT), m2=mean(DeltaT²). Les armatures reçoivent une interpolation spatiale aux couches physiques du sous-modèle. K reste celle de la section continue V11O ; aucun raccord initial V11O n’est utilisé.','',
       cfg['energy_policy'],'',
       'Chaleur sensible du béton : Ac*rho_c*cp_c*m0 ; armatures : sum(As*rho_s*cp_s*Ts), en J/m. rho_c=2400, cp_c=900 ; rho_s=7850, cp_s=600, en unités SI. Le coupon thermique homogène vaut largeur*H_V11P ; la différence composite−coupon est enregistrée, sans être absorbée dans un bilan fictif.','',
       'Garde-fou : maximum des ratios traction béton/ft20, compression béton/fc20 et acier/fy20 ≤0,9. Les contraintes du béton sont contrôlées à tous les nœuds et aux faces, ce qui couvre les extrema de chaque segment linéaire. Le premier essai dépassant 0,9 est isolé, non engagé ; le chemin s’arrête. Cet arrêt n’est ni une rupture calculée, ni une chronologie du WTC.','',
       '## 5. Résultats dérivés','', '| Source | Liaison | Dernier temps engagé (s) | Premier essai refusé (s) |','|---|---|---:|---:|']
    for p in paths: lines.append(f"| {p['job']} | {p['mode']} | {p['last_committed_time_s']} | {p['first_rejected_time_s'] if p['first_rejected_time_s'] is not None else 'aucun à 90 s'} |")
    lines += ['',f"Résidu énergétique relatif maximal {maxima['energy_relative']:.3e} ; écart chaleur du transfert {maxima['heat_error_j_m2']:.3e} J/m² ; ratio engagé maximal {maxima['maximum_committed_strength_ratio']:.9f}.",'',
       f"Correction relative de raideur de flexion par rapport à 160 fibres au milieu des bandes : {cold['relative_bending_change']:.9g}. Le contrôle froid exact est nul ; l’ancienne raideur n’est pas remplacée et l’ancien panneau V11F n’est pas relancé.",'',
       'Les comparaisons spatiales et temporelles utilisent le dernier temps sauvegardé commun à tous les chemins de même liaison. Aucun temps de franchissement n’est ajusté ou interpolé. Voir comparisons.json pour q, réactions, énergie, carré de température et garde-fou.','',
       '## 6. Limites et informations manquantes','',
       'Sections isolées sans charge de gravité ni contraintes de compatibilité du panneau. Une section libre peut développer des contraintes autoéquilibrées sous un gradient non linéaire ; libre ne signifie pas partout sans contrainte. Les seuils restent froids et ne constituent pas une validation thermomécanique à chaud. Pas de plasticité, fissuration, fluage, endommagement, fermeture du premier principe couplé ou effondrement validés. Localisation après fracture complète toujours non validée. Exposition synthétique, pas incendie calculé ; Blender inchangé, visualisation seulement.','',
       '## Suite','',result['next_objective'],'',f"Durée {result['runtime']['seconds']:.3f} s ; graine 11017 sans tirage.",'']
    (out/'rapport_v11q.md').write_text('\n'.join(lines),encoding='utf-8')
    write(out/'offline_manifest.json',{'iteration':'V11Q','implementation_status':result['status'],'input_sha256':before,'output_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    print(json.dumps({'status':result['status'],'tests':len(tests),'states':result['committed_states'],'rejected':result['rejected_trials'],'maxima':maxima,'seconds':result['runtime']['seconds'],'failed':[t for t in tests if not t['pass']]}))
    if result['status']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()
