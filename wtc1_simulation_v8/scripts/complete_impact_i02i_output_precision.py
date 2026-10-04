"""J report and registration: exact decoding, uncertainty, raw failures retained."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import run_impact_i02i_output_precision as j
import diagnose_impact_i02i_terminal_rounding as terminal
h=j.h;ROOT,OUT,CFG=j.ROOT,j.OUT,j.CFG
RAW=OUT/'verification_r1/summary.json'
SUMMARY=OUT/'resultats_impact_i02i_output_precision.json'
REPORT=OUT/'rapport_impact_i02i_output_precision.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_J_HANDOFF.md'
KPLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_k_plan_from_j.json'
OBJECTIVE='K : dériver et vérifier une référence séparable ouverture H2 + cisaillement élastique libre, puis pré-déclarer quatre états neufs sans séparation à 25/12,5 ns. Utiliser la lecture binaire J seulement si sa signature exacte correspond ; traiter énergie et temps par intervalles de représentation déclarés, sans clipping/déphasage. Conserver quatre échecs I, trois critères bruts de fin J, tous E/F/G et le réservoir tangentiel supprimé avec OFF F. J=1/2 GitHub ; prochaine paire J+K après K vérifiée. Gf30 hypothétique, Gf15/60 et conventions NASA ouverts ; V11F/V11R/V11S préservés. Impact Boeing/façade, feu et effondrement non qualifiés.'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def preservation():
    rows=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in rows if h.sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad;return len(rows)
def failure_map(s):return {name:[k for k,v in r['checks'].items() if not v] for name,r in s['cases'].items()}

def prepare():
    assert not SUMMARY.exists() and not REPORT.exists() and not HANDOFF.exists() and not KPLAN.exists()
    raw=read(RAW);cfg=read(CFG);td=read(terminal.OUT);count=preservation();hv=h.harness()
    expected={'NORMAL_ARREST_RETURN_050NS':['no_truncation_or_extrapolation'],'NORMAL_ARREST_RETURN_025NS':[],
        'NORMAL_SUBPEAK_RETURN_025NS':['no_truncation_or_extrapolation'],'NORMAL_SUBPEAK_RETURN_012P5NS':['no_truncation_or_extrapolation']}
    assert failure_map(raw)==expected and raw['case_checks_passed']==53 and raw['case_checks_total']==56
    assert not raw['all_declared_checks_pass'] and td['pass'] and td['raw_failures_preserved']==3
    assert raw['total_values']==49323 and raw['total_rows']==1203
    decoding=all(v['checks']['all_values_reproduce_CSV'] and v['checks']['independent_readers_exact'] and
        v['checks']['all_global_spring_IE_bits_equal'] and v['checks']['header_and_cards'] for v in raw['cases'].values())
    s={'iteration':'IMPACT-I02I-J','created_utc':h.NOW(),'raw_summary':h.rel(RAW),'raw_summary_sha256':h.sha(RAW),
        'case_checks_passed':53,'case_checks_total':56,'reference_checks_passed':6,'reference_checks_total':6,
        'terminal_interval_checks_passed':sum(td['checks'].values()),'terminal_interval_checks_total':len(td['checks']),
        'all_declared_raw_checks_pass':False,'raw_failed_gates':expected,'raw_failures_preserved':3,
        'terminal_interval_diagnostic_pass':True,'binary_value_reader_verified':decoding,'all_49323_values_reproduce_CSV':decoding,
        'total_rows':raw['total_rows'],'total_values':raw['total_values'],'runtime_seconds':raw['runtime_seconds'],
        'binary_sign_observable_near_zero':False,'nearest_rounding_assumption':True,'official_binary_schema_verified':False,
        'original_converter_source_obtained':False,'old_I_four_sign_failures_preserved':True,'old_I_all_declared_checks_pass':False,
        'energy_IE_three_channels_identical':True,'conditional_zero_rounding_compatibility':True,
        'no_solver_run':True,'no_converter_run':True,'no_material_history_modified':True,
        'physical_fracture_calibrated':False,'physical_propagation_qualified':False,'mixed_mode_qualified':False,
        'aircraft_impact_qualified':False,'source_convention_verified':False,'E_sensitivities_resolved':False,
        'inputs_unchanged':True,'qualification':'Four-file decoder and conditional finite-representation diagnostic only; original raw failed gates remain failed'}
    assert decoding;h.dump(SUMMARY,s)
    plan={'id':'IMPACT-I02I-K_PLAN_FROM_J','created_utc':h.NOW(),'seed':1102019,'random_draws':0,
        'saved_J_summary':h.rel(SUMMARY),'saved_J_sha256':h.sha(SUMMARY),
        'scope':'First two free translational modes together before separation; explicit sums of recoverable and unrecovered energy, no real joint calibration',
        'cases_proposed':[
            {'family':'FREE_MIXED_ARREST','initial_vX_mm_per_ms':10.,'initial_vY_mm_per_ms':20.,'initial_total_energy_J':.025,
                'end_ms':.012,'maximum_dt_ms':[.000025,.0000125]},
            {'family':'FREE_MIXED_ELASTIC_RETURN','initial_vX_mm_per_ms':1.,'initial_vY_mm_per_ms':math.sqrt(20),
                'initial_total_energy_J':.00105,'end_ms':.004,'maximum_dt_ms':[.000025,.0000125]}],
        'properties':{'moving_mass_g':.1,'fixed_mass_g':.1,'Kn_N_per_mm':56000.,'Kt_N_per_mm':21500.,
            'normal_peak_N':495.,'Gf_N_per_mm_hypothetical':30.,'rotations':'blocked','Z':'blocked',
            'X_Y':'both free with initial velocities; no imposed path','shear_failure':'disabled; unchanged linear X law'},
        'before_engine':['Derive Y reference from I and X oscillator from H/G, with scaled initial velocity, and verify total E/P and independent integration',
            'Verify Y stays positive and OFF never expected in declared window; retain both histories, no damaged-property changes',
            'Declare all raw per-axis amplitudes <=1%, total energy/work <=0.5%, initial momentum included separately for X and Y',
            'Predeclare IEEE32 and decimal representation intervals for sign/time; report raw signs independently; never override old I/J failures',
            'Validate the exact decoder signature on each new file before using J reader, reject unknown layouts'],
        'energy_reference':'IE=Ux+Uy+Dy; KE=m_g(vx^2+vy^2)/2; WE=0; Ux=Fx^2/(2Kt), Uy=Fy^2/(2Kn); J_support_axis=P_axis-P0_axis',
        'cost':{'maximum_case_wall_seconds':90,'maximum_campaign_wall_seconds':600,'announce_before_run':True},
        'unchanged':['I four raw sign failures','J three raw endpoint failures','E/F/G failures','NASA conventions',
            'Gf15/60 deferred','F tangential energy lost at whole deletion remains open','V11F/V11R/V11S'],
        'deferred':['Mixed free separation','Actual coupling/contact/plate waves and fracture calibration','Boeing/facade/fire/collapse'],
        'publication':'J pending1/2; publish J+K only after K documented and verified; retain H+I baseline'}
    h.dump(KPLAN,plan)
    table=[];ends=[]
    for name,v in raw['cases'].items():
        a=v['metrics'];table.append(f"| {name} | {a['rows']} | {a['values_compared']} | {a['CSV_min_retained_J']:.8g} | {a['binary_min_retained_J']:.8g} | {a['binary_negative_rows']} |")
        t=td['cases'][name];ends.append(f"| {name} | {t['binary_end_ms']:.17g} | {t['declared_end_ms']:.8g} | {t['binary_minus_declared_ms']:.8g} | {'passe' if t['raw_time_gate_still_passes'] else 'échoue'} |")
    report=f'''# WTC1 — IMPACT-I02I-J : précision des sorties sauvegardées

## 1. Faits directement observés ou transcrits

Analyse de quatre T01 et de leurs CSV de I, sans moteur, starter ou convertisseur relancé. Lecture indépendante : {raw['total_rows']} lignes × 41 colonnes = **{raw['total_values']} valeurs**. Toutes reproduisent exactement les jetons .6e de l'export sauvegardé, y compris les temps, forces, vitesses, impulsions et énergies. Deux lecteurs propres distincts (blocs contrôlés avec struct ; accès NumPy à pas constant après validation) donnent les mêmes valeurs. Les trois sorties IE globale, SPRING ENERGY et IE de la liaison sont bit pour bit identiques sur chaque ligne.

Le diagnostic brut J passe 53/56 critères ; les trois échecs concernent uniquement la condition exacte temps_final_binaire≤temps_demandé, sans marge d'arrondi. Ils restent échoués. Six contrôles de lecteur passent, dont rejet de marqueur corrompu, version inconnue, code variable incorrect, troncature et ajout d'octet, plus cinq états élastiques synthétiques pour le calcul exact d'intervalle. Un diagnostic de temps **distinct**, pré-déclaré après ces échecs, passe 8/8 contrôles d'intervalle. Il ne remplace aucun critère brut.

La [documentation /TFILE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tfile_engine_r.htm) associe le type 4 au format binaire IEEE32 ; les cartes I demandent /TFILE/4. L'accès aux sources officielles du convertisseur a renvoyé 404 via API et chemins raw testés, après les mêmes difficultés historiques. Les liens présents dans les résultats de recherche ne constituent pas une lecture du code. Les six essais d'accès sont consignés ; aucun algorithme interne n'est inféré de ce code indisponible.

## 2. Résultats d'un modèle officiel

Aucun nouveau résultat NIST ou modèle historique. Les pages Altair documentent les champs demandés : [IE/FY/OFF de liaison](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm) et [sorties nodales](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm). L'égalité constatée dans ces quatre fichiers ne valide ni le logiciel entier ni un phénomène réel. La documentation continue d'appeler REACX/REACY une force alors que les valeurs sauvegardées se comportent comme une impulsion cumulative ; le centrage exact TH et le chemin interne du convertisseur ne sont pas établis.

## 3. Affirmations des archives locales

Aucune nouvelle assertion d'archive ni vidéo inspectée. {count} fichiers antérieurs vérifiés depuis les inventaires sauvegardés ; aucun rescan d'archive ou ancien solveur relancé. Les quatre échecs IE−U de I restent inchangés. Tous les états E/F/G/H/I et V11F/V11R/V11S sont conservés. H+I publiée reste la base publique ; J seule constitue une itération sur deux avant prochaine publication J+K.

## 4. Hypothèses propres au diagnostic, propriétés et unités

Aucune propriété physique ajoutée. Dans le témoin I : masse mobile 0,1 g, Kn=56000 N/mm, Kt=21500 N/mm, force normale maximale hypothétique 495 N, aire 1 mm², Gf=30 N/mm hypothétique. X/Z et rotations bloqués, pas de cisaillement actif ; U=Fy²/(2Kn). Les sorties d'énergie sont en N mm=mJ, converties en J par ×0,001 ; temps ms, force N, impulsion N ms. IE−U est nommé travail numérique non récupéré, sans assimilation à une chaleur ou fissuration physique.

Schéma **observé localement**, limité à ces quatre fichiers : version entière 3040, entiers et flottants en big-endian, marqueur entier 32 bits donnant la longueur de chaque bloc puis répété après le contenu. Les 16 blocs d'en-tête occupent 916 octets ; titres de calcul, groupes SEAM_HISTORY/NODES, IDs de nœuds 1/2 et codes variables sont contrôlés. À chaque ligne : quatre blocs de 4/88/24/48 octets, soit temps, 22 champs globaux, six champs de liaison et 12 champs nodaux. Toute autre signature, octet final résiduel ou bloc incorrect est refusé. Certains entiers annexes d'en-tête restent opaques, simplement contrôlés ; aucune généralité du lecteur ou validation de schéma officiel n'est revendiquée. Les noms de variables sont reliés aux cartes /TH originales et confrontés à l'export déjà sauvegardé.

Diagnostic de représentation pré-déclaré avant analyse : hypothèse d'arrondi au plus proche binaire32. Pour un flottant x sauvegardé, cellule fermée [(prev32(x)+x)/2,(x+next32(x))/2] ; les deux milieux sont calculés exactement comme fractions dyadiques. Pour F dans [fl,fh], calculer les extrema exacts de F², incluant zéro si l'intervalle change de signe ; puis D_min=0,001(IE_min−U_max), D_max=0,001(IE_max−U_min). Kn et la conversion 0,001 sont des rationnels exacts, sans tolérance ajustée. Pour le CSV, ajouter un demi-pas décimal lu dans chaque jeton .6e. Les décisions d'inclusion de zéro utilisent les fractions exactes ; les bornes en CSV sont arrondies vers l'extérieur pour leur affichage. Aucun clipping de D, changement de phase ou correction d'énergie.

L'hypothèse d'arrondi ne révèle pas la vraie valeur interne du moteur. Un intervalle contenant zéro rend le signe non observable à cette précision ; ce n'est pas la preuve de D=0. Les deux nœuds, loi H2 et références I restent ceux d'origine ; aucun restart ou matériau endommagé modifié.

## 5. Résultats dérivés

| Cas I réutilisé | Lignes | Valeurs | Minimum D CSV (J) | Minimum D binaire (J) | Lignes binaires D<0 |
|---|---:|---:|---:|---:|---:|
{chr(10).join(table)}

L'export décimal ajoute une perte de précision mesurée directement. Lire le binaire réduit les minima négatifs en amplitude, mais ne les élimine pas. Même le seuil original −1e−10 J resterait dépassé dans deux séries binaires ; cette remarque est descriptive et ne réévalue pas les critères de I. Tous les cas à D binaire négatif dans la branche historiquement élastique admettent zéro dans leur intervalle exact. Toutes les lignes négatives CSV admettent aussi zéro après prise en compte des deux représentations. **Le signe près de zéro est donc indécidable avec ces seules sorties et sous l'hypothèse déclarée.** Les quatre échecs de I sont conservés.

Après décharge de l'arrêt endommagé, IE binaire finale ≈0,0192134418488 J et 0,0192133502960 J, avec force normale/U nulles ; cette énergie positive est largement supérieure à l'incertitude. Les contrôles sous pic ont D binaire final ≈−4,02e−13 J et +2,05e−12 J : toujours rapportés tels quels. Les bilans globaux binaires restent au-dessous de 0,008755 % de E0, sans correction de phase ou physique ; leur seuil 0,5 % passe.

| Cas | Temps final binaire (ms) | Temps demandé (ms) | Différence (ms) | Critère brut J |
|---|---:|---:|---:|---|
{chr(10).join(ends)}

Les trois dépassements sont 1,04e−10 ou 1,90e−10 ms. La série arrêt 25 ns se termine une ligne plus tôt, à ≈0,0119749996811 ms, comme son CSV original, sans extrapolation. Le diagnostic supplémentaire teste exactement l'intersection de la cellule binaire du temps final avec [fin−2pas,fin] : les quatre cellules sont compatibles et contiennent aussi leur temps final CSV. L'ordre, le nombre et les valeurs des lignes correspondent entièrement ; aucun octet n'est perdu. Cette compatibilité ne change pas les trois échecs de condition brute.

## 6. Contradictions et informations manquantes

La précision interne et l'arrondi réel du moteur, la source exacte du convertisseur et le schéma binaire officiel ne sont pas établis. J vérifie une lecture propre de quatre fichiers bornés ; son audit brut reste 53/56 et le champ all_declared_raw_checks_pass reste false. Les petits signes IE−U demeurent non résolus ; aucune énergie négative réelle ne peut être identifiée ou exclue par une telle quantification seule.

Conserver les quatre échecs I, les trois critères bruts de fin J, les cinq OFF/FX mixtes F, les huit diagnostics historiques G, les sensibilités et couvertures E, la définition REACX/REACY et le centrage TH. Les conventions NASA restent non identifiées ; Gf30 hypothétique et Gf15/60 différés. J ne ferme pas le réservoir tangentiel perdu lors d'une désactivation complète.

K proposera quatre états neufs libres sur X et Y avec Y sous la séparation : contrôle élastique et arrêt normal H2 avec réserve de cisaillement élastique. Dériver d'abord la référence séparable, Ux+Uy+Dy et les deux impulsions initiales, avant cartes, critères puis moteur. C'est un témoin de modes indépendants simultanés, pas un assemblage réel ou une rupture mixte qualifiée. Rien n'est calculé en K ici.

Impact complet Boeing/façade, incendie et effondrement réel non qualifiés. Localisation en flexion après fracture complète non validée ; température imposée ≠ incendie calculé ; Blender visualisation uniquement. V11F/V11R/V11S préservés.

## Reproduction et reprise

Graines 1102018 sans tirage. Pré-déclaration J, source /TFILE en snapshot non redistribué, six accès sources échoués consignés, lecteur, deux audits distincts, CSV binaires à 17 décimales, intervalles rationnels et journaux de contrôle conservés. Analyse principale : {raw['runtime_seconds']:.6f} s, budget 120 s respecté ; aucun executable scientifique ou convertisseur lancé. Actions : initialize, declare, audit, terminal declare/diagnose, prepare, register. Pré/post-harnais, empreintes et état contrôlés. Vérifier sans solveur avec complete_impact_i02i_output_precision.py verify. Prochaine étape K dans impact_i02i_k_plan_from_j.json ; prochaine publication J+K après K vérifiée, aucun post X.
'''
    REPORT.write_text(report,encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# Passation compacte — IMPACT-I02I-J vers K

Lire AGENTS.md, harness/state.json (prioritaire), cette passation et impact_i02i_k_plan_from_j.json. J terminée comme lecture bornée et diagnostic de représentation ; K prochaine. J seule pending1/2, publication J+K après K vérifiée ; H+I reste base distante.

J : quatre T01 I lus sans moteur/convertisseur, 1203 lignes et 49323 valeurs reproduisent exactement les CSV .6e. Deux lecteurs concordent ; IE globale/SPRING ENERGY/IE liaison bit identiques. Audit brut 53/56 : trois temps binaires finaux dépassent la fin demandée d'environ 1e−10 ms, critères maintenus échoués. Référence 6/6 ; diagnostic terminal distinct 8/8, hypothèse d'arrondi au plus proche. Les négatifs D=IE−Fy²/(2Kn) sont tous compatibles avec une cellule binaire contenant zéro en branche élastique. Le signe interne demeure non observable. Quatre échecs I inchangés ; aucun seuil changé, clipping ou phase ajustée.

Résultats/rapport/publication_verification.json : wtc1_simulation_v8/output/impact_i02i_output_precision/. Pré-déclarations impact_i02i_j_predeclaration.json et impact_i02i_j_terminal_interval_predeclaration.json. Lecteur decode_impact_i02i_t01.py limité aux signatures 3040 déclarées ; code officiel convertisseur inaccessible (404), ne pas prétendre schéma universel. Vérifier sans moteur avec complete_impact_i02i_output_precision.py verify. {count} anciens fichiers épinglés, originaux inchangés.

K : d'abord référence exacte et intégration indépendante, puis quatre états neufs X/Y libres, Z/rotations bloqués, sans séparation. Arrêt : vx=10,vy=20 mm/ms,E0=0,025 J,fin0,012 ms. Sous-pic : vx=1,vy=√20,E0=0,00105 J,fin0,004 ms. Caps25/12,5 ns, seuils bruts1% par mode/impulsion et0,5% énergie avant moteur. IE=Ux+Uy+Dy ; P0 et J support séparément X/Y. Intervalles de temps/signe à pré-déclarer sans promouvoir I/J. Ne pas changer matériau endommagé ni relancer anciens calculs. Annoncer budget90s/cas,600s total avant moteur.

Conserver E/F/G, cinq OFF/FX F et réservoir tangentiel supprimé avec OFF, huit diagnostics historiques G, quatre signes I, trois temps bruts J, REACX/REACY/centrage, conventions NASA, Gf30 hypothétique/Gf15/60 différés, V11F/V11R/V11S. Aucun transfert avion/façade/feu/effondrement ou Blender dynamique ; flexion post-fracture non validée. Aucun post X.
''',encoding='utf-8',newline='\n')
    h.dump(OUT/'release_audit.json',{'created_utc':h.NOW(),'pass':True,'scope':'Integrity and faithful bounded diagnosis; not all raw numerical gates passing',
        'old_files_preserved':count,'harness':hv,'summary_sha256':h.sha(SUMMARY),'raw_failed_gates':expected,
        'all_raw_gates_pass':False,'old_I_failures_retained':4,'official_binary_schema_verified':False,'physical_propagation_qualified':False})
    h.dump(OUT/'harness_after_artifacts.json',h.harness())
    scripts=[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_impact_i02i_output_precision.py','decode_impact_i02i_t01.py',
        'audit_impact_i02i_output_precision.py','diagnose_impact_i02i_terminal_rounding.py','complete_impact_i02i_output_precision.py']]
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,terminal.CFG,KPLAN,HANDOFF]+scripts
    h.dump(OUT/'artifact_manifest.json',{'created_utc':h.NOW(),'files':[{'path':h.rel(p),'bytes':p.stat().st_size,'sha256':h.sha(p)} for p in sorted(set(paths))],
        'exclusions':['self','post-registration verification','mutable harness administration']})

def register():
    assert SUMMARY.exists() and REPORT.exists() and HANDOFF.exists() and KPLAN.exists() and (OUT/'artifact_manifest.json').exists()
    count=preservation();s=read(SUMMARY)
    for name in h.g.f.ADMIN:assert h.sha(ROOT/'harness'/name)==h.sha(OUT/('before_'+Path(name).name)),'Concurrent state change'
    state=read(ROOT/'harness/state.json');cadence=read(ROOT/'harness/publication_cycle.json')
    assert state['current_iteration']=='IMPACT-I02I-I' and state['next_iteration']=='IMPACT-I02I-J' and cadence['pending_iterations']==[]
    when=h.NOW();status='completed_bounded_binary_observability_with_three_raw_endpoint_failures'
    record={'experiment_id':'WTC1-IMPACT-I02I-J','registered_at':when,'status':status,'configurations':[h.rel(CFG),h.rel(terminal.CFG)],
        'report':h.rel(REPORT),'results':h.rel(SUMMARY),'handoff':h.rel(HANDOFF),'artifact_manifest':h.rel(OUT/'artifact_manifest.json'),
        'source_manifest':h.rel(OUT/'source_manifest.json'),'publication_verification':h.rel(OUT/'publication_verification.json'),'K_plan':h.rel(KPLAN),
        **{k:s[k] for k in ['case_checks_passed','case_checks_total','reference_checks_passed','reference_checks_total',
            'terminal_interval_checks_passed','terminal_interval_checks_total','all_declared_raw_checks_pass','raw_failed_gates','raw_failures_preserved',
            'binary_value_reader_verified','total_rows','total_values','runtime_seconds','binary_sign_observable_near_zero','official_binary_schema_verified',
            'old_I_four_sign_failures_preserved','physical_fracture_calibrated','physical_propagation_qualified','mixed_mode_qualified','source_convention_verified','E_sensitivities_resolved']},
        'saved_cases_read':4,'solver_jobs':0,'old_files_preserved':count,'next_iteration':'IMPACT-I02I-K','github_pending_iterations':1}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='IMPACT-I02I-J',current_status=status,next_iteration='IMPACT-I02I-K',next_objective=OBJECTIVE,updated_at=when)
    state['impact_i02i_j_key_results']={k:v for k,v in record.items() if k not in ['experiment_id','registered_at','status','configurations','report','results','handoff',
        'artifact_manifest','source_manifest','publication_verification','K_plan','next_iteration']}
    state['validated_artifacts'].update(impact_i02i_j_report=h.rel(REPORT),impact_i02i_j_results=h.rel(SUMMARY),impact_i02i_j_handoff=h.rel(HANDOFF),
        impact_i02i_j_publication_verification=h.rel(OUT/'publication_verification.json'),impact_i02i_k_plan=h.rel(KPLAN))
    cadence.update(pending_iterations=['IMPACT-I02I-J'],pending_count=1,next_publication_after='Publish J+K after K verified, preserving I/J failures and H+I baseline',updated_at=when)
    h.dump(ROOT/'harness/publication_cycle.json',cadence);temp=ROOT/'harness/state_i02ij_pending.json';h.dump(temp,state);temp.replace(ROOT/'harness/state.json')
    verify(write=True)

def verify(write=False):
    count=preservation();manifest=read(OUT/'artifact_manifest.json');bad=[r['path'] for r in manifest['files'] if h.sha(ROOT/r['path'])!=r['sha256']]
    state=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cadence=read(ROOT/'harness/publication_cycle.json');s=read(SUMMARY);raw=read(RAW)
    prefix=(OUT/'before_registry.jsonl').read_bytes();reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();extra=reg[len(prefix):].decode('utf-8').splitlines()
    protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy','open_limitations']
    hv=h.harness();cfg=read(CFG);tconf=read(terminal.CFG)
    checks={'artifact_hashes':not bad,'old_pins_preserved':True,'registry_prefix':reg.startswith(prefix),
        'one_J_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-J',
        'state_J_to_K':state['current_iteration']=='IMPACT-I02I-J' and state['next_iteration']=='IMPACT-I02I-K',
        'prior_states_preserved':all(state[k]==old[k] for k in protected),'harness_pass':hv['Status']=='PASS',
        'report_handoff_plan_exist':REPORT.exists() and HANDOFF.exists() and KPLAN.exists(),
        'cadence_J_one_pending':cadence['pending_iterations']==['IMPACT-I02I-J'] and cadence['pending_count']==1,
        'H_I_publication_baseline_preserved':all(cadence[k]==read(OUT/'before_publication_cycle.json')[k] for k in ['last_published_iteration','last_published_commit','last_published_release']),
        'raw_audit_hash_guard':h.sha(RAW)==tconf['raw_audit_sha256']==s['raw_summary_sha256'],
        'saved_I_guards':h.sha(j.OLD/'verification_r1/summary.json')==cfg['saved_I_summary_sha256'] and h.sha(j.i.CFG)==cfg['saved_I_config_sha256'],
        '49323_values_decoded':s['binary_value_reader_verified'] and s['total_values']==49323,
        'three_raw_time_failures_preserved':not s['all_declared_raw_checks_pass'] and sum(len(v) for v in failure_map(raw).values())==3,
        'old_I_failures_preserved':not state['impact_i02i_i_key_results']['all_declared_checks_pass'] and len(state['impact_i02i_i_key_results']['failed_gates'])==4,
        'terminal_interval_separate':read(terminal.OUT)['parent_raw_gates_unchanged'] and read(terminal.OUT)['pass'],
        'physical_limits_retained':not s['physical_propagation_qualified'] and not s['mixed_mode_qualified'] and not s['official_binary_schema_verified'],
        'no_executable_rerun':s['no_solver_run'] and s['no_converter_run']}
    result={'created_utc':h.NOW(),'pass':all(checks.values()),'scope':'Integrity and exact saved-file decoding; not all raw gates or physical validation',
        'checks':checks,'manifest_files_checked':len(manifest['files']),'manifest_failures':bad,'old_files_checked':count,'harness':hv,
        'case_checks':'53/56','reference_checks':'6/6','terminal_interval_checks':'8/8','raw_failed_gates':s['raw_failed_gates'],
        'all_declared_raw_checks_pass':False,'binary_sign_observable_near_zero':False,'physical_propagation_qualified':False,
        'next_iteration':'IMPACT-I02I-K','github_pending_iterations':1}
    assert result['pass'],result
    if write:h.dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);args=p.parse_args();globals()[args.action]()
