# WTC 1 - V8Q : flux de réseau contraint et audit du noyau nul

## Conclusion

V8Q trouve un équilibre algébrique exact à chacun des sept étages, mais **n'identifie pas un chemin mécanique unique**. La matrice possède 103 flux inconnus pour 47 équilibres, un rang de 47 et une nullité structurelle de **56**. Sans lois force-déplacement et capacités, les flux bruts compatibles ont donc des directions non bornées dans le noyau nul.

Le seuil prédictif réservé n'est pas franchi selon les critères préenregistrés. Sur les 42 valeurs cachées, la couverture des intervalles est de **40.5 %**, la MAE au milieu des intervalles de **141.5 kip** et l'erreur maximale de **504.7 kip**. L'équilibre seul ne suffit donc pas à autoriser une étape thermique ou Blender.

## 1. Faits et résultats officiels utilisés

- **Résultat du modèle officiel :** les intervalles axiaux proviennent de la numérisation V8P des Figures 4-60 et 4-61 de NIST NCSTAR 1-6D, pages PDF 283-284.
- **Résultat du modèle officiel :** les sommes de charges du noyau par étage proviennent du Tableau 4-20, page PDF 294.
- **Fait de traitement :** les six colonnes 502, 607, 703, 806, 906 et 1003 ont été réservées avant tout réglage V8Q ; leurs 42 intervalles après impact ne participent ni à la sélection interne ni à la résolution finale.

Ce sont des sorties du même modèle global NIST. V8Q teste leur cohérence interne et leur prédictibilité conditionnelle ; il ne constitue pas une validation indépendante du scénario réel.

## 2. Affirmations des archives locales

Aucune nouvelle affirmation d'archive locale n'est introduite dans V8Q. Aucun PDF source, plan, photo ou vidéo de l'archive n'a été modifié.

## 3. Hypothèses propres au modèle

1. Les différences de charge axiale sont équilibrées par un flux signé sur le graphe orthogonal V8L et par des ports externes situés sur le pourtour reconstruit du noyau.
2. Les 79 arêtes sont topologiques ; elles ne correspondent pas à un inventaire as-built complet des poutres, dalles et assemblages.
3. Les 24 ports représentent globalement le chemin noyau-plancher-périmètre manquant, sans lui attribuer de rigidité ou de résistance publiée.
4. Une jauge quadratique choisit un représentant fini : poids de port 1.0, pénalité des cibles observées 0.1. Ce choix vient uniquement des colonnes de validation interne préenregistrées.
5. Les bandes d'incertitude viennent de 256 tirages dans les intervalles de numérisation. Elles sont conditionnelles à cette jauge et ne sont pas les bornes physiques exhaustives.

## 4. Résultats dérivés : équilibre par étage

| Étage | Changement total officiel (kip) | Somme des ports (kip) | Résiduel nodal max (kip) | Flux d'arête max dans la jauge (kip) |
|---:|---:|---:|---:|---:|
| 93 | -555 | -555.000 | 0.00e+00 | 450.2 |
| 94 | -352 | -352.000 | 0.00e+00 | 498.6 |
| 95 | -53 | -53.000 | 0.00e+00 | 488.1 |
| 96 | +261 | +261.000 | 0.00e+00 | 487.5 |
| 97 | +399 | +399.000 | 0.00e+00 | 403.5 |
| 98 | +400 | +400.000 | 0.00e+00 | 318.9 |
| 99 | +398 | +398.000 | 0.00e+00 | 253.8 |

Le résiduel maximal est **0.000e+00 kip**. La faisabilité algébrique passe, mais cette réussite est attendue puisque les ports de bord rendent la matrice de bilan de rang plein.

## 5. Test réellement réservé

| Colonne | Couverture des 7 intervalles | MAE milieu (kip) | Erreur max (kip) |
|---:|---:|---:|---:|
| 502 | 14.3 % | 345.0 | 504.7 |
| 607 | 0.0 % | 194.1 | 335.7 |
| 703 | 57.1 % | 50.8 | 114.6 |
| 806 | 57.1 % | 86.3 | 194.2 |
| 906 | 14.3 % | 126.6 | 235.6 |
| 1003 | 100.0 % | 46.4 | 108.7 |

- Couverture globale des intervalles : **40.5 %**.
- Distance moyenne hors intervalle : **52.1 kip**.
- Couverture des milieux observés par les bandes P5-P95 : **28.6 %**.
- Largeur médiane de ces bandes : **128.7 kip**.
- Validation interne : couverture **50.0 %**, MAE milieu **172.5 kip**.

## 6. Audit d'identifiabilité

| Quantité | Valeur |
|---|---:|
| Nœuds | 47 |
| Arêtes orthogonales | 79 |
| Ports externes | 24 |
| Flux inconnus | 103 |
| Rang | 47 |
| Nullité structurelle | **56** |
| Nullité cyclique des seules arêtes | 33 |
| Composantes ayant un support dans le noyau nul | 103 |

Pour tout flux particulier `x`, tout vecteur `z` du noyau vérifie aussi `M(x+z)=d`. Si une composante de `z` y est non nulle, sa plage mathématique brute est non bornée sans capacité ou loi constitutive. Les valeurs finies du JSON et du graphique sont uniquement celles de la jauge d'énergie minimale.

## 7. Portes de décision

- Faisabilité algébrique : **PASS**.
- Prédiction des colonnes réservées : **FAIL**.
- Identification des transferts : **FAIL**.
- Calibration mécanique des capacités : **ABSENTE / FAIL**.
- Porte froide globale : **FAIL**.
- Couplage thermique ou Blender : **NON AUTORISÉ**.

## 8. Contradictions, incertitudes et portée

- **Pas de contradiction numérique nouvelle avec les totaux NIST :** un réseau suffisamment libre peut reproduire exactement les bilans publiés.
- **Zone d'incertitude majeure :** cette reproduction n'indique pas quelles dalles, poutres, attaches, façades ou mécanismes tridimensionnels ont réellement porté les transferts.
- **Limite falsifiante :** une topologie avec 56 directions nulles ne peut pas transformer l'accord d'équilibre en preuve d'un chemin physique.
- **Aucune inférence sur des explosifs ou la thermite :** V8Q ne contient aucune prédiction distinctive de ces hypothèses et ne peut donc ni les confirmer ni les exclure.
- **Étape suivante justifiée :** borner les ports et arêtes par des lois force-déplacement traçables, ou reconnaître explicitement que l'information as-built nécessaire manque. Une animation Blender resterait une visualisation tant que cette porte mécanique n'est pas franchie.
