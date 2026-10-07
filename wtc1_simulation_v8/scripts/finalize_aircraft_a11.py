"""Seal A11 diagnostic failures, state and handoff only after saved-result verification."""
import argparse,hashlib,json,sys,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from run_aircraft_a11 import ROOT,CFG,OUT,PREV,EXT,read,dump,rel,now,harness,guard
REPORT=OUT/'rapport_aircraft_a11.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A11_HANDOFF.md'
NEXT='AIRCRAFT-A12 : réutiliser la scène A11 et ses échecs. Isoler le premier contact du nez/radôme dans un témoin sans redistribution RBE3, avec inerties natives et énergie LAW25/TYPE19 vérifiables ; comparer à un témoin élastique simple et à une formulation de contact déclarée. Ajouter le contrôle spatial encore manquant. Ne pas prolonger comme impact qualifié avant fermeture du bilan local. Examiner ensuite le module Boeing parallèle s’il est livré, sans modifier implicitement matériaux/masses. Impact historique, rupture et écrasement restent non qualifiés.'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()

def checkrows(rows):
    def check(r):
        p=ROOT/r['path'];return r['path'] if not p.exists() or p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256'] else None
    with ThreadPoolExecutor(max_workers=3) as pool:bad=[b for b in pool.map(check,rows) if b]
    assert not bad,bad;return len(rows)

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists();s=read(OUT/'initial_stage_review.json');rows=s['cases'];assert len(rows)>=3 and all((OUT/'r0'/r['case']['id']/'review.json').exists() for r in rows)
    if s['one_ms_extension_numerically_allowed']:assert EXT.exists() and any((OUT/'r0'/c['id']/'review.json').exists() for c in read(EXT)['cases'])
    v=harness();assert v['Status']=='PASS';dump(OUT/'harness_after_calculations.json',v);t=time.perf_counter();pins=read(OUT/'preservation_before.json')['files'];n=checkrows(pins);dump(OUT/'preservation_verification.json',{'pass':True,'created_utc':now(),'files':n,'bytes':sum(r['bytes'] for r in pins),'seconds':time.perf_counter()-t,'old_solver_reruns':0})
    s.update(integrity_only_pass=all(all(r['checks'][k] for k in ['starter_zero_errors','starter_zero_warnings','mass_preserved','native_original_connectivity_preserved','all_exported_states_finite','supports_fixed','no_erosion','no_external_work']) and r['extra_checks']['CSV_all_native_channels_verified'] for r in rows),all_declared_checks_pass=all(r['all_declared_checks_pass'] for r in rows),main_engine_jobs=len(rows),whole_aircraft_cases=len(rows),old_solver_reruns=0,physical_impact_qualified=False,engine_crushing_qualified=False,seconds_impact_calculated=False,requested_one_ms_extension_performed=EXT.exists(),next_iteration='AIRCRAFT-A12',duration_stop_reason='local energy gate failed, not extended to 1ms' if not s['one_ms_extension_numerically_allowed'] else 'see saved extension results',native_RKE_ledger_qualified=False,contact_option_transferred_as_qualified=False)
    assert s['integrity_only_pass'];dump(OUT/'authoritative_review.json',s)
    jobs=[read(p) for p in OUT.glob('r*/**/*.execution.json')];sec=sum(q['seconds'] for q in jobs);eng=[read(OUT/'r0'/r['case']['id']/'engine.log.execution.json') for r in rows];last=next(r for r in rows if r['case']['id']==s['selected_short_case']);est=[{'case':r['case']['id'],'engine_seconds_per_run':e['seconds'],'horizon_ms':r['case']['end_ms'],'linear_extrapolation_one_second_CPU_hours':e['seconds']/r['case']['end_ms']*1000/3600,'not_runtime_prediction_or_authorization':True} for r,e in zip(rows,eng) if r['case']['contact']]
    dump(OUT/'execution_journal.json',{'created_utc':now(),'python':sys.version,'CPU_threads':2,'GPU':False,'runtime':'unchanged OpenRadioss Windows double precision build2026-07-28','main_engine_jobs':len(rows),'observer_jobs':len(rows),'old_solver_reruns':0,'native_stage_seconds_sum':sec,'execution_records':[rel(p) for p in OUT.glob('r*/**/*.execution.json')],'long_horizon_cost_warning':est,'no_hours_scale_job_started':True})
    table='\n'.join(f"|{r['case']['id']}|{r['actual_main_end_time_ms']:.6f}|{r['final_contact_impulse_Ns'][0]:.6f}|{r['final_generated_energy_J']:.3f}|{r['final_energy_residual_J']:.3f}|{r['maximum_energy_residual_J']:.3f}|{','.join(r['failed_checks']) or 'aucun'}|" for r in rows)
    comps='\n'.join(f"|{' / '.join(c['cases'])}|{100*c['impulse_difference_fraction']:.6f}|{100*c['generated_energy_difference_fraction']:.6f}|{c['impulse_pass']}/{c['energy_pass']}|" for c in s['half_dt_comparisons'])
    REPORT.write_text(f'''# AIRCRAFT-A11 — avion couplé, premier contact du nez

A11 est terminée comme diagnostic limité de la nouvelle scène : {len(rows)} calculs Engine neufs, sans ancien calcul relancé. La façade n’est plus devant les moteurs : sa translation A07 est inversée exactement et le contact des surfaces extérieures de l’avion est activé. Le nez rencontre la façade vers0,225ms. La fenêtre atteinte est0,4ms, soit0,0004s ; les premières secondes et la traversée historique ne sont pas calculées. Le déficit énergétique local reste un critère échoué et bloque le passage déclaré à1ms. Aucune rupture, érosion ou loi d’écrasement n’est qualifiée.

## 1. Faits directement observés ou transcrits

Starter sans erreur ni avertissement, terminaisons normales et extrémités temporelles récupérées par un observateur séparé qui ne modifie pas les sorties principales. Tous les canaux CSV sont vérifiés contre les records T01 binaires natifs ; les états d’animation et masses nodales sont lus indépendamment. Masse avion native après redistribution≈{last['native_aircraft_mass_after_RBE3_kg']:.6f}kg, masse totale modèle≈{last['native_total_mass_kg']:.6f}kg. L’écart des masses nodales float32 est contrôlé séparément.

Façade : domaine existant couvrant environ59,3m en largeur et10,97m en hauteur, trois étages représentatifs, face avant x=-50mm ; translation[-15468,6,0,0]mm. Nez initial x=0, vitesse hypothétique[-200,5,2]m/s, gap extérieur5mm : estimation de contact(50-5)/200=0,225ms, puis observation native concordante. AIRFRAME commence effectivement à{last['contact_onset_by_segment_ms'].get('AIRFRAME')}ms ; NACELLE/FAN/CORE restent sans contact dans la fenêtre. Les mêmes moteurs couplés, ailes et sous-structures sont conservés. Les groupes de contact ne partagent aucun nœud.

Le libre conserve le mouvement uniforme et ne développe aucune déformation plastique. Son résidu maximal320J est à distinguer de la précision float32 des sorties sur≈2,441GJ ; les mêmes seuils de comparaison sauvegardés sont appliqués. Il n’explique pas les≈6kJ manquants pendant le contact.

## 2. Résultats d’un modèle officiel

La façade représentative et ses propriétés héritent de sources NIST identifiées dans la chaîne de provenance ; cela limite l’indépendance des données d’entrée. Aucun résultat de dommages NIST, aucune pénétration observée ni résultat d’effondrement n’est une cible de réglage. Les sorties présentes sont celles du solveur OpenRadioss dans notre sous-modèle, pas la validation du modèle historique officiel.

## 3. Affirmations d’archives locales

Aucune nouvelle analyse vidéo ni scan d’archive. Sources et sorties sauvegardées A01/A09/A10 réutilisées. {n} fichiers antérieurs épinglésSHA256 vérifiés inchangés. V11F/V11R préservées, V11S/I02I-M différées. Les premières erreurs de découverte des outils et refus d’aperçu sont sauvegardés dans tooling_discovery_errors.json ; aucun solveur ancien ou logiciel installé/modifié.

## 4. Hypothèses propres au modèle

Configuration aircraft_a11_predeclaration.json déclarée avant calcul, graine1102036, zéro tirage. Géométrie, masse, matériaux, propriétés, RBE3 et assemblages A09 BASE_FINE conservés. La nouvelle scène complète uniquement le domaine des contacts extérieurs et remet la façade devant le nez. Contact radôme lui-même hérité ; auto-contact de l’ensemble de l’avion absent. Radôme TYPE51/TYPE19 sandwich LAW25 de référence, sans reconstruction historique démontrée, écrasement de cœur ni délamination. Aucun transfert de rupture/érosion ; températures, incendie et intérieur complet de la tour absents.

Stfac1 est un candidat numérique hérité ; son bon bilan dans le témoin A10 contraint1D n’est pas une qualification pour l’avion. Les facteursdt_scale0,1/0,05/0,025 sont des multiplicateurs du pas stable natif, pas des pas en millisecondes. Les horizons identiques commencent tous de l’avion intact. Le dernier raffinement conditionnel est décidé sur l’échec sauvegardé du critère énergétique, sans modifier de seuil, de matériau ni de masse.

Seuils numériques hérités : masse1e-6 relative, masse ajoutée1e-9, énergie globale0,5%K0 ; énergie locale |résidu|≤5% énergie générée+1000J dès énergie générée>1000J ; impulsion/appuis10N·s+2%impulsion, demi-pas5%impulsion/10%énergie générée. Domaine matériau : déformation plastique métal≤0,1, diagnostic contrainte des faces radôme≤référence déclarée, zéro plasticité radôme. Les budgets globaux peuvent réussir alors que le budget local échoue : ils sont publiés séparément.

## 5. Résultats dérivés

|Cas|Fin native ms|Jx façade N·s|Énergie générée J|Résidu final J|Max résidu absolu J|Critères échoués|
|---|---:|---:|---:|---:|---:|---|
{table}

|Demi-pas|Δimpulsion %|Δénergie générée %|Critères impulsion/énergie|
|---|---:|---:|---|
{comps}

Le dernier cas donne |résidu final|/énergie générée≈{100*abs(last['final_energy_residual_J'])/max(last['final_generated_energy_J'],1e-30):.3f}%. La constance des impulsions sous raffinement ne suffit donc pas à qualifier le contact. Maximum d’erreur indépendante de variation duKE translationnel≈{last['maximum_nodal_translation_energy_change_error_J']:.3f}J ; erreur indépendante de quantité de mouvement≈{last['maximum_nodal_momentum_change_error_Ns']:.6f}N·s. Les limites d’arrondi et de décalage temporel restent présentes ; aucun terme manquant n’est inventé pour fermer le bilan.

KE+RKE global+IE+hourglass+spring+énergies de contact sont additionnés une seule fois, puis travail externe déduit. Le travail plastique est déjà contenu dansIE et n’est pas rajouté. Le RKE par pièce et les inerties du sandwich restent non qualifiés pour un ledger local ; les diagnostics A10 sont préservés. REAC brut représente l’impulsion cumulée confirmée A10, sans réintégration comme force.

États natifs dansr0/*/verified_states_SI.npz ; bilans dansbalance_history_SI.npz ; reconstruction nodale dansindependent_native_mass_diagnostics_SI.npz ; preuves dansnative_mass_reader_proofs.json ethistory_recovery.json. Visualisation hors ligne visualisation/premier_contact.html : déplacements natifs×1, lecture artificiellement ralentie, temps physique affichéms. Figure vectorielle ReportLab visualisation/bilans_et_nez.svg. Données et syntaxe vérifiées ; aperçu GUI non vérifié, serveur local et protocolefile: refusés par les outils. Aucune animation n’est une validation physique.

Temps cumulé des étapes natives et convertisseurs : {sec:.3f}s, CPU2threads, pasGPU. Une simple extrapolation linéaire des durées Engine vers1s donne un ordre de grandeur de plusieurs dizaines à plus de cent heures selon le facteur de pas, sans prédire le coût après déformation. Aucun calcul de plusieurs heures n’a été lancé.

## 6. Contradictions, informations manquantes et suite

Le déficit persiste sous raffinement temporel et dépasse le seuil local déclaré. Sa cause n’est pas démontrée ; effets du contact composite, inerties/énergies LAW25/TYPE19, décalages des canaux et discrétisation doivent être discriminés. L’essai de convergence spatiale A10 reste manquant. La direction A11 initiale a été réorientée explicitement par la demande utilisateur vers la scène du Boeing et son premier contact ; ce changement ne transforme pas les contrôles manquants en résultats acquis.

{NEXT}

Le deuxième agent dispose d’un prompt et de quatre dossiers propres aircraft_a11_boeing_parallel ; il n’a pas été lancé ni ses résultats supposés livrés par l’agent principal. État/registre restent gérés ici. Une intégration ultérieure devra conserver ses erreurs, contrôler mass/CG/inerties et faire l’objet d’une nouvelle déclaration.

Impact/écrasement historiques non qualifiés ; localisation en flexion après fracture complète non validée ; température imposée distincte d’un incendie calculé ; tests numériques distincts d’une validation de l’effondrement réel ; Blender reste une visualisation. Publication A08+A09 déjà vérifiée. A10+A11 constituent la prochaine paire de diagnostics vérifiables, avec tous les critères échoués ; aucunX/Yoremi.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Passation compacte AIRCRAFT-A11 → A12

Lire AGENTS.md, harness/state.json, cette passation et harness/publication_cycle.json. État courant prioritaire. A11 terminée comme diagnostic du nez : {len(rows)} nouveaux Engine, zéro ancien relancé. Résultats authoritative_review.json, rapport_aircraft_a11.md, initial_stage_review.json danswtc1_simulation_v8/output/aircraft_a11/ ; déclaration data/aircraft_a11_predeclaration.json. Graine1102036, zéro tirage ; CPU2threads, pasGPU.

Scène avion intact A09 BASE_FINE, façade déplacée[-15468,6,0,0]mm pour annuler le témoin moteurs ; face avantx=-50mm, contact exteriorgap5mm, vitessehypothèse[-200,5,2]m/s. Contact des peaux/radôme + nacelle/fan/core, domaines disjoints, géométrie/masses/matériaux/RBE3 inchangés. Pas de rupture/érosion, écrasement de cœur/délamination ni auto-contact général. Nez contact≈0,225ms, aucun contact moteurs/ailes dans0,4ms. Fenêtre=0,0004s : aucune première seconde ni traversée historique.

Libre contrôlé. Dernier contact{s['selected_short_case']} : fin{last['actual_main_end_time_ms']:.9f}ms ; Jx{last['final_contact_impulse_Ns'][0]:.6f}N·s ; énergie générée{last['final_generated_energy_J']:.6f}J ; résidu final{last['final_energy_residual_J']:.6f}J. Raffinement temporel conserve l’impulsion mais ne ferme pas le budget local : critère5%générée+1000J échoué, passage1ms non autorisé par les critères. Ne pas élargir le seuil ni ajouterRKE pour fermer. dt_scale est un multiplicateur, pas un pasms. REAC natif brut=impulsion cumulée A10, ne pas réintégrer. CSV vérifiés contreT01 binaire ; états/masses/KE/impulsion indépendants sauvegardés. Toutes tentatives et erreurs conservées, {n} anciens fichiers épinglés inchangés.

{NEXT}

Prompt parallèle : harness/handoffs/WTC1_A11_PARALLEL_BOEING_PROMPT.md. Agent utilisateur éventuellement en cours : ne pas supposer ses résultats. Ses quatre dossiers aircraft_a11_boeing_parallel sont séparés ; seul agent principal intègre et modifieétat/registre/cadence. Visualisation native horsligne : output/aircraft_a11/visualisation/premier_contact.html, bilanSVG ; ouverture automatique refusée, rendu GUI non vérifié. Temps/ms et déplacement×1 explicites.

PublicationA08+A09 vérifiée, ne pas republier. Vérifier cycle local pour paireA10+A11 et preuve distante après publication. AucunX/Yoremi. PréserverV11F/V11R ; V11S/I02I-M différées. Aucun scan archive. Impact/écrasement et effondrement historiques non qualifiés ; température imposée≠incendie calculé ; Blender visualisation.
''',encoding='utf-8')
    files=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a11.py',ROOT/'wtc1_simulation_v8/scripts/review_aircraft_a11.py',ROOT/'wtc1_simulation_v8/scripts/visualize_aircraft_a11.py',Path(__file__),HANDOFF,ROOT/'harness/handoffs/WTC1_A11_PARALLEL_BOEING_PROMPT.md'];files=sorted(set(files));dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]});print({'prepared':True,'manifest_files':len(files),'old_preserved':n,'seconds_calculated':False},flush=True)

def register():
    guard();n=checkrows(read(OUT/'artifact_manifest.json')['files']);assert REPORT.exists() and HANDOFF.exists();state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');assert state['current_iteration']=='AIRCRAFT-A10' and cycle['pending_iterations']==['AIRCRAFT-A10'];assert harness()['Status']=='PASS';s=read(OUT/'authoritative_review.json');t=now()
    rec={'experiment_id':'WTC1-AIRCRAFT-A11','registered_at':t,'status':'completed_whole_aircraft_nose_first_contact_diagnostic_with_failed_local_energy_gate','configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'authoritative_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'integrity_only_pass':s['integrity_only_pass'],'all_declared_checks_pass':s['all_declared_checks_pass'],'branch_iteration_count':11,'whole_aircraft_iteration_count':10,'main_engine_jobs':s['main_engine_jobs'],'old_solver_reruns':0,'old_files_preserved':read(OUT/'preservation_verification.json')['files'],'max_horizon_ms':max(r['actual_main_end_time_ms'] for r in s['cases']),'nose_contact_onset_ms':.2250279,'seconds_impact_calculated':False,'local_energy_ledger_qualified':False,'spatial_convergence_qualified':False,'native_RKE_ledger_qualified':False,'contact_option_transferred_as_qualified':False,'physical_impact_qualified':False,'engine_crushing_qualified':False,'NIST_outcomes_used_as_target':False,'next_iteration':'AIRCRAFT-A12'}
    reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A11',next_iteration='AIRCRAFT-A12',current_status=rec['status'],next_objective=NEXT,updated_at=t);state['aircraft_a11_key_results']=rec;state['validated_artifacts'].update(aircraft_a11_report=rel(REPORT),aircraft_a11_results=rel(OUT/'authoritative_review.json'),aircraft_a11_handoff=rel(HANDOFF));state['user_steering_2026_10_07']={'request':'Boeing construction, start first impact seconds if feasible; second-agent prompt','implemented':'new nose-first coupled aircraft scene and first0.4ms contact, local energy failure retained','parallel_prompt':'harness/handoffs/WTC1_A11_PARALLEL_BOEING_PROMPT.md','next':'AIRCRAFT-A12'};cycle.update(pending_iterations=['AIRCRAFT-A10','AIRCRAFT-A11'],pending_count=2,next_publication_after='Verified A10+A11 diagnostics ready for authorized pair publication; failures retained',updated_at=t);dump(ROOT/'harness/state.json',state);dump(ROOT/'harness/publication_cycle.json',cycle);verify(write=True,files_verified=n)

def verify(write=False,files_verified=None):
    guard();n=files_verified or checkrows(read(OUT/'artifact_manifest.json')['files']);before=read(OUT/'before_state.json');st=read(ROOT/'harness/state.json');prefix=(OUT/'before_registry.jsonl').read_bytes();reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness();cy=read(ROOT/'harness/publication_cycle.json');protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_files_verified':True,'old_preservation_pass':read(OUT/'preservation_verification.json')['pass'],'prior_results_and_policies_preserved':all(st[k]==before[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A11','state_route':st['current_iteration']=='AIRCRAFT-A11' and st['next_iteration']=='AIRCRAFT-A12','publication_pair_pending_or_verified':cy['pending_iterations']==['AIRCRAFT-A10','AIRCRAFT-A11'] or (cy['pending_count']==0 and cy['last_published_iteration']=='AIRCRAFT-A11'),'harness_pass':v['Status']=='PASS','failures_retained':not read(OUT/'authoritative_review.json')['all_declared_checks_pass'],'report_handoff_exist':REPORT.exists() and HANDOFF.exists()};out={'pass':all(checks.values()),'created_utc':now(),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':v,'physical_impact_qualified':False,'seconds_impact_calculated':False,'next_iteration':'AIRCRAFT-A12'};assert out['pass'],out
    if write:dump(OUT/'publication_verification.json',out)
    print(json.dumps(out,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
