"""Integrated panel campaign; no legacy driver or heat solve is re-executed."""
import argparse, copy, csv, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import v11r_integrated_panel as model

ROOT=Path(__file__).resolve().parents[2]; CONFIG='wtc1_simulation_v8/data/v11r_integrated_panel.json'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(v):
    if isinstance(v,np.ndarray): return v.tolist()
    if isinstance(v,np.generic): return v.item()
    raise TypeError(type(v).__name__)
def write(p,v): Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False,default=clean)+'\n',encoding='utf-8')
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False,default=clean).encode()).hexdigest()
def inputs_for(cold):
    d=read(ROOT/cold['panel_configuration']); e=read(ROOT/cold['section_configuration']); c=read(ROOT/d['base_configuration'])
    return {'d':d,'e':e,'c':c,'a':read(ROOT/c['base_configuration']),'transfer':read(ROOT/c['transfer']),'seats':read(ROOT/c['seats'])['floor_truss_seats']}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args(); cfg=read(ROOT/CONFIG)
    out=(ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/cfg['scratch_directory']): raise ValueError('New R scratch attempt required')
    out.mkdir(parents=True,exist_ok=False); start=time.perf_counter(); started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    parent=Path(cfg['protected_manifest']).parent; manifest=read(ROOT/cfg['protected_manifest']); before=dict(manifest['input_sha256'])
    before.update({(parent/p).as_posix():h for p,h in manifest['output_sha256'].items()})
    for p in [CONFIG,cfg['protected_manifest'],(parent/'release_audit.json').as_posix(),'harness/handoffs/WTC1_V11Q_HANDOFF.md',
            *['wtc1_simulation_v8/scripts/'+p for p in ['v11r_integrated_panel.py','run_v11r_integrated_panel.py','audit_v11r_integrated_panel.py','render_v11r_summary.py']]]: before[p]=sha(ROOT/p)
    if any(sha(ROOT/p)!=h for p,h in before.items()): raise ValueError('Protected input mismatch')
    write(out/'source_manifest.json',{'input_sha256':before,'sources':cfg['sources']})
    pc=read(ROOT/cfg['panel_configuration']); cc=read(ROOT/pc['cold_panel_configuration']); tc=read(ROOT/pc['thermomechanical_configuration']); sc=read(ROOT/pc['section_configuration']); baseinputs=inputs_for(cc)
    sources={name:read(ROOT/cfg['thermal_directory']/(name+'.json')) for name in {c['source'] for c in cfg['cases']}}
    tests=[]; runs={}; inventories={}; previews={}; cached_cold=[]
    def check(name,value,limit): tests.append({'name':name,'value':float(value),'limit':float(limit),'pass':bool(np.isfinite(value) and value<=limit)})
    for spec in cfg['cases']:
        clock=time.perf_counter(); inputs=copy.deepcopy(baseinputs)
        if 'vertical_tie_stiffness_per_knuckle_N_m' in spec: inputs['d']['vertical_connection']['tension_stiffness_per_equivalent_knuckle_N_m']=spec['vertical_tie_stiffness_per_knuckle_N_m']
        panel=model.NodalPanel(pc,cc,tc,sc,inputs,spec,sources[spec['source']]); inventory=panel.export_inventory(); inventories[spec['id']]=inventory
        write(out/(spec['id']+'_inventory.json'),inventory)
        state=panel.solve(0.,0); work=thermal=0.; max_increment=0.; defects=0.; active_switches=0; history=[model.snapshot(panel,state,0.,0,'ZERO',True)]
        rejection=None; status='REACHED_SOURCE_END'; preload=None; unresolved=None
        planned=[(float(g),0,'PRELOAD') for g in np.linspace(0,spec['gravity'],max(1,int(round(spec['gravity']/cfg['gravity_increment'])))+1)[1:]] if spec['gravity']>0 else []
        planned += [(spec['gravity'],i,'HEATING') for i,h in enumerate(sources[spec['source']]['history']) if i>0 and h['time_s']<=cfg['maximum_source_time_s']]
        for gravity,index,phase in planned:
            try: trial=panel.solve(gravity,index,state['u'])
            except model.inherited.Unresolved as err:
                status='UNRESOLVED_SOLVER_NOT_COLLAPSE'; unresolved={'gravity':gravity,'thermal_step':index,'phase':phase,'message':str(err)}; break
            reason='ELASTIC_GUARD' if trial['max_DCR']>cfg['guard_DCR'] else 'UNQUALIFIED_SUPPORT_DIRECTION' if trial['support_uplift_unchecked'] or trial['support_horizontal_compression_unchecked'] else None
            if reason:
                rejection={**model.snapshot(panel,trial,gravity,index,phase,False),'reason':reason}; status='STOP_'+phase+'_'+reason; break
            dw=float(.5*(state['force']+trial['force'])@(trial['u']-state['u'])); dth=panel.thermal_work_increment(state,trial)
            delta=trial['stored_J']-state['stored_J']; defect=delta-dw-dth
            residual=abs(defect)/max(1,abs(delta),abs(dw),abs(dth)); max_increment=max(max_increment,residual); defects+=defect
            active_switches+=int(state['active_signature']!=trial['active_signature'])
            work+=dw; thermal+=dth; state=trial
            row=model.snapshot(panel,state,gravity,index,phase,True,work,thermal,residual); history.append(row)
            if phase=='PRELOAD' and gravity==spec['gravity']: preload=row
        if spec['gravity']==0: preload=history[0]
        summary={'id':spec['id'],'spec':spec,'status':status,'accepted_count':len(history),'last':{k:v for k,v in history[-1].items() if k not in ['u','term_force_N','term_gap','term_DCR']},
            'preload_reached':preload is not None,'preload':None if preload is None else {k:preload[k] for k in ['stored_J','max_slab_down_m','max_DCR','gravity_load_N','seat_vertical_reaction_N']},
            'rejected':None if rejection is None else {k:v for k,v in rejection.items() if k not in ['u','term_force_N','term_gap','term_DCR']},
            'unresolved':unresolved,'maximum_equilibrium_relative':max(r['equilibrium_residual'] for r in history),
            'maximum_increment_energy_relative':max_increment,'maximum_total_energy_relative':max(r['total_energy_residual_relative'] for r in history),
            'active_set_switch_increments':active_switches,'accumulated_work_quadrature_defect_J':defects,'runtime_seconds':time.perf_counter()-clock,
            'heating_accepted':sum(r['phase']=='HEATING' for r in history),'energy_qualified':max_increment<=cfg['acceptance']['increment_energy_relative'] and max(r['total_energy_residual_relative'] for r in history)<=cfg['acceptance']['total_energy_relative']}
        run={'summary':summary,'history':history,'rejected_trial':rejection}; runs[spec['id']]=run; write(out/(spec['id']+'.json'),run)
        check(spec['id']+':equilibrium',summary['maximum_equilibrium_relative'],cfg['acceptance']['equilibrium_relative'])
        check(spec['id']+':committed_guard',max(r['max_DCR'] for r in history)-cfg['guard_DCR'],cfg['acceptance']['guard_absolute'])
        check(spec['id']+':vertical_balance',max(r['vertical_balance_relative'] for r in history),1e-7)
        check(spec['id']+':horizontal_balance',max(r['horizontal_balance_absolute_N'] for r in history),1e-4)
        check(spec['id']+':nonnegative_energy',-min(r['stored_J'] for r in history),1e-8)
        if spec['id']==cfg['reference_case'] and preload is not None:
            with (ROOT/'wtc1_simulation_v8/output/v11f_panel_coupling/path_history.csv').open(encoding='utf-8-sig',newline='') as stream:
                cached=next(r for r in csv.DictReader(stream) if r['case_id']=='COLD_R02' and abs(float(r['gravity_factor'])-.25)<1e-12)
            for newkey,oldkey,floor in [('stored_J','stored_J',1.),('max_slab_down_m','max_slab_down_m',1e-6),('seat_vertical_reaction_N','seat_reaction_N',1.)]:
                old=float(cached[oldkey]); error=abs(preload[newkey]-old)/max(floor,abs(old)); check('cached_V11F:'+newkey,error,cfg['acceptance']['cold_response_relative'])
                cached_cold.append({'quantity':newkey,'old':old,'new':preload[newkey],'relative_difference':error})
        print(json.dumps({'case':spec['id'],'status':status,'heating_states':summary['heating_accepted'],'time':summary['last']['time_s'],'g':summary['last']['gravity'],'DCR':summary['last']['max_DCR'],'energy_qualified':summary['energy_qualified'],'seconds':summary['runtime_seconds']}),flush=True)
    # Common saved-time sensitivities: never compare differing end times as if equal.
    comparisons=[]; ref=runs[cfg['reference_case']]
    for name,run in runs.items():
        if name==cfg['reference_case']: continue
        for t in cfg['comparison_times_s']:
            a=next((r for r in ref['history'] if r['phase']=='HEATING' and r['time_s']==t),None)
            b=next((r for r in run['history'] if r['phase']=='HEATING' and r['time_s']==t),None)
            row={'case':name,'time_s':t,'status':'COMMON_ACCEPTED' if a is not None and b is not None else 'UNAVAILABLE_NO_INTERPOLATION'}
            if row['status']=='COMMON_ACCEPTED': row.update({k:b[k]-a[k] for k in ['max_slab_down_m','stored_J','seat_vertical_reaction_N','max_DCR','max_opening_m']})
            comparisons.append(row)
    check('protected_sources_unchanged',sum(sha(ROOT/p)!=h for p,h in before.items()),0)
    result={'iteration':'V11R','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL','test_count':len(tests),'tests_passed':sum(t['pass'] for t in tests),
        'case_count':len(runs),'accepted_states':sum(len(r['history']) for r in runs.values()),'cases_with_heating':sum(r['summary']['heating_accepted']>0 for r in runs.values()),
        'energy_qualified_cases':sum(r['summary']['energy_qualified'] for r in runs.values()),'summaries':{n:r['summary'] for n,r in runs.items()},
        'numerical_digest_sha256':digest({'runs':runs,'inventories':inventories,'comparisons':comparisons,'cold':cached_cold}),
        'runtime':{'seconds':time.perf_counter()-start,'started_utc':started,'python':platform.python_version(),'numpy':np.__version__},
        'panel_assembled':True,'historical_event_validated':False,'fire_solved':False,'heated_fracture_solved':False,'coupled_first_law_closed':False,
        'old_drivers_rerun':False,'cold_V11F_preserved':True,'blender_changed':False,'global_energy_credit_J':0.,
        'next_iteration':'V11S','next_objective':'Traiter en priorité le premier blocage du panneau intégré identifié dans la synthèse V11R. Ne pas repartir des coupons ni refaire les calculs qualifiés. Compléter seulement la loi ou le contrôle manquant (direction d’appui, domaine fissuré ou bilan de changement de contact selon résultats) avec hypothèses explicites ; préserver la charge nominale comme témoin et la séparation des bilans. Transfert visuel limité aux états mécaniques effectivement qualifiés.'}
    for name,v in [('results_v11r.json',result),('comparisons.json',comparisons),('cold_comparison.json',cached_cold),('numerical_audit.json',tests)]: write(out/name,v)
    lines=['# V11R — panneau intégré : thermique, gravité, ferme, dalle et liaisons','',
        '## Résultat du jalon','',f"{len(runs)} configurations, {result['accepted_states']} états engagés ; {result['cases_with_heating']} chemins avec chauffage engagé. {result['energy_qualified_cases']} configurations satisfont les tolérances de travail/énergie sur leur domaine engagé. PASS des contrôles ne signifie pas que tous les objectifs physiques sont atteints.",'',
        '| Cas | Charge relative | Dernier temps (s) | États chauffés | Arrêt | Bilan énergie |','|---|---:|---:|---:|---|---|']
    for name,r in runs.items():
        s=r['summary']; lines.append(f"| {name} | {s['spec']['gravity']} | {s['last']['time_s']} | {s['heating_accepted']} | {s['status']} | {'PASS' if s['energy_qualified'] else 'NON QUALIFIÉ'} |")
    lines += ['', '## 1. Faits observés dans les fichiers','', 'V11P fournit les profils résolus ; V11Q a qualifié le transfert de section. V11R assemble ces intégrales dans le panneau V11F/I : dalle-poutre, ferme, sièges, contact compressif, attaches verticales en traction et attaches horizontales. Les sources sauvegardées ne sont pas recalculées.','',
        '## 2. Modèles officiels','', 'Les capacités et dimensions documentées héritées restent référencées par les configurations V11A/C/D. Aucun nouveau résultat officiel, incendie ni champ de dommages importé. Le panneau équivalent n’est pas un étage as-built complet.','',
        '## 3. Archives locales','', 'Aucune archive rescannée, vidéo analysée ou source modifiée.','',
        '## 4. Hypothèses et unités','',cfg['method'],'',cfg['local_heating'],'',
        'Gravité : charge de référence 80 psf, appliquée une seule fois à la dalle ; facteurs 0, 0,25, 0,5 et 1 pré-déclarés. Maillage de dalle : 2/4/8 éléments par travée de ferme, topologie métallique et stations de connexion fixes. Sensibilité de raideur des attaches verticales : 1e7/1e8/1e9 N/m par connecteur équivalent, hypothèses non mesurées.','',
        'Dalle : largeur 2,032 m, épaisseur 0,11049 m, béton E=2500 ksi, alpha=1e-5/K ; armatures E=200 GPa, alpha=1,2e-5/K, fraction0,002. Sections planes et petits déplacements, propriétés constantes, forces N, moments N·m, déplacement m, rotation rad, énergie de panneau J. Les profils nodaux et le carré de température sont intégrés exactement dans l’épaisseur ; deux points de Gauss par élément dans la longueur.','',
        'Kq−f fournit les résultants N/M de section. L’assemblage Bᵀ(Kq−f), les forces de ferme/contact/attaches et le vecteur de gravité sont équilibrés sur tous les degrés de liberté. Les réactions de sol proviennent des ressorts d’appui ; leur déplacement côté sol est nul. Le travail de gravité et le travail thermique sont calculés séparément de la chaleur sensible.','',cfg['energy_policy'],'',cfg['guard_policy'],'',
        '## 5. Résultats dérivés et contrôles','',
        'Le contrôle froid compare le nouveau panneau à la ligne V11F COLD_R02 déjà sauvegardée à g=0,25. L’inertie continue modifie légèrement la raideur par rapport aux fibres au milieu des bandes ; cold_comparison.json conserve les écarts. Aucun historique froid endommagé ni ancienne matrice n’est réécrit.','',
        'Chaque premier essai refusé est conservé avec son déplacement, ses forces et sa raison, sans engagement. Une direction d’appui sans capacité déclarée constitue un arrêt de qualification, pas une rupture démontrée. Les comparaisons emploient uniquement les temps effectivement sauvegardés et engagés des deux cas ; aucun instant inventé.','',
        '## 6. Limites et décisions','',
        'Chauffage de la dalle seulement ; ferme et connexions froides, pas d’isolant, humidité, feu de compartiment, géométrie non linéaire, fissuration chaude ou dynamique globale. Les gradients localisés sont une sensibilité sans conduction longitudinale. Une absence de rupture avant l’arrêt ne prouve pas la stabilité du WTC. Localisation en flexion après fracture complète non validée. Blender et ses anciennes animations inchangés.','',
        'La priorité suivante est déterminée par les motifs d’arrêt de ce panneau intégré, pas par une nouvelle série de coupons. Les limites refusées restent visibles ; aucun réglage postérieur de charge ou de capacité ne sert à forcer un résultat.','',
        '## Suite','',result['next_objective'],'',f"Calcul CPU : {result['runtime']['seconds']:.2f} s ; graine11018 sans tirage. {result['tests_passed']}/{result['test_count']} contrôles de campagne.",'']
    (out/'rapport_v11r.md').write_text('\n'.join(lines),encoding='utf-8')
    write(out/'offline_manifest.json',{'iteration':'V11R','implementation_status':result['status'],'input_sha256':before,'output_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    print(json.dumps({'status':result['status'],'seconds':result['runtime']['seconds'],'failed':[t for t in tests if not t['pass']]}),flush=True)
    if result['status']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()
