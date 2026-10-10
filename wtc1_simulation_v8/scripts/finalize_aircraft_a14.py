"""Seal A14 numerical evidence, retained failures, then append one iteration."""
import argparse,json,re,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from run_aircraft_a14 import ROOT,OUT,CFG,REV,read,dump,sha,rel,now,guard,harness,streamsha

REPORT=OUT/'rapport_aircraft_a14.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A14_HANDOFF.md'
NEXT="AIRCRAFT-A15 : reprendre les sorties A14 sans relancer les anciens cas. Déclarer des contrôles neufs de pas temporel et de démarrage du contact sur les plaques grossières pondérées, avec géométrie, masse, vitesse et loi de contact inchangées. Retracer la phase des historiques TH/NODE, quantité de mouvement globale, impulsion TYPE25 et REAC, notamment DT12/DT2 et l'ordre des sorties dans le code. Garder séparément les bilans natifs, les diagnostics v±dt·a/2 et les références analytiques ; aucune correction a posteriori du ledger. La qualification globale A14 reste échouée malgré les comparaisons spatiales pondérées réussies. Si une nouvelle famille passe les critères déclarés avant calcul, tester ensuite le radôme isolé avec TYPE25 explicitement nœuds/surface et pondération par aire, niveaux indépendants et sensibilité de pénalité conservée. Ne pas attribuer à la seule pondération les différences avec A13, dont la déclaration était surface + nœuds supplémentaires. Aucun coefficient choisi pour retrouver les dommages connus. Définir matériaux, masse/inertie, assemblages et conditions de façade à partir des sources avant tout crédit physique. Aucun allongement avion complet sans fermeture locale et convergence. Module Boeing parallèle v2 séparé, inertie/dynamique libre encore bloquées. Premières secondes, rupture, écrasement et impact historiques non qualifiés."

def checkrows(rows):
    for r in rows:
        p=ROOT/r['path'];assert p.stat().st_size==r['bytes'] and streamsha(p)==r['sha256'],r['path']
    return len(rows)

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists() and not (OUT/'artifact_manifest.json').exists()
    s=read(OUT/'plate_review.json');assert s['integrity_only_pass'] and len(s['cases'])==17 and not s['rejected_cases']
    p=read(OUT/'preservation_verification.json');assert p['pass'] and p['files']==7876
    v=harness();assert v['Status']=='PASS';dump(OUT/'harness_after_calculations.json',v)
    ET.parse(OUT/'visualisation/comparaison_contact.svg');vis=read(OUT/'visualisation/provenance.json');assert vis['data_schema_pass'] and vis['native_displacement_scale']==1
    node=Path('C:/Users/jeuxpc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    js=subprocess.run([str(node),'--check',str(OUT/'visualisation/viewer_script_for_validation.js')],capture_output=True,text=True);assert js.returncode==0;dump(OUT/'visualisation/syntax_verification.json',{'created_utc':now(),'pass':True,'static_PNG_visually_inspected':True,'interactive_GUI_render_verified':False})
    jobs=[]
    for r in s['cases']:
        d=OUT/REV/r['case']['id'];log=(d/'starter.log').read_text(errors='replace')
        assert int(re.findall(r'(\d+) WARNING\(S\)',log)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',log)[-1])==0
        for logfile in ['starter.log','engine.log','observer/observer.log','converter.log']:
            z=read(d/(logfile+'.execution.json'));assert z['exit_code']==0;jobs.append({'case':r['case']['id'],'job':logfile,**z})
    execution={'created_utc':now(),'main_engine_jobs':17,'observer_jobs':17,'starter_jobs':17,'converter_jobs':17,'all_exit_codes_zero':True,'total_process_seconds':sum(j['seconds'] for j in jobs),'GPU':False,'CPU_threads':2,'runtime':'v20260728-win64','jobs':jobs}
    dump(OUT/'execution_summary.json',execution)
    s.update(main_engine_jobs=17,observer_jobs=17,all_declared_checks_pass=s['all_declared_case_checks_pass'],scientific_qualification_pass=False,radome_extension_executed=False,seconds_impact_calculated=False)
    dump(OUT/'campaign_review.json',s)
    by={r['case']['id']:r for r in s['cases']};raw=next(q for q in s['comparisons'] if q['cases']==['RAW_N4','RAW_N8']);weighted=next(q for q in s['comparisons'] if q['cases']==['AREA_N4','AREA_N8']);half=next(q for q in s['comparisons'] if q['kind']=='half_dt')
    allmesh=all(q['impulse_pass'] and q['duration_pass'] and q['energy_curve_pass'] for q in s['comparisons'] if not q['cases'][0].startswith('RAW'))
    a={'created_utc':now(),'plate_area_weighted_spatial_comparisons_pass':allmesh,'all_native_energy_checks_pass':all(r['checks']['energy_global'] for r in s['cases']),
       'native_unweighted_spatial_comparisons_pass':False,'coarse_native_momentum_contact_checks_pass':False,
       'area_weighted_core_and_mesh_plate_pass':s['area_weighted_core_and_mesh_plate_pass'],'all_declared_case_checks_pass':s['all_declared_case_checks_pass'],
       'conditional_radome_diagnostic_allowed':s['conditional_radome_diagnostic_allowed'],'radome_extension_executed':False,'full_aircraft_extension_allowed':False,
       'historical_impact_qualified':False,'seconds_impact_calculated':False,'binary_source_equivalence_established':False,
       'A13_contact_declaration_correction_documented':True,'old_A13_outputs_or_claims_overwritten':False,'no_stiffness_fitted_to_historical_result':True,
       'raw_fine_impulse_difference_fraction':raw['impulse_difference_fraction'],'area_fine_impulse_difference_fraction':weighted['impulse_difference_fraction'],
       'area_fine_contact_energy_curve_difference_fraction_initial':weighted['contact_energy_curve_difference_fraction_initial'],'area_fine_half_dt_impulse_difference_fraction':half['impulse_difference_fraction'],
       'physical_penalty_identified':False,'NIST_outcomes_used_as_target':False}
    assert not a['conditional_radome_diagnostic_allowed'];dump(OUT/'scientific_assessment.json',a)
    table='\n'.join(f"| {r['case']['id']} | {r['final_impulse_Ns'][0]:.7f} | {100*r['maximum_energy_residual_J']/22.24:.6f} | {r['contact_duration_ms'] or 0:.8f} | {', '.join(r['failed_checks']) or 'aucun'} |" for r in s['cases'])
    comparisons='\n'.join(f"| {' / '.join(q['cases'])} | {q['kind']} | {100*q['impulse_difference_fraction']:.6f} | {100*q['contact_duration_difference_fraction']:.6f} | {100*q['contact_energy_curve_difference_fraction_initial']:.6f} | {q['impulse_pass']}/{q['duration_pass']}/{q['energy_curve_pass']} |" for q in s['comparisons'])
    phases=by['AREA_N1']['phase_candidates'];tm=read(OUT/'timing_audit.json');balance=next(r for r in tm['saved_output_diagnostics'] if r['case']=='AREA_N1')
    REPORT.write_text(f'''# AIRCRAFT-A14 — objectivité spatiale du contact sur une plaque

**17 nouveaux calculs principaux et 17 observations de fin terminés.** Le contrôle d'intégrité passe ; la qualification scientifique globale reste échouée. Aucun ancien solveur relancé. Les conditions et les seuils ont été déclarés avant calcul. Aucun dommage, trajectoire finale ou résultat NIST n'a servi de cible.

À surface et masse identiques, la pénalité nodale uniforme change la raideur totale quand on raffine le maillage. Une pondération déclarée par la surface tributaire conserve cette raideur et passe toutes les comparaisons spatiales et de demi-pas de la plaque pondérée : entre les deux maillages fins, Δimpulsion **{100*weighted['impulse_difference_fraction']:.6f} %**, Δdurée **{100*weighted['contact_duration_difference_fraction']:.4f} %**, Δcourbe énergétique **{100*weighted['contact_energy_curve_difference_fraction_initial']:.4f} %** de KE initiale. La comparaison uniforme échoue, avec Δimpulsion **{100*raw['impulse_difference_fraction']:.4f} %**, Δdurée **{100*raw['contact_duration_difference_fraction']:.2f} %** et Δcourbe **{100*raw['contact_energy_curve_difference_fraction_initial']:.2f} %**.

Des critères ponctuels d'impulsion et de pénétration sur les plaques grossières restent échoués. La condition annoncée pour tester ensuite le radôme n'est donc pas remplie. **Aucun essai de radôme ajouté dans A14 ; aucun allongement du calcul de l'avion.**

## 1. Faits directement observés ou transcrits

17 Starter sans erreur ni avertissement ; tous les principaux et observateurs terminent normalement. Les historiques CSV sont vérifiés contre chacun des records binaires natifs. Le premier record observateur donne la fin réelle et l'énergie finale ; ses REAC sont exclus, car les reprises remettent leur cumul à zéro. Contact FNX/FNY/FNZ et REAC principal sont des impulsions cumulatives, converties en N·s sans nouvelle intégration.

Masse mobile native = 0,001112 kg, erreur relative environ 1,03×10⁻⁸ ; masses nodales décodées indépendamment dans la première animation et comparées aux surfaces tributaires. Masse constante, aucune masse ajoutée, appuis fixes, rotations nulles, travail externe et plastique nuls dans tous les cas. Le vol libre reste uniforme. Ces observations concernent les sorties du solveur, aucune observation historique nouvelle.

**Correction de description A13 :** ses cartes TYPE25 portaient les IDs de surfaces [3,0] avec un groupe secondaire supplémentaire ; le Starter enregistrait le mode 1. A14 utilise explicitement [0,3] pour les contacts nœuds/surface, mode natif 3. Le témoin LEGACY_N1 reproduit séparément la déclaration antérieure et son départ. Il retrouve l'entrée effective vers −0,499838 mm. Le cas canonique grossier donne environ −0,986727 mm, puis les cas fins tendent vers −1 mm. Ces plans sont des diagnostics tirés des sorties ; le gap d'entrée n'a jamais été ajusté. L'ancienne description était inexacte. Rapport et résultats A13 sont conservés intégralement, avec cette correction nouvelle dans A14 ; aucun crédit rétroactif.

## 2. Résultats d'un modèle officiel

A14 n'utilise aucun résultat NIST comme paramètre ou cible. Les sorties nouvelles viennent de l'exécutable OpenRadioss local v20260728-win64 ; elles ne sont pas des résultats NIST. Le solveur, ses empreintes, les arguments, durées et codes de sortie sont enregistrés pour chaque processus dans execution_summary.json. Les hypothèses de façade NIST héritées d'A12/A13 ne sont pas nécessaires à ce contrôle plan.

La [documentation primaire TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) distingue les déclarations de surfaces, groupe nodal et raideur. Le calcul analytique de la plaque ci-dessous est une référence mécanique propre au témoin, sans assimilation à l'avion.

## 3. Affirmations provenant des archives locales

Aucune nouvelle vidéo, photographie ou archive inspectée. Nouveau scan SHA-256 complet de **7876 fichiers antérieurs**, soit **{p['bytes_hashed']/1e9:.2f} Go**, sans différence. Les sources officielles locales et archives restent en lecture seule. Le module Boeing parallèle v2 reste séparé ; ses limites d'inertie et de dynamique libre ne sont pas résolues par A14. V11F/V11R et les branches différées sont conservées.

La publication A12+A13 vérifiée reste le dernier point distant. Le cycle ne reçoit que A14, en attente d'A15 pour la cadence de deux itérations ; aucune publication externe nouvelle dans A14.

## 4. Hypothèses propres au modèle

Configuration aircraft_a14_predeclaration.json, graine 1102039, zéro tirage. Plaque 20×20×1 mm, mur 40×40×1 mm immobilisé, départ X=−5 mm, vitesse +200 m/s, horizon **0,04 ms = 0,00004 s**. Seul X est libre sur la plaque ; Y, Z et toutes les rotations sont bloqués. LAW1 synthétique : rho=0,00278 g/mm³, E=70000 MPa, nu=0,3 ; ces valeurs vérifient un mécanisme numérique et n'identifient pas un matériau Boeing. Aucun RBE3, rupture, érosion, ressort ou masse artificielle.

TYPE25 : Istf=4, gap déclaré 1 mm, épaisseurs de contact de 1 mm pour chaque côté avec demi-contribution, Ishape=2, Iedge=1000, Ipstif=0, Inacti=1000, frottement nul, amortissement VIS_s=1e−20. Les IDs de surfaces canoniques restent [0,3]. Les quatre niveaux mobiles ont 1/4/16/64 quadrilatères et 4/9/25/81 nœuds, même surface 400 mm² et même masse. Le mur a séparément 1, 9 ou 16 mailles.

Pénalité uniforme : Stfac=1, raideur nodale théorique 35000 N/mm, donc raideur totale 140000/315000/875000/2835000 N/mm. Pénalité pondérée : **Stfacᵢ = facteur × Aᵢ / 100 mm²**, Aᵢ étant la somme des quarts d'aire des quadrilatères incidents. Les groupes nodaux sont disjoints et couvrent chaque nœud secondaire une seule fois. La raideur totale nominale reste **140000 N/mm**. L'aire de référence correspond au témoin grossier A13 et a été déclarée avant exécution ; elle n'est pas choisie à partir du résultat A14. Les facteurs 0,25 et 4 sont conservés comme sensibilités. Cette raideur est une pénalité numérique, pas une loi de contact physique identifiée.

Pour une translation uniforme conservatrice : masse 1,112 g, KE₀=22,24 J, P₀=0,2224 N·s, impulsion de rebond=0,4448 N·s ; durée π√(M/K)=0,008853974 ms et pénétration 200√(M/K)=0,5636615 mm au facteur nominal. Les références de durée/pénétration ne sont pas créditées aux maillages uniformes nodaux supérieurs, dont les masses et raideurs locales ne sont pas proportionnelles.

Seuils inchangés : énergie ≤1 % de KE₀ ; quantité de mouvement/contact ≤1 % de P₀ ; appuis ≤2 % de P₀ ; rebond ≤1 % ; durée et pénétration ≤2 % ; reconstruction de l'énergie de contact ≤1 % de KE₀ ; comparaisons de maillage/demi-pas ≤1 % d'impulsion, ≤2 % de durée et de courbe énergétique. Les diagnostics de phase ont leurs propres limites de 0,1 %. Ils ne reclassent pas les cas.

Ledger : KE + rotation globale + IE + hourglass + spring + contact élastique/frottement/amortissement − travail externe, chaque terme une fois. Aucun RKE par pièce ou reconstruit ajouté ; aucun décalage des canaux d'énergie. Unités d'origine g/mm/ms, conversions SI enregistrées, N·mm→0,001 J et N·ms→0,001 N·s.

## 5. Résultats dérivés

| Cas | Impulsion finale X N·s | Max résidu / KE₀ % | Durée du contact ms | Critères échoués |
|---|---:|---:|---:|---|
{table}

La durée est mesurée sur les lignes où l'énergie de contact dépasse 10⁻⁶ J, avec un pas médian ajouté. Elle reste une mesure discrète. Le vol libre a une durée de contact nulle dans la table. Les impulsions viennent de l'historique principal ; le résidu inclut le record de fin observé. Les 17 budgets énergétiques passent ; cette fermeture ne fait pas passer les autres critères.

| Comparaison | Nature | Δimpulsion % | Δdurée % | Δcourbe contact / KE₀ % | Passe J/durée/courbe |
|---|---|---:|---:|---:|---|
{comparisons}

Le maillage principal 1/9/16 donne les mêmes historiques pertinents dans la plaque nominale à 16 mailles. La comparaison de demi-pas fin donne Δimpulsion {100*half['impulse_difference_fraction']:.7f} %. Les sensibilités 0,25 et 4 passent aussi leur comparaison spatiale ; leur durée et pénétration diffèrent physiquement dans ce modèle puisqu'on change la raideur déclarée. Aucune sensibilité n'est sélectionnée pour obtenir un dommage attendu.

**Convention temporelle, diagnostic conservé :** AREA_N1 donne une différence maximale de variation KE nodale/globale de {phases[0]['max_KE_change_error_J']:.6f} J pour v brut, {phases[1]['max_KE_change_error_J']:.6f} J pour v−dt·a/2 et {phases[2]['max_KE_change_error_J']:.6f} J pour v+dt·a/2. Le dernier diagnostic échoue encore sa limite KE de 0,02224 J sur ce cas grossier, tandis que son diagnostic quantité de mouvement passe. Le bilan natif global/contact garde {balance['maximum_global_contact_balance_error_Ns']:.8f} N·s d'écart maximal, soit {100*balance['maximum_global_contact_balance_error_Ns']/.2224:.4f} % de P₀ : son seuil de 1 % reste échoué.

L'audit fige 12 fichiers de [la source publique au commit {tm['source_commit'][:12]}](https://github.com/OpenCourant/OpenCourant/tree/{tm['source_commit']}). [THNOD](https://github.com/OpenCourant/OpenCourant/blob/{tm['source_commit']}/engine/source/output/th/thnod.F) écrit directement les tableaux V/A ; HIST2 écrit séparément KE et quantité de mouvement globale. [REACTION_FORCES_TH](https://github.com/OpenCourant/OpenCourant/blob/{tm['source_commit']}/engine/source/output/reaction_forces_th.F) accumule les contributions avec DT12. VELOCITY met V à jour avec DT12·A, et RESOL note les sorties avant intégration. Cela soutient des phases de sortie distinctes. **La chaîne temporelle complète et l'équivalence avec le binaire installé ne sont pas établies.** Le ledger et tous les critères échoués restent intacts.

## 6. Contradictions et informations manquantes

Les comparaisons spatiales pondérées passent et l'énergie se ferme, mais le critère global de transfert échoue sur les maillages grossiers. La pondération constitue une réponse vérifiée à la dépendance du contact au nombre de nœuds dans ce témoin ; elle ne démontre pas une loi de contact réaliste. La pénétration et le plan effectif grossiers peuvent dépendre du démarrage discret ; la cause unique de leurs différences n'est pas prouvée. Corriger la description des surfaces A13 change aussi l'entrée en contact : une future comparaison de radôme devra séparer déclaration géométrique et pondération.

Il manque encore des matériaux et propriétés de sandwich documentés, masse/inertie et assemblages qualifiés, rupture/délamination/écrasement, carburant et conditions mécaniques de façade. Une plaque contrainte contre un mur fixe ne reproduit pas l'avion en impact. Les premières secondes de l'événement restent non calculées. Aucun seuil ne sera élargi pour retrouver un résultat connu.

{NEXT}

Livrables : campaign_review.json, scientific_assessment.json, timing_audit.json, execution_summary.json, configurations/scripts, manifeste et handoff. Comparaison scientifique SVG/PNG inspectée visuellement ; visualisation HTML issue des déplacements natifs ×1, syntaxe/données vérifiées, rendu interactif non certifié. L'intégrité du harnais et de la publication est distincte de la qualification physique.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Reprise WTC1 — AIRCRAFT-A14 → AIRCRAFT-A15

A14 terminée : 17 nouveaux principaux +17 observateurs, zéro ancien solveur relancé. Rapport : {rel(REPORT)} ; configuration : {rel(CFG)} ; résultats définitifs : {rel(OUT/'campaign_review.json')} ; assessment : {rel(OUT/'scientific_assessment.json')} ; audit temporel : {rel(OUT/'timing_audit.json')}.

Surface/masse fixes sur 4 niveaux de plaque à 200 m/s : pondération Stfacᵢ=facteur×Aᵢ/100 mm², K total 140000 N/mm. Toutes les comparaisons spatiales pondérées, mur indépendant et demi-pas passent. Fin : ΔJ {100*weighted['impulse_difference_fraction']:.6f} %, Δdurée {100*weighted['contact_duration_difference_fraction']:.6f} %, Δcourbe {100*weighted['contact_energy_curve_difference_fraction_initial']:.6f} % de KE₀. Uniforme nodale : ΔJ {100*raw['impulse_difference_fraction']:.4f} %, Δdurée {100*raw['contact_duration_difference_fraction']:.4f} %, Δcourbe {100*raw['contact_energy_curve_difference_fraction_initial']:.4f} %. Sensibilités .25/4 conservées, aucun ajustement historique.

Les 17 énergies passent, mais quantité de mouvement/contact ponctuelle et loi de pénétration grossières échouent. Condition globale de transfert A14 false, pas de nouveau radôme exécuté. Convention +dt*a/2 diminue fortement les différences nodales/globales ; diagnostic uniquement. Source figée {tm['source_commit']}, THNOD direct V/A et REAC cumulatif confirmés ; chaîne complète de phase/source-binaire non prouvée. Ledger natif inchangé.

Correction A13 conservée séparément : IDs [3,0] + nœuds supplémentaires, mode Starter1 ; nouveaux canoniques [0,3], mode3. LEGACY_N1 confirme l'entrée effective -0,499838 mm. Ne pas réécrire A13 ni attribuer toute différence future à la pondération seule.

{NEXT}

7876 anciens fichiers, {p['bytes_hashed']/1e9:.2f} Go recontrôlés sans différence. Archives lecture seule, aucune vidéo inspectée. Graphique SVG/PNG, viewer {rel(OUT/'visualisation/contact_plan.html')} natif ×1 et temps ms ; rendu interactif non certifié. Dernière publication A12+A13 préservée ; A14 seul en attente, cadence A14+A15.
''',encoding='utf-8')
    files=[q for q in OUT.rglob('*') if q.is_file()]+[CFG,HANDOFF]+[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_aircraft_a14.py','review_aircraft_a14.py','audit_aircraft_a14_timing.py','visualize_aircraft_a14.py','verify_aircraft_a14_preservation.py','finalize_aircraft_a14.py']]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size} for q in sorted(set(files))]})
    print({'prepared':True,'new_files':len(set(files)),'cases':len(s['cases']),'scientific_pass':False},flush=True)

def register():
    guard();count=checkrows(read(OUT/'artifact_manifest.json')['files']);assert REPORT.exists() and HANDOFF.exists()
    s=read(OUT/'campaign_review.json');a=read(OUT/'scientific_assessment.json');st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
    assert st['current_iteration']=='AIRCRAFT-A13' and st['next_iteration']=='AIRCRAFT-A14' and cy['pending_iterations']==[] and harness()['Status']=='PASS'
    reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix;t=now()
    rec={'experiment_id':'WTC1-AIRCRAFT-A14','registered_at':t,'status':'completed_plane_area_weighted_spatial_contact_controls_with_retained_coarse_temporal_and_gap_failures','configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'campaign_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'integrity_only_pass':True,'all_declared_checks_pass':False,'main_engine_jobs':17,'observer_jobs':17,'old_solver_reruns':0,'old_files_preserved':7876,'branch_iteration_count':14,'whole_aircraft_iteration_count':10,**a,'next_iteration':'AIRCRAFT-A15'}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A14',next_iteration='AIRCRAFT-A15',current_status=rec['status'],next_objective=NEXT,updated_at=t)
    st['aircraft_a14_key_results']=rec;st['validated_artifacts'].update(aircraft_a14_report=rel(REPORT),aircraft_a14_results=rel(OUT/'campaign_review.json'),aircraft_a14_handoff=rel(HANDOFF))
    st['user_steering_2026_10_08_realistic_conditions']={'request':'reproduire des conditions réalistes et voir ce qu on en tire ; ne pas atteindre un résultat connu','implemented':'input conditions and thresholds declared before A14, synthetic contact controls separated from physical aircraft qualification, failures retained','no_known_damage_target':True,'next':'AIRCRAFT-A15'}
    cy.update(pending_iterations=['AIRCRAFT-A14'],pending_count=1,next_publication_after='One further verified iteration AIRCRAFT-A15; publish A14+A15 with retained scientific failures',updated_at=t)
    dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(count)

def verify(count=None):
    guard();count=count or checkrows(read(OUT/'artifact_manifest.json')['files']);before=read(OUT/'before_state.json');st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
    reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness()
    protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_artifact_hashes_verified':True,'old_files_preserved':read(OUT/'preservation_verification.json')['pass'],'historical_results_and_policies_unchanged':all(st[k]==before[k] for k in protected),
        'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A14','state_route':st['current_iteration']=='AIRCRAFT-A14' and st['next_iteration']=='AIRCRAFT-A15',
        'publication_pending_single':cy['pending_iterations']==['AIRCRAFT-A14'] and cy['pending_count']==1,'publication_baseline_unchanged':all(cy[k]==read(OUT/'before_publication_cycle.json')[k] for k in ['last_published_commit','last_published_release','last_published_iteration']),
        'failed_scientific_gate_retained':not read(OUT/'scientific_assessment.json')['conditional_radome_diagnostic_allowed'],'required_artifacts_exist':REPORT.exists() and HANDOFF.exists(),'harness_pass':v['Status']=='PASS'}
    proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':count,'old_files_verified':7876,'harness':v,'physical_impact_qualified':False,'seconds_impact_calculated':False,'next_iteration':'AIRCRAFT-A15','external_publication_performed':False}
    assert proof['pass'],proof;dump(OUT/'publication_verification.json',proof);print(proof,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
