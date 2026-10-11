"""Durable raw-result assessment before preservation/final sealing; no registration."""
from run_aircraft_a34 import *

def main():
    guard();p=OUT/'ongoing_assessment.json';assert not p.exists();rows=read(OUT/'native_case_summary.json')['cases'];assert len(rows)==4;fields=read(OUT/'native_fields_review.json');ref=read(OUT/'cached_reference_field_review.json')
    h=dict(np.load(OUT/'w1/FACE_BENDING_N48_Z4/histories_SI.npz'));h2=dict(np.load(OUT/'w1/FACE_BENDING_N48_Z4_HALF/histories_SI.npz'));mask=(h['time_ms']>=h2['time_ms'][0])&(h['time_ms']<=h2['time_ms'][-1]);T=h['time_ms'][mask];ie=h['IE_J']+h['HE_J'];ie2=h2['IE_J']+h2['HE_J'];diff=float(abs(ie[mask]-np.interp(T,h2['time_ms'],ie2)).max());ratio=float(np.median(h2['time_step_ms'][1:])/np.median(h['time_step_ms'][1:]));dt={'actual_dt_ratio':ratio,'elastic_energy_difference_J':diff,'checks':{'actually_shorter':ratio<.6,'energy_converges':diff<.002*float(abs(ie).max())+1e-7}}
    meshes=[]
    for label,aa,bb in [('XY24_to48',PREV/'w1/FACE_BENDING_N24_Z4/review.json',OUT/'w1/FACE_BENDING_N48_Z4/review.json'),('Z4_to8',OUT/'w1/FACE_BENDING_N48_Z4/review.json',OUT/'w1/FACE_BENDING_N48_Z8/review.json')]:
        a=read(aa);b=read(bb);ea=a['native_IE_J']+a['native_HE_J'];eb=b['native_IE_J']+b['native_HE_J'];delta=abs(ea-eb)/eb;meshes.append({'comparison':label,'source_cases':[rel(aa),rel(bb)],'native_J':[ea,eb],'difference_fraction':delta,'pass':delta<.05,'original_individual_gates':[a['pass'],b['pass']]})
    assessment={'created_utc':now(),'iteration':'AIRCRAFT-A34','configuration_sha256':streamsha(CFG),'native_complete':True,'native_controls':4,'native_individual_sets_passed':sum(r['pass'] for r in rows),'native_full_balances_passed':sum(r['checks']['native_full_balance'] for r in rows),'failed_controls':[{'case':r['case'],'checks':[k for k,v in r['checks'].items() if not v]} for r in rows if not r['pass']],'native_field_samples':len(fields['samples']),'native_fields_pass':fields['pass'],'cached_reference_field_refinement_pass':ref['pass'],'time_refinement':dt,'spatial_refinement':meshes,'interior_relaxation_qualified':False,'whole_insertion_ready':False,'old_native_solver_reruns':0,'software_installation_or_compilation_performed':False,'registration_pending':True,'preservation_and_final_seal_pending':True,'objective1_complete':False}
    dump(p,assessment);ex=[{'path':rel(q),**read(q)} for q in sorted(OUT.rglob('*.execution.json'))];dump(OUT/'runtime_manifest_live.json',{'created_utc':now(),'CPU_threads_per_solver':1,'GPU':False,'software':'OpenRadioss native win64 double precision20260728','executions':ex,'execution_seconds_sum':sum(x.get('seconds',0) for x in ex),'engine_sha256':streamsha(RUNTIME/'engine_win64.exe')})
    table='\n'.join(f"| {r['case']} | {r['native_IE_J']+r['native_HE_J']:.9g} | {r['independent_reference_J'] if r['independent_reference_J'] is not None else 'sans objet'} | {r['maximum_residual_J']:.9g} | {'réussi' if r['pass'] else '**échoué** : '+', '.join(k for k,v in r['checks'].items() if not v)} |" for r in rows)
    (OUT/'rapport_preliminaire_aircraft_a34.md').write_text(f'''# A34 — résultats bruts vérifiés, scellage en attente

Quatre nouveaux calculs natifs terminés. Un ensemble individuel passe, trois échouent au champ intérieur. Les quatre bilans et les douze échantillons natifs passent. Rapport préliminaire; conservation cumulative, rapport final, manifeste et inscription restent à terminer.

## 1. Faits directement observés ou transcrits

Graine1102059, aucun tirage. Même plaque 10×10×0,5 mm, densité0,00183g/mm³, masse0,0915g, TYPE6/Isolid24, Ismstr4, Icpre3, Iframe2, source LAW12 et axesY,−X,Z inchangés. Maillage48 dans le plan, quatre/huit cellules physiques dans l’épaisseur. Faces seules prescrites en flexion, intérieur libre. Rotation libreY, flexionZ4/Z8 et flexionZ4à demi-pas. Quatre nouvelles exécutions, aucune ancienne relancée. Douze champs natifs: identifiants, finitude, coordonnées/déplacements avec borne d’impression, absence de suppression.

## 2. Résultats d’un modèle officiel

Formulation HEPH24 à stabilisation physique selon la documentation TYPE6 déjà conservée. La présence de cette formulation ne démontre pas l’équivalence de son opérateur à la référence conventionnelle. Même binaire Windows20260728, empreinte et journaux dans runtime_manifest_live.json. Aucun résultatNIST utilisé comme référence.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse d’archive, photographie ou vidéo. Les budgets/materials et inventaires des prises courbes hérités restent inchangés. Aucun résultat du coupon identifié comme propriété d’un assemblage réel d’AA11.

## 4. Hypothèses propres au modèle

Témoin LAW12élastique A29, E/G/coefficientstransverses conservés; seuils géants sans qualification historique de résistance ou rupture. κ=0,001/mm, rampe0,1ms, champ exact aux deux faces identique A33; ΩY=10rad/ms durant0,05ms. Référence3D indépendante192×192×16A32 avec mêmes faces et intérieur libre. Ses changements de champs Z8→16etXY96→192 sont vérifiés aux nœuds correspondants avant calcul natif. Tolérances originelles conservées: énergie2%+10⁻⁷J, déplacement intérieur2%de la relaxation+2×10⁻⁶mm, raffinements5%spatial/0,2%temporel, rapport de pas<0,6. Aucun seuil élargi après résultat, aucune densité/massescaleouRKEinventé.

## 5. Résultats dérivés

| Contrôle | IE+HE(J) | Référence au temps natif(J) | Résidu maximal(J) | Ensemble original |
|---|---:|---:|---:|---|
{table}

Z8 atteint un écart énergétique d’environ0,038%, mais échoue au champ intérieur. Erreurs de déplacements d’environ7,8×10⁻⁶mm face à une tolérance2,74×10⁻⁶mm. Les deux contrôles du champ de référence passent au seuil déclaré. Rapport de pas demi/initial={ratio:.9g}; différence énergétique={diff:.9g}J. Les variations énergétiques XY/Z passent5%, sans remplacer les critères individuels échoués. Bilans, impulsions et travail aux faces passent; les détails sont conservés.

## 6. Contradictions et informations manquantes

L’accord énergétique se rapproche mais le défaut du champ intérieur persiste après raffinement XY/Z/temps. Sa cause n’est pas identifiée: ne pas l’attribuer à un opérateur précis sans contrôle distinct. Comparaison avec une formulation pleinement intégrée et examen des opérateurs stabilisés possibles avant toute prise courbe. Propriétés historiques, rupture, décollement et modèle entier restent ouverts.

A32+A33 publiées et vérifiées, ancien registre152et étatA33→A34. A34n’est pas encore inscrite. Aucun processus natif restant. Une compilation séparée MUMPS est proposée dans A33, accord Jeremy demandé et non reçu à ce stade; aucune installation ou compilation effectuée. Meilleur impact entierA20=20ms; vidéo3D10secondes physiques incomplète.
''',encoding='utf8')
    hand=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A34_LIVE_HANDOFF.md';hand.write_text('''# Reprise A34 en cours

A32+A33 publiées et vérifiées : https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-11-aircraft-a32-a33
Preuve : outputs/github_publication/updates_2026-10-11_aircraft_a32_a33/final_remote_verification.json
Commits scientifique72c5bf0ab683a8cc74e6e47c433cf1de7a4d1f92, final5c997b19d9b37d4e5ac5fecdd3518663c172e542, deux CI réussies. Une archive140422033octets etSHA256SUMS129octets; SHAarchive1992f267169d2a90fb0a04fa5efdb6b39d96e592912f914560f61097275cae2e. Registre152, étatA33→A34, cadence0enattente, prochainepaireA34+A35.

A34déclarée après publication. Quatre nouveaux calculs complets, un ensemble individuel réussi, trois échecs independent_interior_relaxation. Tous les bilans et douze échantillons natifs passent. Aucun processus actif. Lire data/aircraft_a34_predeclaration.json, native_case_summary.json, ongoing_assessment.json, rapport_preliminaire_aircraft_a34.md et cached_reference_field_review.json. Le raffinement du champ indépendant passe les seuils déclarés. Z8donne0,038%d’écart énergétique, mais environ7,8e-6mmd’erreur de déplacement pour2,74e-6mmadmis; XY/Z/temps ne suffisent pas à fermer ce défaut. Ne pas annoncer une cause démontrée ou une qualification entière.

Reste conservation cumulative des anciens fichiers, rapport final six rubriques, manifeste/scellage puis registre/état après sorties existantes. A35peut comparer la formulation pleinement intégrée Isolid18déjà qualifiée localement dans A29/A31avec Isolid24, sur mêmes faces libres et même référence, avant toute insertion. Pas de nouvelle masse/densité, seuil relâché ou RKEartificiel.

La proposition A33native_build_preflight est concrète et la question d’accord pour installer les outils manquants dans UbuntuWSLetcompiler un solveur séparéMUMPSa été posée dans le chat. Aucune réponse reçue lors de cette passation. Pas d’installation/compilation sans réponse humaine explicite. Aucun nouveau solveur lancé, aucun paquet installé. Nouvelle version ne serait pas identique au binaire Windows; pas de restart compatible présumé.

Objectif10secondes physiques toujours actif et incomplet, meilleur entierA20=20ms. Publication cadence suivante après A34+A35scellées; garder les échecs précédents et versions des publications.
''',encoding='utf8')
    print({'A34_live_handoff_written':True,'native_cases':4,'native_field_samples':12,'registry_unchanged':True,'qualification':False},flush=True)

if __name__=='__main__':main()
