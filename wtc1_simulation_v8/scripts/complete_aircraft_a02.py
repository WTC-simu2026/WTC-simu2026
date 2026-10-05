"""Deliver and register bounded A02 results, including strict failed criteria."""
import argparse,csv,json,re,shutil,subprocess,sys
import numpy as np
from run_aircraft_a02 import ROOT,CFG,OUT,PREV,read,dump,sha,rel,now,harness,preserved
REPORT=OUT/'rapport_aircraft_a02.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A02_HANDOFF.md'
def part_audit():
    mesh=read(ROOT/'wtc1_simulation_v8/output/aircraft_a01/verification_r2/airframe_mesh_SI.json');x=np.array(mesh['nodes_m'])
    p=OUT/'r1/translation_dt080/A02_translation_dt080_0000.out';s=p.read_text();s=s[s.index('PART MASS & INERTIA'):]
    pat=r'PART :\s+(\d+),\s+([^\n]+)\n\s+Mass[^\n]+\n([^\n]+)\n\s+X[^\n]+\n([^\n]+)';parts=[]
    for r in re.finditer(pat,s):
        pid,title,ml,xl=r.groups();title=title.strip();mass=float(ml.split()[0])*.001;cg=np.array([float(t) for t in xl.split()[:3]])*.001
        el=[e for e in mesh['triangular_shells']+mesh['equivalent_elastic_beams'] if e['part']==title];M=sum(e['mass_kg'] for e in el);cg0=sum(e['mass_kg']*x[e['nodes']].mean(axis=0) for e in el)/M
        parts.append({'part':title,'id':int(pid),'element_type':'beam' if any(e['part']==title for e in mesh['equivalent_elastic_beams']) else 'triangle','native_mass_kg':mass,'A01_mass_kg':M,'native_CG_m':cg.tolist(),'A01_CG_m':cg0.tolist(),'CG_difference_m':(cg-cg0).tolist()})
    assert len(parts)==18
    predicted_delta=sum(p['A01_mass_kg']*np.array(p['CG_difference_m']) for p in parts)/read(OUT/'r1/mapping_audit.json')['reference_A01']['total_kg']
    a=read(OUT/'r1/translation_dt080/audit.json');measured_delta=np.array(a['native_CG_m'])-read(OUT/'r1/mapping_audit.json')['reference_A01']['CG_m'];closure=float(np.linalg.norm(measured_delta-predicted_delta))
    diagnostic=read(OUT/'native_mass_diagnostic/result.json');same=float(np.linalg.norm(np.array(diagnostic['native_CG_m'])-a['native_CG_m']))
    result={'created_utc':now(),'parts':parts,'native_minus_A01_global_CG_m':measured_delta.tolist(),'predicted_from_native_part_CG_difference_m':predicted_delta.tolist(),'first_moment_ledger_closure_error_m':closure,
        'coupled_and_uncoupled_reported_CG_difference_m':same,'beam_max_CG_difference_m':max(float(np.linalg.norm(p['CG_difference_m'])) for p in parts if p['element_type']=='beam'),
        'conclusion':'Reported native triangular-part first moments explain global CG offset; removing RBE3 has zero effect on reported CG. Underlying triangle mass/summary algorithm not established, so no corrective mass fitting applied.',
        'checks':{'first_moment_difference_accounted':closure<1e-7,'RBE3_not_cause_of_reported_CG_offset':same<1e-12,'native_part_masses_preserved':all(abs(p['native_mass_kg']-p['A01_mass_kg'])/p['A01_mass_kg']<1e-7 for p in parts)}}
    result['pass']=all(result['checks'].values());assert result['pass'];dump(OUT/'native_part_moment_audit.json',result);return result
def state_export_audit():
    cases=read(OUT/'r1/summary.json')['cases'];v=[]
    for c in cases:
        p=OUT/'r1'/c['case']['id']/'verified_states_SI.npz';a=np.load(p);vel=np.array(c['case']['velocity_m_s']);tm=a['time_s'];d=a['displacement_m']
        v.append({'case':c['case']['id'],'states':len(tm),'nodes':len(a['node_ids']),'maximum_translation_error_m':float(np.max(abs(d-tm[:,None,None]*vel))),
            'maximum_velocity_error_m_s':float(np.max(abs(a['velocity_m_s']-vel))),'all_finite':bool(all(np.all(np.isfinite(a[k])) for k in a.files)),
            'sha256':sha(p),'times_s':tm.tolist(),'scope':'Saved states re-read, no solver rerun; rounded animation export does not resolve sub-serialization errors.'})
    checks={'two_complete_5_state_3228_node_exports':all(r['states']==5 and r['nodes']==3228 for r in v),'displacement_identity':all(r['maximum_translation_error_m']<2e-5 for r in v),'uniform_velocity':all(r['maximum_velocity_error_m_s']<.001 for r in v),'all_finite':all(r['all_finite'] for r in v)}
    r={'created_utc':now(),'checks':checks,'pass':all(checks.values()),'cases':v};assert r['pass'];dump(OUT/'state_export_audit.json',r);return r
def prepare():
    assert not REPORT.exists() and not HANDOFF.exists();s=read(OUT/'r1/summary.json');assert s['whole_aircraft_uniform_translation_checks_pass'] and not s['all_literal_checks_pass'];count=preserved();parts=part_audit();export=state_export_audit();c=s['cases'][0];cfg=read(CFG);old=read(OUT/'before_state.json')
    times=[sum(e['seconds'] for e in r['runtime']) for r in s['cases']];table='\n'.join(f"| {r['case']['id']} | {sum(e['seconds'] for e in r['runtime']):.3f} | {r['actual_final_time_ms']:.6f} | {r['initial_KE_J']/1e9:.9f} | {r['checks_passed']}/{r['checks_total']} |" for r in s['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A02 — avion entier dans OpenRadioss, translation libre et limites de transfert

Le Boeing paramétrique complet A01 est maintenant un assemblage mécanique exécutable : **2860 nœuds de structure, 6538 coques triangulaires, 4600 poutres, 368 nœuds de masse et 368 interpolations locales RBE3**. Les deux calculs finaux de l'avion entier se terminent sans erreur ni avertissement. Ses 3228 nœuds conservent leur translation uniforme pendant environ 1 ms, sans force extérieure, contact, gravité, appui ni corps rigide global. Ce contrôle porte sur l'inertie et le mouvement libre, pas sur la résistance au choc.

**43/49 critères littéraux passent; six échecs sont conservés, trois par cas.** Le contrôle de translation passe; le transfert complet des moments de masse n'est pas déclaré entièrement qualifié. Aucun seuil de la configuration initiale n'est changé après observation. Le registre passe de120 à121 entrées : A02 est une itération d'assemblage complet, ses trois calculs Engine et un diagnostic Starter ne deviennent pas quatre nouvelles itérations.

## 1. Faits directement observés ou transcrits

Les fichiers A01 verification_r2 sont relus sans reconstruction. ConfigurationA02, paramètres, scripts, decks, journaux, fichiers binaires, CSV, tableauxSI et cinq états par cas sont conservés. Tous les3228 nœuds, y compris les masses additionnelles, sont présents dans l'export natif. Starter final annonce0erreur et0avertissement; Engine termine normalement. Versions et empreintes des exécutables sont journalisées dans chaque fichier *.execution.json (OpenRadioss Windows64 double précision, version2026; bibliothèque localev20260728-win64). Python3.14.3 et NumPy effectuent le transfert et l'audit; aucun tirage aléatoire, graine déclarée1102027.

Les références primaires de syntaxe sont [BEAM](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/beam_starter_r.htm), [TYPE3](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type3_beam_starter_r.htm), [SH3N](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/sh3n_starter_r.htm), [TYPE1](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type1_shell_starter_r.htm), [LAW1](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law1_elast_starter_r.htm), [ADMAS](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/admas_starter_r.htm) et [RBE3](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe3_starter_r.htm). Elles définissent les cartes du solveur et non la construction réelle d'un767. Les sources Boeing/GE d'A01 et les constantes statiques génériques restent celles de leur manifeste. Aucune nouvelle donnée de masse moteur ou de structure manquante n'est supposée acquise.

## 2. Résultats de modèles officiels

Aucun dommage, vitesse, attitude ou résultat NIST n'est utilisé comme cible. OpenRadioss est ici notre outil de calcul, pas une nouvelle reconstitution officielle. La vitesse test(-200,5,2)m/s est une condition ronde d'A02; elle n'est pas attribuée àAA11. Le signeX négatif fait avancer le nez dans le repèreA01 oùX pointe vers la queue. Les petitsY/Z vérifient les trois translations. Une plage historique de conditions d'impact reste à établir par données indépendantes avant une interprétation historique.

## 3. Affirmations des archives locales

Aucune archive ou vidéo rescannée, aucune source modifiée, aucun ancien calcul relancé. {count} fichiers prédécesseurs sont épinglés et contrôlés. V11F froid, V11R, les échecs I02I et la passationA01 restent identiques. I02I-M demeure différée, plan intact. L'état local prioritaire reste la route avion entier demandée le5octobre2026, et non l'ancien texteV8H.

## 4. Hypothèses, unités, propriétés et liaisons

Les entrées sont SI(m,kg,s,Pa,J,kgm²); le solveur reçoitmm,g,ms,MPa. Conversion:m×1000,kg×1000,Pa×1e-6,ρkg/m³×1e-6 versg/mm³,A×1e6 versmm²,I/J×1e12 versmm⁴; énergieNmm×0,001 versJ, quantitég·mm/ms×0,001 versN·s. Vitessem/s=mm/ms numériquement. Unités d'origine et conversions restent dans leJSON.

Les coques gardentρ2780kg/m³,E73,1GPa,ν0,33; éléments internesρ2810kg/m³,E71,7GPa,ν0,33. LAW1 intact élastique, aucun historique endommagé modifié, aucune plasticité ou rupture introduite. TrianglesC0/Ish3n2, Ismstr4, intégration élastique globaleN0; poutresTYPE3 avec aire/inertiesA01, géométrie non linéaire, cisaillement et rotations reliées. Axes locaux: projection de la base globale la moins parallèle à chaque poutre, normalisation, contrôle du produit vectoriel; Iyy=Izz dansA01 rend le choix résiduel d'orientation invariant en flexion. J=2I demeure une équivalence hypothétique, pas une section certifiée. Les zéros des champs d'amortissement activent certains défauts natifs: flexion poutresdf0,01 et champcoquedn0,015; ils sont signalés, et ne dissipent ici aucune énergie puisque les déformations sont nulles. Le champdn concerne le quadrilatèreQEPH, absent de notre maillage triangulaire.

Masse de structure nativeρ*t*aire ouρ*A*longueur, sans ajout des anciennes quadratures structurelles. Les368 points de carburant, moteurs, charge utile et réserve vide conservent leurs masses/positionsA01, puisADMAS5 etRBE3 les relient chacun aux8nœuds structuraux les plus proches. Interpolation en translation, poids égaux, I_modif2(pas de correction automatique), Iform2(purement cinématique). Les hôtes ne sont pas quasi collinéaires: conditionnement maximal3,183 pour l'ajustement local de mouvement rigide. Aucun nœud de masse n'est hôte d'un autreRBE3. Cette connexion répartit une inertie, elle ne fournit ni raideur supplémentaire à la structure manquante ni résistance interne de moteur ni loi d'écoulement du carburant.

La réserve vide53187,424kg(64,7% du vide) inclut structure manquante, systèmes et aménagements: l'appeler entièrement«nonstructurelle» serait faux malgré le nom de la carteADMAS. Moteurs2×4500kg et cylindres d'inertie, fuel30000kg, charge10000kg restent des hypothèses. Assemblages aile/fuselage et pylônes sont les poutres équivalentes d'A01, sans rupture. Un contrôle de translation n'éprouve pas ces résistances.

## 5. Résultats dérivés, bilans et essais de sensibilité

M={c['native_mass_kg']:.9f}kg contre122159,1859781kg A01. La prédiction de masses structurelles concentrées aux sommets/bouts conserveM etCG, et change la norme du tenseur d'inertie de0,067305%. Les moments réellement annoncés parStarter changent la norme de0,127335%, sous le seuil1% déclaré; CGnatif=({c['native_CG_m'][0]:.9f},{c['native_CG_m'][1]:.9f},{c['native_CG_m'][2]:.9f})m, écart{1000*c['native_CG_error_m']:.6f}mm. Le seuilCG10µm échoue; aucune masse n'est ajustée pour masquer cet écart.

Le diagnostic conserve exactement les coordonnées/propriétés/masses de l'avion entier et retire uniquement368RBE3, sans lancerEngine. SonCG annoncé est identique. Le bilan des18parts retrouve le décalage global à{parts['first_moment_ledger_closure_error_m']:.3e}m: les centres des parts triangulaires natifs diffèrent des barycentres de surfaceA01; les parts poutres coïncident à~1e-7m. Le mécanisme exact de résumé/concentration natif des triangles reste à vérifier; il n'est pas attribué arbitrairement auxRBE3. Le deck diagnostic aux masses non reliées n'est jamais accepté comme modèle de vol ou d'impact.

K0=½M·v²={c['expected_KE_J']:.3f}J=2,444955028GJ. P0=Mv=(-24431837,195620;610795,929891;244318,371956)N·s. Réactions de support inexistantes parce qu'aucun support n'est défini. Travail extérieur0, énergie interne0, rotation0, hourglass0 dans les sorties. Bilan E=Ktranslation+Krotation+Uinterne+hourglass; ΔE−Wext=0 à la précision duCSV. ΔP=0 à la précision duCSV. Aucune énergie d'impact, de fracture, de feu ou d'ejection n'est calculée.

| Cas | Temps Starter+Engine+CSV(s) | Dernier état(ms) | K initiale(GJ) | Critères du cas |
|---|---:|---:|---:|---:|
{table}

Le facteur de pas0,8 est réduit à0,4 sur le même assemblage entier, sans changer masse/propriétés/conditions initiales. Les états et bilans restent identiques aux précisions exportées; aucun contrôle élémentaire ancien n'est relancé. Chaque point vérifieu(t)=v0*t etv(t)=v0 à ses horodatages réels. Cinq états,20 ou21 échantillons globaux selon cadence native; l'exportSI est relu indépendamment(4/4 critères). LeCSV arrondit les bilans à~7chiffres significatifs; l'ASCII d'animation arrondit aussi les coordonnées, identitéposition−position0−déplacement jusqu'à0,0505mm. Les déplacements, vitesses et identifiants sont utilisés pour le contrôle; les positions arrondies ne servent pas à revendiquer une précision submicrométrique.

Premier essair0 conservé:40avertissements de champs réservés contenant des zéros, malgré terminaison normale. r1 remplace ces champs par des blancs aux positions documentées. Ni seuil, donnée physique ni vitesse ne change. r0 reste visible(24/28 critères), ainsi que son générateur et ses sorties. r1:43/49, contrôle spécifique de translation accepté, **tout le transfert massique n'est pas qualifié**.

## 6. Contradictions et informations manquantes

Chaque cas garde trois critères stricts en échec: CG1,2045mm contre10µm; colonne«ADDED MASS»4,917383e-7g contre1e-8g; fin1,000260ms contre1,000000ms avec tolérance1e-5ms. L'ajout apparent vaut4,02539e-15 deM, aucun mécanisme de mass scaling n'est activé, et le dépassement vaut~une fraction du dernier pas. Ces observations évoquent arithmétique/scheduling natifs, **interprétations et non excuses pour effacer les échecs**. Un audit futur peut distinguer résuméStarter, inertie nodale effective et précision des sorties. Aucun seuil n'est relaxé dansA02.

Le mouvement sans déformation est un contrôle nécessaire de l'assemblage, pas une qualification des modes de rotation ou des efforts. Les nombreuses données internes manquantes dominent toujours la fidélité de résistance au choc: épaisseurs, sections, découpes, fixations, moteur détaillé, carburant, loi d'écrasement, plasticité et fracture. Aucun changement de propriétés d'un matériau déjà endommagé, aucune énergie de dommage modifiée. Ne pas appliquer aux nouveaux assemblages une ancienne loiI02I échouée comme si elle était validée. Grande déformation et fragmentation non qualifiées; localisation en flexion après fracture complète non validée; température imposée≠incendie calculé; aucun effondrement réel validé. Blender/OBJ reste une visualisation; seuls les étatsNPZ de ce contrôle sont reliés aux sorties vérifiées du solveur.

## Suite et reprise

A03: **assembler l'avion entier avec une façade représentative et préparer/lancer un premier contact borné**, en partant des moments natifs explicitement sauvegardés et en conservant le problèmeCG ouvert. Déclarer la portée du test(élastique/intact et premier contact), les conditions, les hypothèses de façade et les plafonds avant les sorties. Vérifier les forces/contact, réactions et énergie, garder toute réponse non physique. Pas de résultat de dégâts fixé, pas de valeurNIST à rejoindre; les plages historiques nécessitent des sources indépendantes. Ne pas revenir automatiquement à une chaîne de coupons. Le bilan de moments triangulaires est une question précise à résoudre si elle affecte le contact, pas une raison de retarder indéfiniment l'assemblage.

Les anciens calculs restent en cache. Reprise rapide: complete_aircraft_a02.py verify contrôle empreintes/administration et résultats sauvegardés, sans solveur. run_aircraft_a02.py ne doit être utilisé que dans une nouvelle révision/dossier; chaque deck et tentative refusent l'écrasement. A02 apporte1itération en attente sur2; publication prévue aprèsA03 vérifiée. Aucun nouveaupostX ni action surYoremi.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Passation compacte AIRCRAFT-A02 → A03

Lire AGENTS.md puis harness/state.json(prioritaire) et cette passation. Route voulue: Boeing entier et conditions explicites, sans ajuster versNIST. AncienV8H périmé; I02I-M différée et son plan intact.

A02: avionA01 transféré àOpenRadioss,2860nœuds structuraux+368masses/RBE3,6538triangles+4600poutres. Dossiersr0/r1 conservés. Deux contrôles finaux de translationlibre~1ms,v=(-200,5,2)m/s(test, pasAA11),facteursdt0,8/0,4: terminaisonnormale,0erreur/0avertissement,3228nœuds×5états,csv etNPZ. Aucune forceextérieure,gravité,appui,contact ou corpsrigideglobal. Energieinterne/rotation/hourglass/travail0; énergie etP conservées àprécisionCSV. TroisEngine au total(r0+2r1),4Starter(dontdiagnostic entier sansRBE3),zéro anciencalcul relancé.

Résultats: r1/summary.json,rapport_aircraft_a02.md,configaircraft_a02_predeclaration.json. **43/49critères littéraux**, contrôletranslation seul passe; transfert completmassique/déformation/impact nonqualifiés. Échecs×2: CG1,204527mm(contre10µm),addedmass4,917383e-7g(contre1e-8g, fraction4e-15),fin1,000260ms(contre1ms,tol1e-5ms). Seuils immuables. Inertie native écartnorme0,127335%,predictionnodes0,067305%. M122159,1859781kg. Diagnostic sansRBE3 retrouve exactementCG/inertieStarter; native_part_moment_audit explique l'écartCG par centresdesparts triangulaires, à{parts['first_moment_ledger_closure_error_m']:.3e}m. Algorithmeprecisàdocumenter, pas de massecompensatrice ajustée. Exportcoordonnéesarrondi~0,05mm; contrôlerdéplacements/vitesses auxhorodatagesréels.

A03 concret: avionentier+façadereprésentative,conditionsgelées,bilanforces/énergie,calculpremiercontact borné. Utiliser momentsnatifs sauvegardés en exposantl'écartCG; résolutionlocale siimpactée. Déclarer vitesse/attitude etportéeélastique/intact, sans simulerune rupture nonqualifiée. Sourcesindépendantes nécessaires pour conditionsAA11; géométriefaçade héritée peut dépendreNIST, le signaler séparément desortiescibles. Pasde nouvelenchaînement automatique decoupons. Garder échecsprédictifs; pasdefitversNIST. Toute correction devra avoir justificationindépendante et versionvisible.

Réservevide53,187t inclut structuremanquante,pasraideurcachée. Moteurséquivalents4500kg chacun,fuelsansécoulement,attachesélastiques sansrupture; toushypothèsesA01. Défautsamortissementnatif signalés dansrapport. V11F/V11R/brancheV11S etéchecsI02Ipréservés. Flexionaprèsfracture/feu/effondrementréel nonvalidés; Blender visualisation.

Vérification rapide sansrecalcul: C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_aircraft_a02.py verify. Préserver{count}fichiersanciens etnouveaumanifeste. CadenceGithub: A02pending1/2; prochainepublicationA02+A03après vérification. Pas depublication immédiate niX niYoremi. Registre121aprèsA02.
''',encoding='utf-8')
    dump(OUT/'release_audit.json',{'created_utc':now(),'integrity_pass':True,'specific_translation_control_pass':True,'all_scientific_literal_criteria_pass':False,'strict_failed_criteria_preserved':True,'old_files_preserved':count,'native_moment_audit':parts['checks'],'state_export_audit':export['checks'],'harness':harness(),
        'solver_jobs':3,'starter_jobs':4,'old_solver_reruns':0,'python_version':sys.version,'numpy_version':np.__version__})
    scripts=[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_aircraft_a02.py','audit_aircraft_a02.py','diagnose_aircraft_a02_mass.py','complete_aircraft_a02.py']]
    paths=[p for p in OUT.rglob('*') if p.is_file()]+scripts+[CFG,HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)],'excluded':['self','publication_verification.json','mutable administration state registry cadence'],'scope':'Reproducible bounded whole-plane controls; failed scientific criteria preserved.'})
    print(json.dumps({'prepared':True,'old_files_preserved':count,'strict_checks':f"{s['checks_passed']}/{s['checks_total']}"}))
def register():
    assert REPORT.exists() and HANDOFF.exists() and not (OUT/'publication_verification.json').exists();preserved();s=read(OUT/'r1/summary.json');assert s['whole_aircraft_uniform_translation_checks_pass']
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']: assert sha(ROOT/'harness'/name)==sha(OUT/('before_'+name.split('/')[-1]))
    for r in read(OUT/'artifact_manifest.json')['files']: assert sha(ROOT/r['path'])==r['sha256'],r['path']
    v=harness();assert v['Status']=='PASS';state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');assert state['current_iteration']=='AIRCRAFT-A01' and cycle['pending_count']==0
    t=now();status='completed_whole_aircraft_free_translation_with_mass_mapping_precision_limits'
    record={'experiment_id':'WTC1-AIRCRAFT-A02','registered_at':t,'status':status,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'r1/summary.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),
        'checks_passed':s['checks_passed'],'checks_total':s['checks_total'],'all_literal_criteria_pass':False,'whole_aircraft_uniform_translation_control_pass':True,'native_CG_error_m':s['cases'][0]['native_CG_error_m'],'native_inertia_relative_norm_error':s['cases'][0]['native_inertia_relative_norm_error'],
        'solver_jobs':3,'starter_jobs':4,'old_solver_reruns':0,'old_files_preserved':len(read(OUT/'preservation_before.json')['files']),'NIST_outcomes_used':False,'impact_qualified':False,'whole_aircraft_deformation_qualified':False,'whole_aircraft_mass_mapping_fully_qualified':False,'next_iteration':'AIRCRAFT-A03'}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f: f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A02',current_status=status,next_iteration='AIRCRAFT-A03',next_objective=read(CFG)['next_objective'],updated_at=t)
    state['aircraft_a02_key_results']=record;state['user_steering_2026_10_05']['next']='AIRCRAFT-A03'
    state['validated_artifacts'].update(aircraft_a02_report=rel(REPORT),aircraft_a02_results=rel(OUT/'r1/summary.json'),aircraft_a02_handoff=rel(HANDOFF),aircraft_a02_native_moments=rel(OUT/'native_part_moment_audit.json'),aircraft_a02_states=rel(OUT/'r1/translation_dt080/verified_states_SI.npz'))
    cycle.update(pending_iterations=['AIRCRAFT-A02'],pending_count=1,next_publication_after='A02+A03 after A03 verified; whole aircraft route, strict failures included',updated_at=t)
    dump(ROOT/'harness/publication_cycle.json',cycle);dump(ROOT/'harness/state.json',state);verify(write=True)
def verify(write=False):
    count=preserved();m=read(OUT/'artifact_manifest.json');bad=[r['path'] for r in m['files'] if sha(ROOT/r['path'])!=r['sha256']];s=read(OUT/'r1/summary.json');old=read(OUT/'before_state.json');state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');v=harness()
    reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();suffix=reg[len(prefix):].decode('utf-8').splitlines();protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy','open_limitations']
    source=read(OUT/'source_manifest.json');checks={'all_new_artifact_hashes':not bad,'predecessors_unchanged':True,'configuration_immutable':sha(CFG)==read(OUT/'declaration_guard.json')['sha256'],'registry_prefix_unchanged':reg.startswith(prefix),
        'one_new_record':len(suffix)==1 and json.loads(suffix[0])['experiment_id']=='WTC1-AIRCRAFT-A02','state_route':state['current_iteration']=='AIRCRAFT-A02' and state['next_iteration']=='AIRCRAFT-A03',
        'prior_results_and_limits_preserved':all(old[k]==state[k] for k in protected),'M_still_deferred':state['user_steering_2026_10_05']['deferred_iteration']=='IMPACT-I02I-M',
        'pending_one_of_two':cycle['pending_iterations']==['AIRCRAFT-A02'] and cycle['pending_count']==1,'saved_inputs_unchanged':all(sha(ROOT/r['path'])==r['sha256'] for r in source['input_files']),
        'translation_control_saved_and_passed':s['whole_aircraft_uniform_translation_checks_pass'],'strict_failures_retained':not s['all_literal_checks_pass'] and s['checks_passed']==43 and s['checks_total']==49 and all(len(c['literal_failed_checks'])==3 for c in s['cases']),
        'saved_state_re_read_pass':read(OUT/'state_export_audit.json')['pass'],'native_first_moment_ledger_closed':read(OUT/'native_part_moment_audit.json')['pass'],'no_full_mapping_or_impact_claim':not s['whole_aircraft_mass_mapping_fully_qualified'] and not s['impact_qualified'] and not s['whole_aircraft_deformation_qualified'],
        'no_NIST_outcome_fit':not read(CFG)['outcome_calibration_allowed'] and not s['NIST_outcomes_used'],'zero_old_solver_reruns':s['old_solver_reruns']==0,'harness_pass':v['Status']=='PASS'}
    result={'created_utc':now(),'pass':all(checks.values()),'checks':checks,'new_files_checked':len(m['files']),'old_files_checked':count,'harness':v,'scientific_literal_checks':'43/49','translation_control_pass':True,'all_literal_criteria_pass':False,'impact_qualified':False,'pending_Github_iterations':1,'next_iteration':'AIRCRAFT-A03'}
    assert result['pass'],result
    if write: dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','register','verify']);a=ap.parse_args();globals()[a.action]()
