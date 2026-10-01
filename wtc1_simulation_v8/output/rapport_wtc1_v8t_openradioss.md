# WTC 1 — V8T : qualification locale d’OpenRadioss

## Résultat

La chaîne locale OpenRadioss **passe le test d’installation V8T** : le Starter et l’Engine terminent avec le code 0, l’Engine annonce une terminaison normale après 16 796 cycles, et la ligne numérique du cycle 16 750 reproduit exactement la référence officielle au format publié. Le maximum des écarts absolus et relatifs sur les neuf grandeurs comparées vaut respectivement **0** et **0**.

Cette réussite qualifie l’exécution locale et ce test élémentaire de coques. Elle **ne qualifie pas encore** les lois de matériau, contacts, ruptures, érosion, convergence de maillage ou bilan énergétique nécessaires au sous-modèle d’impact WTC 1.

## 1. Faits directement observés

- Paquet source inspecté en lecture seule : C:\OpenRadioss.
- Build Starter/Engine : Windows 64 bits, double précision, daté du 28 juillet 2026.
- Starter : code 0, durée mesurée 0.612 s.
- Engine : code 0, durée mesurée 3.757 s, terminaison normale, 16 796 cycles.
- L’installation source et System32 n’ont pas été modifiés.

## 2. Source officielle du cas d’essai

Le modèle TWISBEAM provient du répertoire officiel qa-tests/miniqa/SMOKE_TEST d’OpenRadioss, commit 18707be39cd8b6385a04d698709c540f288ea95c. Les entrées et la sortie de référence sont conservées avec leurs empreintes SHA-256 dans la configuration V8T. Le fichier source décrit un modèle de poutre de torsion avec éléments de coque Batoz ; il ne représente aucun élément du WTC.

## 3. Hypothèse et adaptation locale

Le démarrage direct sélectionnait une ancienne libiomp5md.dll système (version 20170525), incompatible avec le build 2026. L’adaptation retenue place des liens vers les exécutables officiels et des copies de leurs DLL officielles dans un dossier d’exécution isolé du projet. Cette adaptation change uniquement le chargement des dépendances ; elle ne change ni les exécutables, ni les entrées, ni les archives.

Le Starter signale l’avertissement 100214 sur un champ /IOFLAG du format 2019. Il poursuit sans erreur et produit l’état attendu ; cet avertissement est donc documenté, non effacé.

## 4. Résultat dérivé

| Grandeur au cycle 16 750 | Calcul local | Référence officielle | Écart absolu |
|---|---:|---:|---:|
| Temps | 0.01996 | 0.01996 | 0 |
| Pas de temps | 1.191E-06 | 1.191E-06 | 0 |
| Énergie interne | 0.004376 | 0.004376 | 0 |
| Énergie cinétique de translation | 0.00124 | 0.00124 | 0 |
| Énergie cinétique de rotation | 0.0001197 | 0.0001197 | 0 |
| Travail externe | 0.005737 | 0.005737 | 0 |
| Masse totale | 0.009214 | 0.009214 | 0 |

## 5. Limites et prochaine étape

Le résultat ne dit rien sur la fidélité d’une simulation du vol AA11 ou du WTC 1. La prochaine itération doit qualifier séparément, sur un petit panneau représentatif et traçable : contact à grande vitesse, plasticité dépendante du taux, rupture/érosion, sensibilité au maillage et au pas de temps, bilan d’énergie et répétabilité multithread. Le modèle complet et Blender restent bloqués jusqu’à ces validations.