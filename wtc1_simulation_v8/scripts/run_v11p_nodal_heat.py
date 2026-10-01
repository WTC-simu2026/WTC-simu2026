"""Versioned V11P experiment; preserves all previous results."""
import argparse, copy, hashlib, json, platform, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import v11p_nodal_heat as model

ROOT=Path(__file__).resolve().parents[2]
CONFIG='wtc1_simulation_v8/data/v11p_nodal_heat.json'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj): Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args()
    out=(ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/'tmp/v11p_nodal_heat'): raise ValueError('Use versioned P scratch directory')
    out.mkdir(parents=True,exist_ok=False)
    clock=time.perf_counter(); started=datetime.now(timezone.utc).isoformat()
    cfg=read(ROOT/CONFIG); thermal=read(ROOT/cfg['thermal_configuration'])
    inherited=read(ROOT/cfg['protected_manifest']); before=dict(inherited['input_sha256'])
    parent=Path(cfg['protected_manifest']).parent
    before.update({(parent/p).as_posix():h for p,h in inherited['output_sha256'].items()})
    additions=[cfg['protected_manifest'],(parent/'release_audit.json').as_posix(),CONFIG,
               'wtc1_simulation_v8/scripts/v11p_nodal_heat.py',
               'wtc1_simulation_v8/scripts/run_v11p_nodal_heat.py',
               'wtc1_simulation_v8/scripts/audit_v11p_nodal_heat.py']
    before.update({p:sha(ROOT/p) for p in additions})
    for p,h in before.items():
        if sha(ROOT/p)!=h: raise ValueError('Protected input changed: '+p)
    write(out/'source_manifest.json',{'input_sha256':before,'policy':cfg['source_policy']})
    tests=[]
    def check(name,value,limit): tests.append({'name':name,'value':float(value),'limit':float(limit),'pass':bool(value<=limit)})
    a=cfg['acceptance']; cases={c['id']:c for c in thermal['cases']}; runs={}
    maincase=copy.deepcopy(cases[cfg['main_case']]); maincase['duration_s']=cfg['duration_s']
    jobs=[(j['id'],maincase,j['intervals'],j['steps']) for j in cfg['jobs']]
    jobs += [(c,cases[c],cfg['control_intervals'],cfg['control_steps']) for c in cfg['controls']]
    eigen=cases['CONVECTION_EIGENMODE_TRANSIENT']
    jobs += [('EIGEN_S'+str(s),eigen,cfg['time_reference_intervals'],s) for s in cfg['time_reference_steps']]
    for name,case,n,s in jobs:
        run=model.run(thermal,case,n,s); runs[name]=run; write(out/(name+'.json'),run)
        r=run['summary']; check(name+'_width',abs(r['total_width_m']-thermal['geometry']['thickness_m']),a['total_width_absolute_m'])
        for metric,tol in [('maximum_local_balance_w_m2','local_balance_absolute_w_m2'),
                           ('maximum_increment_heat_error_j_m2','increment_heat_absolute_j_m2'),
                           ('maximum_total_heat_error_j_m2','total_heat_absolute_j_m2')]: check(name+'_'+metric,r[metric],a[tol])
        if name in cfg['controls']:
            exact=model.reference.analytical_temperature_c(thermal,case,np.array(run['x_m']),case['duration_s'])
            check(name+'_steady',np.max(np.abs(np.array(run['profiles'][-1]['temperature_c'])-exact)),a['steady_temperature_absolute_k'])
        if name.startswith('N'):
            check(name+'_initial',np.max(np.abs(np.array(run['profiles'][0]['temperature_c'])-20)),a['initial_temperature_absolute_k'])
            check(name+'_initial_heat',abs(r['initial']['enthalpy_j_m2']),1e-12)
            lo=min(h['minimum_temperature_c'] for h in run['history']); hi=max(h['maximum_temperature_c'] for h in run['history'])
            check(name+'_maximum_principle',max(20-lo,hi-250,0),a['maximum_principle_k'])
        print(name+' solved',flush=True)
    space=[model.exact_linear_semidiscrete(thermal,eigen,n) for n in cfg['space_reference_intervals']]
    exact_time=model.exact_linear_semidiscrete(thermal,eigen,cfg['time_reference_intervals'])
    time_errors=[{'steps':s,'linf_temporal_error_k':float(np.max(np.abs(np.array(runs['EIGEN_S'+str(s)]['profiles'][-1]['temperature_c'])-exact_time['semidiscrete_terminal_c'])))} for s in cfg['time_reference_steps']]
    for rows,key,prefix,limits in [(space,'linf_spatial_error_k','space',a['space_order_range']),
                                   (time_errors,'linf_temporal_error_k','time',a['time_order_range'])]:
        for old,new in zip(rows,rows[1:]):
            order=float(np.log2(old[key]/new[key])); new['observed_order']=order
            check(prefix+'_order_'+str(len(tests)),max(limits[0]-order,order-limits[1],0),0)
        check(prefix+'_finest_error',rows[-1][key],a['finest_eigenmode_error_k'])
    convergence={'space':space,'time':time_errors,'time_reference':exact_time}
    replay=model.run(thermal,cases[cfg['controls'][0]],cfg['control_intervals'],cfg['control_steps'])
    check('deterministic_control_replay',int(digest(replay)!=digest(runs[cfg['controls'][0]])),0)
    comparisons=[]
    for n in [64,128,256]:
        cached=read(ROOT/cfg['cached_directory']/('C'+str(n)+'_S640.json')); new=runs['N'+str(n)+'_S640']
        for i in [0,1,320,640]:
            old=cached['history'][i]; row=new['history'][i]
            comparisons.append({'intervals':n,'time_s':row['time_s'],'old_time_s':old['time_s'],
                'nodal_surface_c':row['top_surface_temperature_c'],'cached_surface_c':old['top_surface_temperature_c'],
                'surface_difference_k':row['top_surface_temperature_c']-old['top_surface_temperature_c'],
                'nodal_enthalpy_j_m2':row['enthalpy_j_m2'],'cached_enthalpy_j_m2':old['enthalpy_j_m2'],
                'enthalpy_difference_j_m2':row['enthalpy_j_m2']-old['enthalpy_j_m2']})
            check('cached_time_N'+str(n)+'_'+str(i),abs(row['time_s']-old['time_s']),1e-12)
    sensitivities=[]
    for kind,names in [('space',['N64_S640','N128_S640','N256_S640','N512_S640']),
                       ('time',['N256_S160','N256_S320','N256_S640','N256_S1280'])]:
        for old,new in zip(names,names[1:]):
            left=runs[old]['summary']['final']; right=runs[new]['summary']['final']
            sensitivities.append({'kind':kind,'coarse':old,'fine':new,
                'surface_difference_k':right['top_surface_temperature_c']-left['top_surface_temperature_c'],
                'enthalpy_relative_difference':(right['enthalpy_j_m2']-left['enthalpy_j_m2'])/right['enthalpy_j_m2'],
                'mean_square_relative_difference':(right['mean_square_delta_k2']-left['mean_square_delta_k2'])/right['mean_square_delta_k2']})
    check('protected_inputs_unchanged',sum(sha(ROOT/p)!=h for p,h in before.items()),0)
    payload={'runs':runs,'convergence':convergence,'cached_comparisons':comparisons,'sensitivities':sensitivities}
    result={'iteration':'V11P','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL',
        'test_count':len(tests),'tests_passed':sum(t['pass'] for t in tests),'run_count':len(runs),
        'saved_state_count':sum(len(r['history']) for r in runs.values()),'numerical_digest_sha256':digest(payload),
        'run_summaries':{n:r['summary'] for n,r in runs.items()},
        'space_orders':[r['observed_order'] for r in space[1:]],'time_orders':[r['observed_order'] for r in time_errors[1:]],
        'maximum_local_balance_w_m2':max(r['summary']['maximum_local_balance_w_m2'] for r in runs.values()),
        'maximum_total_heat_error_j_m2':max(r['summary']['maximum_total_heat_error_j_m2'] for r in runs.values()),
        'startup_temperature_continuous_at_fixed_mesh':True,'time_interpolation_qualified':False,
        'qualification_scope':'Nodal heat balances, cold initial state, steady references, smooth eigenmode convergence; nonlinear step sensitivities measured, not a continuum-error bound.',
        'thermal_model_ready_for_bounded_transfer':True,'panel_history_solved':False,'coupled_first_law_closed':False,
        'cold_V11F_preserved':True,'heated_fracture_solved':False,'fire_solved':False,'blender_changed':False,'global_energy_credit_j':0.,
        'runtime':{'seconds':time.perf_counter()-clock,'started_utc':started,'python':platform.python_version(),'numpy':np.__version__},
        'next_iteration':'V11Q','next_objective':'Transférer directement les profils nodaux V11P aux intégrales exactes de section V11O sur une plage élastique limitée ; vérifier froid, dilatations, réactions et travail thermique avec garde-fou de résistance. Comparer raffinements spatiaux/temporels et carré de température. Ne pas interpoler avant le premier pas sans qualification ; ne pas engager de matériau endommagé ni confondre chaleur sensible et travail thermoélastique.'}
    for name,obj in [('results_v11p.json',result),('numerical_audit.json',tests),('convergence.json',convergence),
                     ('cached_comparisons.json',comparisons),('sensitivities.json',sensitivities)]: write(out/name,obj)
    lines=['# V11P — conduction nodale avec stockage aux surfaces','',f"{result['tests_passed']}/{result['test_count']} contrôles ; {len(runs)} calculs, {result['saved_state_count']} états sauvegardés.",'',
        '## 1. Faits observés dans les fichiers','',
        'V11O signalait un raccord reconstruit incompatible avec les flux. V11P résout de nouveaux profils thermiques et compare uniquement des sorties V11M sauvegardées. V11F et les anciennes itérations sont protégés par empreintes ; aucun ancien pilote complet relancé.','',
        '## 2. Modèles officiels','', 'Aucun nouveau résultat officiel importé. Les références de méthode et de constantes restent celles de la configuration V11K ; il ne s’agit pas d’une reproduction de l’incendie du WTC.','',
        '## 3. Archives locales','', 'Aucune nouvelle affirmation ni inspection d’archive.','',
        '## 4. Hypothèses, unités et équations','',
        'Coupon de 1 m², épaisseur 4,35 in × 0,0254 = 0,11049 m ; rho=2400 kg/m³, cp=900 J/(kg K), k=1 W/(m K), propriétés constantes, sans humidité ni changement de phase. Masse 265,176 kg/m² ; capacité thermique 238658,4 J/(m² K). Ces valeurs sont des paramètres de vérification hérités, non une calibration WTC.','',
        'N intervalles donnent N+1 nœuds, dont les deux surfaces. Largeurs de contrôle dx à l’intérieur et dx/2 à chaque extrémité : somme L. C_i=rho*cp*largeur_i en J/(m² K). Euler arrière : C_i*(Tnouveau−Tancien)/dt=somme des flux entrants, en W/m². Newton emploie la dérivée exacte du rayonnement.','',
        'qconv=h*(Tgaz−Tsurface), qrad=epsilon*sigma*((Trad+273,15)^4−(Tsurface+273,15)^4), sigma=5,670374419e−8 W/(m² K⁴). Exposition synthétique principale : gaz/rayonnement 250 °C en haut, 20 °C en bas ; h=25/10 W/(m² K), epsilon=0,7/0,8 (haut/bas).','',
        cfg['flux_interpretation'],'',cfg['startup'],'',
        'H=rho*cp*sum(largeur_i*(T_i−20)) en J/m². Chaque incrément égale dt fois les quatre flux extérieurs au nouveau pas. Pour les contrôles initialement chauds, le bilan porte sur H−Hinitial. Les intégrales du profil linéaire par morceaux m0=mean(DeltaT), m1=mean((x/L−1/2)*DeltaT), m2=mean(DeltaT²) sont exactes, sans projection sur des fibres. Le profil représente une approximation discrète ; son gradient terminal n’est pas une condition extérieure exacte.','',
        '## 5. Résultats dérivés','',
        '| Maillage/pas | Surface à 90 s (°C) | H à 90 s (J/m²) |','|---|---:|---:|']
    for j in cfg['jobs']:
        row=runs[j['id']]['summary']['final']; lines.append(f"| {j['id']} | {row['top_surface_temperature_c']:.9f} | {row['enthalpy_j_m2']:.6f} |")
    lines += ['',f"Résidu local maximal : {result['maximum_local_balance_w_m2']:.3e} W/m² ; résidu global cumulé maximal : {result['maximum_total_heat_error_j_m2']:.3e} J/m².",'',
        f"Ordres spatiaux sur mode propre Robin lisse : {result['space_orders']}. Ordres temporels contre exponentielle du même opérateur discret : {result['time_orders']}. Ces tests isolent les deux erreurs ; ce ne sont pas des bornes d’erreur du démarrage non linéaire.",'',
        'Les quatre références stationnaires sont maintenues. La température initiale des surfaces vaut maintenant 20 °C, sans saut ni chaleur initiale. La vitesse initiale de chauffage est finie pour chaque maillage mais augmente avec son raffinement : elle ne prouve pas une dérivée temporelle finie dans la limite continue. Le stockage du demi-volume ferme explicitement l’écart entre flux extérieur et flux intérieur.','',
        'Comparaisons V11M aux instants 0, 0,140625, 45 et 90 s : voir cached_comparisons.json. Raffinements séparés et sensibilité du carré de la température : voir sensitivities.json. Les écarts ne sont pas assimilés à une probabilité ni à une validation physique.','',
        '## 6. Limites et informations manquantes','',
        'Qualification numérique bornée de conduction 1D à propriétés constantes. Aucun panneau mécanique chargé dans V11P, aucune fissuration chaude ou modification d’historique endommagé. Pas d’incendie calculé, de premier principe thermo-mécanique couplé fermé, de temps d’effondrement ni de preuve de l’événement réel. Localisation en flexion après fracture complète non validée. Blender inchangé, visualisation ; crédit énergétique global nul. Les premières fractions de pas ne sont plus fabriquées par le raccord V11O, et leur interpolation éventuelle reste à qualifier.','',
        '## Suite','',result['next_objective'],'',f"Durée CPU/murale mesurée du pilote : {result['runtime']['seconds']:.3f} s ; Python {platform.python_version()}, NumPy {np.__version__}, graine 11016 sans tirage.",'']
    (out/'rapport_v11p.md').write_text('\n'.join(lines),encoding='utf-8')
    write(out/'offline_manifest.json',{'iteration':'V11P','implementation_status':result['status'],'input_sha256':before,
                                     'output_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    print(json.dumps({'status':result['status'],'tests':len(tests),'seconds':result['runtime']['seconds'],'failed':[t for t in tests if not t['pass']]}),flush=True)
    if result['status']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()
