# AIRCRAFT-A55 — corruption mémoire localisée, cohésion implicite non qualifiée

Le moteur A54 inchangé s'arrête avant la charge dans les témoins cohésifs implicites. Une surveillance native établit l'écriture qui corrompt un en-tête mémoire, puis sa libération échoue. Un nouveau correctif limité au tampon temporaire est préparé ; l'accord explicite reçu couvre sa future application et compilation A56. Aucun temps physique entier supplémentaire n'est obtenu.

## 1. Faits directement observés ou transcrits

Seize nouveaux Engine, un CPU, plafond180s, aucun calcul GPU. Quinze s'arrêtent code3 à NC=0/T=0 avec free(): invalid pointer ; les lanceurs observateurs terminent0 mais le code Engine reste3. Le CHECK solide ordinaire termine normalement, sans volume nul, mais garde1erreur de matrice définie positive : ce n'est pas un CHECK propre. Aucun ancien Engine rejoué.

Quatre témoins implicites initialement prescrits échouent. Quatre variantes libérant des déplacements transversaux non chargés échouent aussi ; leurs quatre premières préparations avaient échoué à la lecture de configuration Starter, conservées dans leur dossier initial. R1 utilise l'environnement déjà établi et quatre Starter propres. Deux autres contrôles ne changent que les sorties nodales (sans réaction, puis sans bloc nodal) : deux Starter propres, deux arrêts identiques. Dix lancements Starter au total, quatre échecs de configuration et six préparations sans erreur ni avertissement. Les hypothèses simples de contrainte complète et de sortie nodale ne résolvent pas l'arrêt.

La capture SIGABRT déroule15trames CFI puis conserve honnêtement l'arrêt sur règle non prise en charge. RESOL libère NODREAC. La surveillance matérielle observe son allocation alignée, en-tête0x31, puis une écriture SRCOORK+0x4488 qui remplace cet en-tête par0 avant free/SIGABRT. R1 n'avait pas capturé le contexte SRCOORK car la sonde désactivait son propre point d'entrée ; cette observation incomplète reste conservée. R2 corrige uniquement l'observateur : un appel, NEL=1, IGTYP=43, ISMSTR=1, JHBE=0, JCVT=1, connectivité1..8. La destination calculée par les registres correspond exactement à l'en-tête surveillé. Aucune instruction mécanique ni tableau du moteur n'est modifié par la sonde.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle historique officiel. Le binaire A54 SHA256 c4a18b981b9beb461fbb570a12d5ef04aa9a97293c61875c9d458ea99579d3b2 reste intact. Le logiciel figé déclare SAV(NEL,21) dans SRCOORK ; S8ZKE3 transmet GBUF%SMSTR et l'allocation temporaire implicite utilise NEL*G_SMSTR. Sources archivées en lecture seule ; aucune installation, application de patch ni compilation A55.

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive, photographie, vidéo ou PDF historique consulté. Les sources et les anciennes sorties sont préservées. Les dégâts connus ne constituent pas une cible.

## 4. Hypothèses propres au modèle

Graine1102080, aucun tirage ; unités g/mm/ms, conversion Nmm vers J=0,001. Les variantes de supports et de sorties sont déclarées séparément ; masses, matériaux et budgets ne changent pas. L'insuffisance de capacité du tampon est inférée du contrat source et de l'écriture observée ; la capacité native G_SMSTR n'a pas été lue. Cette inférence ne prouve pas la compatibilité physique implicite des TYPE43.

## 5. Résultats dérivés

La proposition réserve au moins21*NEL valeurs dans le SMSTR temporaire TYPE43 uniquement et initialise si l'allocation réussit. Source/restart et autres types restent inchangés.48cas arithmétiques/bornes et72colonnes passent ; aucun contrôle Fortran compilé n'est revendiqué. La première proposition utilisant ZERO absent de la portée est conservée ; R1 emploie0.0D0. Les sources dérivées et patch AGPL restent hors du manifeste public MIT ; proposition, empreintes et scripts propres sont publiables. Accord humain reçu distinctement pour ce correctif, quatrième moteur isolé, plafond1h/sixCPU, puis contrôles bornés180s.

Préservation vérifiée par métadonnées et manifestes antérieurs, hash neuf du binaire A54, harnais PASS. L'intégrité de cette itération ne constitue pas un passage des critères physiques.

## 6. Contradictions et informations manquantes

Aucune réponse cohésive implicite chargée, énergie, traction, rechargement ou demi-pas obtenue. Aucun résultat à convertir en vidéo3D nouvelle. Le CHECK entier A54 garde15erreurs,624messages de volume et5TYPE25 ignorés. Les critères échoués, y compris l'erreur du témoin solide, restent conservés. A52 non intégré ; contacts entiers, inerties/travaux et couverture énergétique manquent encore. La meilleure fenêtre entière reste0,0200001220703125s ; dix secondes physiques et leur vidéo restent incomplètes.

AIRCRAFT-A56 : accord explicite reçu le13octobre pour le nouveau correctif A55 du tampon SMSTR temporaire TYPE43, patch a0d52993240ac373a726185b2a3400d447bd947a59aa483b7f60e45c2bdc8503, source alloc_elbuf_imp.F seulement ; préserver le correctif de graphe A53, source figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a. Compiler un quatrième moteur isolé a56_type43_scratch_candidate, une heure maximum/sixCPU/sansGPU ni installation, puis contrôles natifs capacité/mémoire et cohésion implicite chargée, graphe/CHECK et régressions explicites/TYPE7 avec critères inchangés et180s par processus. A55 :16Engine,10Starter dont4échecs de configuration conservés, aucun temps physique chargé ; corruption malloc directement écrite par SRCOORK surTYPE43, insuffisance de capacité inférée du contrat SAV(NEL,21) et allocation NEL*G_SMSTR ; capacité native G_SMSTR non lue. La suppression de la corruption ne qualifiera pas les lois, les15erreurs CHECK entières ni les5TYPE25 ignorés. Le contrôle solide ordinaire termine mais conserve1erreur de matrice définie positive. A52 non intégré, budgets et tous échecs conservés, aucune RKE compensatoire. Meilleur impact entier A20=0,0200001220703125s ; objectif1 dix secondes physiques puis vidéo3D toujours incomplet. Publication A54+A55 à vérifier avant remise à zéro de la cadence.
