# AIRCRAFT-A56 — correctif temporaire insuffisant, capacité nulle du tampon d'origine mesurée

Le quatrième moteur isolé applique le correctif A55 explicitement autorisé. Il compile et conserve les contrôles de graphe et témoins explicites/TYPE7, mais les cohésifs implicites s'arrêtent encore avant le premier pas. Une mesure native établit que SAV est le tampon d'origine de capacité zéro, pas la copie temporaire visée. Cette hypothèse échouée reste conservée. Aucun temps physique entier supplémentaire.

## 1. Faits directement observés ou transcrits

Accord humain distinct A55 enregistré. Source et dépendances cachées vérifiées, correctifs exacts A53 graphe et A55 tampon temporaire appliqués ; compilation/export en environ301s, plafond1h/sixCPU, sans GPU ni installation. Binaire ff062b207c262381e6886f0da3e3a568724d48651a21913b2a1f5596222b53f1 séparé, anciens moteurs intacts, espace ext4 démonté.

Dix-sept Engine nouveaux, zéro Starter, un CPU/cap180s chacun. Sept arrêts cohésifs implicites code3 àNC=0/T=0 : CHECK isolé, quatre témoins chargés et deux observations. Les lanceurs observateurs code0 ne sont pas des passages Engine. Le CHECK solide ordinaire termine mais garde1erreur de matrice définie positive. Les deux CHECK entiers et l'oracle de graphe terminent normalement tout en conservant15erreurs,624messages de volume et5TYPE25 ignorés.

La surveillance observe le retour de SRCOORK avec21colonnes lues et NODREAC0x31→0 ; elle ne prétend pas lire un descripteur à partir d'un en-tête malloc. Une seconde sonde capture740appels d'allocateur et leurs labels. Pour ELBUF_STR%GBUF%SMSTR : demande0, élémentdouble8octets, bornes natives1..0, capacité0. Le pointeur alloué est exactement SAV transmis à SRCOORK, TYPE43/NEL1. Le retour appelant0x468d01 est dans ALLOCBUF_AUTO. Une première garde statique d'ABI supposait le même registre dans deux auxiliaires simple précision ; échec avant lancement Engine, conservé. R1 utilise les deux auxiliaires double précision et vérifie les vrais offsets du descripteur par le désassemblage du binaire.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle historique officiel. Source moteur fixée3d75ff13d1946f6d28a43920eac4fa2aae41b27a, mêmes dépendances et outils hérités d'A54 ; écart de version71→67 conservé. La routine SRCOORK attend SAV(NEL,21), et ALLOCBUF_AUTO charge/alloue l'original selon la largeur du redémarrage. Les sondes ne changent aucune instruction ou donnée mécanique du processus.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou PDF inspecté ou modifié. Aucune cible de dégâtsNIST.

## 4. Hypothèses propres au modèle

Graine1102081, aucun tirage. Entrées physiques et critères des témoins restent identiques ; aucune masse, inertie ou RKE compensatoire. L'hypothèse A55 « le tampon temporaire seul est insuffisant » ne résout pas la corruption. La capacité nulle du tampon réellement passé est maintenant une mesure native directe ; cela ne valide pas sa future correction ni la physique implicite.

## 5. Résultats dérivés

256opérations de graphe passent l'oracle d'ensembles ; les3024attaches du modèle original et du candidat A52 correspondent exactement à la référence enregistrée. Aucun message de connectivité manquante. Quatre témoins cohésifs explicites passent travail/énergie, traction, rechargement, aire et demi-pas ; deuxTYPE7/MUMPS passent bilans et demi-pas.600champs passent la règle de précision ASCII/float32 déjà établie ; échecs littéraux conservés. La passerelle de métadonnées completion est fournie avant analyse afin de ne pas rejouer le défaut de lecture connu.

Proposition distincte allocbuf_auto.F : réserver au moins21*NEL dans l'original TYPE43, initialiser le stockage, conserver largeur sérialisée, offsets, SDP_RBUF et valeurs restaurées.48cas arithmétiques/restauration passent, aucune compilation de cette proposition. Sources/patch/binaire AGPL hors manifeste MIT, empreintes et scripts propres conservés. Préservation des anciens fichiers par métadonnées et manifestes SHA256, hash neuf du moteur, harnais PASS.

## 6. Contradictions et informations manquantes

Le correctif temporaire a compilé mais échoue à son objectif mémoire. Aucun bilan cohésif implicite chargé n'est obtenu. Le CHECK entier et TYPE25 restent bloquants ; A52 non intégré, inerties/travaux et énergie locale entière manquent encore. La meilleure fenêtre entière demeure0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes. Aucun nouveau calcul entier ou rendu GPU lancé.

AIRCRAFT-A57 : attendre accord explicite sur le nouveau correctif de l’allocation d’origine TYPE43 dans allocbuf_auto.F ; patch ef56cf633e4d43b2dd4298f1c5995da1cae7f4a22130aea35e9702dc57c0427e, proposé et non appliqué. La mesure native A56 confirme demande0/capacité0/bornes1..0/double8octets, pointeur original ELBUF_STR%GBUF%SMSTR identique à SAV reçu par SRCOORK. Le correctif A55 appliqué au tampon temporaire dans A56 ne suffit pas ; cet échec reste conservé. Moteur A56 SHA256 ff062b207c262381e6886f0da3e3a568724d48651a21913b2a1f5596222b53f1, compilation301s plafonnée1h,17Engine, aucun Starter. Graphe256opérations et3024attaches exactes passent ; quatre témoins explicites et deuxTYPE7 passent ; sept arrêts cohésifs avantT=0 restent. Cinquième moteur séparé prévu, correctifs A53 graphe et A55 temporaire conservés, nouvelle seule différence allocbuf_auto.F,1h/sixCPU/sansGPU ni installation, capacité/pointeur/mémoire puis cohésion chargée et régressions avec critères inchangés,180s chacun. Largeurs de redémarrage, offsets, compteurs de lecture et budgets inchangés ; source fixée3d75ff13d1946f6d28a43920eac4fa2aae41b27a. CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés, témoin ordinaire1erreur de matrice, A52 non intégré, couverture mécanique/énergétique entière manquante. Meilleur impact entier A20=0,0200001220703125s ; objectif1 dix secondes physiques puis vidéo3D incomplet, aucun temps des diagnostics crédité. A54+A55 publiées/vérifiées f44bcdfbe820eb624346ee51ce547c9bd0c5d215 ; prochaine cadence A56+A57 vérifiées.
