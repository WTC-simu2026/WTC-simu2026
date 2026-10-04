"""K report, immutable inventory, registration and solver-free verification."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import run_impact_i02i_free_mixed as run
h=run.h;ROOT,OUT,CFG=run.ROOT,run.OUT,run.CFG
SUMMARY=OUT/'verification_r1/summary.json'
REPORT=OUT/'rapport_impact_i02i_free_mixed.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_K_HANDOFF.md'
LPLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_l_plan_from_k.json'
OBJECTIVE='L : établir un registre énergétique de la réserve tangentielle lors de OFF, d’abord à partir des cas F sauvegardés et des références H/K. Pré-déclarer le diagnostic, garder les lignes brutes et vérifier toute signature binaire avant lecture ; quantifier Ux avant, IE/KE/WE après et ce que les sorties ne permettent pas d’identifier. Aucun déphasage, clipping, modification d’état endommagé ou ancien solveur relancé. Aucun nouveau mode mixte libre avec séparation avant référence énergétique explicite. Conserver E/F/G, quatre signes I et trois fins brutes J ; NASA/Gf30 hypothétique/Gf15/60 ouverts, V11F/V11R/V11S conservés. J+K GitHub due après contrôle distant/archives/CI. Impact Boeing/façade, feu et effondrement non qualifiés.'
read=run.read

def preservation():
    rows=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in rows if h.sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad;return len(rows)

def prepare():
    assert not REPORT.exists() and not HANDOFF.exists() and not LPLAN.exists(),'Preserve iterations'
    s=read(SUMMARY);cfg=read(CFG);count=preservation();hv=h.harness()
    assert s['all_declared_checks_pass'] and s['case_checks_passed']==s['case_checks_total']==254
    assert s['comparison_checks_passed']==s['comparison_checks_total']==28 and s['reference_checks_passed']==s['reference_checks_total']==26
    files={'saved_F_summary':'wtc1_simulation_v8/output/impact_i02i_dtcap/verification_r1/summary.json',
        'saved_H_reference':'wtc1_simulation_v8/output/impact_i02i_free_fracture/reference_verification.json',
        'saved_K_summary':h.rel(SUMMARY),'saved_K_reference':h.rel(OUT/'reference_verification.json')}
    plan={'id':'IMPACT-I02I-L_PLAN_FROM_K','created_utc':h.NOW(),'seed':1102020,'random_draws':0,
        'scope':'Saved-output energy ledger at whole-element deletion before new free mixed separation',
        'inputs':{k:{'path':v,'sha256':h.sha(ROOT/v)} for k,v in files.items()},
        'before_analysis':['Read saved F event measures and H/K references; do not rerun historical engines',
            'Predeclare inventory, exact signature guards, raw-row event selection and rational quantization; reject unknown binary layouts',
            'Separate Ux, Uy, accumulated IE, KE and external work on original times; do not move OFF/FX or reinterpret same-row failures',
            'Compare a conditional ledger with released Ux versus retained Ux at deletion, explicitly distinguishing bookkeeping from a material law',
            'Identify unobservable internal channel/centering and do not infer thermal or physical mixed fracture energy from IE alone'],
        'expected_F_control':'FIXED cases retain IE about 0.0343 J after OFF with pre-OFF elastic X reserve about 0.0043 J; imposed kinematics are not a free-release validation',
        'before_future_engine':'Derive separable free mixed separation plus declared deletion-energy policy; fresh state only, no modification of an old damaged material',
        'budget':{'maximum_diagnostic_seconds':120,'solver_jobs_planned':0,'source_archive_scan':False},
        'unchanged':['Five same-row OFF/FX F failures','Eight strict G diagnostics','E inertia/angle/coverage',
            'Four raw I sign failures','Three raw J endpoint failures','NASA conventions','Gf30 hypothetical;15/60 deferred','V11F/V11R/V11S'],
        'physical_propagation_qualified':False,'publication':'J+K due after K verified, then next pair L+M; local cadence authoritative'}
    h.dump(LPLAN,plan)
    table=[];raw=[]
    for n,r in s['cases'].items():
        m=r['metrics'];f=m['fractions'];v=m['final']
        table.append(f"| {n} | {m['rows']} | {100*f['vx_mm_per_ms']:.6g} | {100*f['vy_mm_per_ms']:.6g} | {100*f['energy_balance']:.6g} | {v['Ux_J']:.10g} | {v['raw_D_J']:.10g} |")
        raw.append(f"| {n} | {m['minimum_raw_D_J']:.10g} | {m['negative_raw_D_rows']} | {m['end_record_ms']:.17g} | {'passe' if m['raw_end_coverage_without_quantization'] else 'échoue'} |")
    REPORT.write_text(f'''# WTC1 — IMPACT-I02I-K : ouverture et cisaillement libres sans séparation

## 1. Faits directement observés ou transcrits

Quatre états neufs, douze jobs (starter, moteur et export de chaque cas), sans warning de précontrôle, avec terminaison normale. Durée cumulée des jobs : {s['runtime_seconds']:.6f} s, budget 90 s/cas et 600 s/campagne. Les 1922 lignes ont chacune 41 valeurs : 78802 valeurs binaires reproduisent exactement les jetons CSV .6e. Deux lecteurs indépendants concordent ; IE globale, SPRING ENERGY et IE de liaison sont identiques bit pour bit. TH une ligne par cycle, pas maximal mesuré 25/12,5 ns, aucune masse ajoutée et WE=0.

Les critères pré-déclarés passent : **254/254 de cas, 28/28 comparaisons et 26/26 références**. Les 20 références mécaniques incluent une intégration RK4 directe indépendante (4096/8192 pas), les équations de mouvement et l’identité énergétique. Les six références de lecture vérifient les rejets de fichiers invalides et des états élastiques exacts avec deux forces. OFF=1 dans tous les cas, Y reste positif et inférieur à la séparation complète.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat NIST ni modèle historique. Le solveur est utilisé pour quatre témoins TYPE8 bornés, pas comme validation du WTC. Les propriétés et mots-clés hérités sont documentés dans les manifestes I/J/H ; aucune nouvelle donnée physique ou source primaire nécessaire pour cette combinaison des mêmes lois. Le lecteur J n’est accepté que sur les signatures déclarées, version 3040, blocs et codes vérifiés. Le schéma binaire officiel et le code original du convertisseur restent non obtenus. La définition documentaire REACX/REACY comme force et leur comportement observé d’impulsion cumulative restent une limite ; le centrage interne TH demeure non établi.

## 3. Affirmations des archives locales

Aucune nouvelle assertion d’archive et aucune vidéo inspectée. {count} fichiers antérieurs épinglés depuis les inventaires sauvegardés, vérifiés inchangés. Aucun ancien moteur relancé ni archive rescannée. Les échecs I/J et E/F/G ainsi que le contrôle froid V11F et la branche V11R → V11S sont conservés.

## 4. Hypothèses propres au modèle, propriétés, unités et historique

Deux nœuds, chacun de masse 0,1 g ; nœud 1 fixe, nœud 2 libre sur X et Y, Z et rotations bloqués. Une liaison TYPE8, sans contact ni couplage matériel entre axes. Kn=56000 N/mm, Kt=21500 N/mm, pic normal hypothétique 495 N, aire 1 mm², Gf=30 N/mm hypothétique. Séparation normale δf=0,1212121212 mm, début d’adoucissement δ0=0,0088392857 mm ; aucun OFF attendu dans les fenêtres. Loi tangentielle purement élastique, rupture tangentielle désactivée. Tous les états sont neufs, sans restart ou modification d’une propriété endommagée.

Unités : g, mm, ms et N, car 1 g·mm/ms²=1 N ; 1 N·mm=0,001 J. Vitesses mm/ms (=m/s), impulsions N·ms. Cas arrêt : vx0=10, vy0=20, E0x=0,005 J et E0y=0,020 J, total0,025 J, fin0,012 ms. Cas sous-pic : vx0=1, vy0=√20, E0x=0,00005 J, E0y=0,001 J, total0,00105 J, fin0,004 ms. Seed1102019, zéro tirage. Caps25 et12,5 ns ; aucun déplacement X/Y imposé.

Référence séparable : ωx=√(Kt/m), x=vx0/ωx·sin(ωx t), vx=vx0 cos(ωx t), Fx=Kt x. Y reprend la référence H2 vérifiée en I avec maximum historique δmax conservé. À la décharge, Fy=max[0,Fenveloppe(δmax)+Kn(y−δmax)] ; Dy=Wchargement(δmax)−Fenveloppe(δmax)²/(2Kn), sans réinitialisation de l’histoire. Réserve récupérable Ux=Fx²/(2Kt), Uy=Fy²/(2Kn), puis conversion en J ; IE=Ux+Uy+Dy ; KE=m(vx²+vy²)/2 ; E0+WE=IE+KE. Dy est du travail numérique non récupéré, sans identification à une chaleur ou fissuration réelle.

P0x=m vx0, P0y=m vy0 ; Jappui,axe=Paxe−P0axe. Les intégrales −∫Faxe dt sont comparées séparément aux sorties REAC, et ∫(Fx dx+Fy dy) au travail interne. Force élastique, force H2, énergie issue du maximum historique et références en temps sont contrôlées séparément. Seuils déclarés avant moteur : amplitudes par axe/impulsions ≤1 %, énergie/travail et comparaisons ≤0,5 %, avec échelles fixes prévues.

Précision pré-déclarée : cellules binaires32 au plus proche, milieux exacts entre voisin et valeur stockée (fractions dyadiques), calcul exact de l’intervalle IE−Fx²/(2Kt)−Fy²/(2Kn). Borne supérieure ≥0 à chaque ligne ; dans la phase historiquement élastique, intervalle contenant0. Temps final : cellule intersectant [fin−2pas,fin]. Il s’agit d’hypothèses de représentation, sans accès à la valeur interne. Aucun clipping, tolérance de signe ajustée, déphasage ou promotion d’un ancien échec. Les valeurs brutes et les fractions exactes sont sauvegardées.

## 5. Résultats dérivés

| Cas | Lignes | Erreur vx (% amplitude) | Erreur vy (% amplitude) | Résidu énergie (% E0) | Ux finale (J) | IE−Ux−Uy final brut (J) |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(table)}

Le plus grand écart brut de vitesse/impulsion est 0,93546 % dans le cas sous-pic 25 ns, puis ≈0,46772 % à12,5 ns. Aucun ajustement temporel. Les forces/déplacements ont des écarts nettement plus faibles. Le résidu énergétique maximal est 0,008443 % de E0 ; le critère0,5 % passe. Les comparaisons sont faites aux temps déclarés couverts, sans extrapolation.

Dans l’arrêt normal, Uy et Fy deviennent nuls, vy≈−3,966 mm/ms ; Dy≈0,0192134 J persiste, tandis que X continue à osciller et Ux finale≈0,0022 J. La réserve X n’est donc pas supprimée lorsque Y se décharge **tant que l’élément reste actif**. Ce résultat ne traite pas la désactivation totale OFF. Dans le sous-pic, l’intervalle de D contient0 sur toutes les lignes : retour numériquement compatible avec la référence élastique séparable.

| Cas | Minimum D brut (J) | Lignes D brut<0 | Temps final binaire (ms) | Condition brute fin sans intervalle (diagnostic) |
|---|---:|---:|---:|---|
{chr(10).join(raw)}

Les quatre minima bruts restent sous −1e−10 J, seuil historique I mentionné à titre descriptif seulement. Les deux fins sous-pic dépassent la fin demandée de ≈1,90e−10 ms. **Aucun signe brut ni temps n’est corrigé** ; les critères K portent dès leur déclaration sur les intervalles de représentation. Toutes les bornes supérieures de D sont non négatives et les cellules élastiques contiennent0. Les cellules de fin passent. Ces compatibilités ne résolvent pas le signe interne et ne modifient pas les quatre échecs I ou les trois critères bruts J.

## 6. Contradictions et informations manquantes

K vérifie deux modes indépendants simultanés sans séparation ; aucun vrai couplage de contact, de matériau, de dalle ou de rupture mixte. Le devenir de Ux lorsque la rupture normale désactive tout l’élément reste ouvert. F avait conservé IE≈0,0343 J sous cisaillement fixé, avec réserve tangentielle≈0,0043 J avant suppression ; cela ne qualifie pas sa restitution dans un corps libre. L’étape L préparera le registre énergétique sur les sorties F sauvegardées avant une nouvelle séparation mixte libre. Toute politique de suppression/rétention/restitution d’énergie devra être explicite et comparée à une référence avant moteur, sans changer un état endommagé ancien.

Conserver cinq échecs OFF/FX F, huit diagnostics stricts G, sensibilités d’inertie/angle et couverture E, quatre signes I et trois fins J, limites de précision/centrage/REAC. Les conventions NASA restent non identifiées, Gf30 hypothétique et Gf15/60 différés. Aucune calibration physique de fracture, impact complet Boeing/façade, incendie ou effondrement réel. Flexion localisée après fracture complète non validée ; température imposée ≠ incendie calculé ; Blender reste une visualisation.

## Reproduction et reprise

Configuration JSON, référence, scripts, sources héritées, cartes, exécutables hachés, versions, journaux, T01/CSV, comparaisons et intervalles exacts conservés. Vérifier sans moteur : complete_impact_i02i_free_mixed.py verify. Rapport et passation existent avant registre/état. J+K publication due après vérification d’intégrité, avec anciens échecs conservés ; ensuite L+M. Cadence locale fait foi, aucune publication X.
''',encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# Passation compacte — IMPACT-I02I-K vers L

Lire AGENTS.md, harness/state.json (prioritaire), cette passation puis impact_i02i_l_plan_from_k.json. K terminée ; prochaine L. J+K atteint2/2 ; publication et cadence exactes dans harness/publication_cycle.json et preuve privée outputs/github_publication/updates_2026-10-04_i02i_k/final_remote_verification.json si présente. Après envoi vérifié, prochaine paire L+M.

K : quatre états neufs X/Y libres sans séparation/compression, caps25/12,5 ns,12jobs,{s['runtime_seconds']:.6f}s. 254/254 critères,28/28 comparaisons,26/26 références ;1922lignes,78802valeurs reproduisent CSV. Kn56000,Kt21500 N/mm,m_mobile0,1g,Gf30 hypothétique,H2historique inchangé. Arrêt vx10/vy20,E0.025J,fin.012ms ; sous-pic vx1/vy√20,E0.00105J,fin.004ms. IE=Ux+Uy+Dy ; impulsions incluent P0 séparément. OFF1 partout ; au retour normal Fy/Uy nuls, Dy≈.0192134J, Xcontinue et Ux≈.0022J. Deux lois indépendantes, pas vrai couplage.

Signes D bruts −1,22e−10 à−2,16e−10J et deux fins brutes légèrement dépassées restent affichés. Intervalles exacts déclarés avant moteur passent, sans clipping/déphasage et sans modifier I/J. Vérifier sans solveur via complete_impact_i02i_free_mixed.py verify ; rapport, auditeur et artifact_manifest dans impact_i02i_free_mixed. {count} anciens fichiers épinglés.

L : registre énergétique de la réserve tangentielle à OFF sur F sauvegardée, avec références H/K ; pré-déclarer diagnostic/signature et conserver les lignes originales. Distinguer Ux avant, IE/KE/WE après et travail non récupéré de mécanisme physique. Pas ancien moteur/restart/changement de matériau endommagé. Avant future séparation mixte libre, dériver référence avec politique explicite du devenir de Ux. Budget diagnostic120s, aucun moteur prévu par ce plan.

Conserver cinq OFF/FX F et réserve tangentielle à suppression complète, huit diagnostics G, E, quatre signes I, trois fins J, REAC/centrage, NASA, Gf15/60 différés,V11F/V11R/V11S. Aucun impact Boeing/façade/feu/effondrement qualifié, flexion post-fracture non validée, Blender visualisation. Aucun post X.
''',encoding='utf-8',newline='\n')
    h.dump(OUT/'release_audit.json',{'created_utc':h.NOW(),'pass':True,'old_files_preserved':count,'harness':hv,
        'summary_sha256':h.sha(SUMMARY),'all_K_declared_checks_pass':True,'old_failures_retained':True,'physical_propagation_qualified':False})
    h.dump(OUT/'harness_after_artifacts.json',h.harness())
    scripts=[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_impact_i02i_free_mixed.py','reference_impact_i02i_free_mixed.py','audit_impact_i02i_free_mixed.py','complete_impact_i02i_free_mixed.py']]
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,LPLAN,HANDOFF]+scripts
    h.dump(OUT/'artifact_manifest.json',{'created_utc':h.NOW(),'files':[{'path':h.rel(p),'bytes':p.stat().st_size,'sha256':h.sha(p)} for p in sorted(set(paths))],
        'exclusions':['self','post-registration verification','mutable harness administration']})

def register():
    assert REPORT.exists() and HANDOFF.exists() and LPLAN.exists() and (OUT/'artifact_manifest.json').exists();count=preservation();s=read(SUMMARY)
    for name in h.g.f.ADMIN:assert h.sha(ROOT/'harness'/name)==h.sha(OUT/('before_'+Path(name).name)),'Concurrent state change'
    state=read(ROOT/'harness/state.json');cadence=read(ROOT/'harness/publication_cycle.json')
    assert state['current_iteration']=='IMPACT-I02I-J' and state['next_iteration']=='IMPACT-I02I-K' and cadence['pending_iterations']==['IMPACT-I02I-J']
    status='completed_bounded_separable_free_XY_without_separation';when=h.NOW()
    record={'experiment_id':'WTC1-IMPACT-I02I-K','registered_at':when,'status':status,'configuration':h.rel(CFG),'report':h.rel(REPORT),
        'results':h.rel(SUMMARY),'handoff':h.rel(HANDOFF),'L_plan':h.rel(LPLAN),'artifact_manifest':h.rel(OUT/'artifact_manifest.json'),
        'source_manifest':h.rel(OUT/'source_manifest.json'),'publication_verification':h.rel(OUT/'publication_verification.json'),
        **{k:s[k] for k in ['case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','reference_checks_passed','reference_checks_total',
            'all_declared_checks_pass','runtime_seconds','total_rows','no_old_solver_rerun','old_I_four_sign_failures_preserved','old_J_three_raw_endpoint_failures_preserved','official_schema_verified','mixed_fracture_calibrated','physical_propagation_qualified','aircraft_impact_qualified']},
        'cases':4,'solver_jobs':12,'old_files_preserved':count,'numerical_two_separable_modes_verified':True,'mixed_mode_qualified':False,
        'source_convention_verified':False,'E_sensitivities_resolved':False,'next_iteration':'IMPACT-I02I-L','github_pending_iterations':2}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='IMPACT-I02I-K',current_status=status,next_iteration='IMPACT-I02I-L',next_objective=OBJECTIVE,updated_at=when)
    state['impact_i02i_k_key_results']={k:v for k,v in record.items() if k not in ['experiment_id','registered_at','status','configuration','report','results','handoff','L_plan','artifact_manifest','source_manifest','publication_verification','next_iteration']}
    state['validated_artifacts'].update(impact_i02i_k_report=h.rel(REPORT),impact_i02i_k_results=h.rel(SUMMARY),impact_i02i_k_handoff=h.rel(HANDOFF),
        impact_i02i_k_publication_verification=h.rel(OUT/'publication_verification.json'),impact_i02i_l_plan=h.rel(LPLAN))
    cadence.update(pending_iterations=['IMPACT-I02I-J','IMPACT-I02I-K'],pending_count=2,next_publication_after='J+K due after remote tree, digest and CI checks; next pair L+M',updated_at=when)
    h.dump(ROOT/'harness/publication_cycle.json',cadence);temp=ROOT/'harness/state_i02ik_pending.json';h.dump(temp,state);temp.replace(ROOT/'harness/state.json');verify(write=True)

def verify(write=False):
    count=preservation();manifest=read(OUT/'artifact_manifest.json');bad=[r['path'] for r in manifest['files'] if h.sha(ROOT/r['path'])!=r['sha256']]
    state=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cadence=read(ROOT/'harness/publication_cycle.json');s=read(SUMMARY)
    prefix=(OUT/'before_registry.jsonl').read_bytes();reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();extra=reg[len(prefix):].decode('utf-8').splitlines()
    protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy','open_limitations']
    pending=cadence['pending_iterations']==['IMPACT-I02I-J','IMPACT-I02I-K'] and cadence['pending_count']==2
    published=cadence['last_published_iteration']=='IMPACT-I02I-K' and cadence['pending_count']==0 and cadence['pending_iterations']==[]
    hv=h.harness();cfg=read(CFG);checks={'artifact_hashes':not bad,'old_pins_preserved':True,'registry_prefix':reg.startswith(prefix),
        'one_K_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-K',
        'state_K_to_L':state['current_iteration']=='IMPACT-I02I-K' and state['next_iteration']=='IMPACT-I02I-L',
        'prior_states_preserved':all(state[k]==old[k] for k in protected),'harness_pass':hv['Status']=='PASS',
        'report_handoff_plan_exist':REPORT.exists() and HANDOFF.exists() and LPLAN.exists(),'cadence_pending_or_published':pending or published,
        'reference_guard':read(OUT/'reference_verification.json')['pass'] and h.sha(OUT/'reference_verification.json')==cfg['reference_guard_sha256'],
        'all_K_declared_counts':s['all_declared_checks_pass'] and s['case_checks_passed']==s['case_checks_total']==254 and s['comparison_checks_passed']==28 and s['reference_checks_passed']==26,
        'old_I_failures_retained':not state['impact_i02i_i_key_results']['all_declared_checks_pass'] and len(state['impact_i02i_i_key_results']['failed_gates'])==4,
        'old_J_failures_retained':not state['impact_i02i_j_key_results']['all_declared_raw_checks_pass'] and state['impact_i02i_j_key_results']['raw_failures_preserved']==3,
        'physical_limits_retained':not s['physical_propagation_qualified'] and not s['mixed_fracture_calibrated'] and not s['official_schema_verified'],
        'no_old_solver_rerun':s['no_old_solver_rerun']}
    result={'created_utc':h.NOW(),'pass':all(checks.values()),'scope':'K bounded numerical and integrity verification; no physical event qualification',
        'checks':checks,'manifest_files_checked':len(manifest['files']),'manifest_failures':bad,'old_files_checked':count,'harness':hv,
        'case_checks':'254/254','comparison_checks':'28/28','reference_checks':'26/26','all_declared_checks_pass':True,
        'old_failures_retained':True,'physical_propagation_qualified':False,'next_iteration':'IMPACT-I02I-L','github_pending_iterations':cadence['pending_count']}
    assert result['pass'],result
    if write:h.dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);args=p.parse_args();globals()[args.action]()
