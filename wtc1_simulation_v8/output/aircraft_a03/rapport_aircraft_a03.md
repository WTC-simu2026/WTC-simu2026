# AIRCRAFT-A03 — premier contact de l'avion entier avec une façade représentative

L'assemblage complet A02 est relié à une bande de façade de59colonnes et3étages. Trois nouveaux calculs sont conservés : contactdésactivé et deux contacts avec facteurdepas0,8/0,4. Aucun dommage, déplacement ou résultat historique n'est fixé. **Premiercontact vers0,2256ms; dépassement des repères élastiques au plus tard dans l'état0,2753ms.** Ce n'est pas une simulation qualifiée de rupture du767 ou d'effondrement. Registre122aprèsA03, une itération et trois calculsEngine, zéro anciencalcul relancé.

## 1. Faits directement observés ou transcrits

2860nœuds structuraux+368masses/RBE3 de l'avion;6538triangles+4600poutres inchangés. Façade31792nœuds+31986quadrilatères; total35020nœuds. Chaque cas sauve20états(0à~0,475ms),100échantillons temporels(0à~0,495ms). Starter etEngine terminent normalement,0erreur/0avertissement. Tous les nœuds et les connectivités sont relus et contrôlés. Le convertisseur padde les triangles avec un quatrième sommet répété; le premier audit déclarait ainsi la connectivité fausse. cached_review normalise cette représentation et démontre les6538triangles originaux identiques, sans changer les decks, résultats ou premiersaudits. Les identifiants sont réordonnés avant toute comparaison; le rang d'un nœud dansVTK n'est pas sonidentifiant.

Les références primaires [TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm), [TH/INTER](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_inter_starter_r.htm) et [ANIM/SHELL/VONM](https://2022.help.altair.com/2022/hwsolvers/rad/topics/solvers/rad/anim_shell_restype_engine_r.htm) définissent le contact et les sorties. L'URLVONM initiale n'était pas la bonne; source_addendum la corrige, sans réécrire la déclaration initiale. VONM indique une contrainte moyenne de coque, pas un maximum dans les fibres ni une contrainte de poutre. Aucune source physique nouvelle de radome ou de construction du767 n'est acquise.

## 2. Résultats de modèles officiels

Les dimensions nominales de façade viennent des entréesNIST déjà transcrites dansV8V/I02A :59colonnes,14in de largeur,40in de pas,52in de traverse. Les épaisseurs voisines5/16in et3/8in et l'étage12ft restent une façade représentative, pas la nomenclature exacte des niveaux impactés. **Cette dépendance aux données nominalesNIST est explicite; aucun résultat de dégâtsNIST ne sert de cible.** OpenRadioss réalise notre calcul exploratoire, pas une nouvelle reconstitution officielle. La vitesse(-200,5,2)m/s, l'attitude nulle et l'alignement central ne sont pas attribués àAA11.

## 3. Affirmations des archives locales

Aucune archive rescannée, aucune vidéo analysée, aucun PDFsource modifié. 2322anciens fichiers épinglés sont identiques. A01/A02, les échecsI02I et le planI02I-M différé sont conservés. V11F froid et la branche thermiqueV11R→V11S demeurent séparés. Un renduPillow projette les états mécaniques sauvegardés à déplacement réel×1; ce dessin ne constitue aucune validation physique supplémentaire. Blender reste visualisation.

## 4. Hypothèses, propriétés, unités et conditions

Le nez est la fermeture en aluminium hypothétique d'A01, **pas un radomecomposite reconstruit**. Les moteurs restent4500kg chacun avec attacheséquivalentes; leurs cylindres visuels n'ont pas de surfaces decontact. Réservevide53,187t comprend de la structuremanquante sansraideur cachée. Géométrie interne,épaisseurs,assemblages et distribution de carburant restent hypothétiques. Pas de gravité, précontrainte, incendie, fracture, érosion, contactentrearêtes ou autocontact.

MétauxLAW1 élastiques intacts : aluminiumpeau2024,rho2780kg/m³,E73,1GPa,nu0,33; internes7075,rho2810,E71,7GPa,nu0,33; acier représentatif,rho7860,E200GPa,nu0,3. Références typiques de limiteélastique310,264/503,32/427,656MPa : **diagnostics uniquement**, pas lois de rupture. Poutres de section et inertieséquivalentes héritées avec amortissement numériquepar défaut signalé enA02; sa contribution au bilan local n'est pas identifiée ici. Les critères diagnostiques ne suppriment aucun élément.

Colonnes carrées355,6×355,6mm,paroi7,9375mm; traversesfrontales1320,8mm de hauteur,9,525mm d'épaisseur. Panneau60960×10972,8mm; jonctionspar nœudscommuns parfaites,944nœuds hauts/bas bloqués sur6degrés. Ni planchers,noyau,coins,épissuresfragiles ni souplesseglobaletour. Appuisimmobiles : travail0, réactions quasi nulles sur cette fenêtre, sans en déduire leurs unités indépendamment.

Unitésnativesg/mm/ms/MPa/N/Nmm. 1kg=1000g;1m=1000mm;1ms=0,001s;1Nmm=0,001J;1Nms=0,001N·s;1mm/ms=1m/s. Masseavion122159,1859781kg,façade69310,977272kg; masseensemble191470,163250kg. La façade initialement immobile ne contribue pas àK0=½Mavion|v|²=2,444955028GJ. Le décalageCG natifA02 de1,204527mm est conservé, sans ajuster la masse pour le masquer.

Distanceinitialeneztoplan50mm; enveloppenumériqueTYPE7 constante5mm, clairance45mm, activationbalistique(50−5)/200=0,225ms. TYPE7 unilatéralnœudsexternesavion→coquesfaçade,Istf4(minraideurs),Igap1000,Stfac1,friction0,VISs1e−20 pour éviter le défaut0,05, sansdéplacementautomatiqueinitial(Inacti1000). La clairanceinitiale exclut géométriquement les pénétrations; aucune correction de position n'est faite. L'avion n'a aucune trajectoire imposée aprèsv0. Nouveaux calculs frais; aucune propriété d'un matériauendommagé changée en cours de parcours.

## 5. Résultats dérivés et bilans

|Cas|Starter+Engine+CSV(s)|Dernier état(ms)|Dernière histoire(ms)|Contactdétecté(ms)|
|---|---:|---:|---:|---:|
|FREE_F200_DT080|10.786|0.475510|0.495353|None|
|CONTACT_F200_DT080|9.845|0.475029|0.495592|0.2256282|
|CONTACT_F200_DT040|16.522|0.475005|0.495201|0.2252607|

Contrôle sanscontact : translation uniforme de3228nœudsavion,façadeimmobile; énergieinterne,rotation,hourglass,travail0, conservation auxprécisionssauvées. Aveccontact, premièresimpulsions0,2256282/0,2252607ms. Différence en divisantdtpar2 : 0.11193% sur l'impulsionvectorielle à l'instantcommun0.4952009ms; décalagedétection0.0003675ms. Ce contrôle de pas ne valide ni le maillage spatial du contact ni les mécanismes de rupture.

TH nommeFNX/FNY/FNZ des forces; **la sortie de cette version se comporte comme une impulsioncumuléeNms**. Casdt0,8 : colonnefinaleX−2763584, soit−2763,584N·s selon cette interprétation; quantitédemouvementfaçade−2754,313N·s. Interpréter la colonnecommeforce etl'intégrer produit seulement−485,904N·s. Les deux interprétations et colonnesbrutes sont sauvées; écartmaximum du bilanvectorielcumulé38,019N·s, contre une allowance déclarée10N·s+2% de l'impulsion(~65N·s). Écartfinal~0,34%,paségalitéexacte; effet possible d'échantillonnage/staggering non démontré. Pglobal inclut l'avion etla façade; Pavion=Pglobal−Pfaçade pour conserver ses massesadditionnelles absentes desPART structurels. Les réactionsprèsde0 sur cette courtefenêtre ne distinguent pas leurs deux interprétations force/impulsion. Aucun contact moteur n'est présent.

BilanE=Ktranslation+Krotation+Uinterne+hourglass+ressorts+contactélastique+friction+dissipationdecontact; ΔE−Wext est sauvé. CONTACT ENERGY global n'est pas ajouté une seconde fois à ses composantes. Casdt0,8 à0,4955922ms : K2,444606GJ; rotation72445,260J; interne223896,100J; contactélastique3371,093J; travail,friction,hourglass,dampingcontact0. **Résidumax49624,413J**, soit0,002030% deK0, inférieur au seuilglobal déclaré0,5%. Mais ce résidu représente **16.56%** des~299712J d'énergiesmécaniques générées dans le dernier échantillon. Le bilan local n'est donc **pas complètement qualifié**; l'énergie manquante ne reçoit pas une interprétation physique inventée. Beamdfpar défaut, intégration, sorties non comptées et couplages sont des pistes à départager, pas des explications établies. Les valeursglobalesCSV sont arrondies à7chiffres; le résidudépasse ce seul arrondi. Aucun massscaling; addedmass apparent~2,13e−4g(~1,11e−12fraction), conforme au nouveau critère relatifA03. L'anciencritère absoluA02 reste échoué dansses propresrésultats.

Diagnosticàl'état0,275270ms(0,275245avec½dt) : premierdépassement d'au moins une référence. Maximumssauvéspeau2470,09MPa,acier2343,85MPa; extensiongéométriqueabsoluedes arêtesavion1,706%(½dt1,708%). Ces fortescontraintes **signalent l'extrapolation de la loiélastique**, sansprédire contraintesréelles aprèsplasticité ni fracture. Les contraintesmoyennes peuvent sous-estimer la flexion externe; contraintesde poutres nonexportées. L'heureexacte du premieryield entreétats et le comportement physique du radome sont inconnus.

## 6. Contradictions et informations manquantes

Intégrité, connectivité et relecture passent. **Toutes les acceptationsnumériques ne passent pas** : la finEngine exacte n'est pas exportée, critère detolérancefin reste nonvérifié/false dans les troiscas. Les derniersétats~0,475ms ne sontpas lafin0,5ms; le premieraudit les avait traités commetels, conservé. Normaltermination etcycles ne donnentpas ici un horodatagefinal de précisionrequise. Aucun seuildéplacé ni recalcul pour effacer cet échec. Les hypothèsesélastiques sontdépassées; bilangénergiquelocal ouvert et incertitudeCGA02 conservée. La robustessephysique du chocentier n'est pas acquise.

Il manque constructionradome,épaisseurs/fixationspropresau767,moteursdéformables,carburantdistribué,loisplastiques etfracture,conditionsAA11 indépendantes,maillagedecontactconvergent,réponseétages/noyau etconditionsde gravité. Aucun feu ni effondrement calculé. Localisation en flexionaprèsfracture complète nonvalidée; températureimposée≠incendie; testsnumériques≠validationde l'événement. Pas de calibrageversNIST. A03 conserve le résultatobservé même s'il n'estpas physiquementexploitable sur toutela fenêtre.

## Reprise

AIRCRAFT-A04: premier contact de l'avion entier avec plasticite metallique explicite et sensibilites independantes, dans un nouveau depart intact a t=0. Documenter la limite du nez/radome; completer bilan local des energies et amortissements, contraintes de poutres/fibres et horodatage final. Aucun fit vers NIST ni transfert arbitraire d'historique endommage. Garder cas A03 et controle froid V11F.

Relecture sanssolveur : complete_aircraft_a03.py verify. Config,scripts,decks,sortiesbrutes,NPZ,rapports,manifestes etpremieraudits sontconservés. PublicationA02+A03 due aprèscontrôle d'intégrité, avecéchecs explicites; cadence ne sera remise àzéro qu'après vérificationdistante. AucunpostX ni opérationYoremi.
