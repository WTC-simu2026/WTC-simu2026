"""Seal A13 scientific diagnostic, then register a single durable iteration."""
import argparse,json,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
from run_aircraft_a13 import ROOT,OUT,CFG,REV,read,dump,sha,rel,now,guard,harness
REPORT=OUT/'rapport_aircraft_a13.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A13_HANDOFF.md'
NEXT="AIRCRAFT-A14 : réutiliser A12/A13 sans relance ancienne. Tester l'objectivité spatiale du contact sur une plaque élastique plane à 200 m/s, avec masse/aire/gap fixes et raffinements indépendants : contrôler le nombre de nœuds actifs, la raideur de pénalité nodale et sa relation à l'aire tributaire. Déclarer séparément tout contact pondéré par aire, sans choisir Stfac sur un dommage NIST. Qualifier les bilans énergie/impulsion et le demi-pas avant de réessayer le radôme. Vérifier la convention temporelle v + dt*a/2 à partir des sorties natives et de la source exacte, sans décaler le ledger ni crédit rétroactif. TYPE25 ferme l'énergie mais sa variation spatiale de 23,53 % reste échouée ; DKT18/TYPE7 ne ferme pas l'énergie. Aucun allongement avion complet avant fermeture locale et convergence spatiale. Module Boeing parallèle v2 séparé, inertie/dynamique libre bloquées. Premières secondes, écrasement, rupture et impact historiques non qualifiés."

def streamsha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()

def checkrows(rows):
    for r in rows:
        p=ROOT/r['path'];assert p.stat().st_size==r['bytes'] and streamsha(p)==r['sha256'],r['path']
    return len(rows)

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists() and not (OUT/'artifact_manifest.json').exists()
    s=read(OUT/'campaign_review.json');assert s['integrity_only_pass'] and len(s['cases'])==13 and not s['rejected_cases']
    preservation=read(OUT/'preservation_verification.json');assert preservation['pass'] and preservation['files']==7240
    v=harness();assert v['Status']=='PASS';dump(OUT/'harness_after_calculations.json',v)
    ET.parse(OUT/'visualisation/bilans_maillage.svg');vis=read(OUT/'visualisation/provenance.json');assert vis['data_schema_pass'] and vis['native_displacement_scale']==1
    by={r['case']['id']:r for r in s['cases']};mesh=next(q for q in s['comparisons'] if q.get('files') and '/T25_L2/' in q['files'][0] and '/T25_L3/' in q['files'][1]);half=next(q for q in s['comparisons'] if q['type']=='half_dt')
    type25=[by[f'T25_L{x}'] for x in range(4)]+[by['T25_L2_HALF']]
    assessment={'created_utc':now(),'TYPE25_local_energy_pass_all_five_radome_cases':all(r['checks']['energy_local'] for r in type25),'TYPE25_spatial_pass':False,'TYPE25_half_dt_pass':half['impulse_pass'] and half['generated_pass'],'high_speed_TYPE25_witness_pass_both_steps':all(by[k]['all_checks_pass'] for k in ['W25_DT050','W25_DT025']),'high_speed_TYPE7_witness_pass':False,'DKT18_TYPE7_local_energy_pass':False,'native_velocity_plus_half_step_acceleration_reduces_RKE_mismatch':True,'timing_diagnostic_only_no_retroactive_acceptance':True,'full_aircraft_extension_allowed':False,'unique_energy_cause_proven':False,'historical_impact_qualified':False,'seconds_impact_calculated':False}
    dump(OUT/'scientific_assessment.json',assessment)
    table='\n'.join(f"| {r['case']['id']} | {r['actual_end_ms']:.8f} | {r['final_impulse_Ns'][0]:.6f} | {r['final_generated_J']:.3f} | {r['final_energy_residual_J']:.4f} | {', '.join(r['failed_checks']) or 'aucun'} |" for r in s['cases'])
    comp='\n'.join(f"| {' / '.join(q.get('cases') or [Path(p).parent.name for p in q['files']])} | {q['type']} | {100*q['impulse_difference_fraction']:.5f} | {100*q.get('generated_difference_fraction',q.get('energy_residual_change_fraction_initial',0)):.5f} | {q['impulse_pass']}/{q.get('generated_pass',q.get('energy_pass'))} |" for q in s['comparisons'] if q['declared_acceptance'])
    w7=by['W7_DT025'];w25=by['W25_DT025'];coarse=by['T25_L0'];phase=coarse['timing_candidates'];dkt=by['DKT7_L2']
    REPORT.write_text(f'''# AIRCRAFT-A13 — énergie, contact alternatif et formulation triangulaire

Treize nouveaux calculs principaux et treize reprises observateur se terminent normalement, sans avertissement Starter. Aucun ancien calcul relancé. L'intégrité du harnais et des fichiers passe ; la qualification scientifique globale reste échouée. La fenêtre du radôme reste **0,4 ms = 0,0004 s**.

Le contact TYPE25 ferme le bilan énergétique sur quatre maillages et un demi-pas du nez isolé. Entre les deux maillages les plus fins, l'impulsion varie encore de **{100*mesh['impulse_difference_fraction']:.2f} %** et l'énergie générée de **{100*mesh['generated_difference_fraction']:.2f} %** : seuils de 10 % échoués. TYPE25 n'est donc pas encore transférable à l'avion complet. Le remplacement C0 par DKT18 en gardant TYPE7 conserve un déficit local. L'amélioration énergétique est une discrimination numérique, pas une sélection de contact pour l'événement historique.

## 1. Faits directement observés ou transcrits

13 Starter sans erreur ni avertissement, 13 terminaisons principales normales, 13 reprises de fin isolées. Les CSV sont vérifiés contre tous les records binaires natifs T01. Le premier record T02 donne la fin principale réelle, mais les réactions de cette reprise sont exclues des critères d'appui : le cumul REAC s'y réinitialise. REAC principal et FNX/FNY/FNZ sont traités comme impulsions cumulées, sans réintégration. L'observation ici concerne les fichiers solveur, aucun film historique.

Les masses nodales sont décodées indépendamment des animations ; positions, vitesses, identifiants et connectivité sont contrôlés. Pas d'ajout de masse, érosion, travail externe, travail plastique ou ressort dans ces témoins. Le premier agrégat authoritative_review.json a été produit pendant que le reste de la campagne tournait : il est conservé comme tentative incomplète et n'a jamais servi au registre. **campaign_review.json** est l'agrégat final des 13 cas, avec garde exigeant leur terminaison ; aucune qualification n'est tirée du premier agrégat.

## 2. Résultats d'un modèle officiel

Les dimensions et les entrées acier de la façade restent celles héritées de la chaîne NIST utilisée par A11. La façade tronquée et immobilisée n'est pas le bâtiment historique. Aucun dommage NIST ne sert de cible. Les résultats nouveaux sont ceux d'OpenRadioss installé v20260728, avec empreintes exécutables, durées et arguments dans les journaux ; ce ne sont pas des résultats d'impact NIST.

## 3. Affirmations provenant des archives locales

Aucune vidéo, photographie ou nouvelle source d'archive inspectée. Les **7240 fichiers antérieurs**, soit {preservation['bytes_hashed']/1e9:.2f} Go, ont fait l'objet d'un nouveau contrôle SHA-256 complet en flux : zéro différence. La correction de sélection du manifeste parallèle déjà documentée en A12 est appliquée explicitement au point de départ, sans modifier le premier échec ni les sources. Le module Boeing parallèle v2 reste séparé ; inertie et dynamique libre encore bloquées. V11F/V11R et les branches différées sont conservées.

## 4. Hypothèses propres au modèle

Déclaration aircraft_a13_predeclaration.json, graine 1102038, zéro tirage. Radôme libre sans RBE3, restes d'avion, moteurs ni ADMAS. Les 216/864/3456/13824 triangles conservent la surface plane par morceau, les matériaux et la masse de 41,062724 kg. La façade conserve les 540 quadrilatères fixes d'A12. Vitesse [-200,5,2] m/s, gap 5 mm, sans frottement ; rupture, cœur écrasable, délamination et auto-contact absents.

TYPE25 est déclaré comme alternative à pénalité constante, avec groupe nodal secondaire, surface principale, Istf=4, Stfac=1, Igap=5, épaisseurs de contact secondaire/principale de 5 mm chacune à facteur 1, soit gap total 5 mm. Bord rond Ishape=2, Iedge=1000, Ipstif=0 et VIS_s=1e-20. Sa raideur, son traitement des bords et son algorithme diffèrent de TYPE7 : la comparaison ne distingue pas une cause unique. Ces choix viennent de [la documentation primaire TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm), sans ajustement sur des dégâts historiques.

Le contrôle coque remplace seulement Ish3n=2 par Ish3n=30 (DKT18) dans TYPE51 ; mêmes couches, orientation, géométrie, contact TYPE7 et amortissement déclaré. [La documentation TYPE51](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm) décrit ces deux formulations. L'inertie numérique peut changer ; la formule c3inmas C0 n'est pas créditée à DKT18 sans preuve propre.

Témoin rapide : plaque LAW1 20×20×1 mm, masse 0,001112 kg, surface fixe 40×40 mm ; mouvement X seul et rotations bloquées. Départ x=-1,01 mm, gap 1 mm, vx=200 m/s. KE initiale 22,24 J, impulsion de rebond conservatif 0,4448 N·s. Horizon 0,02 ms. TYPE7 et TYPE25 aux facteurs de pas 0,05/0,025 ; pas libre distinct. Matériau E=70000 MPa, rho=0,00278 g/mm³, nu=0,3 synthétique, aucun crédit Boeing.

Ledger inchangé : KE + rotation globale + IE + hourglass + spring + contact élastique/frottement/amortissement − travail externe. Chaque terme une fois ; RKE par pièce ou reconstruit jamais ajouté. Critères radôme hérités A12 : résidu≤5 % énergie générée+1 J dès >100 J, global≤0,5 % initial, maillage≤10 % impulsion/énergie, demi-pas≤5 %/10 %. Témoin rapide : énergie et vitesse de rebond à 1 %, impulsion à 1 %, appuis à 2 %. Aucun seuil élargi.

## 5. Résultats dérivés

| Cas | Fin native ms | Impulsion X native N·s | Énergie générée J | Résidu final J | Critères échoués |
|---|---:|---:|---:|---:|---|
{table}

FNX est de signe positif pour la plaque allant en +X et négatif pour le radôme allant en −X : impulsion sur la surface principale, opposée au changement de quantité de mouvement du secondaire. Les appuis sont testés sur le seul historique principal. La fin de la table utilise l'observation de fin pour l'énergie, pas ses REAC.

| Comparaison | Nature | Δimpulsion % | Δénergie % | Critères impulsion/énergie |
|---|---|---:|---:|---|
{comp}

Pour les témoins rapides, la dernière colonne énergie est la variation du maximum de résidu divisée par KE initiale, avec seuil 0,5 % ; elle n'est pas la variation d'énergie générée quasi nulle. TYPE7 peut passer la comparaison de demi-pas tout en échouant le budget absolu : au demi-pas, résidu {w7['final_energy_residual_J']:.4f} J, soit {100*abs(w7['final_energy_residual_J'])/22.24:.2f} % de KE initiale. TYPE25 passe le rebond aux deux pas ; au demi-pas, résidu final {w25['final_energy_residual_J']:.6f} J.

Sur TYPE25 radôme, tous les bilans locaux passent. Le maximum |résidu|/énergie générée dans la fenêtre >100 J reste inférieur à {100*max(r['max_local_residual_fraction'] for r in type25):.4f} %. T25_L0 échoue encore la comparaison brute de KE nodale, conservée sans correction. Le demi-pas T25_L2 change l'impulsion de {100*half['impulse_difference_fraction']:.5f} %, mais le raffinement spatial de {100*mesh['impulse_difference_fraction']:.2f} % : stabilité temporelle et spatiale sont distinctes.

Décalage temporel, diagnostic pré-déclaré : enregistrer [les accélérations natives TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm), puis comparer séparément v, v−dt·a/2 et v+dt·a/2, avec le TIME STEP natif de chaque ligne. Pour T25_L0, erreur maximale de variation KE {phase[0]['max_KE_change_difference_J']:.6f} J brute → {phase[2]['max_KE_change_difference_J']:.6f} J avec +demi-pas ; différence de rotation globale {phase[0]['max_C0_RKE_difference_J']:.6f} J → {phase[2]['max_C0_RKE_difference_J']:.9f} J. Les autres cas et les deux signes restent dans les JSON. Ce résultat soutient un décalage natif ; il n'est pas une preuve d'équivalence entre source c3inmas sauvegardée et binaire installé. Aucun critère raté n'est reclassé, aucune énergie n'est ajoutée, la dynamique RKE reste non qualifiée.

DKT18 + TYPE7 garde un résidu final {dkt['final_energy_residual_J']:.3f} J au niveau 3456 et échoue le critère local. Changer de triangle ne suffit donc pas à fermer le budget dans cette famille de témoins. La cause énergétique unique n'est pas établie, et la convergence TYPE25 reste à traiter.

## 6. Contradictions et informations manquantes

Énergie TYPE25 fermée, convergence spatiale échouée : ces deux constats sont conservés ensemble. La raideur de pénalité et le nombre de nœuds actifs varient avec le maillage ; leur relation à l'aire tributaire reste à tester sur une plaque analytique. Les formulations et traitements de bord différents empêchent d'attribuer le gain à un seul paramètre. Les coefficients de contact ne sont pas identifiés comme paramètres physiques réels.

Géométrie graphique, matériaux sandwich hypothétiques, racine libre et façade fixée ne représentent pas l'avion en impact réel. Rupture, écrasement, délamination, carburant et dynamique complète ne sont pas calculés. Une fermeture d'énergie sur ce témoin ne valide ni pénétration historique, ni feu, ni effondrement. L'animation utilise les états natifs ×1 et affiche les millisecondes ; sa lecture est ralentie, sans valeur dynamique propre. Syntaxe et données vérifiées, rendu interactif non certifié.

{NEXT}

Reprise : campaign_review.json, scientific_assessment.json, scripts conservés, manifeste et handoff. Publication A12+A13 selon cadence déjà autorisée, avec échecs et anciennes archives conservés ; l'intégrité de publication reste distincte de la physique.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Reprise WTC1 — AIRCRAFT-A13 → AIRCRAFT-A14

A13 terminée : 13 cas principaux +13 observateurs, 0 ancien solveur relancé. configuration : {rel(CFG)} ; rapport : {rel(REPORT)} ; résultats définitifs : {rel(OUT/'campaign_review.json')} ; assessment : {rel(OUT/'scientific_assessment.json')}.

TYPE25 ferme l'énergie dans les 5 radômes, témoin rapide 200 m/s correct aux deux pas. TYPE7 rapide garde ~20,8 % de perte ; DKT18/TYPE7 échoue encore le bilan local. Maillage TYPE25 3456→13824 : ΔJ={100*mesh['impulse_difference_fraction']:.5f} %, Δénergie={100*mesh['generated_difference_fraction']:.5f} %, échecs retenus ; demi-pas ΔJ={100*half['impulse_difference_fraction']:.5f} %, passe. Fenêtre 0,4 ms, premières secondes non calculées.

TH/NODE accélérations + TIME STEP : v+dt*a/2 explique une grande part du mismatch KE/RKE. Diagnostic pré-déclaré, aucun déphasage du ledger, aucun ajout RKE, aucune requalification rétroactive de T25_L0. Inertie C0 comparée à c3inmas sauvegardée, source/binaire non équivalents prouvés ; formule non créditée DKT. Support REAC cumulatif principal seulement ; observateur réinitialise REAC.

L'agrégat initial authoritative_review.json est conservé comme tentative incomplète pendant exécution ; ne pas l'utiliser. campaign_review.json couvre exactement 13/13 cas terminés. Aucun échec masqué.

{NEXT}

7240 anciens fichiers, {preservation['bytes_hashed']/1e9:.2f} Go, nouveau scan SHA256 complet sans différence. Module Boeing parallèle v2 conservé sans intégration ; inertie/dynamique libre bloquées. V11F/V11R et branches différées conservées. Archives lecture seule, aucune vidéo inspectée. Animation : {rel(OUT/'visualisation/premier_contact.html')}, états natifs ×1, ms, sans physique Blender ; SVG comparatif. Cycle publication A12+A13 atteint, vérifier le fichier final de publication avant de considérer la cadence remise à zéro.
''',encoding='utf-8')
    files=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,HANDOFF]+[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_aircraft_a13.py','review_aircraft_a13.py','visualize_aircraft_a13.py','verify_aircraft_a13_preservation.py','finalize_aircraft_a13.py']]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size} for p in sorted(set(files))]})
    print({'prepared':True,'new_files':len(set(files)),'preserved_files':preservation['files']},flush=True)

def register():
    guard();count=checkrows(read(OUT/'artifact_manifest.json')['files']);assert REPORT.exists() and HANDOFF.exists();s=read(OUT/'campaign_review.json');assessment=read(OUT/'scientific_assessment.json');st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st['current_iteration']=='AIRCRAFT-A12' and cy['pending_iterations']==['AIRCRAFT-A12'] and harness()['Status']=='PASS'
    reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix;t=now()
    rec={'experiment_id':'WTC1-AIRCRAFT-A13','registered_at':t,'status':'completed_alternative_contact_and_shell_diagnostics_with_TYPE25_energy_closure_and_retained_spatial_failure','configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'campaign_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'integrity_only_pass':True,'all_declared_checks_pass':False,'main_engine_jobs':s['main_engine_jobs'],'observer_jobs':s['observer_jobs'],'old_solver_reruns':0,'old_files_preserved':7240,'branch_iteration_count':13,'whole_aircraft_iteration_count':10,**assessment,'next_iteration':'AIRCRAFT-A14'}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A13',next_iteration='AIRCRAFT-A14',current_status=rec['status'],next_objective=NEXT,updated_at=t);st['aircraft_a13_key_results']=rec;st['validated_artifacts'].update(aircraft_a13_report=rel(REPORT),aircraft_a13_results=rel(OUT/'campaign_review.json'),aircraft_a13_handoff=rel(HANDOFF));cy.update(pending_iterations=['AIRCRAFT-A12','AIRCRAFT-A13'],pending_count=2,next_publication_after='Authorized A12+A13 pair verified; publish without old rerun, preserve failed gates',updated_at=t);dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(count)

def verify(count=None):
    count=count or checkrows(read(OUT/'artifact_manifest.json')['files']);before=read(OUT/'before_state.json');st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness()
    protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_files_hashes_verified':True,'old_preservation_pass':read(OUT/'preservation_verification.json')['pass'],'historical_results_and_policies_unchanged':all(st[k]==before[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A13','state_route':st['current_iteration']=='AIRCRAFT-A13' and st['next_iteration']=='AIRCRAFT-A14','publication_pending_pair':cy['pending_iterations']==['AIRCRAFT-A12','AIRCRAFT-A13'] and cy['pending_count']==2,'publication_baseline_unchanged':cy['last_published_commit']==read(OUT/'before_publication_cycle.json')['last_published_commit'],'required_artifacts_exist':REPORT.exists() and HANDOFF.exists(),'failed_spatial_gate_retained':not read(OUT/'scientific_assessment.json')['TYPE25_spatial_pass'],'harness_pass':v['Status']=='PASS'}
    proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':count,'old_files_verified':7240,'harness':v,'physical_impact_qualified':False,'seconds_impact_calculated':False,'next_iteration':'AIRCRAFT-A14'};assert proof['pass'],proof;dump(OUT/'publication_verification.json',proof);print(proof,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
