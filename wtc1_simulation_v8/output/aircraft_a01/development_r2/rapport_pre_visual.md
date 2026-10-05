# AIRCRAFT-A01 - Boeing complet : geometrie, topologie intacte et masses

Le 5 octobre 2026, Jeremy demande de construire l'avion complet et des conditions realistes sans forcer un resultat NIST. Le registre comptait119 entrees,22 dans la branche impact; les12 dernieres I02I-A a L etaient surtout des diagnostics locaux. AIRCRAFT-A01 quitte cette succession de microtests. I02I-M est **differee**, son plan conserve. A01 ne remplace ni ne requalifie les anciennes lois echouees.

Livrable concret : un fuselage complet, deux ailes avec caisson central, longerons, nervures et raidisseurs, empennages horizontal/vertical, deux moteurs equivalents et leurs attaches; maillage SI 2860noeuds,6538triangles,4600poutres. La configuration, le maillage JSON, l'OBJ/GLB,l'apercu et la quadrature spatiale des masses sont sauvegardes dans verification_r2. Les cylindres de moteur dans OBJ/GLB sont visuels : seuls masse/inertie et pylones equivalents existent mecaniquement. Aucun moteur structurel lance en A01 : il reste a transferer ces masses au solveur sans perdre l'inertie, puis verifier le vol libre. Le maillage n'est pas declare pret a lancer un impact.

## 1. Faits directement transcrits

Les plans primaires [Boeing CAD](https://www.boeing.com/commercial/airports/3-view) et [D6-58328 RevK](https://www.boeing.com/content/dam/boeing/v2/airports/acaps/767_REV_K.pdf),PDF28/section2-8, donnent longueur159ft2in, envergure156ft1in, largeur16ft6in et hauteur de fuselage17ft9in. Conversion exacte :48,514m;47,5742m;5,0292m;5,4102m. Un dessin de planification n'est pas un plan de fabrication. Boeing annonce une precision indicative+/-6in=0,1524m pour les vues CAD; cela ne borne pas nos inconnues internes.

Dans le DXF, les extensions de cote x92,7878 et2002,7878 different de1910unites. La cote159ft2in confirme une unite en pouces. Origine du plan declaree x92,7878,y-637,838561; x vers l'arriere,y transversal,z vers le haut. Les contours d'aile selectionnes sont traces dans le JSON, pas interpretes comme positions de longerons. Les raccords, l'arrondi du bout et les stations retenues sont des approximations annoncees. Les anciennes geometries FR24 restent intactes et ne fournissent aucune raideur a A01.

PDF21/2-1 : OEW comprend structure,moteurs,equipements,amenagements,agents inutilisables et certains elements necessaires aux operations; il exclut carburant utilisable et charge utile. PDF23/2-3, les configurations types767-200ER ont OEW181130..181610lb; nous choisissons181130lb x0,45359237=82159.185978100kg. Ce n'est pas la pesee de N334AA. Les capacites de carburant utilisable publiees varient63216..91379L selon configuration. Aucun de ces maximums ne donne le carburant effectivement present a l'impact.

La page primaire [GE CF6](https://www.geaerospace.com/commercial/aircraft-engines/cf6) cite le CF6-80A sur767 et une longueur167in=4,2418m. Elle ne donne pas ici la masse ni la deformation interne; ces informations restent ouvertes. Un moteur equivalent de4500kg n'est pas un CF6-80A2 detaille valide.

## 2. Resultats de modeles officiels

**Aucun resultat NIST ne sert d'entree ni de cible dans ce nouveau constructeur.** La vitesse443mph, la masse totale, les dommages de facade et le remplacement NIST des moteurs par un PW4000 ne sont pas imposes. Les anciens sous-modeles bases sur des hypotheses/topologies NIST restent etiquetes comme tels, sans etre effaces. Le NIST pourra constituer une comparaison externe apres gel des conditions et calcul des sorties; aucun parametre ne devra etre reajuste pour supprimer un ecart observe. Modifier un parametre apres comparaison demandera une justification independante de l'ecart et une nouvelle iteration visible.

## 3. Affirmations des archives locales

Aucune nouvelle assertion issue de videos ou d'archives locales n'est examinee. Pas de rescan d'archive. 2162 fichiers anterieurs sont epingles et verifies inchanges, y compris V11F froid,V11R et les diagnostics I02I. Les sources Boeing existantes sont lues sans modification; le DXF nouvellement acquis et son ZIP sont conserves avec hashes,copyright et exclusion de redistribution. Les extractions ciblees sont locales. La publication utilise une reconstruction parametrique propre et des liens, sans incorporer le CAD Boeing.

## 4. Hypotheses, proprietes, unites et histoire

Systeme SI :m,kg,s,N,J,Pa; inertieskgm2. Proprietes generiques statiques deja referencees :aluminium2024 rho2780kg/m3,E73,1GPa,nu0,33; aluminium7075 rho2810kg/m3,E71,7GPa,nu0,33. Attribuer ces alliages aux peaux et elements internes est une hypothese, pas une nomenclature Boeing. Lois **lineaires elastiques intactes seulement**; aucune limite de rupture,d'ecrasement ou de fissuration n'est calibree. La plasticite/fracture anterieure n'est pas transferee arbitrairement a cet avion.

Peaux fuselage2,54mm,aile3,175mm,empennage2mm; ames3,175mm; deux longerons a25%/65% de corde; cadres tous les~0,6m et24raidisseurs de fuselage. Ce sont des choix de premier assemblage. SectionsA,I,J des poutres explicites dansJSON; J=2I est une equivalence circulaire hypothetique, pas une section reelle certifiee. Pylones/attaches=equivalents elastiques sans rupture. La peau du fuselage continue aux intersections d'aile, sans decoupes portes/fenetres; elle peut surestimer certaines rigidites. Les moteurs sont des masses/inerties de cylindres equivalents; leur structure interne ne porte aucune resistance d'impact qualifiee. Aucun materiau deja endommage n'est modifie; neuf et sans energie de dommage.

Toutes les masses de structure sont rho x volume :coques rho*t*A,poutres rho*A*L. Quadrature3points sur triangles exacte jusqu'au degre2,2points sur poutres,8points sur boites et16points sur cylindres pour les moments du modele. Les poutres sont comptabilisees en lignes, sans inertie transversale de section : simplification explicite. CG=sum(m*r)/M; I=sum[m*((r-CG)^2*Id-(r-CG)tensor(r-CG))]. L'audit relit leCSV independamment du constructeur.

Masse vide=structure explicite+2moteurs+**reserve de masse vide non resolue**, puis masse totale=vide+carburant+charge utile. La reserve n'est pas ajoutee au vide une deuxieme fois. Elle inclut la structure manquante autant que les equipements,amenagements et elements d'exploitation. Sa distribution dans une boite fuselage est une hypothese; elle n'a **aucun credit de raideur cache**. Ajuster cette reserve conserve une enveloppe de masse publiee et expose l'incompletude; les epaisseurs ne sont pas ajustees pour atteindre cette enveloppe ou un degat. Si la structure depasse le budget, le cas est rejete.

Carburant nominal30000kg,densite800kg/m3 :scenario arrondi propre, pas reconstruction AA11; sensibilites20000/40000kg. Distribution symetrique proportionnelle au volume geometrique du caisson entre25%/65% de corde,jusqu'a75% de la demi-envergure,caisson central inclus. Pas de sloshing ni pression. La capacite geometrique hypothetique=66137.4kg et le remplissage nominal=0.45360; la capacite Boeing depend de la configuration et n'est pas ajustee pour coïncider. Charge utile nominal10000kg,boite cabine,variations5000/15000kg. Epaisseurs peaux x0,7/x1,3; distribution de la reserve translatee de-3/+3m. Pas de probabilites attribuees a ces9scenarios.

## 5. Resultats derives et controle energetique

Nominal :structure explicite19.972t,moteurs9t,reserve vide53.187t (64.7% du vide),carburant30t,charge10t,total122.159t. CG=(22.44066,3.294e-16,-0.33092)m. Ces valeurs caracterisent nos distributions, pas le centre de gravite mesure de l'avion historique.

| Scenario | Masse totale (t) | CG x (m) | Vide non resolu (t) | Iyy (millions kg m2) |
|---|---:|---:|---:|---:|
| NOMINAL | 122.159 | 22.4407 | 53.187 | 8.7637 |
| FUEL20 | 112.159 | 22.4607 | 53.187 | 8.7073 |
| FUEL40 | 132.159 | 22.4236 | 53.187 | 8.8197 |
| PAYLOAD5 | 117.159 | 22.4595 | 53.187 | 8.3764 |
| PAYLOAD15 | 127.159 | 22.4233 | 53.187 | 9.1501 |
| SKIN07 | 122.159 | 22.3376 | 56.624 | 8.5856 |
| SKIN13 | 122.159 | 22.5437 | 49.751 | 8.9392 |
| MASS_FORWARD | 122.159 | 21.1345 | 53.187 | 9.0150 |
| MASS_AFT | 122.159 | 23.7468 | 53.187 | 9.0529 |

Les29182points de masse reproduisent le bilan a erreur relative2.382e-16. 66/66criteres declares passent, plus4/4controles de relecture des masses et6/6controles d'export geometrique/conversion. Connexite,absence d'aires nulles exportees,symetrie de masse,inertie positive et capacite conditionnelle controlees. L'erreur maximale des positions float32GLB=1.896e-06m. Maillage double :variation de masse structure0.2106%,norme d'inertie0.0238%,seuils2% declares avant calcul. Ces tests verifient cette construction numerique, pas les proprietes reelles de l'avion.

Premiere execution r0 conservee au niveau racine :57/66criteres,neuf echecs de symetrie de masse. Le decoupage identique des quadrilateres gauchis sur les deux ailes ne refletait pas la diagonale physique et introduisait unCG transversal~1,3e-7m. Correction r1 :diagonales en miroir. Aucun seuil,propriete,masse cible ou resultat externe modifie; ancien script preserve dans development_r0. Ces neuf echecs r0 restent visibles. r2 conserve egalement r1 et corrige une erreur arithmetique de3e-6kg dans la conversion decimale predeclaree d'OEW : calcul direct181130lb x0,45359237. Le champ original errone reste dans la configuration immuable et la difference est affichee dans chaque bilan. Ce n'est pas un changement de masse physique pour ajuster une sortie. L'apercu r2 utilise la meme echelle sur les deux axes du plan et exporte des cylindres moteur visuels.

Dans cet etat neuf non sollicite,Uelastique=0 et energie de dommage=0 par definition. Aucune reaction ou collision calculee. A titre inertiel seulement, une translation uniforme a200m/s donnerait KE=0,5*M*v²=2.443184GJ, vitesse ronde hypothetique **non attribuee a AA11**. Aucun bilan d'absorption/ejection/incendie n'est encore produit. Reactions,travail interne et repartition energetique d'impact devront venir des sorties mecaniques futures, jamais d'une animation imposee.

## 6. Contradictions et donnees manquantes

La fraction importante de vide non resolu montre exactement pourquoi ce premier Boeing n'est pas encore un modele de resistance d'impact complet. Le plan de chargement,le CG,l'etat de carburant et la configuration specifique ne sont pas etablis. Les epaisseurs,sections,pylones,fixations,moteur interne et lois a grande deformation restent incomplets. Le maillage ferme visuellement n'est pas une preuve de fidelite mecanique. La masse de coque et les inerties convergent pour les hypotheses actuelles; elles ne permettent pas d'identifier les inconnues.

A02 :transfert de masses/inerties au solveur,orientation locale des poutres et controle de l'avion intact en vol libre court; recherches primaires ciblees sur les inconnues qui dominent les charges/rigidites. Ensuite un impact de l'avion entier sur facade representative, avec plage de vitesse/attitude declaree avant observation des degats. Des mailles plastiques non physiques,une energie non conservee ou une fracture non calibree resteront des echecs affiches. Ne pas repousser indefiniment l'assemblage complet pour finir tous les microtests :I02I-M reste disponible si un blocage concret de la loi exige son execution.

Preserver les echecs E/F/G/I/J,L,convention NASA et Gf30hypothetique; aucune propagation physique qualifiee. V11F froid conserve,V11R versV11S differee. Localisation en flexion apres fracture complete non validee; temperature imposee n'est pas un incendie calcule. Aucun effondrement historique valide. Blender/OBJ/apercu restent des visualisations de la configuration, sans animation d'impact forcee.

## Reproduction et passation

Configuration et garde declarees avant construction; graine1102026,aucun tirage. Construction5.263s,zéro moteur; lecture seule des anciens calculs. Ne pas relancer inutilement :complete_aircraft_a01.py verify verifie les sorties sauvegardees. Dans un dossier neuf, utiliserles scripts avec les sources ciblees referencées; ne jamais ecraser A01.

AIRCRAFT-A02 est la prochaine route; passation WTC1_AIRCRAFT_A01_HANDOFF.md. Publication cadence2iterations :L+A01 apres verification. Aucune publication X n'est autorisee dans ce travail.
