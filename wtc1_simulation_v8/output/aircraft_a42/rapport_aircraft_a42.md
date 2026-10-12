# AIRCRAFT-A42 — incompatibilité LAW117 entre préparateur Windows et moteur Linux localisée

Le calcul entier avorte dans le premier calcul des forces cohésives LAW117. La reprise Windows fournit un ancien format matériau sans les tableaux attendus par le moteur Linux MUMPS figé. Une variante d’entrée algébriquement équivalente ne corrige pas la transmission. Le même état initial frais démarre avec le moteur Windows installé. Aucune extension entière ni qualification des dix secondes.

## 1. Faits directement observés ou transcrits

La sonde explicite entière initiale utilise la reprise A37 conservée octet pour octet, sans CHECK implicite. Elle termine avec code3 avant la première avance. La seconde sonde CHECK conditionnelle est donc omise. L’option installée OpenMPI de trace d’avortement permet une observation nouvelle sur ce même échec : SIGEPS117+0x9ce, appelée par SUSER43 puis SUFORC3 et FORINT. Ce n’est pas une erreur exclusive au mode implicite.

Le symbole ELF commence0x146e970 ; l’instruction fautive0x146f33e est une lecture mémoire. La source précise n’est pas disponible par DWARF, qui retourne ??:? ; aucune ligne exacte n’est prétendue. La région inférée d’accès à la première table est corroborée séparément par les données de reprise et le code d’allocation.

La préparation Windows fraîche de l’entrée à fonctions constantes termine avec0erreur,2avertissements, comme la préparation A37. Son critère strict de zéro avertissement reste échoué : IDs343(pénétrations initiales) et1166(interface). Le moteur Linux avorte à nouveau. Le même état initial et les mêmes cartes Engine, vérifiés par empreintes, terminent normalement en3cycles dans le moteur Windows installé. Terme demandé0,00001ms, un thread, aucun GPU, chaque processus borné180s. Cette sonde initiale n’étend pas les20ms A20.

Deux erreurs de scripts avant solveur sont conservées : insertion du paramètre de trace dans un mauvais segment du lanceur, puis import Python manquant pour l’environnement Windows. Les essais corrigés ont leurs propres dossiers. Aucun résultat natif échoué n’est supprimé.

## 2. Résultats d’un modèle officiel

La documentation décrit les fonctions de LAW117 en fonction de la taille d’élément ; TN/TT deviennent leurs facteurs d’ordonnée. Elle fournit les relations d’initiation TN/EN et TT/ET et de séparation ultime2GIC/TN et2GIIC/TT. Elle ne valide pas ces hypothèses de résistance de l’avion ni l’interopérabilité des versions.

- [Format et paramètres LAW117](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm)
- [Option OpenMPI de trace à l’avortement](https://docs.open-mpi.org/en/v5.0.8/app-debug/debug-options.html)

La source du candidat reste bad6688602d770e019b75773d2d5a48b4f9bd918. Son préparateur LAW117 attend14paramètres réels,6entiers et2tables. READ_MATPARAM alloue les tables seulement si leur nombre est positif ; SIGEPS117 accède aux tableaux de paramètres et aux deux tables. L’identité avec la version Windows n’avait jamais été supposée.

## 3. Affirmations provenant des archives locales

Aucune nouvelle lecture de vidéo, photographie, PDF ou archive. Aucun nouveau fait historique transcrit. Le démarrage d’un calcul ne constitue pas une identification du mécanisme réel et une fraction de critères réussis ne représente pas une probabilité historique.

## 4. Hypothèses propres au modèle

Graine1102067, zéro tirage. Même entrée entière A20 reprise par A37 :48171nœuds,624éléments cohésifs, une LAW117/117, cinq contacts TYPE25, anciens assemblages et conditions inchangés. Unités g,mm,ms ; contraintes MPa et énergies de séparation N/mm. Les budgets de masse, densité, géométrie, inertie, rigidité et vitesse initiale restent inchangés.

Variante déclarée avant exécution : fonctions286 et287 constantes égales1 pour abscisses0 et10^12mm, facteurs TN450MPa et TT100MPa inchangés, Fscale_x1. Courbes de facteur unitaire, et non450/100 multipliés une seconde fois. EN4400, ET800, GIC/GIIC50 restent inchangés. Les pics sont450/100MPa ; séparations initiales450/4400 et100/800mm ; ultimes100/450 et100/100mm. Les relations sont algébriquement identiques pour la forme linéaire par défaut. Aucune validation de rupture physique ne découle de cette équivalence d’entrée.

Le contrôle de différence récupère intégralement toutes les lignes de l’original après retrait des deux cartes et restauration des seuls identifiants de fonctions et noms. Aucun remplacement de LAW117, de TYPE25 ou de reprise binaire. Les traces sont des observations supplémentaires sur un échec, pas un recalcul des témoins réussis A41.

## 5. Résultats dérivés

Le bloc MATPARAM est identifié de façon unique par les six couples loi/identifiant matériau ordonnés et le record par défaut, avec25entiers big-endian par record. Ce parseur est limité à cet en-tête ; il ne prétend pas interpréter toute la reprise. Dans les deux reprises, originale et à courbes constantes, LAW117 contient NUPARAM=0,NIPARAM=0,NFUNC=0,NTABLE=0. La source du moteur attend14,6,2 et ne possède pas de tables allouées pour cette représentation. Le contrôle Windows réussi sur le même état et la trace Linux localisent ensemble une incompatibilité de version/représentation LAW117. La cause ne se corrige pas en ajoutant des fonctions à l’ancien préparateur.

Les cinq fonctions absentes à l’édition de liens du Starter Linux A35 restent à résoudre. Une préparation de même version permettrait ensuite de contrôler les autres incompatibilités entières séparément. Aucun terme énergétique inventé ou ajustement vers une empreinte d’impact connue.

## 6. Contradictions et informations manquantes

Le critère strict de préparation reste échoué avec2avertissements. L’équivalence native de la variante n’est pas qualifiée : Linux ne la calcule pas. Les autres matériaux, ruptures, assemblages et contacts implicites entiers restent à vérifier après une préparation compatible ; les TYPE25 ne sont pas validés par cette localisation. Le contact direct TYPE7 A41 reste qualifié uniquement dans son témoin ; reprise chargée/croissance A40, peaux A34 et raffinement A36 restent échoués.

Pas de nouvelle installation, compilation, modification de source ou de binaire. La compilation A35 reste terminée39,29min. Le meilleur impact entier reste A20≈20ms. Dix secondes physiques3D puis MP4/GIF sont incomplètes. Aucun coût10s extrapolé depuis ce démarrage.

AIRCRAFT-A43 : résoudre la préparation de la même version que le moteur MUMPS. A42 localise l’avortement initial entier dans SIGEPS117 : les reprises Windows contiennent NUPARAM=0,NIPARAM=0,NTABLE=0 pour LAW117; le moteur figé attend14,6,2. Deux courbes constantes unitaires, à résistances450/100MPa inchangées, ne corrigent pas cette représentation. Le même état frais avance3cycles et termine normalement dans le moteur Windows installé. Aucun patch de reprise ou substitution matérielle accepté. Inspecter les cinq symboles manquants du Starter Linux et leurs dépendances/source en cache, préparer une voie complète et bornée avec sources/empreintes avant toute nouvelle modification de logiciel. La compilation A35 terminée39,29min reste conservée. A41 contact direct TYPE7 à pas fixes6,25e-6/3,125e-6ms reste qualifié uniquement dans son témoin. Reprise chargée et croissance de pas A40, peaux A34 et raffinement A36 restent échoués. Les cinq TYPE25 entiers restent à vérifier séparément après préparation compatible. Pas de coût10s déduit du cube ou de la sonde de démarrage. Meilleur impact entier A20≈20ms; objectif dix secondes physiques3D puis MP4/GIF incomplet. Publication A40+A41 vérifiée; A42 en attente de la paire A42+A43 selon cadence autorisée.
