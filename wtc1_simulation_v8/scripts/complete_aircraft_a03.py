"""Seal first-contact evidence; integrity may pass while physical/end-time gates fail."""
import argparse,json,sys
import numpy as np
from run_aircraft_a03 import ROOT,CFG,OUT,PREV,read,dump,sha,rel,now,harness,preserved
REPORT=OUT/'rapport_aircraft_a03.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A03_HANDOFF.md'
NEXT="AIRCRAFT-A04: premier contact de l'avion entier avec plasticite metallique explicite et sensibilites independantes, dans un nouveau depart intact a t=0. Documenter la limite du nez/radome; completer bilan local des energies et amortissements, contraintes de poutres/fibres et horodatage final. Aucun fit vers NIST ni transfert arbitraire d'historique endommage. Garder cas A03 et controle froid V11F."

def prepare():
    assert not REPORT.exists() and not HANDOFF.exists();n=preserved();cfg=read(CFG);s=read(OUT/'r0/summary.json');review=read(OUT/'cached_review/review.json');assert review['saved_state_review_pass'];c=s['cases'][1]
    # Independently re-read histories and exported arrays; never rerun science to seal it.
    states=[]
    for row in s['cases']:
        z=np.load(OUT/'r0'/row['case']['id']/'verified_states_SI.npz');h=np.load(OUT/'r0'/row['case']['id']/'balance_history_SI.npz')
        assert len(z['time_s'])==20 and len(z['node_ids'])==35020 and all(np.all(np.isfinite(z[k])) for k in z.files)
        assert np.max(abs(h['energy_residual_J']))==row['energy_residual_max_J'];states.append({'case':row['case']['id'],'all_finite':True,'saved_states':20,'nodes':35020,'state_sha256':sha(OUT/'r0'/row['case']['id']/'verified_states_SI.npz')})
    h=np.load(OUT/'r0/CONTACT_F200_DT080/balance_history_SI.npz');mechanical=sum(c['last_history_energy_J'][k] for k in ['ROTATION ENERGY','INTERNAL ENERGY','ELASTIC CONTACT ENERGY']);localratio=c['energy_residual_max_J']/mechanical
    dump(OUT/'saved_result_review.json',{'created_utc':now(),'pass':True,'cases':states,'last_generated_mechanical_energy_J':mechanical,'maximum_energy_residual_to_last_generated_mechanical_energy':localratio,'local_energy_ledger_fully_qualified':False,'reason':'Global acceptance uses initial 2.445GJ and masks relative size of residual in short contact energy. Missing/dissipated ledger not attributed without evidence.'})
    dump(OUT/'source_addendum.json',{'created_utc':now(),'predeclaration_not_modified':True,'dead_predeclared_VONM_URL':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_shell_vonm_engine_r.htm','correct_primary_document':'https://2022.help.altair.com/2022/hwsolvers/rad/topics/solvers/rad/anim_shell_restype_engine_r.htm','VONM_scope':'mean shell stress, not outer-fiber or beam stress','no_new_historical_input_claim':True})
    table='\n'.join(f"|{r['case']['id']}|{sum(v['seconds'] for v in r['runtime']):.3f}|{r['final_state_time_ms']:.6f}|{r['last_history_time_ms']:.6f}|{str(r['contact_onset_history_ms'])}|" for r in s['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A03 — premier contact de l'avion entier avec une façade représentative

L'assemblage complet A02 est relié à une bande de façade de59colonnes et3étages. Trois nouveaux calculs sont conservés : contactdésactivé et deux contacts avec facteurdepas0,8/0,4. Aucun dommage, déplacement ou résultat historique n'est fixé. **Premiercontact vers0,2256ms; dépassement des repères élastiques au plus tard dans l'état0,2753ms.** Ce n'est pas une simulation qualifiée de rupture du767 ou d'effondrement. Registre122aprèsA03, une itération et trois calculsEngine, zéro anciencalcul relancé.

## 1. Faits directement observés ou transcrits

2860nœuds structuraux+368masses/RBE3 de l'avion;6538triangles+4600poutres inchangés. Façade31792nœuds+31986quadrilatères; total35020nœuds. Chaque cas sauve20états(0à~0,475ms),100échantillons temporels(0à~0,495ms). Starter etEngine terminent normalement,0erreur/0avertissement. Tous les nœuds et les connectivités sont relus et contrôlés. Le convertisseur padde les triangles avec un quatrième sommet répété; le premier audit déclarait ainsi la connectivité fausse. cached_review normalise cette représentation et démontre les6538triangles originaux identiques, sans changer les decks, résultats ou premiersaudits. Les identifiants sont réordonnés avant toute comparaison; le rang d'un nœud dansVTK n'est pas sonidentifiant.

Les références primaires [TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm), [TH/INTER](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_inter_starter_r.htm) et [ANIM/SHELL/VONM](https://2022.help.altair.com/2022/hwsolvers/rad/topics/solvers/rad/anim_shell_restype_engine_r.htm) définissent le contact et les sorties. L'URLVONM initiale n'était pas la bonne; source_addendum la corrige, sans réécrire la déclaration initiale. VONM indique une contrainte moyenne de coque, pas un maximum dans les fibres ni une contrainte de poutre. Aucune source physique nouvelle de radome ou de construction du767 n'est acquise.

## 2. Résultats de modèles officiels

Les dimensions nominales de façade viennent des entréesNIST déjà transcrites dansV8V/I02A :59colonnes,14in de largeur,40in de pas,52in de traverse. Les épaisseurs voisines5/16in et3/8in et l'étage12ft restent une façade représentative, pas la nomenclature exacte des niveaux impactés. **Cette dépendance aux données nominalesNIST est explicite; aucun résultat de dégâtsNIST ne sert de cible.** OpenRadioss réalise notre calcul exploratoire, pas une nouvelle reconstitution officielle. La vitesse(-200,5,2)m/s, l'attitude nulle et l'alignement central ne sont pas attribués àAA11.

## 3. Affirmations des archives locales

Aucune archive rescannée, aucune vidéo analysée, aucun PDFsource modifié. {n}anciens fichiers épinglés sont identiques. A01/A02, les échecsI02I et le planI02I-M différé sont conservés. V11F froid et la branche thermiqueV11R→V11S demeurent séparés. Un renduPillow projette les états mécaniques sauvegardés à déplacement réel×1; ce dessin ne constitue aucune validation physique supplémentaire. Blender reste visualisation.

## 4. Hypothèses, propriétés, unités et conditions

Le nez est la fermeture en aluminium hypothétique d'A01, **pas un radomecomposite reconstruit**. Les moteurs restent4500kg chacun avec attacheséquivalentes; leurs cylindres visuels n'ont pas de surfaces decontact. Réservevide53,187t comprend de la structuremanquante sansraideur cachée. Géométrie interne,épaisseurs,assemblages et distribution de carburant restent hypothétiques. Pas de gravité, précontrainte, incendie, fracture, érosion, contactentrearêtes ou autocontact.

MétauxLAW1 élastiques intacts : aluminiumpeau2024,rho2780kg/m³,E73,1GPa,nu0,33; internes7075,rho2810,E71,7GPa,nu0,33; acier représentatif,rho7860,E200GPa,nu0,3. Références typiques de limiteélastique310,264/503,32/427,656MPa : **diagnostics uniquement**, pas lois de rupture. Poutres de section et inertieséquivalentes héritées avec amortissement numériquepar défaut signalé enA02; sa contribution au bilan local n'est pas identifiée ici. Les critères diagnostiques ne suppriment aucun élément.

Colonnes carrées355,6×355,6mm,paroi7,9375mm; traversesfrontales1320,8mm de hauteur,9,525mm d'épaisseur. Panneau60960×10972,8mm; jonctionspar nœudscommuns parfaites,944nœuds hauts/bas bloqués sur6degrés. Ni planchers,noyau,coins,épissuresfragiles ni souplesseglobaletour. Appuisimmobiles : travail0, réactions quasi nulles sur cette fenêtre, sans en déduire leurs unités indépendamment.

Unitésnativesg/mm/ms/MPa/N/Nmm. 1kg=1000g;1m=1000mm;1ms=0,001s;1Nmm=0,001J;1Nms=0,001N·s;1mm/ms=1m/s. Masseavion122159,1859781kg,façade69310,977272kg; masseensemble191470,163250kg. La façade initialement immobile ne contribue pas àK0=½Mavion|v|²=2,444955028GJ. Le décalageCG natifA02 de1,204527mm est conservé, sans ajuster la masse pour le masquer.

Distanceinitialeneztoplan50mm; enveloppenumériqueTYPE7 constante5mm, clairance45mm, activationbalistique(50−5)/200=0,225ms. TYPE7 unilatéralnœudsexternesavion→coquesfaçade,Istf4(minraideurs),Igap1000,Stfac1,friction0,VISs1e−20 pour éviter le défaut0,05, sansdéplacementautomatiqueinitial(Inacti1000). La clairanceinitiale exclut géométriquement les pénétrations; aucune correction de position n'est faite. L'avion n'a aucune trajectoire imposée aprèsv0. Nouveaux calculs frais; aucune propriété d'un matériauendommagé changée en cours de parcours.

## 5. Résultats dérivés et bilans

|Cas|Starter+Engine+CSV(s)|Dernier état(ms)|Dernière histoire(ms)|Contactdétecté(ms)|
|---|---:|---:|---:|---:|
{table}

Contrôle sanscontact : translation uniforme de3228nœudsavion,façadeimmobile; énergieinterne,rotation,hourglass,travail0, conservation auxprécisionssauvées. Aveccontact, premièresimpulsions0,2256282/0,2252607ms. Différence en divisantdtpar2 : {s['half_dt_impulse_relative_difference']*100:.5f}% sur l'impulsionvectorielle à l'instantcommun{s['half_dt_comparison_common_time_ms']:.7f}ms; décalagedétection{s['half_dt_onset_difference_ms']:.7f}ms. Ce contrôle de pas ne valide ni le maillage spatial du contact ni les mécanismes de rupture.

TH nommeFNX/FNY/FNZ des forces; **la sortie de cette version se comporte comme une impulsioncumuléeNms**. Casdt0,8 : colonnefinaleX−2763584, soit−2763,584N·s selon cette interprétation; quantitédemouvementfaçade−2754,313N·s. Interpréter la colonnecommeforce etl'intégrer produit seulement−485,904N·s. Les deux interprétations et colonnesbrutes sont sauvées; écartmaximum du bilanvectorielcumulé38,019N·s, contre une allowance déclarée10N·s+2% de l'impulsion(~65N·s). Écartfinal~0,34%,paségalitéexacte; effet possible d'échantillonnage/staggering non démontré. Pglobal inclut l'avion etla façade; Pavion=Pglobal−Pfaçade pour conserver ses massesadditionnelles absentes desPART structurels. Les réactionsprèsde0 sur cette courtefenêtre ne distinguent pas leurs deux interprétations force/impulsion. Aucun contact moteur n'est présent.

BilanE=Ktranslation+Krotation+Uinterne+hourglass+ressorts+contactélastique+friction+dissipationdecontact; ΔE−Wext est sauvé. CONTACT ENERGY global n'est pas ajouté une seconde fois à ses composantes. Casdt0,8 à0,4955922ms : K2,444606GJ; rotation72445,260J; interne223896,100J; contactélastique3371,093J; travail,friction,hourglass,dampingcontact0. **Résidumax49624,413J**, soit0,002030% deK0, inférieur au seuilglobal déclaré0,5%. Mais ce résidu représente **{localratio*100:.2f}%** des~{mechanical:.0f}J d'énergiesmécaniques générées dans le dernier échantillon. Le bilan local n'est donc **pas complètement qualifié**; l'énergie manquante ne reçoit pas une interprétation physique inventée. Beamdfpar défaut, intégration, sorties non comptées et couplages sont des pistes à départager, pas des explications établies. Les valeursglobalesCSV sont arrondies à7chiffres; le résidudépasse ce seul arrondi. Aucun massscaling; addedmass apparent~2,13e−4g(~1,11e−12fraction), conforme au nouveau critère relatifA03. L'anciencritère absoluA02 reste échoué dansses propresrésultats.

Diagnosticàl'état0,275270ms(0,275245avec½dt) : premierdépassement d'au moins une référence. Maximumssauvéspeau2470,09MPa,acier2343,85MPa; extensiongéométriqueabsoluedes arêtesavion1,706%(½dt1,708%). Ces fortescontraintes **signalent l'extrapolation de la loiélastique**, sansprédire contraintesréelles aprèsplasticité ni fracture. Les contraintesmoyennes peuvent sous-estimer la flexion externe; contraintesde poutres nonexportées. L'heureexacte du premieryield entreétats et le comportement physique du radome sont inconnus.

## 6. Contradictions et informations manquantes

Intégrité, connectivité et relecture passent. **Toutes les acceptationsnumériques ne passent pas** : la finEngine exacte n'est pas exportée, critère detolérancefin reste nonvérifié/false dans les troiscas. Les derniersétats~0,475ms ne sontpas lafin0,5ms; le premieraudit les avait traités commetels, conservé. Normaltermination etcycles ne donnentpas ici un horodatagefinal de précisionrequise. Aucun seuildéplacé ni recalcul pour effacer cet échec. Les hypothèsesélastiques sontdépassées; bilangénergiquelocal ouvert et incertitudeCGA02 conservée. La robustessephysique du chocentier n'est pas acquise.

Il manque constructionradome,épaisseurs/fixationspropresau767,moteursdéformables,carburantdistribué,loisplastiques etfracture,conditionsAA11 indépendantes,maillagedecontactconvergent,réponseétages/noyau etconditionsde gravité. Aucun feu ni effondrement calculé. Localisation en flexionaprèsfracture complète nonvalidée; températureimposée≠incendie; testsnumériques≠validationde l'événement. Pas de calibrageversNIST. A03 conserve le résultatobservé même s'il n'estpas physiquementexploitable sur toutela fenêtre.

## Reprise

{NEXT}

Relecture sanssolveur : complete_aircraft_a03.py verify. Config,scripts,decks,sortiesbrutes,NPZ,rapports,manifestes etpremieraudits sontconservés. PublicationA02+A03 due aprèscontrôle d'intégrité, avecéchecs explicites; cadence ne sera remise àzéro qu'après vérificationdistante. AucunpostX ni opérationYoremi.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Passation compacte AIRCRAFT-A03 → A04

Lire AGENTS.md puisstate.json(prioritaire) et cettepassation. Routeavionentier,aucunfitNIST; ancienV8H périmé,I02I-M différée.

A03: r0 intact,35020nœuds(3228avion+31792façade),6538triangles+4600poutres+31986quads;59colonnes×3étages,haut/basfixes944nœuds. TroisEngine~9/8/15s,0erreur/avertissement. v=(-200,5,2)m/s,attitudenulle,testnonhistorique; gapinitial50mm/contact5mm,TYPE7 sansfriction niamortissementnormal(1e−20). ToutLAW1intact; pas rupture/feu/gravity/core. Moteursmasseséquivalentes sans surfacesdecontact,nezaluminiumhypothétique≠radome.

Onset0,2256282ms/0,2252607ms; réductiondt½ donneimpulsiondiff0,111931%,sauvegardes20étatsà~0,475ms,histoire100échantillonsà~0,495ms. Fin0,5ms demandée,normaltermination; horodatageEnginefinal inconnu,critèrefin nonvérifié/false(3cas). Premieraudit conserve fauxéchecconnectivité:convertisseurpadtriangle[1,2,3,3],correctedcached_review relittousids/connectivités avecnormalisation, sansrecalcul. Tous35020nœuds sontsauvés,utiliser x0+Displacement plutôt quecoordASCII arrondies.

Picpeau2470MPa/acier2344MPa,extensionarétes1,7%,référencesélastiquesdépasséesà0,27527ms auplustard. Réponseau-delà nonqualifiée,n'estpas ruptureprédite. Courbesetfigurecached_review/A03_premier_contact.png issuesétats×1,visualisationseulement. Premièresloisplastiques etradomeàtraiter; contraintesbeam/fibresmanquantes.

THFN secomportecommeimpulsionNms(démonstrationcomparativePfaçade),nonforceNàintégrer:dt0,8Jx−2763,584Ns/Pfaçade−2754,313Ns; erreurmax38,019Ns,tol10+2%~65. Forceintégréeerr~2278Ns. Supportssignauxquasinuls,unitésnonqualifiéesindépendamment. Pavion=Pglobal−Pfaçade,massesADMASincluses. Bilanénergieinclut contactélastique,sansdoublecompterCONTACT ENERGY. Résidu49,624kJ=0,00203%K0 mais~{localratio*100:.2f}%énergiesgénérées : **ledgerlocalnonqualifié**,nepasinventerorigine. Amortissementbeampar défaut/intégration/sortiespistesseulement. A02CG1,204527mm etses6échecslittérauxpreservés,aucunfitmassique.

Suiteconcrète : {NEXT}

Résumé r0/summary.json,premiersaudits,cached_review/review.json,saved_result_review.json,rapportA03. complete_aircraft_a03.py verify sanssolveur. {n}anciensfichierspréservés,registre122,cadenceA02+A03pending2jusqu'àvérificationdistantede publication; aprèspublicationvérifiéelastpublishedA03pending0,prochainepaireA04+A05. Toujourslirepublication_cycle.json. V11F/V11R/brancheV11S/flexionpostfracturelimitesintacts. PasX/Yoremi,aucunanciencalcul relancé.
''',encoding='utf-8')
    dump(OUT/'release_audit.json',{'created_utc':now(),'integrity_pass':True,'old_files_preserved':n,'state_review_pass':True,'all_numerical_acceptance_checks_pass':False,'all_elastic_diagnostics_pass':False,'physical_impact_qualified':False,'local_energy_ledger_fully_qualified':False,'solver_jobs':3,'starter_jobs':3,'old_solver_reruns':0,'numpy_version':np.__version__,'python_version':sys.version,'harness':harness()})
    scripts=[ROOT/'wtc1_simulation_v8/scripts'/name for name in ['run_aircraft_a03.py','audit_aircraft_a03.py','review_aircraft_a03_cached.py','complete_aircraft_a03.py']]
    paths=[p for p in OUT.rglob('*') if p.is_file()]+scripts+[CFG,HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)],'excluded':['self','publication_verification.json','mutable state registry cadence'],'scope':'Bounded whole-plane first contact, all limits/unverified gates retained.'});print({'prepared':True,'old_files_preserved':n})

def register():
    assert REPORT.exists() and HANDOFF.exists() and not (OUT/'publication_verification.json').exists();preserved()
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:assert sha(ROOT/'harness'/name)==sha(OUT/('before_'+name.split('/')[-1]))
    for row in read(OUT/'artifact_manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    assert harness()['Status']=='PASS';state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');assert state['current_iteration']=='AIRCRAFT-A02' and cycle['pending_iterations']==['AIRCRAFT-A02']
    s=read(OUT/'r0/summary.json');t=now();status='completed_whole_aircraft_first_contact_with_elastic_and_local_energy_limits'
    record={'experiment_id':'WTC1-AIRCRAFT-A03','registered_at':t,'status':status,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'r0/summary.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),
        'saved_state_connectivity_review_pass':True,'all_numerical_acceptance_checks_pass':False,'all_elastic_diagnostics_pass':False,'physical_impact_qualified':False,'local_energy_ledger_fully_qualified':False,'half_dt_impulse_difference_fraction':s['half_dt_impulse_relative_difference'],
        'first_saved_elastic_limit_exceedance_ms':s['cases'][1]['first_saved_elastic_diagnostic_exceedance_ms'],'NIST_outcomes_used_as_target':False,'NIST_nominal_facade_input_dependency':True,'solver_jobs':3,'old_solver_reruns':0,'old_files_preserved':len(read(OUT/'preservation_before.json')['files']),'next_iteration':'AIRCRAFT-A04'}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A03',next_iteration='AIRCRAFT-A04',current_status=status,next_objective=NEXT,updated_at=t);state['aircraft_a03_key_results']=record;state['user_steering_2026_10_05']['next']='AIRCRAFT-A04'
    state['validated_artifacts'].update(aircraft_a03_report=rel(REPORT),aircraft_a03_results=rel(OUT/'r0/summary.json'),aircraft_a03_handoff=rel(HANDOFF),aircraft_a03_states=rel(OUT/'r0/CONTACT_F200_DT080/verified_states_SI.npz'),aircraft_a03_review=rel(OUT/'cached_review/review.json'))
    cycle.update(pending_iterations=['AIRCRAFT-A02','AIRCRAFT-A03'],pending_count=2,next_publication_after='A02+A03 verified pair due now; include elastic/local energy/end-time limitations',updated_at=t)
    dump(ROOT/'harness/state.json',state);dump(ROOT/'harness/publication_cycle.json',cycle);verify(True)

def verify(write=False):
    n=preserved();m=read(OUT/'artifact_manifest.json');bad=[r['path'] for r in m['files'] if sha(ROOT/r['path'])!=r['sha256']];before=read(OUT/'before_state.json');state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');v=harness();reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();suffix=reg[len(prefix):].decode().splitlines()
    protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];s=read(OUT/'r0/summary.json');rv=read(OUT/'cached_review/review.json')
    pending=cycle['pending_count']==2 and cycle['pending_iterations']==['AIRCRAFT-A02','AIRCRAFT-A03'];published=cycle['pending_count']==0 and cycle['last_published_iteration']=='AIRCRAFT-A03' and cycle['last_published_release']=='snapshot-2026-10-05-aircraft-a02-a03'
    if published:
        proof=read(ROOT/'outputs/github_publication/updates_2026-10-05_aircraft_a02_a03/final_remote_verification.json');published=proof['pass'] and proof['cadence_pending_count']==0
    checks={'new_artifact_hashes':not bad,'predecessors_preserved':True,'predeclaration_unchanged':sha(CFG)==read(OUT/'declaration_guard.json')['sha256'],'registry_append_only':reg.startswith(prefix),'one_new_record':len(suffix)==1 and json.loads(suffix[0])['experiment_id']=='WTC1-AIRCRAFT-A03',
        'state_route':state['current_iteration']=='AIRCRAFT-A03' and state['next_iteration']=='AIRCRAFT-A04','old_results_and_limits_preserved':all(before[k]==state[k] for k in protected),'inputs_preserved':all(sha(ROOT/r['path'])==r['sha256'] for r in read(OUT/'source_manifest.json')['local_inputs']),
        'saved_states_and_native_connectivity_pass':rv['saved_state_review_pass'] and read(OUT/'saved_result_review.json')['pass'],'old_A02_failures_visible':not read(PREV/'r1/summary.json')['all_literal_checks_pass'],
        'new_failed_gates_visible':not s['all_elastic_diagnostics_pass'] and not rv['all_numerical_acceptance_checks_pass'] and all('end_overshoot_within_one_native_step' in r['unresolved_numerical_checks'] for r in rv['cases']),
        'no_physical_impact_or_local_energy_claim':not s['physical_impact_qualified'] and not read(OUT/'saved_result_review.json')['local_energy_ledger_fully_qualified'],
        'no_NIST_outcome_fit':not read(CFG)['NIST_outcomes_used_as_target'],'cadence_pending_or_remote_verified':pending or published,'harness_pass':v['Status']=='PASS'}
    result={'created_utc':now(),'pass':all(checks.values()),'checks':checks,'new_files_checked':len(m['files']),'old_files_checked':n,'harness':v,'integrity_only':True,'all_numerical_acceptance_checks_pass':False,'all_elastic_diagnostics_pass':False,'physical_impact_qualified':False,'pending_Github_iterations':cycle['pending_count'],'next_iteration':'AIRCRAFT-A04'}
    assert result['pass'],result
    if write:dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);a=p.parse_args();globals()[a.action]()
