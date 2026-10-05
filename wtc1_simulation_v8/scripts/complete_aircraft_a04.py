"""Seal whole-aircraft plasticity evidence, retaining failed physical/numerical gates."""
import argparse,json,sys,csv
import numpy as np
from run_aircraft_a04 import ROOT,OUT,CFG,PREV,read,dump,sha,rel,now,harness,preserved
from audit_aircraft_a04 import histories
REPORT=OUT/'rapport_aircraft_a04.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A04_HANDOFF.md'
NEXT=('AIRCRAFT-A05 : améliorer le nez/radôme dans le modèle d’avion entier à partir de sources primaires et de variantes explicites, puis reprendre un départ intact. Traiter la dégénérescence du maillage et le besoin d’autocontact sans érosion ni mass scaling arbitraires ; conserver les comparaisons A03/A04 et le bilan local ouvert. Ne pas choisir H=0,02E simplement pour atteindre 2 ms et ne pas forcer un résultat NIST. Préserver V11F et la branche thermique différée.')

def prepare():
    assert not REPORT.exists() and not HANDOFF.exists() and not (OUT/'artifact_manifest.json').exists();n=preserved();cfg=read(CFG);s=read(OUT/'cached_review/review.json');assert s['integrity_only_pass'];nom=s['cases'][3];hard=s['cases'][7]
    for row in read(OUT/'source_manifest.json')['local_inputs']:assert sha(ROOT/row['path'])==row['sha256']
    extra=[]
    for c in s['cases']:
        d=OUT/'r1'/c['case']['id'];m=read(d/'generation.json');h=histories(d/(m['name']+'T01.csv'));pw=h['PLASTIC WORK']*.001;ie=h['INTERNAL ENERGY']*.001
        assert np.all(pw<=ie+1.)
        z=np.load(d/'verified_states_SI.npz');assert all(np.all(np.isfinite(z[k])) for k in z.files)
        extra.append({'case':c['case']['id'],'global_plastic_work_subset_of_IE_all_saved_main_histories':True,'states':len(z['time_s']),'nodes':len(z['node_ids']),'original_audit_sha256':sha(d/'audit.json'),'maximum_state_time_s':float(z['time_s'][-1])})
    execs=[read(p) for p in OUT.rglob('*.execution.json')];mainexecs=[r for r in execs if r['exe'].endswith('engine_win64.exe') and r['args'][1].endswith('_0001.rad')];observerexecs=[r for r in execs if r['exe'].endswith('engine_win64.exe') and r['args'][1].endswith('_0002.rad')]
    assert len(mainexecs)==9 and len(observerexecs)==6
    review={'created_utc':now(),'pass':True,'integrity_only':True,'cases':extra,'old_files_preserved':n,'main_solver_jobs':len(mainexecs),'observation_jobs':len(observerexecs),'starter_jobs':9,'old_solver_reruns':0,'main_timeboxed_jobs':sum(r['exit_code']=='TIMEOUT' for r in mainexecs),'main_wall_seconds_sum':sum(r['seconds'] for r in mainexecs),'observer_continuation_not_credited_to_physical_window':True,'physical_impact_qualified':False,'local_energy_ledger_fully_qualified':False,'python_version':sys.version,'numpy_version':np.__version__,'harness_after_computations':harness()};dump(OUT/'saved_result_review.json',review)
    table='\n'.join(f"| {r['case']['id']} | {r['last_history_time_ms']:.7f} | {r['last_animation_time_ms']:.6f} | {'terminé' if r['requested_horizon_reached'] else 'plafond 300 s'} | {r['final_global_plastic_work_J']/1000:.3f} | {r['maximum_shell_plastic_strain']:.6g} | {r['maximum_sampled_beam_plastic_strain']:.6g} |" for r in s['cases'])
    balance='\n'.join(f"| {r['case']['id']} | {r['final_contact_impulse_Ns'][0]:.3f} | {r['final_energy_residual_J']/1000:.3f} | {r['final_generated_energy_J']/1000:.3f} |" for r in s['cases'][3:])
    failures='\n'.join(f"- **{r['case']['id']}** : {', '.join(r['failed_checks']) or 'aucun échec dans les critères déclarés'}." for r in s['cases'])
    compare='\n'.join(f"| {r['case']} | {r['A04_energy_residual_J']/1000:.3f} | {(r['difference_J'])/1000:.3f} |" for r in s['A03_cached_comparison'])
    sources=cfg['sources'];area=s['nose_triangle_4050']['area_history'][-1]['area_ratio_to_initial'];Hseconds=hard['runtime'][1]['seconds']
    REPORT.write_text(f'''# AIRCRAFT-A04 — plasticité du Boeing entier et de la façade

Le modèle complet possède maintenant des lois élastoplastiques pour les peaux, les structures internes et l’acier de façade. Huit cas nouveaux r1 sont sauvegardés : trois contrôles et cinq variantes plastiques. Le contrôle sans contact conserve une translation uniforme et une énergie plastique nulle. **Le premier travail plastique non négligeable apparaît vers 0,2401 ms.** Les quatre variantes sans écrouissage n’atteignent pas les 2 ms prévues : un écrasement du maillage du nez réduit considérablement le pas de temps. La variante H=0,02E termine à {hard['actual_main_end_time_ms']:.7f} ms en {Hseconds:.2f} s d’Engine.

Cela établit une sensibilité du modèle à sa loi de comportement, sans sélectionner la variante qui atteint le plus loin comme représentation vraie du 767. Les grandes déformations, le radôme, la rupture et le bilan énergétique local restent non qualifiés. Aucun résultat de dégâts ou d’effondrement n’est imposé ou utilisé comme cible NIST. A04 est une itération complète de recherche avec des essais arrêtés et des critères échoués explicitement conservés.

## 1. Faits directement observés ou transcrits

Le graphe A03 est conservé : 35 020 nœuds, dont 3 228 pour l’avion (2 860 structuraux et 368 références de masses/RBE3), 6 538 triangles d’avion, 4 600 poutres équivalentes et 31 986 quadrilatères de façade. Les cartes de géométrie, masses, inerties géométriques de section, appuis, RBE3 et vitesse initiale sont identiques à celles d’A03. Les huit Starter r1 signalent chacun zéro erreur et zéro avertissement. Les huit ensembles d’états sauvegardés sont finis et leurs connectivités sont contrôlées avec les identifiants natifs, indépendamment de leur ordre dans VTK.

La fiche [Kaiser 2024, page 1]({sources[0]}) donne une limite typique de 47 ksi, imprimée 324 MPa, pour T4/T351 et une éprouvette de diamètre 0,500 in. Ce n’est pas une nomenclature de peaux 767 en T3. La fiche [Kaiser 7075, page 1]({sources[1]}) donne 73 ksi, imprimé 503 MPa, pour T651 ; sa table scannée est inspectée visuellement. Sa valeur d’allongement 11 % n’est employée ni comme déformation à la résistance maximale ni comme seuil d’effacement d’éléments. La source [Boeing ARFF 767, page PDF 6]({sources[2]}) répertorie le radôme parmi les emplacements de matériaux composites ; sa feuille porte la date du 29 avril 2022. Elle ne fournit ni stratification, ni épaisseur, ni loi d’écrasement, et ne constitue pas une description d’AA11 en 2001.

Les trois copies PDF nouvelles sont épinglées par SHA-256 et conservées dans input/aircraft_a04_sources. Elles restent des sources externes en lecture seule, exclues des livrables propres au modèle à republier. Les JSON d’acquisition, les conversions et un script de réacquisition uniquement si un fichier manque rendent leur provenance traçable.

## 2. Résultats d’un modèle officiel

Aucun résultat officiel nouveau n’est adopté comme résultat attendu. La façade nominale héritée de V8V/I02A dépend d’entrées NIST déjà transcrites : 59 colonnes et 3 étages, largeur 14 in, pas 40 in et traverses de 52 in. Les épaisseurs de référence et la hauteur d’étage restent représentatives. Cette dépendance à des données nominales est explicite ; les sorties de dégâts NIST ne servent pas à identifier les lois, la vitesse, le contact ou les seuils. OpenRadioss calcule ici notre modèle exploratoire.

## 3. Affirmations des archives locales

Aucune vidéo n’est analysée, aucun parcours de l’archive n’est relancé. Les {n} fichiers antérieurs épinglés, dont les résultats A01–A03 et leurs échecs, sont identiques. V11F froid, V11R et la branche V11S différée restent conservés ; IMPACT-I02I-M demeure différée selon l’orientation vers l’avion entier. Aucune affirmation des archives n’est transformée en propriété de matériau ou en condition initiale de cette itération.

## 4. Hypothèses, propriétés, unités et historique

Chaque cas r1 repart intact à t=0. Aucun matériau déjà endommagé d’A03 n’est relu avec une loi modifiée. Les reprises utilisées pour observer les fins et les libellés conservent strictement les mêmes matériaux et leur historique propre à A04 ; elles ne prolongent pas la fenêtre physique publiée.

| Attribution hypothétique | Masse volumique (kg/m³) | E (GPa) | ν | Limite a (MPa) |
|---|---:|---:|---:|---:|
| Peaux et nez, aluminium de référence 2024 | 2780 | 73,1 | 0,33 | 324 |
| Cadres, longerons et poutres internes, référence 7075 | 2810 | 71,7 | 0,33 | 503 |
| Acier représentatif de façade | 7860 | 200 | 0,30 | 427,656 |

Les deux attributions aluminium sont des hypothèses, pas des nuances et traitements identifiés sur chaque pièce du 767. La densité 2780 kg/m³ est héritée d’A01 tandis que Kaiser indique 2770 ; E=71,7 GPa du 7075 est hérité tandis que la fiche indique 71,0. Elles sont conservées pour isoler la modification de loi. L’acier 62 ksi converti antérieurement à 427,656 MPa reste une référence non attribuée à chaque plaque impactée ; il n’est pas présenté comme une reconstruction des grades exacts.

La loi native [LAW2, Iflag=0]({sources[3]}) emploie σécoulement = a + b·εp^n, n=1. Le cas nominal a b=0 : élasticité puis plasticité parfaite. Les variantes a×0,8 et a×1,2 concernent tous les métaux. La variante H=b=0,02E a H=1462/1434/4000 MPa selon les trois matériaux. Ces lois et sensibilités sont déclarées avant calcul. Elles ne sont pas des courbes dynamiques identifiées. c=0 désactive le terme de vitesse de déformation ; l’absence d’identification dynamique reste une limite à l’impact. Aucun adoucissement thermique, aucune rupture, aucune érosion ni mass scaling ne sont activés. Les champs de température de référence du format LAW2 n’imposent aucune montée en température ou incendie ; le modèle reste mécanique sans couplage thermique.

Les coques plastiques et le contrôle à limite fictivement très haute utilisent N=5 points dans l’épaisseur. Les tenseurs UPPER/LOWER sont ceux des points extrêmes d’intégration, selon [ANIM/SHELL/TENS]({sources[7]}), sans extrapolation d’une contrainte extérieure. VONM est conservé séparément. Les poutres TYPE3 utilisent toujours leurs sections équivalentes, avec dm=0 et df=10⁻²⁰ pour éviter le défaut df=0,01. Ce choix explore l’amortissement numérique ; il ne mesure pas un amortissement physique. TYPE3 ne résout pas une plastification progressive de fibres de section. Les historiques de 696 poutres sont sélectionnés avant calcul par max(X des extrémités)≤8 m ; SX est axial, pas une contrainte maximale de flexion. Cette sélection n’est pas un maximum global sur les 4 600 poutres.

Le nez demeure le substitut métallique d’A01, alors que la source Boeing situe un composite au radôme. Il n’est pas renommé composite. Construction interne, épaisseurs, assemblages et distributions de masses restent hypothétiques. Les moteurs de 4500 kg chacun ont des attaches équivalentes et aucune surface de contact déformable. La réserve de masse vide non résolue de 53,187 t n’a pas de raideur ajoutée pour la dissimuler. L’avion a 122 159,1859781 kg, la façade 69 310,977272 kg ; le total reste 191 470,163250 kg, et le décalage de CG natif d’A02 de 1,204527 mm est conservé.

Conditions A03 : v=(-200,5,2) m/s, attitude nulle, alignement propre au test, pas des conditions AA11 identifiées. Façade haute/basse fixée sur 944 nœuds ; pas de noyau, planchers, coins, gravité ou précharge. Distance nez-plan initial 50 mm, gap de contact TYPE7 5 mm, friction nulle, amortissement normal presque nul, aucune correction de position initiale. Pas d’autocontact ni de contact entre arêtes. La trajectoire évolue à partir de v0, sans déplacement forcé après l’initialisation.

Unités natives : g, mm, ms, MPa, N et N·mm. 1 g=0,001 kg ; 1 mm=0,001 m ; 1 ms=0,001 s ; 1 N·mm=0,001 J ; 1 N·ms=0,001 N·s ; 1 mm/ms=1 m/s. εp est une déformation plastique équivalente sans dimension, et ne signifie pas un allongement d’éprouvette à rupture. K0=½Mavion|v0|²=2,444955028 GJ. Les graines et paramètres sont dans le JSON ; le calcul est déterministe, aucun tirage aléatoire n’est effectué.

## 5. Résultats dérivés, réactions et bilans

| Cas | Dernière histoire (ms) | Dernier état (ms) | Sortie principale | PW (kJ) | εp max coques | εp max poutres échantillonnées |
|---|---:|---:|---|---:|---:|---:|
{table}

Les dernières histoires des cas plafonnés sont des sauvegardes antérieures à l’interruption, pas des horodatages de terminaison vérifiés. L’Engine nominal est interrompu à environ 1,628 ms d’après sa ligne de cycle arrondie, avec Δt≈6,001×10⁻⁸ ms et le triangle 4050 limitant. Ce triangle est identifié dans fuselage_caps, au nez initial X=0 ; son aire initiale est 0,0001980619225 m². À l’état {nom['last_animation_time_ms']:.5f} ms, son aire n’est plus que {area*100:.3f} % de l’aire initiale. Cela démontre une dégénérescence géométrique calculée, pas une fracture physique. Le cas de résistance basse devient également limité par un triangle proche du nez. Ajouter du temps de calcul n’est pas considéré comme une solution physique à cette dégénérescence.

Le travail plastique nominal dépasse le seuil de lecture 10⁻⁶ J à {nom['plastic_work_onset_history_ms']:.7f} ms ; le premier état spatial non nul sauvé est à {nom['first_saved_plastic_strain_ms']:.6f} ms. Ces cadences ne donnent pas l’instant exact de premier écoulement. Le diagnostic déclaré εp≤0,1 est dépassé dès l’état de coque proche de 0,6 ms ; il ne supprime aucun élément et n’est pas un seuil de fracture réel. Le nominal atteint εp≈3,73 en coque et 5,41 dans les poutres échantillonnées. La variante écrouissante atteint encore 0,871/0,738. Le fait qu’elle termine ne rend donc pas ses grandes déformations qualifiées.

À l’instant commun {s['half_dt_common_time_ms']:.7f} ms des deux cas nominaux, réduire le pas par deux donne un écart vectoriel d’impulsion de {s['half_dt_impulse_relative_difference']*100:.5f} % et un écart d’énergies générées de {s['half_dt_generated_energy_relative_difference']*100:.5f} %. Les limites préalables 5 % et 10 % passent sur cette fenêtre. Cela ne valide pas une convergence spatiale, la rupture, les composites, les assemblages ou la partie d’impact non calculée. Les ailes n’ont pas encore atteint la façade dans ces états.

### Quantité de mouvement et réactions

La colonne de contact est testée à nouveau contre Pfaçade. Elle se comporte comme une impulsion cumulée N·ms : J=0,001·(colonne−colonneinitiale), sans intégration supplémentaire. Nominal, dernier Jx={nom['final_contact_impulse_Ns'][0]:.3f} N·s, Pfaçade,x={nom['final_facade_momentum_Ns'][0]:.3f} N·s ; l’erreur vectorielle maximale est {nom['contact_balance_max_error_Ns']:.3f} N·s pour une tolérance 10+2 % de |J|≈{nom['momentum_allowance_Ns']:.3f} N·s. Interpréter la même colonne comme une force puis l’intégrer donne une erreur maximale d’environ 1941 N·s. Les deux interprétations sont conservées dans la relecture. Les appuis sont immobiles et leur travail est nul ; leurs petites sorties de réaction ne suffisent toujours pas à distinguer indépendamment leurs unités par rapport à la quantification de Pglobal. Les deux interprétations de réactions sont conservées, sans fabriquer une force ou une puissance. Pavion=Pglobal−Pfaçade inclut les masses additionnelles, absentes des PART structuraux.

### Énergie

Ecomptée=Ktranslation+Krotation+Uinterne+hourglass+ressorts+contactélastique+friction+dissipationcontact. Le résidu est ΔEcomptée−Wextérieur. CONTACT ENERGY n’est pas additionnée une seconde fois à ses composantes. **PW est un sous-ensemble de Uinterne, jamais une énergie additionnelle** ; cette inclusion est contrôlée sur toutes les histoires principales sauvées. Hourglass, ressorts, friction, damping contact et travail extérieur sont nuls dans ces cas. L’origine du résidu n’est pas attribuée à une dissipation physique manquante sans preuve.

| Cas plastique | Jx dernier (N·s) | Résidu E dernier (kJ) | Énergie générée dernière (kJ) |
|---|---:|---:|---:|
{balance}

Nominal : PW={nom['final_global_plastic_work_J']/1000:.3f} kJ, Uinterne={nom['final_energy_terms_J']['INTERNAL ENERGY']/1000:.3f} kJ, Krotation={nom['final_energy_terms_J']['ROTATION ENERGY']/1000:.3f} kJ, contactélastique={nom['final_energy_terms_J']['ELASTIC CONTACT ENERGY']/1000:.3f} kJ. Résidu dernier {nom['final_energy_residual_J']/1000:.3f} kJ, soit environ {abs(nom['final_energy_residual_J'])/nom['final_generated_energy_J']*100:.2f} % de l’énergie générée. Les écarts restent petits par rapport aux 2,445 GJ initiaux et tous les critères globaux 0,5 % passent. Mais **les critères locaux 5 % de l’énergie générée +1000 J, au-delà de 1000 J générés, échouent pour tous les contacts**. Le maximum relatif précoce nominal vaut 2,671 ; les courbes de résidu sont sauvegardées, et ce nombre n’est pas une probabilité. L’arrondi CSV à sept chiffres est explicitement pris en compte par les 1000 J préalablement déclarés.

La comparaison avec les résultats A03 sauvegardés est faite à 0,4955922 ms, sans relancer A03. Son résidu à cet instant vaut −49,288 kJ ; le maximum A03 sur toute sa fenêtre était 49,624 kJ.

| Cas A04 | Résidu à l’instant commun (kJ) | Différence signée avec A03 (kJ) |
|---|---:|---:|
{compare}

Le remplacement du seul amortissement df dans le contrôle élastique ne retire qu’environ 1,51 kJ du déficit à cet instant commun. Il ne résout pas le bilan local A03. Le contrôle LAW2 à haute limite et N=5 produit presque la même réponse élastique ; le nominal change aussi l’écoulement plastique. Aucun écart n’est corrigé en modifiant artificiellement l’énergie ou les propriétés.

### Horodatage et erreurs d’outillage conservées

Une première tentative r0 ELASTIC_N0_DFMIN a terminé, mais son observateur dans le même dossier a remplacé son animation A007. Cette frame r0 n’a pas été récupérée et la tentative n’est pas acceptée comme série intacte ; son anomalie, ses sorties restantes et son script sont conservés. **Les anciennes itérations A01–A03 n’ont pas été touchées.** r1 corrige l’observateur en copiant la reprise nouvelle dans un dossier isolé et en vérifiant tous les fichiers principaux par hash. Les quatre cas r1 terminés possèdent ainsi un premier enregistrement T02 et une animation correspondant à la vraie fin principale. Le cycle additionnel de l’observateur reste exclu de la fenêtre physique. Les quatre cas plafonnés n’ont pas d’observateur de fin et leurs critères de terminaison restent false.

Les cinq premiers audits interprétaient les neuf canaux de poutre dans l’ordre demandé du deck. Le moteur les écrit dans l’ordre canonique **F1,F2,F3,M1,M2,M3,IE,SX,EPSP**. Une observation isolée à matériaux inchangés avec /TH/TITLE établit cet ordre pour les 696 poutres. Les premiers audits et tableaux bruts demeurent inchangés ; cached_review/review.json porte l’interprétation corrigée. Les différences restantes de cette relecture sont l’arrondi du conteneur float32. Les libellés d’unité parasites du convertisseur sont ignorés, les unités viennent de la déclaration native. SX nominal maximal corrigé 503 MPa ne doit pas être confondu avec une énergie de poutre en N·mm ni une contrainte de fibre de flexion.

Le premier PNG a montré un défaut de découpe graphique du zoom et une borne verticale trop basse ; il est conservé. **A04_contact_plastique_v2.png** est le rendu retenu, inspecté visuellement : états enregistrés, projection XY, déplacement ×1, lignes du nez découpées au panneau, aucune trajectoire d’animation imposée. Le trait vertical représente le plan INITIAL de façade ; sa déformation n’est pas dessinée. Il s’agit d’une projection de calcul, pas d’une validation visuelle du mécanisme réel.

## 6. Contradictions, critères échoués et données manquantes

{failures}

Le critère strict PW=0 du contrôle à haute limite échoue littéralement avec seulement 8,55×10⁻¹⁹ J ; εp coque est nul et εp poutre corrigé est d’environ 2×10⁻²⁵. Ce résidu microscopique n’est pas présenté comme une plasticité mesurable. Le critère ne reçoit pas une tolérance modifiée après observation.

Les contraintes VONM moyennes et les tenseurs des points extrêmes sont des sorties séparées. Dans le nominal, le VONM acier maximal vaut environ 499 MPa tandis que les tenseurs extrêmes sont proches de 427,657 MPa. Le VONM aluminium dépasse également 324 MPa alors que les points extrêmes sont proches de cette référence. La [documentation de post-traitement](https://2021.help.altair.com/2021/hwsolvers/rad/topics/solvers/rad/faq_rad_post_processing_r.htm) décrit VONM à partir des contraintes moyennes. La différence observée n’est pas expliquée ni utilisée pour revendiquer un écoulement exact partout ; sorties intermédiaires, cisaillement transversal, formulations et synchronisation restent à examiner. Le maximum dans toutes les fibres d’une poutre n’est pas obtenu.

Il manque une construction du radôme et de ses fixations, les propriétés et épaisseurs propres aux différentes pièces, la dépendance à la vitesse de déformation, des lois de rupture identifiées, l’autocontact et le contact des moteurs, une convergence spatiale et la réponse des planchers/noyau. La dégénérescence du nez doit être traitée par une représentation et une méthode défendables, pas par un seuil d’érosion choisi pour prolonger ou rapprocher le résultat attendu. Les fractions ou sensibilités de cas ne sont pas des probabilités de l’événement réel.

La localisation en flexion après fracture complète reste non validée. Une température imposée n’est pas un incendie calculé. La réussite de tests numériques ne valide pas l’effondrement réel. Blender reste visualisation tant qu’il n’est pas relié à des états mécaniques vérifiés. A04 ne calcule aucun incendie ni effondrement.

## Reproductibilité et reprise

OpenRadioss v20260728-win64, Engine marqué /VERS/2026, deux threads par cas, versions et hashes des exécutables dans chaque journal. Histoires toutes les 0,01 ms, animations toutes les 0,1 ms, timeout principal 300 s. Il y a 9 nouveaux départs principaux au total (la tentative r0 incluse), 6 observations auxiliaires à matériaux inchangés, 9 Starter et **zéro ancien calcul relancé**. Quatre des huit cas r1 atteignent leur horizon demandé, dont un des cinq cas plastiques avec contact. Les autres sont des résultats partiels explicitement bornés.

Les paramètres restent dans aircraft_a04_predeclaration.json ; decks, scripts, journaux, animations binaires, reprises, CSV, NPZ, premières interprétations et relecture corrigée sont conservés. La source des résultats à reprendre est **cached_review/review.json**. complete_aircraft_a04.py verify relit les hashes et le harnais sans calcul de dynamique.

{NEXT}

Après enregistrement, le registre contient 123 itérations historiques, dont A01–A04 pour l’avion entier ; ce compteur ne mesure pas une fidélité physique. Publication GitHub : A02+A03 déjà vérifiée, A04 première itération en attente (1/2), prochaine paire A04+A05. Aucune écriture GitHub n’est requise pour A04 seule.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Passation compacte AIRCRAFT-A04 → A05

Lire AGENTS.md, harness/state.json (prioritaire), puis cette passation. A04 est terminée comme itération exploratoire, avec des critères numériques et physiques échoués conservés. Route avion entier, aucun fit vers NIST ; V8H périmée, I02I-M et V11S différées, contrôle V11F conservé.

Graphe A03 inchangé : 35 020 nœuds, 6 538 triangles avion + 4 600 poutres + 31 986 quads façade, 59 colonnes×3 étages, 944 appuis fixes. v=(-200,5,2) m/s, attitude nulle, conditions de test propres au modèle. Masse avion 122159,1859781 kg, façade 69310,977272 kg. Moteurs masses/RBE3 sans contact ; nez métallique hypothétique, pas un radôme composite reconstruit.

A04 r1 : 8 départs intacts, tous Starter sans erreur/avertissement. LAW2 σ=a+Hεp, a=324/503/427,656 MPa, n=1,c=0 ; N=5, dm=0,df=10⁻²⁰, aucune fracture/érosion/mass scaling/autocontact. Variantes a×0,8/1,2 et H=0,02E déclarées avant calcul. Références Kaiser T4/T351 et T651, pas nomenclature767 ; Boeing ARFF page6 identifie le radôme composite sans propriétés/épaisseurs historiques. PDF sources dans input/aircraft_a04_sources, exclure de publication et ne pas modifier.

FREE plastique : uniforme, PW=0. Contrôles élastiques à0,6004377 ms. Cas nominal et½dt/a×0,8/a×1,2 plafonnés300s à~1,63ms ; derniers états~1,6ms, histoires1,620001/1,630002/1,63ms : aucune fin vérifiée. Triangle4050=fuselage_caps, nœuds2040/17/18,X0=0,aireinitiale1,980619225e−4m² ; aire à1,60003ms={area*100:.3f}% initiale,Δt terminalnominal~6e−8ms. Pas assimilé à une fracture. H=0,02E termine en{Hseconds:.2f}s à{hard['actual_main_end_time_ms']:.7f}ms, mais εp coque0,871/poutre0,738 : non qualifié en grandes déformations, ne pas retenir comme vérité parce qu’il termine.

PW nominal onset0,2401098ms, premier étatplastique0,300254ms. Nominal dernier PW561,388kJ,IE784,251kJ, résidu−64,879kJ (~7,88%gen823,121kJ),Jx−5189,161Ns.½dt diffJ{s['half_dt_impulse_relative_difference']*100:.5f}%,diffgen{s['half_dt_generated_energy_relative_difference']*100:.5f}% à1,620001ms, pas qualification spatiale. Coquesεp3,726,poutres5,408. H dernierPW1166,090kJ,Jx−10160,490Ns. Touscontacts échouent bilanlocal5%gen+1000J au-delà1kJ, malgré bilan globalpetit/K0. dfmin seul améliore résiduA03 d’environ1,51kJ à0,4955922ms, ne résout pas ledger. PW inclus dansIE, ne pas additionner.

TH contact brut secomportecomme impulsioncumulée Nms (retestPfaçade : erreurmax38Ns contre~1941Ns si forceintégrée). Réactions petites facequantificationPglobal, unités non distinguées ; conserver deuxinterprétations. Poutres ordre natif prouvé par history_label_probe : F1,F2,F3,M1,M2,M3,IE,SX,EPSP. Les cinqpremiersaudits avaient mauvaisordre ; premiersaudits immuables, métriquescorrectes dans cached_review/review.json ; SXnominalmax503MPa, pas contraintefibreflexion. VONM moyen>limite tandisque tenseursextremes≈limite : différence non expliquée, ne pas effacer.

r0 uneanimationA007 écrasée par premierobservateur, nonrécupérée et tentative nonacceptée. r1 observe dans dossierisolé et hashes principaux identiques. PremierT02/animation observe fin principale, soncyclecontinuation exclu ; nepasutiliserd’observateur pour prétendrefin desTIMEOUT. A02CG1,204527mm etancienséchecs restentvisibles. {n}anciensfichierspréservés. 9calculsprincipauxneufs/6observations/9Starter, zéroancienEngine relancé. Rapport,NPZ,raws,decks,manifestes conservés ; complete_aircraft_a04.py verify sanssolveur.

Figure retenue cached_review/A04_contact_plastique_v2.png : projectionXY, déplacement×1, planINITIALfaçade seulement, pas façade déformée. PremierPNG conservé avec défautdedécoupe ; v2corrige présentation sanschangerétats. Ailes pas encoreaucontact ; feu/effondrement absents. Les limitesflexionpostfracture/V11F/thermique/Blender demeurent.

Suite : {NEXT}

Cadence GitHub : lire publication_cycle.json, A03 dernière publiée ; aprèsA04 pending1/2, envoyerA04+A05 seulementaprèsvérificationA05 avec ceséchecs. AucunpostX ni opérationYoremi demandé.
''',encoding='utf-8')
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[ROOT/'wtc1_simulation_v8/scripts'/name for name in ['run_aircraft_a04.py','audit_aircraft_a04.py','collect_aircraft_a04_partial.py','probe_aircraft_a04_labels.py','review_aircraft_a04_cached.py','plot_aircraft_a04.py','complete_aircraft_a04.py','acquire_aircraft_a04_sources.py']]+[CFG,HANDOFF]+list((ROOT/'wtc1_simulation_v8/input/aircraft_a04_sources').glob('*.json'))
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)],'excluded':['self','publication_verification.json','mutable harness/state registry cadence','external PDF sources and rendered copyrighted source inspection images'],'scope':'Own whole-aircraft outputs, configurations and scripts, all failed attempts/criteria preserved; external sources pinned separately.'})
    print({'prepared':True,'manifest_files':len(paths),'old_files_preserved':n,'harness':review['harness_after_computations']['Status']})

def register():
    assert REPORT.exists() and HANDOFF.exists() and not (OUT/'publication_verification.json').exists();preserved()
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:assert sha(ROOT/'harness'/name)==sha(OUT/('before_'+name.split('/')[-1]))
    for row in read(OUT/'artifact_manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    assert harness()['Status']=='PASS';state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');assert state['current_iteration']=='AIRCRAFT-A03' and cycle['pending_iterations']==[]
    s=read(OUT/'cached_review/review.json');t=now();status='completed_whole_aircraft_plastic_contact_with_timeboxed_and_physical_limits'
    record={'experiment_id':'WTC1-AIRCRAFT-A04','registered_at':t,'status':status,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'cached_review/review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'saved_arrays_and_connectivity_pass':True,'all_declared_checks_pass':False,'physical_impact_qualified':False,'local_energy_ledger_fully_qualified':False,'radome_reconstructed':False,'fresh_intact_cases_r1':8,'r1_requested_horizons_reached':4,'r1_timeboxed_cases':4,'main_solver_jobs_including_r0':9,'same_material_observation_jobs':6,'starter_jobs':9,'old_solver_reruns':0,'old_files_preserved':2464,'half_dt_impulse_relative_difference':s['half_dt_impulse_relative_difference'],'half_dt_generated_energy_relative_difference':s['half_dt_generated_energy_relative_difference'],'nominal_last_saved_history_ms':s['cases'][3]['last_history_time_ms'],'hardening_actual_end_ms':s['cases'][7]['actual_main_end_time_ms'],'NIST_outcomes_used_as_target':False,'NIST_nominal_facade_input_dependency':True,'next_iteration':'AIRCRAFT-A05'}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A04',next_iteration='AIRCRAFT-A05',current_status=status,next_objective=NEXT,updated_at=t);state['aircraft_a04_key_results']=record;state['user_steering_2026_10_05']['next']='AIRCRAFT-A05'
    state['validated_artifacts'].update(aircraft_a04_report=rel(REPORT),aircraft_a04_results=rel(OUT/'cached_review/review.json'),aircraft_a04_handoff=rel(HANDOFF),aircraft_a04_states=rel(OUT/'r1/PLASTIC_NOMINAL/verified_states_SI.npz'),aircraft_a04_figure=rel(OUT/'cached_review/A04_contact_plastique_v2.png'))
    cycle.update(pending_iterations=['AIRCRAFT-A04'],pending_count=1,next_publication_after='A04+A05 after one further verified iteration; include timeboxed runs and plasticity/energy/radome limits',updated_at=t)
    dump(ROOT/'harness/state.json',state);dump(ROOT/'harness/publication_cycle.json',cycle);verify(True)

def verify(write=False):
    n=preserved();manifest=read(OUT/'artifact_manifest.json');bad=[r['path'] for r in manifest['files'] if sha(ROOT/r['path'])!=r['sha256']];before=read(OUT/'before_state.json');state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');v=harness();reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();suffix=reg[len(prefix):].decode().splitlines();s=read(OUT/'cached_review/review.json')
    protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_artifact_hashes':not bad,'predecessors_preserved':n==2464,'predeclaration_unchanged':sha(CFG)==read(OUT/'declaration_guard.json')['sha256'],'registry_append_only':reg.startswith(prefix),'one_new_record':len(suffix)==1 and json.loads(suffix[0])['experiment_id']=='WTC1-AIRCRAFT-A04','state_route':state['current_iteration']=='AIRCRAFT-A04' and state['next_iteration']=='AIRCRAFT-A05','old_results_and_limits_preserved':all(before[k]==state[k] for k in protected),'source_and_inherited_inputs_preserved':all(sha(ROOT/r['path'])==r['sha256'] for r in read(OUT/'source_manifest.json')['local_inputs']),'saved_state_and_graph_review':s['integrity_only_pass'] and read(OUT/'saved_result_review.json')['pass'],'partial_runs_and_failed_gates_visible':not s['all_declared_checks_pass'] and sum(not r['requested_horizon_reached'] for r in s['cases'])==4 and all(r['actual_main_end_time_ms'] is None for r in s['cases'] if not r['requested_horizon_reached']),'no_physical_impact_or_local_energy_claim':not s['physical_impact_qualified'] and not s['local_energy_ledger_fully_qualified'],'r0_collision_retained':not read(OUT/'r0/ELASTIC_N0_DFMIN/observer_preservation.json')['main_outputs_unchanged'],'beam_order_proved_and_first_audits_preserved':s['native_beam_channel_order']==['F1','F2','F3','M1','M2','M3','IE','SX','EPSP'] and all(sha(ROOT/r['audit_path'])==r['audit_sha256'] for r in s['saved_result_proof']),'no_NIST_outcome_fit':not read(CFG)['NIST_outcomes_used_as_target'],'cadence_one_pending_and_previous_publication_preserved':cycle['pending_count']==1 and cycle['pending_iterations']==['AIRCRAFT-A04'] and all(cycle[k]==read(OUT/'before_publication_cycle.json')[k] for k in ['last_published_iteration','last_published_commit','last_published_release','repository']),'harness_pass':v['Status']=='PASS'}
    result={'created_utc':now(),'pass':all(checks.values()),'checks':checks,'new_files_checked':len(manifest['files']),'old_files_checked':n,'harness':v,'integrity_only':True,'all_declared_checks_pass':False,'physical_impact_qualified':False,'local_energy_ledger_fully_qualified':False,'pending_Github_iterations':1,'Github_publication_performed_this_iteration':False,'next_iteration':'AIRCRAFT-A05'}
    assert result['pass'],result
    if write:dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);a=p.parse_args();globals()[a.action]()
