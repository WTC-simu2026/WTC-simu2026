"""Seal A16 implemented damage, retaining missing fracture physics and old failures."""
import argparse,json,re,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from run_aircraft_a16 import ROOT,OUT,CFG,PARENT,read,dump,rel,now,guard,harness,streamsha,failure
from run_aircraft_a04 import blocks

REPORT=OUT/'rapport_aircraft_a16.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A16_HANDOFF.md'
NEXT="AIRCRAFT-A17 : repartir du contact couplé et des sorties A15/A16 sans anciens solveurs relancés. La perte de résistance des peaux est maintenant native et l'historique au même pic est contrôlé. Elle ne constitue pas une fissure énergétique objective ni des fragments libres. Priorité à une représentation de séparation avec travail stocké/dissipé, surface de fissure et énergie indépendants du maillage, puis écrasement du cœur et liaisons réelles. Réutiliser la référence de traction-ouverture déclarée et les sources A06, ne pas transférer ORTHENERG rejetée ni augmenter G pour tolérer le maillage. Documenter les données physiques absentes ; toute nouvelle plage reste déclarée avant calcul et ne vise ni NIST ni une perforation connue. Contrôler la loi une seule famille nécessaire, puis revenir au même avion/façade avec coût borné. Résidus énergétiques, limites métalliques, convergence spatiale, carburant et conditions historiques restent à qualifier. Aucun état10ms hors domaine ne devient un état historique validé. Module parallèle séparé. Publication A14+A15 due, A16 en attente ; vérifier cette tâche indépendamment."

def checkrows(rows):
    for r in rows:
        p=ROOT/r['path'];assert p.stat().st_size==r['bytes'] and streamsha(p)==r['sha256'],r['path']
    return len(rows)

def effective_configuration():
    cfg=read(CFG);pg=read(PARENT/'generation.json')
    parent={b[0]:b for b in blocks((PARENT/(pg['name']+'_0000.rad')).read_text().splitlines()) if b[0] not in ['/BEGIN','/TITLE','/END']}
    rows=[]
    for c in cfg['execution']['cases']:
        d=OUT/'r0'/c['id'];g=read(d/'generation.json');deck=d/(g['name']+'_0000.rad');actual={b[0]:b for b in blocks(deck.read_text().splitlines()) if b[0] not in ['/BEGIN','/TITLE','/END']}
        assert set(actual)==set(parent)|{'/FAIL/ORTHSTRAIN/4'} and all(actual[k]==v for k,v in parent.items())
        assert actual['/FAIL/ORTHSTRAIN/4']==failure(c['transition_fraction'])
        job=read(d/'engine.log.execution.json');assert job['timeout_s']==cfg['execution']['engine_timeout_s']==1200
        rows.append({'case':c['id'],'deck':rel(deck),'sha256':streamsha(deck),'unchanged_parent_mechanical_cards':True,'only_new_mechanical_card':'/FAIL/ORTHSTRAIN/4','transition_fraction':c['transition_fraction'],'parent':rel(PARENT),'engine_timeout_s':job['timeout_s'],'external_contact_keywords':[k for k in actual if k.startswith('/INTER/TYPE25/')],'prescribed_aircraft_motion':False})
    dump(OUT/'effective_configuration.json',{'created_utc':now(),'pass':True,'immutable_predeclaration_retained':True,'decks_compared_to_actual_parent':True,'cases':rows,'inherited_metadata_overridden_by_A16':{'sandwich.failure_disabled':'LAW25 built-in failure remains disabled; the new independent FAIL/ORTHSTRAIN/4 is enabled on skins','failure_transfer_enabled':'inherited qualification/transfer false, not absence of the new damage card','scene_changes.rupture_erosion':'no whole-shell erosion, but native skin resistance damage is active','declared_mechanism_controls.material_failure':'legacy diagnostic context; A16 damage section governs the added skin law','local_control_scope':'legacy engine-only context; the four exterior whole-aircraft contacts remain active as in A15','stages.execution':'legacy600s narrative; A16 execution.engine_timeout_s and actual execution records specify1200s','parent':'legacy A11 ancestor; actual direct parent is the cached A15 intact start deck'},'physical_impact_qualified':False})

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists() and not (OUT/'artifact_manifest.json').exists();s=read(OUT/'campaign_review.json');w=read(OUT/'witness_review.json');p=read(OUT/'preservation_verification.json');assert s['cases'] and w['mechanical_gate_pass'] and p['pass'] and p['files']==9052
    assert all(read(OUT/'r0'/r['case']['id']/'damage_end_reader_verification.json')['pass'] for r in s['cases'])
    effective_configuration()
    v=harness();dump(OUT/'harness_after_calculations.json',v);assert v['Status']=='PASS'
    ET.parse(OUT/'visualisation/comparaison_impact.svg');vis=read(OUT/'visualisation/provenance.json');assert vis['data_schema_pass'] and vis['displacement_scale']==1 and vis['gzip_roundtrip_exact']
    node=Path('C:/Users/jeuxpc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe');j=subprocess.run([str(node),'--check',str(OUT/'visualisation/viewer_script_for_validation.js')],capture_output=True,text=True);assert j.returncode==0
    dump(OUT/'visualisation/syntax_verification.json',{'created_utc':now(),'pass':True,'static_PNGs_visually_inspected':['comparaison_impact.png','impact_dommage_natif.png'],'interactive_GUI_render_verified':False})
    jobs=[]
    for base,cases in [('w0',read(CFG)['witness']['cases']),('r0',read(CFG)['execution']['cases'])]:
        for c in cases:
            d=OUT/base/c['id']
            for log in ['starter.log','engine.log','observer/observer.log','converter.log']:
                fn=d/(log+'.execution.json')
                if fn.exists():jobs.append({'case':c['id'],'family':base,'job':log,**read(fn)})
    exe={'created_utc':now(),'witness_engine_jobs':4,'whole_engine_jobs':2,'completed_whole_engine_jobs':len(s['cases']),'observer_jobs':sum(j['job']=='observer/observer.log' for j in jobs),'total_process_seconds':sum(j['seconds'] for j in jobs),'all_exit_codes_zero':all(j['exit_code']==0 for j in jobs),'CPU_threads':2,'GPU':False,'runtime':'v20260728-win64','old_solver_reruns':0,'jobs':jobs};dump(OUT/'execution_summary.json',exe)
    a={'created_utc':now(),'whole_exploratory_damage_impacts_completed':len(s['cases']),'maximum_history_native_implementation_pass':w['mechanical_gate_pass'],'equal_peak_damage_growth_maximum':max(r['damage_growth_equal_peak'] for r in w['cases']),'native_damage_history_monotone_all':all(d['native_damage_maximum_history_monotone'] for d in s['damage']),'core_damage_zero_all':all(d['core_damage_zero'] for d in s['damage']),'native_logged_ply_failures':[d['native_logged_failed_plies'] for d in s['damage']],'integrity_only_pass':s['integrity_only_pass'],'global_energy_pass_all_completed':all(r['checks']['global_energy'] for r in s['cases']),'local_energy_pass_all_completed':all(r['checks']['local_energy'] for r in s['cases']),'metal_material_limits_all_pass':all(r['checks']['metal_material_domain'] and r['checks']['beam_material_domain'] for r in s['cases']),'all_retained_material_diagnostics_pass':all(r['checks']['metal_material_domain'] and r['checks']['beam_material_domain'] and r['checks']['radome_face_reference_domain'] for r in s['cases']),'physical_fracture_energy_qualified':False,'mesh_objective_fracture':False,'core_crushing_delamination_modelled':False,'topological_fragmentation':False,'physical_impact_qualified':False,'historical_impact_qualified':False,'seconds_impact_calculated':False,'old_ORTHENERG_failure_retained':True,'old_A11_A15_gates_retained':True,'NIST_outcomes_used_as_target':False,'no_material_or_contact_fit_to_damage':True,'parallel_module_integrated':False};dump(OUT/'scientific_assessment.json',a)
    results='\n'.join(f"| {r['case']['id']} | {r['end_ms']:.9f} | {r['last_main_contact_impulse_Ns'][0]/1000:.6f} | {r['maximum_facade_displacement_mm']:.3f} | {r['final_generated_energy_J']/1e6:.6f} | {r['final_energy_residual_J']/1000:.6f} | {'; '.join(r['failed_checks']) or 'aucun'} |" for r in s['cases'])
    damages='\n'.join(f"| {d['case']['id']} | {d['first_saved_skin_damage_ms']} | {d['first_saved_full_skin_failure_ms']} | {d['final_skin_counts']['skin_layers_at_full_failure']} / {d['final_skin_counts']['total_skin_layer_elements']} | {d['native_logged_failed_plies']} |" for d in s['damage'])
    witness='\n'.join(f"| {r['case']['id']} | {r['native_damage_error']:.7f} | {r['damage_growth_equal_peak']:.7f} | {r['maximum_work_balance_residual_J']:.9f} | {r['reaction_impulse_work_error_J']:.9f} | {r['final_IE_J']:.7f} |" for r in w['cases'])
    cmp='\n'.join(f"| {r['case']} | {r['common_time_ms']:.6f} | {100*r['impulse_difference_fraction']:.6f} | {100*r['generated_energy_difference_fraction']:.6f} |" for r in s['comparisons_with_cached_A15'])
    energy_rows=[]
    for wr in w['cases']:
        L=wr['case']['L_mm'];le=L/2**.5;energy_rows.append({'case':wr['case']['id'],'IE_total_J':wr['final_IE_J'],'initial_face_volume_mm3':L*L,'normalization_length_candidate_mm':le,'total_IE_normalized_by_face_volume_per_length_N_mm':wr['final_IE_J']*1000*le/(L*L),'includes_core_IE_not_fracture_toughness':True})
    assert read(OUT/'energy_size_diagnostic.json')=={'diagnostic_only':True,'no_new_acceptance_gate':True,'rows':energy_rows}
    complete=len(s['cases']);r=s['cases'][0];rejected=json.dumps(s['rejected_cases'],ensure_ascii=False) if s['rejected_cases'] else 'Aucun calcul couplé rejeté.'
    REPORT.write_text(f'''# AIRCRAFT-A16 — dommage natif des peaux dans l'impact avion–façade

**Quatre contrôles mécaniques courts passent ; {complete} nouveaux impacts couplés achevés avec dommage des peaux du radôme.** Le défaut d'histoire observé avec ORTHENERG dans A06 est évité : décharge et recharge au même maximum ne créent pas de dommage supplémentaire dans les nouveaux témoins. L'avion, la façade, les masses, les assemblages et les contacts A15 sont conservés. Aucun résultat historique ou NIST visé.

Cette avancée est une **perte de résistance des peaux calculée par le solveur**, pas encore une fissure de ténacité mesurée, une ouverture complète ni des fragments libres. L'âme reste intacte, les coques ne sont pas supprimées. L'énergie de fracture physique, la convergence spatiale et l'impact historique restent non qualifiés. Les nouveaux bilans et leurs échecs sont conservés ci-dessous.

## 1. Faits directement observés ou transcrits

Configuration épinglée avant génération et calcul, quatre témoins neufs et deux impacts demandés de10ms. Journaux, arguments, durées, exécutables et codes de sortie enregistrés. Historique natif/CSV intégral vérifié :10000 lignes par témoin, tous les records et canaux ; les sorties couplées et leurs records de fin sont vérifiés avec le même lecteur A15. REAC et contact sont des impulsions cumulées, non des forces à réintégrer. REAC/contacts de l'observateur exclus car leurs cumuls repartent à zéro.

Les animations portent les indices natifs de dommage par couche et les messages moteur nomment les peaux41/43 défaillantes. Le cœur42 ne reçoit pas de loi de dommage. Lecture directe des scalaires binaires FASTMAGI10 vérifiée contre le convertisseur sur premier, milieu et dernier états : indices élémentaires concordants, précision d'affichage respectée. **Toutes les images natives de dommage0,1ms** sont lues ; géométrie/vitesses/masses détaillées sur états réguliers≈0,5ms, premier et dernier inclus, comme dans A15. Tous les fichiers bruts sont conservés.

Le champ DAMA d'une couche est un maximum sur les points dans son épaisseur. D=1 signale au moins un point totalement endommagé, pas nécessairement toute la couche. Les messages de défaillance de pli donnent un indicateur distinct après les règles d'intégration. Les comptages ci-dessous sont des nombres d'éléments/couches, **pas une surface exacte ni une probabilité de l'événement**. Pas de nouvelle observation historique.

## 2. Résultats d'un modèle officiel

Les nouvelles sorties proviennent d'OpenRadioss v20260728-win64, pas d'un modèle officiel NIST de dommages. Entrées de façade représentative nominales NIST héritées ; cette dépendance d'entrée reste signalée, sans ajustement à ses résultats. Conditions historiques AA11 non établies.

La [documentation primaire ORTHSTRAIN](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/fail_orthstrain.htm) décrit un dommage fondé sur un maximum conservé, avec seuil de début et fin, puis réduction du tenseur. A16 choisit la déformation vraie et désactive les dépendances à la vitesse et à la taille. Les [règles TYPE51](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm) distinguent défaillance de pli et suppression de coque. Les [sorties DAMA](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_shell_dama_engine_r.htm) sont contrôlées ici séparément des efforts et du travail. Ces descriptions identifient le mécanisme numérique ; elles ne fournissent pas des propriétés mesurées du radôme réel.

## 3. Affirmations provenant des archives locales

Aucune nouvelle vidéo ni photographie, aucune archive/PDF source modifié. **9052 fichiers antérieurs, {p['bytes_hashed']/1e9:.3f}Go** recontrôlés intégralement par SHA-256, sans différence. Copies de documentation nouvelles sous les seules sorties A16, empreintes et exclusions de redistribution tierce enregistrées. Sources officielles locales en lecture seule. Module Boeing parallèle séparé ; ses limites restent ouvertes.

Le rapport A06 et ses sorties sont réutilisés sans relance : ORTHENERG y accumulait du dommage à recharge égale, et le travail ne correspondait pas au G entré. Cette loi n'est pas transférée. Les échecs A11-A15 et les champs anciens ne sont pas reclassés. Dernière publication distante vérifiée A12+A13 ; paire A14+A15 due, A16 s'ajoute à l'attente locale. Aucune publication externe nouvelle par ce script.

## 4. Hypothèses propres au modèle

Graine1102041, zéro tirage. Avion complet de≈121963kg,37228 nœuds couplés, façade de31986 quadrilatères sur trois étages représentatifs :944 nœuds de bord fixes et intérieur déformable. Vitesse[-200,5,2]m/s, gap5mm, quatre interfaces TYPE25 canoniques uniformes Stfac1, auto-contact TYPE7 du radôme. Pas d'auto-contact global, carburant résolu, intérieur de tour ou incendie. Aucun mouvement imposé dans l'avion. Tous les nouveaux départs sont intacts ; l'état hors domaine A15 n'est pas utilisé comme état physique validé.

**Seule nouvelle carte mécanique : /FAIL/ORTHSTRAIN/4**, appliquée au matériau des deux peaux0,5mm. Cœur8mm conservé. Géométrie/matières/propriétés/masse/RBE3/BCS/INIVEL/contact comparés à l'identique du parent A15 ; seules les sorties de dommage et les titres sont ajoutés. Matériaux métalliques et leurs lois de rupture absentes restent inchangés.

Le JSON de pré-déclaration conserve des libellés hérités d'anciennes étapes, notamment « failure_disabled », le contexte moteur seul et un ancien plafond de 600 s. Ils ne sont pas corrigés après calcul. **effective_configuration.json** les distingue des cartes réellement exécutées : nouvelle loi des peaux active, quatre contacts extérieurs actifs, parent direct A15 et plafond effectif de 1200 s vérifiés. Le mécanisme de rupture interne de LAW25 reste désactivé ; la nouvelle loi FAIL est distincte. Aucune ancienne qualification n'est transformée en réussite.

En simplification uniaxiale, εdébut,traction=450/22000={450/22000:.9f} et εdébut,compression=460/22000={460/22000:.9f}. Les450/460MPa et22GPa proviennent de la référence HexPly913/7781 héritée ; ce n'est pas une identification du matériau Boeing. Les directions11/22 utilisent les mêmes valeurs par approximation du tissu équilibré. Le cisaillement indépendant et les modes33 ne sont pas identifiés et restent désactivés ; aucun65MPa de short-beam shear n'est substitué à une résistance de cisaillement dans le plan.

εfin=(1+r)εdébut : **r=0,20** reprend le ratio de transition par défaut documenté, **r=0,02** est une sensibilité propre d'une décennie. Ces largeurs ne sont pas des mesures de déchirure et ne sont pas choisies pour obtenir une perforation. Seuil de défaillance d'épaisseur=1 au matériau et au stack : le cœur intact empêche la suppression de toute la coque. Ni délamination, écrasement, séparation des liaisons ni fragmentation topologique.

**Aucun G de fracture n'est entré ou annoncé validé.** Dans la référence uniaxiale à petit déplacement, la contrainte résistante décroît linéairement entre εdébut et εfin, et le travail total par volume vaut½E εdébut εfin. Sa normalisation par une longueur dépend du maillage. Le travail total n'est donc pas une ténacité objective ; aucune augmentation de G pour tolérer les mailles grossières. Des données et une représentation de séparation adaptées restent nécessaires.

Témoins : deux triangles du même sandwich, carrés10/20mm, déplacements affines prescrits seulement pour ces contrôles, chemin de déformation vraie0→0,0225→0→0,0225→0,04 aux temps0/0,25/0,5/0,75/1ms, interpolation cubique lisse sur chaque branche. Contraction Y=−0,25εX. Quatre cas, dont demi-pasR20 ; limites de pas25/12,5ns, TH0,1µs, animations5µs. Seuils déclarés : erreur absolue D≤0,02 ; croissance au même pic≤0,002 ; cycle énergétique≤2% ; travail/bilan≤1%+0,001J ; positions≤0,001mm ; demi-pas IE≤1%.

Impacts :10ms par cas, facteur de pas stable0,5, deux threads CPU, zéro GPU, plafond1200s par principal d'après le coût A15. TH0,01ms, images0,1ms. Ledger hérité : KE+rotation globale+IE+hourglass+spring+contact élastique/frottement/amortissement−travail externe, une fois chacun. PW inclus dans IE, aucun RKE reconstruit ajouté. Unités g/mm/ms/MPa/N/Nmm : ×0,001 pour g→kg, mm→m, ms→s, Nmm→J et Nms→Ns ; mm/ms→m/s a un facteur1. Critères de bilan/masse/quantité de mouvement A15 inchangés. Le critère local garde sa marge absolue de 1000 J liée à la précision des sorties : il ne signifie pas que chaque rapport résidu/énergie reste sous 5% dès les premiers instants. Les contraintes imprimées après dommage sont des contraintes effectives ; elles ne mesurent pas directement l'effort résistant endommagé. Leur ancien diagnostic de référence est conservé, pas utilisé comme preuve que le dommage est absent.

## 5. Résultats dérivés

| Témoin | Max erreur D | ΔD même pic | Max résidu J | Écart travail impulsions J | IE finale J |
|---|---:|---:|---:|---:|---:|
{witness}

Tous les contrôles déclarés passent. Demi-pas : ΔIE **{100*w['half_dt_final_IE_difference_fraction']:.7f}%**. Le casR20 garde D≈0,545 aux deux pics identiques ; le casR02 a déjà atteint1 au premier pic. L'âme garde D=0 ; pas d'érosion. Ces essais valident le mécanisme d'histoire/implémentation, pas une énergie de fracture physique ni la localisation d'une fissure. Le changement de taille des témoins ne constitue pas une étude d'objectivité spatiale de l'avion.

Diagnostic séparé de taille, sans nouveau critère a posteriori : IE totale normalisée par le volume initial des faces et une longueur géométrique candidate L/√2 donne39,5421N/mm enR20/L10 et79,0843N/mm enR20/L20. Cette valeur inclut aussi IE du cœur et n'est pas une ténacité. Son doublement quand la longueur double confirme qu'on ne peut annoncer une énergie surfacique objective avec cette loi. Le calcul est reproduit et comparé exactement dans ce finaliseur ; aucun G n'est ajusté.

| Impact | Fin observée ms | Impulsion X dernier TH kN·s | Max déplacement façade échantillonné mm | Énergie hors translation finale MJ | Résidu final kJ | Critères échoués |
|---|---:|---:|---:|---:|---:|---|
{results}

{rejected}

| Impact | Premier dommage enregistré ms | Premier pointD=1 enregistré ms | Couche/élémentDmax=1 | Plis défaillants consignés au journal |
|---|---:|---:|---:|---:|
{damages}

Les instants sont ceux des images espacées0,1ms, pas des temps exacts de début. Le dommage est monotone dans tous les états enregistrés, le cœur reste à0, les coques restent présentes, masse inchangée sans masse ajoutée. Des peaux défaillantes natives coexistent donc avec un maillage continu de radôme. Contact, quantité de mouvement, énergie et travail des matériaux restent interprétés séparément.

| Comparaison avec A15 intact mis en cache | Temps commun ms | Δimpulsion % | Δénergie hors translation % |
|---|---:|---:|---:|
{cmp}

Il s'agit de **sensibilités de loi de dommage**, pas de convergence ni d'une sélection du meilleur résultat. Le casR20 est affiché car premier déclaré, sans classement d'après la forme obtenue. Le radôme ne devient pas historiquement validé parce que ses efforts changent. Aucun ancien solveur relancé. A16 n'allonge pas encore l'horizon au-delà de0,01s : il change un mécanisme matériel dans l'impact déjà lancé.

La visualisation est issue des déplacements et du dommage natifs, ×1, lecture ralentie sans interpolation géométrique. Rouge : au moins un point de peau totalement endommagé ; jaune : dommage partiel ; coque encore présente. Image statique inspectée et diagramme comparatif inspecté, données comprimées avec retour exact, syntaxe JS vérifiée ; rendu GUI interactif non certifié.

## 6. Contradictions et informations manquantes

L'histoire au même pic est désormais contrôlée et des points/plis perdent leur résistance dans l'avion, mais cette loi reste sans ténacité physique mesurée et sans objectivité spatiale. La résistance/E uniaxiale est une approximation de début de dommage, pas une enveloppe multiaxiale identifiée. La réduction de tout le tenseur par le maximum d'un mode peut aussi affecter le cisaillement ; ce couplage n'est pas validé pour le radôme réel.

L'âme intacte laisse une coque continue et un contact géométrique de sandwich, même si les peaux portent moins d'effort. Une coque affaiblie n'est pas un fragment ni un trou. Métaux, assemblages, auto-contact, écrasement, séparation des couches, carburant, conditions historiques et convergence spatiale restent ouverts. Les critères énergétiques ou matériels échoués ci-dessus sont conservés intégralement. Les premières secondes et toute chaîne d'effondrement restent non calculées.

{NEXT}
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Reprise WTC1 — AIRCRAFT-A16 → AIRCRAFT-A17

Rapport : {rel(REPORT)} ; configuration : {rel(CFG)} ; résultats : {rel(OUT/'campaign_review.json')} ; témoins : {rel(OUT/'witness_review.json')} ; assessment : {rel(OUT/'scientific_assessment.json')}.

Quatre témoins neufs passent : ORTHSTRAIN à histoire maximale, r0,20/0,02, eps_t450/22000, eps_c460/22000, déformation vraie. Recharge au même maximum : ΔD=0 ; demi-pas IE {100*w['half_dt_final_IE_difference_fraction']:.7f}%. Contrairement à ORTHENERG A06 rejetée, pas de dommage supplémentaire au même pic. Aucune énergie de fracture physique qualifiée : pas de G entré, pas d'objectivité spatiale revendiquée.

{complete} impacts neufs couplés achevés, même avion/façade A15, seule nouvelle carte FAIL/ORTHSTRAIN/4 + sortiesDAMA. Peaux41/43 endommagées/défaillantes natives ; âme42 intacte, stackPthick1, aucune coque supprimée. Les comptagesDAMA maximum ne valent pas tous les points du pli ; messages de pli traités séparément. Critères énergétiques/matériels échoués dans campaign_review conservés. Pas de physique historique validée.

9052 anciens fichiers {p['bytes_hashed']/1e9:.3f}Go vérifiés sans changement, zéro ancien solveur relancé. Visualisation {rel(OUT/'visualisation/impact_avion_facade_dommage.html')}, déplacements×1 et indices de dommage natifs, PNG inspectés, GUI interactive non certifiée. Publication A14+A15 due, A16 en attente.

{NEXT}
''',encoding='utf-8')
    names=['run_aircraft_a16.py','review_aircraft_a16_witness.py','review_aircraft_a16.py','verify_aircraft_a16_preservation.py','visualize_aircraft_a16.py','finalize_aircraft_a16.py'];files=[q for q in OUT.rglob('*') if q.is_file()]+[CFG,HANDOFF]+[ROOT/'wtc1_simulation_v8/scripts'/n for n in names]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)} for q in sorted(set(files))]});print({'prepared':True,'files':len(set(files)),'physical_qualified':False},flush=True)

def register():
    guard();n=checkrows(read(OUT/'artifact_manifest.json')['files']);assert REPORT.exists() and HANDOFF.exists();st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st['current_iteration']=='AIRCRAFT-A15' and st['next_iteration']=='AIRCRAFT-A16' and harness()['Status']=='PASS'
    assert cy['pending_iterations']==['AIRCRAFT-A14','AIRCRAFT-A15'];prefix=(OUT/'before_registry.jsonl').read_bytes();reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==prefix;s=read(OUT/'campaign_review.json');a=read(OUT/'scientific_assessment.json');t=now()
    rec={'experiment_id':'WTC1-AIRCRAFT-A16','registered_at':t,'status':'completed_exploratory_whole_aircraft_skin_damage_with_native_maximum_history_and_retained_fracture_energy_material_limits','configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'campaign_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'all_declared_checks_pass':s['all_declared_checks_pass'],'witness_engine_jobs':4,'main_engine_jobs':2,'completed_main_engine_jobs':len(s['cases']),'old_solver_reruns':0,'old_files_preserved':9052,'branch_iteration_count':16,'whole_aircraft_iteration_count':12,**a,'next_iteration':'AIRCRAFT-A17'}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A16',next_iteration='AIRCRAFT-A17',current_status=rec['status'],next_objective=NEXT,updated_at=t);st['aircraft_a16_key_results']=rec;st['validated_artifacts'].update(aircraft_a16_report=rel(REPORT),aircraft_a16_results=rel(OUT/'campaign_review.json'),aircraft_a16_handoff=rel(HANDOFF))
    cy.update(pending_iterations=['AIRCRAFT-A14','AIRCRAFT-A15','AIRCRAFT-A16'],pending_count=3,next_publication_after='A14+A15 pair remains due; A16 additionally pending. Prepare and verify immutable releases independently of scientific qualification',updated_at=t)
    dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or checkrows(read(OUT/'artifact_manifest.json')['files']);before=read(OUT/'before_state.json');st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness();protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_artifact_hashes':True,'old_files_preserved':read(OUT/'preservation_verification.json')['pass'],'old_results_policies_unchanged':all(st[k]==before[k] for k in protected),'registry_one_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A16','route':st['current_iteration']=='AIRCRAFT-A16' and st['next_iteration']=='AIRCRAFT-A17','pending_publications_retained':cy['pending_iterations']==['AIRCRAFT-A14','AIRCRAFT-A15','AIRCRAFT-A16'] and cy['pending_count']==3,'remote_baseline_unchanged':all(cy[k]==read(OUT/'before_publication_cycle.json')[k] for k in ['last_published_iteration','last_published_commit','last_published_release']),'mechanical_gate_documented':read(OUT/'witness_review.json')['mechanical_gate_pass'],'physical_failures_retained':not read(OUT/'scientific_assessment.json')['physical_fracture_energy_qualified'],'required_artifacts_exist':REPORT.exists() and HANDOFF.exists(),'harness_pass':v['Status']=='PASS'}
    proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':9052,'harness':v,'external_publication_performed':False,'physical_impact_qualified':False,'next_iteration':'AIRCRAFT-A17'};assert proof['pass'],proof;dump(OUT/'publication_verification.json',proof);print(proof,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
