"""Versioned V11M experiment. Old drivers never rerun; attempts never overwritten."""
import argparse
import copy
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import run_v11i_thermoelastic_panel as inherited
import v11k_surface_exchange_model as conduction
import v11l_profile_panel as transfer
import v11m_early_thermal as adapter

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'wtc1_simulation_v8/data/v11m_early_thermal.json'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v): Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,allow_nan=False).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',required=True); parser.add_argument('--reuse-attempt')
    args=parser.parse_args(); cfg=read(CONFIG); out=(ROOT/args.output).resolve()
    if not any(out==r or r in out.parents for r in [(ROOT/cfg[k]).resolve() for k in ('scratch_directory','output_directory')]):
        raise ValueError('Outside V11M output roots')
    if out.exists(): raise FileExistsError(out)
    lc=read(ROOT/cfg['transfer_configuration']); kc=read(ROOT/cfg['thermal_configuration'])
    ic=read(ROOT/lc['panel_configuration']); cc=read(ROOT/ic['cold_panel_configuration'])
    hc=read(ROOT/ic['thermomechanical_configuration']); ec=read(ROOT/ic['section_configuration'])
    inputs,paths=inherited.load_inputs(cc)
    before={}; controls={}
    for name in [cfg['protected_manifest'],*lc['sources']]:
        manifest=read(ROOT/name); parent=(ROOT/name).parent
        expected=dict(manifest['input_sha256'])
        expected.update({(parent/p).relative_to(ROOT).as_posix():h for p,h in manifest['output_sha256'].items()})
        bad=[p for p,h in expected.items() if sha(ROOT/p)!=h]
        if bad or read(parent/'release_audit.json')['status']!='PASS': raise ValueError((name,bad))
        controls[manifest['iteration']]={'hash_count':len(expected),'status':'PASS','old_driver_rerun':False}
        before.update(expected)
        for p in [ROOT/name,parent/'release_audit.json']: before[p.relative_to(ROOT).as_posix()]=sha(p)
    for p in [CONFIG,*[ROOT/'wtc1_simulation_v8/scripts'/n for n in
              ('v11m_early_thermal.py','run_v11m_early_thermal.py','audit_v11m_early_thermal.py')]]:
        before[p.relative_to(ROOT).as_posix()]=sha(p)
    case=copy.deepcopy(next(c for c in kc['cases'] if c['id']==cfg['source_case']))
    case['duration_s']=cfg['duration_s']
    clock=time.perf_counter(); started=datetime.now(timezone.utc).isoformat(); out.mkdir(parents=True)
    tests=[]
    def check(n,c,e): tests.append({'name':n,'pass':bool(c),'evidence':e})
    thermal={}; cached_runs={}; cache=None
    if args.reuse_attempt:
        cache=(ROOT/args.reuse_attempt).resolve()
        if (ROOT/cfg['scratch_directory']).resolve() not in cache.parents: raise ValueError('Cache outside V11M scratch')
        oldcfg=read(cache/'input_snapshot/v11m_early_thermal.json')
        if any(cfg.get(k)!=v for k,v in oldcfg.items()): raise ValueError('Cached physical configuration changed')
        cached_runs={r['id']:r for r in read(cache/'panel_runs.partial.json')}
        for p in [*cache.glob('C*_S*.json'),cache/'panel_runs.partial.json',*list((cache/'input_snapshot').iterdir())]:
            before[p.relative_to(ROOT).as_posix()]=sha(p)
    for job in cfg['thermal_jobs']:
        active=copy.deepcopy(kc); active['discretization']['stored_history_intervals']=job['steps']
        saved=read(cache/(job['id']+'.json')) if cache else conduction.run_case(active,case,job['cells'],job['steps'])
        thermal[job['id']]=saved; write(out/(job['id']+'.json'),saved)
        s=saved['summary']
        check(job['id']+'_every_step_saved',len(saved['profiles'])==len(saved['history'])==job['steps']+1,len(saved['profiles']))
        for metric,threshold in [('maximum_increment_energy_residual_absolute_j_m2','thermal_increment_energy_j_m2'),
                                 ('maximum_total_energy_residual_absolute_j_m2','thermal_total_energy_j_m2'),
                                 ('maximum_surface_balance_residual_w_m2','surface_balance_w_m2'),
                                 ('maximum_principle_violation_k','temperature_bound_k')]:
            check(job['id']+'_'+metric,s[metric]<=cfg['acceptance'][threshold],s[metric])
        print('thermal',job['id'],s['final_top_surface_temperature_c'],flush=True)
    runs=[]; models={}; rejected=[]; diagnostics={}
    def run(label,source_id,interval,face=False,mode='profile'):
        source=transfer.SavedProfile(adapter.sampled(thermal[source_id],interval),lc)
        active=copy.deepcopy(ic); active['discretization']['concrete_depth_fibers']=cfg['reference_fibers']
        m=adapter.EarlyPanel(active,cc,hc,ec,inputs,source,mode,cfg['reference_subdivisions'],boundary_face_screen=face)
        # The inherited adapter is only used when its scheduled inputs pass unchanged.
        diagnostic=[adapter.mapping_diagnostic(m,float(t)) for t in source.times]
        bad=next((d for d in diagnostic if d['minimum_proposed_concrete_delta_k'] < -1e-10),None)
        if bad:
            rejected.append({'id':label,'thermal_job':source_id,'snapshot_interval_s':interval,
                             'boundary_face_screen':face,'status':'REJECTED_TRANSFER',
                             'reason':'Inherited moment projection creates below-reference fiber temperature',
                             'first_rejected_scheduled_sample':bad,'guard_time_s':None,'mechanical_path_claimed':False})
            write(out/'rejected_transfers.json',rejected)
            print('REJECTED',label,bad,flush=True)
            return None
        value=copy.deepcopy(cached_runs[label]) if label in cached_runs else transfer.trace(m,lc,cfg['interpolation_substeps'],reverse=False)
        value.update({'id':label,'thermal_job':source_id,'snapshot_interval_s':interval,'boundary_face_screen':face,
                      'cycle_test_performed':False,'terminal_probes':m.saved_probes(value)})
        # Legacy trace reports end-minus-preload in these fields even without a cycle.
        value.pop('cycle_displacement_error',None); value.pop('cycle_stored_error_J',None)
        runs.append(value); models[label]=m
        write(out/'panel_runs.partial.json',runs)
        print('panel',label,value['terminal']['profile_time_coordinate_s'],value['terminal']['governing'],flush=True)
        return value
    common=cfg['common_snapshot_interval_s']
    for job in cfg['thermal_jobs']: run(job['id'],job['id'],common)
    # Dense-step diagnostics also inspect inputs omitted by a coarser saved grid.
    for job in cfg['thermal_jobs']:
        source=transfer.SavedProfile(thermal[job['id']],lc)
        m=adapter.EarlyPanel(ic,cc,hc,ec,inputs,source,'profile',cfg['reference_subdivisions'])
        diagnostics[job['id']]=[adapter.mapping_diagnostic(m,float(t)) for t in source.times]
    write(out/'mapping_diagnostics.json',diagnostics)
    for interval in cfg['snapshot_sensitivity_intervals_s']:
        run('SNAP_'+str(interval),cfg['reference_thermal_job'],interval)
    for source_id in ('C64_S640','C128_S640','C256_S640'):
        run('FACE_'+source_id,source_id,common,True)
    cold=run('COLD',cfg['reference_thermal_job'],common,mode='cold')
    by={r['id']:r for r in runs}; ref=by[cfg['reference_thermal_job']]
    coldrow=inherited.cached_cold_row(ic)
    for key,oldkey,lim in [('stored_J','stored_J','cold_energy_j'),('max_slab_down_m','max_slab_down_m','cold_displacement_m')]:
        err=abs(cold['terminal'][key]-float(coldrow[oldkey])); check('V11F_'+key,err<=cfg['acceptance'][lim],err)
    # Exact baseline adapter check at an already reached state; no old simulation rerun.
    oldm=transfer.ProfilePanel(ic,cc,hc,ec,inputs,models[ref['id']].source,'profile',4)
    oldstate=oldm.solve(.25,ref['terminal']['profile_time_coordinate_s'])
    check('frozen_V11L_adapter_identity',abs(oldstate['max_DCR']-ref['terminal']['max_DCR'])<1e-10 and
          abs(oldstate['stored_J']-ref['terminal']['stored_J'])<1e-6,
          {'DCR_delta':oldstate['max_DCR']-ref['terminal']['max_DCR'],'stored_delta_J':oldstate['stored_J']-ref['terminal']['stored_J']})
    comparisons=[]
    def compare(kind,a,b):
        if a not in by or b not in by:
            comparisons.append({'kind':kind,'coarse_or_baseline':a,'fine_or_alternative':b,
                                'status':'INDETERMINATE_REJECTED_TRANSFER','relative_guard_change':None,
                                'reason':'No accepted mechanical path for one or both inputs; no guard time inferred.'})
            return
        ta=by[a]['terminal']['profile_time_coordinate_s']; tb=by[b]['terminal']['profile_time_coordinate_s']
        common_t=min(ta,tb); ma,mb=models[a],models[b]
        sa=ma.solve(.25,common_t); sb=mb.solve(.25,common_t)
        diff={k:abs(sa[k]-sb[k])/max(floor,abs(sb[k])) for k,floor in
              [('stored_J',1.),('max_slab_down_m',1e-6),('seat_vertical_reaction_N',1.),('max_DCR',1e-6)]}
        change=abs(tb-ta)/max(tb,1e-9)
        comparisons.append({'kind':kind,'status':'MEASURED','coarse_or_baseline':a,'fine_or_alternative':b,
                            'first_guard_a_s':ta,'first_guard_b_s':tb,'relative_guard_change':change,
                            'small_change_indicator':change<cfg['small_change_indicator_relative'],
                            'common_time_s':common_t,'common_response_relative':diff})
    for a,b in zip(('C64_S80','C64_S160','C64_S320'),('C64_S160','C64_S320','C64_S640')): compare('thermal_dt',a,b)
    for a,b in [('C64_S640','C128_S640'),('C128_S640','C256_S640')]: compare('thermal_depth',a,b)
    snaps=['SNAP_45.0','SNAP_22.5','SNAP_4.5','C64_S640','SNAP_0.140625']
    for a,b in zip(snaps,snaps[1:]): compare('saved_sampling',a,b)
    for name in ('C64_S640','C128_S640','C256_S640'): compare('face_screen_only',name,'FACE_'+name)
    allrows=[row for r in runs for row in r['history']]
    maxima={
        'equilibrium_relative':max(r['equilibrium_residual'] for r in allrows),
        'energy_relative':max(r['energy_residual_relative'] for r in allrows),
        'increment_energy_relative':max(r['increment_residual_relative'] for r in allrows),
        'mean_mapping_error_k':max(abs(r['mapping']['mean_delta_k']-r['mapping']['mapped_mean_delta_k']) for r in allrows),
        'gradient_mapping_error_k':max(abs(r['mapping']['reference_equivalent_gradient_k']-r['mapping']['mapped_equivalent_gradient_k']) for r in allrows),
        'maximum_fiber_correction_k':max(r['mapping']['maximum_fiber_correction_k'] for r in allrows),
        'minimum_mapped_delta_k':min(min(r['fiber_delta_temperature_k']) for r in allrows),
        'accepted_DCR':max(r['max_DCR'] for r in allrows)}
    for metric,limit in [('equilibrium_relative',1e-8),('energy_relative',2e-8),('increment_energy_relative',2e-8),
                         ('mean_mapping_error_k',1e-10),('gradient_mapping_error_k',1e-10),('accepted_DCR',.900001)]:
        check(metric,maxima[metric]<=limit,{'value':maxima[metric],'limit':limit})
    check('no_cold_undershoot',maxima['minimum_mapped_delta_k']>=-1e-10,maxima['minimum_mapped_delta_k'])
    check('planned_paths_partitioned',len(runs)+len(rejected)==14 and len({r['id'] for r in runs+rejected})==14,
          {'accepted':len(runs),'rejected':len(rejected)})
    check('rejections_not_credited',all(r['guard_time_s'] is None and not r['mechanical_path_claimed'] for r in rejected),rejected)
    for r in runs:
        bracket=r['guard_bracket']
        check(r['id']+'_guard', (r['mode']=='cold' and bracket is None) or
              (bracket is not None and bracket['accepted_DCR']<.9<=bracket['rejected_DCR'] and
               bracket['rejected_time_s']-bracket['accepted_time_s']<=1e-6 and not bracket['rejected_committed']),bracket)
    check('inputs_unchanged',all(sha(ROOT/p)==h for p,h in before.items()),len(before))
    elapsed=time.perf_counter()-clock
    thermal_depth=[]
    for a,b in [('C64_S640','C128_S640'),('C128_S640','C256_S640')]:
        sa,sb=thermal[a]['summary'],thermal[b]['summary']
        thermal_depth.append({'a':a,'b':b,'time_s':90.,'top_surface_difference_k':sb['final_top_surface_temperature_c']-sa['final_top_surface_temperature_c'],
                              'mean_difference_k':sb['final_mean_temperature_c']-sa['final_mean_temperature_c'],
                              'enthalpy_relative_change':abs(sb['enthalpy_change_j_m2']-sa['enthalpy_change_j_m2'])/abs(sb['enthalpy_change_j_m2'])})
    payload={'runs':runs,'comparisons':comparisons,'rejected':rejected,'mapping_diagnostics':diagnostics,
             'thermal_summaries':{k:v['summary'] for k,v in thermal.items()}}
    old_result=read(ROOT/'wtc1_simulation_v8/output/v11l_profile_panel/results_v11l.json')
    result={'iteration':'V11M','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL',
            'test_count':len(tests),'tests_passed':sum(t['pass'] for t in tests),'thermal_case_count':len(thermal),
            'panel_case_count':len(runs),'rejected_transfer_count':len(rejected),'transfer_qualification':'PARTIAL' if rejected else 'BOUNDED_PASS',
            'state_count':len(allrows),'maxima':maxima,'controls':controls,
            'reference_terminal':ref['terminal'],'thermal_depth_comparisons':thermal_depth,
            'previous_V11L_guard_s':old_result['profile_terminal']['profile_time_coordinate_s'],
            'comparisons':comparisons,'numerical_digest_sha256':digest(payload),
            'runtime':{'seconds':elapsed,'started_utc':started,'python':platform.python_version(),'numpy':np.__version__},
            'thermal_history_computed_this_iteration':True,'one_way_profile_transfer':True,
            'coupled_first_law_closed':False,'surface_remap_validated':False,'fire_solved':False,
            'heated_fracture_solved':False,'global_energy_credit_J':0.,'blender_changed':False,
            'next_iteration':'V11N',
            'next_objective':'Qualifier une reconstruction conservative et positive incluant les températures de surface, et sa compatibilité avec les fibres mécaniques aux tout premiers instants ; croiser ensuite les raffinements thermiques et mécaniques avant toute fissuration chaude. Conserver V11F et les bilans séparés.'}
    write(out/'panel_runs.json',runs); write(out/'comparisons.json',comparisons); write(out/'rejected_transfers.json',rejected)
    write(out/'results_v11m.json',result); write(out/'numerical_audit.json',tests)
    write(out/'source_manifest.json',{'controls':controls,'input_sha256':before,'case':case,'sources':cfg['sources']})
    v=ref['terminal']
    lines=['# V11M — premières 90 secondes du coupon synthétique','',
        f"Contrôles des sorties bornées : {result['tests_passed']}/{result['test_count']} ; statut {result['status']}. Qualification du transfert : {result['transfer_qualification']} ({len(runs)} chemins acceptés, {len(rejected)} rejetés). Les rejets ne sont pas des calculs mécaniques validés.",'',
        '## 1. Faits observés ou transcrits','',
        'Les fichiers V11L et les contrôles V11F/H/I/K sont vérifiés par empreintes. Six nouveaux historiques thermiques sont sauvegardés à chaque pas, de 0 à 90 s. Les anciens calculs complets ne sont pas relancés.','',
        '## 2. Modèles officiels','',
        'Aucun nouveau résultat officiel. Les références primaires de méthode et les constantes de vérification sont héritées de V11K, sans nouvelle calibration WTC.','',
        '## 3. Archives locales','',
        'Aucune nouvelle consultation d’archive, photographie ou vidéo.','',
        '## 4. Hypothèses, unités et méthode','',
        'Coupon 1 m², épaisseur 4,35 in × 0,0254 = 0,11049 m ; béton k=1 W/(m K), rho=2400 kg/m³, cp=900 J/(kg K). Initialement 20 °C. En haut : gaz et rayonnement 250 °C, h=25 W/(m² K), epsilon=0,7 ; en bas : 20 °C, h=10, epsilon=0,8. Ce palier est synthétique_non_WTC.','',
        'Conduction : volumes finis, Euler implicite, bilans de surface sans masse. q entrant=h(Tgaz−Ts)+epsilon*sigma[(Trad+273,15)^4−(Ts+273,15)^4]. H=rho*cp*dx*sum(T−20), en J/m² ; DeltaH=dt*(qbas+qhaut) à chaque pas.','',
        'Panneau élastique à petites déformations, précharge 0,25 gravité ; 4 subdivisions longitudinales, 160 fibres béton et 2 couches d’armatures. E et résistances sont ceux de V11H/I, conservés dans chaque état de section ; alpha béton=1e-5/K, acier=1,2e-5/K. Les treillis et assemblages restent froids.','',
        cfg['energy'],'',cfg['surface_diagnostic'],'',cfg['sensitivity_policy'],'',
        '## 5. Résultats dérivés','',
        '| Cas | Pas thermique (s) | Profils utilisés (s) | Premier garde-fou (s) | DCR |',
        '|---|---:|---:|---:|---:|']
    for r in runs:
        row=r['terminal']; lines.append(f"| {r['id']} | {thermal[r['thermal_job']]['summary']['dt_s']:.6f} | {r['snapshot_interval_s']:.6f} | {row['profile_time_coordinate_s']:.9f} | {row['max_DCR']:.9f} |")
    lines += ['', 'COLD atteint simplement 90 s sans garde-fou thermique. Les chiffres des autres lignes sont des seuils du modèle élastique, pas des temps de rupture.','',
        '| Sensibilité | Paire | Écart du garde-fou |','|---|---|---:|']
    for c in comparisons:
        change='indéterminé : transfert rejeté' if c['relative_guard_change'] is None else f"{100*c['relative_guard_change']:.6f} %"
        lines.append(f"| {c['kind']} | {c['coarse_or_baseline']} → {c['fine_or_alternative']} | {change} |")
    lines += ['',f"V11L sauvegardée : {result['previous_V11L_guard_s']:.9f} s. Nouvelle référence à 64 cellules : {v['profile_time_coordinate_s']:.9f} s. Aucun temps de garde-fou n’est attribué aux transferts rejetés. Le temps physique calculé concerne uniquement ce coupon synthétique ; le seuil est interpolé entre ses pas sauvegardés.",'',
        f"Référence : U={v['stored_J']:.9f} J ; Wext={v['external_work_J']:.9f} J ; Wth={v['thermal_work_J']:.9f} J ; réaction verticale={v['seat_vertical_reaction_N']:.6f} N. Résidu mécanique relatif maximal={maxima['energy_relative']:.3e}.",'',
        f"Enthalpie composite={v['sensible_enthalpy_J']:.6f} J ; coupon brut étendu={v['gross_coupon_sensible_J']:.6f} J ; différence={v['composite_minus_gross_sensible_J']:.6f} J. Cette différence est tracée, pas compensée.",'',
        '## 6. Limites et informations manquantes','',
        'La première tentative s’est arrêtée sur le contrôle de positivité à 128 cellules. Ses entrées et ses sorties sont conservées. La présente publication réutilise ses six historiques thermiques et quatre chemins terminés, tous relus et audités. Aucun seuil de positivité n’est relâché.','',
        'La correction héritée T*(1+a+b*y/h) peut devenir négative dans les queues froides du profil. Plus fondamentalement, si le barycentre thermique cible dépasse celui de la fibre la plus proche de la surface, aucune distribution non négative sur ces fibres fixes ne peut conserver simultanément les deux moments demandés. Les diagnostics non engagés de chaque pas sont sauvegardés dans mapping_diagnostics.json. Une correction simplement tronquée détruirait les moments.','',
        f"Comparaisons purement thermiques à 90 s (distinctes des chemins mécaniques rejetés) : {json.dumps(thermal_depth,ensure_ascii=False)}",'',
        'Le diagnostic FACE ne remplace que les sondes de contrainte aux deux faces, de mesure volumique nulle. Il ne valide pas une nouvelle température continue ni sa compatibilité avec une quadrature de section. Le point initial mécanique reste froid malgré la réponse algébrique instantanée d’une surface sans masse : cette régularisation est limitée au premier intervalle sauvegardé.','',
        'Le raffinement de profondeur change aussi les positions des sondes intérieures du profil ; le nombre de fibres mécaniques et le maillage longitudinal restent fixes. Les sensibilités enregistrées ne sont donc pas une certification d’erreur globale. Pas de fissuration chaude, de dégradation de propriétés, de rétroaction thermodynamique, de flambement géométrique, de dynamique globale ou d’effondrement calculé. La localisation en flexion après fracture complète reste non validée. Une exposition thermique imposée n’est pas un incendie calculé. Blender est inchangé et reste une visualisation. Aucun résultat historique n’est présupposé.','',
        '## Suite','',result['next_objective'],'',f'CPU : {elapsed:.2f} s ; graine 11013, sans tirage.','']
    (out/'rapport_v11m.md').write_text('\n'.join(lines),encoding='utf-8')
    write(out/'offline_manifest.json',{'iteration':'V11M','implementation_status':result['status'],
          'input_sha256':before,'output_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    print(json.dumps({'status':result['status'],'tests':len(tests),'seconds':elapsed,'failed':[t for t in tests if not t['pass']]}),flush=True)
    if result['status']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()
