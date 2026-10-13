# AIRCRAFT-A50 — bilans natifs au démarrage et limites du contrôle d’assemblage

La copie à chaînes rigides composées démarre en explicite avec les contacts d’origine. Ses bilans et mouvements initiaux correspondent aux résultats A45 conservés. La fenêtre est20ns, pas une extension de l’impact. La source précise également pourquoi CHECK ne teste pas le solveur demandé et pourquoi ses blocs manquants empêchent de qualifier la raideur.

## 1. Faits directement observés ou transcrits

Un seul Engine nouveau, un thread CPU, sans GPU, cap180s, temps écoulé17,858s. Aucun nouveau Starter : l’état initial natif fraîchement produit en A49 est transféré intégralement, avec SHA256 identique. Le contrôle explicite reprend les paramètres A45, seul le nom /RUN change. Terminaison normale/code0, trois cycles, aucun USERBREAK/SIGSEGV ni TYPE25 ignoré. Les résultats A45 sont copiés et convertis dans un nouveau dossier ; aucun ancien Engine relancé.

Deux histoires natives enregistrent0et10ns ; les trois animations sont0,10,20ns. Tous les champs comparés sont finis, avec mêmes labels, temps, éléments et parts. Les neuf canaux masse, masse ajoutée, énergies cinétique/rotation/interne, travail externe et impulsionsXYZ ont un écart nul à la précision enregistrée. Positions, déplacements et vitesses des48171nœuds ont aussi un écart nul sur les trois états. Aucune érosion.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Inspection en lecture seule de la source moteur figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a : PUT_KIJ retourne IERR1 avant d’ajouter le bloc lorsqu’une colonne attendue est absente. Les49370messages du CHECK A49 signalent donc des blocs non assemblés ; ils ne valident pas une raideur nulle physique.

Dans lectur.F, IMP_CHK>0 impose ISOLV1, IPREC5, ILINE1 et D_TOL0. imp_init.F associeIPREC5àIKPAT1, comme les captures A48/A49. CHECK ne résout donc pas une dynamique MUMPS parce que /IMPL/SOLVER/2 apparaît dans la carte. Changer ce mot-clé seul ne permet pas de tester un autre chemin CHECK. La source évite cette variante sans effet ; aucun logiciel modifié. Les anciens rapports sont conservés, l’addendum précise la portée des contrôles.

- [Ajout de blocs et messages : source figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/imp_glob_k.F)
- [Contrôles effectifs de CHECK : source figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/input/lectur.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle source historique, photographie ou vidéo inspectée. Aucun dégât réel ou résultat NIST utilisé pour ajuster la copie. Archives sources en lecture seule.

## 4. Hypothèses propres au modèle

Graine1102075, zéro tirage. Même modèle et état initial A49 à144références rigides composées, mêmes cinq TYPE25 et budgets physiques. Pas explicite fixé1e−5ms, fin nominale1e−5ms comme A45 ; le moteur écrit aussi l’état suivant2e−5ms. Conversion native g/mm/ms vers SI : masse×0,001kg, énergieNmm×0,001J, impulsiongmm/ms×0,001Ns. Les seuils sont déclarés avant le lancement et ne sont pas modifiés.

La comparaison brute de toute la topologie inclut les traits de visualisation des contraintes, dont les références changent par conception en A49. Son échec reste conservé. Un audit supplémentaire distinct confronte chaque extrémité changée à la liste pré-déclarée :144relations et384traits par état. Tous les types, identifiants d’élément/part, cellules physiques et autres traits restent identiques. Aucune nouvelle dynamique n’est lancée pour corriger la lecture de ces représentations.

## 5. Résultats dérivés

Les bilans globaux et mouvements passent les critères du démarrage. L’égalité brute topologique reste échouée ; l’audit supplémentaire de topologie physique et des384changements exactement déclarés passe. Les changements ne sont pas une modification cachée des éléments.

La masse de l’histoire est191273800g à sa précision d’écriture, cohérente avec les191273837,9425g du Starter. Énergie cinétique initiale2,441026e9J. Le compteur natif ADDED MASS vaut0,0002019107g : minuscule, mais non nul, identique à la référence A45. Aucun nouvel ajout compensatoire ou écart de masse n’est introduit ; ne pas confondre ce compteur avec les100368522,1367g d’ADMAS non structurelles prescrites. Le paramètre nominal sans nouvelle prescription de mise à l’échelle n’autorise pas à déclarer ce compteur observé égal à zéro.

Ces états sont essentiellement une translation initiale, sans charge mécanique significative. Ni l’inertie en rotation, ni les efforts/travaux locaux sous charge, ni les20ms de l’impact antérieur ne sont validés par cette égalité. Le convertisseur d’animation ne fournit pas de tensor d’inertie ou champ de masse nodale dans ces sorties ; aucun n’est inventé.

## 6. Contradictions et informations manquantes

Le démarrage passe, le graphe de raideur entier reste non qualifié. CHECK A49 conserve15erreurs, cinq avertissements récapitulatifs et49370messages de connectivité TYPE2/RBE2, ainsi que cinq TYPE25 ignorés en implicite. Les indices imprimés NI/NJ ne sont pas assimilés aux labels originaux sans correspondance indépendante. Aucun impact implicite lancé en ignorant ses contacts.

A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués ; structure intérieure, gravité, ruptures et bilans entiers restent ouverts. Meilleur impact entierA20=0,0200001220703125s. Objectif dix secondes physiques3D puisMP4/GIF toujours incomplet, aucun crédit des20ns de diagnostic.

Anciennes sorties préservées : audit tailles/dates et manifestes SHA256 existants, sans nouvelle lecture de tous les contenus. Original entier et moteur recontrôlés. Rapport, sorties et validation du harnais précèdent le registre. A48+A49 sont publiées, deux archives complémentaires et125anciennes archives vérifiées, deuxCI réussies ; cette intégrité ne valide pas la physique.

AIRCRAFT-A51 : analyser la construction du graphe et la composition des contraintes du modèle entier, depuis la source figée et les messages49370TYPE2/RBE2 du CHECK A49. A50 confirme les bilans et mouvements du démarrage explicite composé sur deux histoires0/10ns et trois animations0/10/20ns, avec TYPE25 conservés ; cela ne qualifie pas l’inertie en rotation ou les efforts sous charge. Les384extrémités de traits de liaison changent exactement comme les144chaînes pré-déclarées ; éléments physiques et autres liaisons restent identiques. L’égalité brute de tout le tableau topologique reste échouée, l’audit supplémentaire de la topologie physique passe. Le compteur natifADDED MASS=0,0002019107g est minuscule mais non nul et identique à la référence A45 ; aucune nouvelle compensation. PUT_KIJ retourne sans ajouter un bloc quand une colonne est absente. /IMPL/CHECK forceISOLV1/IPREC5/ILINE1 puisIKPAT1 : changer seulement le mot-clé de solveur ne teste pas un autre chemin, et CHECK ne qualifie pas MUMPS sous charge. Ne pas relancer une variante ainsi neutralisée. Identifier les contraintes imbriquées et leur fermeture du graphe, en distinguant indices internes et labels originaux, puis tester une composition équivalente explicitement déclarée ou préparer un correctif logiciel concret si nécessaire. Aucun patch moteur, ajout de masse/inertie ou impact implicite avec contacts ignorés. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; objectif dix secondes physiques3D puisMP4/GIF inchangé et incomplet. A48+A49 publiées/vérifiées, A50 en attente deA50+A51.
