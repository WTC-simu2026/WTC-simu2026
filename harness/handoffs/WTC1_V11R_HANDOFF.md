# WTC1 — panneau intégré V11R ; suite V11S

Lire `AGENTS.md`, l’état local, puis cette passation. L’utilisateur demande d’avancer par **lots intégrés**, sans multiplier les petites étapes nécessitant une nouvelle relance. Réutiliser les résultats sauvegardés ; ne pas revenir aux coupons déjà qualifiés ni relancer les anciens pilotes.

## Jalon atteint

V11R assemble effectivement **dalle + ferme métallique + contacts + attaches + appuis + gravité + profils thermiques nodaux V11P**, avec intégrales exactes de section V11O/Q. Référence : portée 18,1102 m, largeur 2,032 m, 33 nœuds métalliques, 63 barres, 65 nœuds de dalle, 128 sections de Gauss, 261 degrés de liberté, 117 termes mécaniques. Ce panneau équivalent n’est pas la tour complète ni un étage as-built certifié.

16 configurations calculées, **7288 états engagés**, 14 premiers essais refusés non engagés ; 84/84 contrôles de campagne et **22255/22255 vérifications de relecture**, incluant la reconstruction indépendante de 7302 états. Calcul du lot environ 49,78 s CPU/mural avec un thread BLAS. Les 16 chemins ont accepté du chauffage ; aucun blocage de solveur ni de direction d’appui dans ce lot.

**13/16 configurations qualifiées pour le bilan de travail/énergie** sur leur domaine engagé. Les trois exceptions restent explicitement non qualifiées ; le PASS global qualifie l’implémentation et la transparence de ces diagnostics, pas tous les chemins physiques.

Sorties : `wtc1_simulation_v8/output/v11r_integrated_panel/`, 45 fichiers identiques à `tmp/v11r_integrated_panel/attempt_001`. Empreinte du paquet numérique : `214a49057f25d6beb1b4e5f67b74c8482817b71c661dff1644af0204e26b64d9` (inclut les temps de calcul des résumés, ne pas attendre un digest identique lors d’une relance). Python 3.14.3, NumPy 2.4.6, graine 11018 sans tirage. Pas de SciPy requis, aucune installation.

## Sensibilités réunies dans ce lot

- Sept profils V11P : N64/128/256/512 à 640 pas, N256 à 160/320/1280 pas.
- Maillage mécanique : 2/4/8 éléments de dalle par travée de ferme ; topologie métallique et stations de connexion fixes.
- Gravité : 0/0,25/0,5/1 fois la charge héritée de 80 psf, appliquée **une seule fois** à la dalle. La charge nominale a été conservée, pas abaissée après résultat.
- Exposition sur toute la longueur ou seulement le quart central, frontières alignées avec les éléments. Le reste reste froid : sensibilité spatiale déclarée, sans conduction longitudinale ni feu de compartiment.
- Raideur des attaches verticales par connecteur équivalent : 1e7/1e8/1e9 N/m, paramètres exploratoires non mesurés.

## Résultats principaux — temps synthétiques, pas chronologie WTC

| Cas | Dernier état engagé | Premier essai refusé | Résultat |
|---|---:|---:|---|
| Toute longueur, g=0,25, référence | 60,609375 s | 60,75 s | Garde-fou traction béton |
| Toute longueur, g=0,5 | 58,359375 s | 58,5 s | Garde-fou traction béton |
| Toute longueur, g=1 | 53,4375 s | 53,578125 s | Garde-fou traction béton |
| Quart central, g=0,25 | 90 s | aucun dans la fenêtre | Ratio maximal 0,649045 |
| Quart central, g=1 | 90 s | aucun dans la fenêtre | Ratio maximal 0,716683 |

À charge nominale, toute longueur, dernier état : flèche dalle **42,1342 mm**, charge/réaction verticale totale **140959,2005 N**, U=2102,4416 J, travail externe1877,6512 J, travail thermique224,7904 J. Les barres/liaisons ont un ratio maximal0,556489, tandis que la traction du béton gouverne à0,898976. Surface chauffée61,6992 °C ; c’est le scénario de vérification à gaz/rayonnement250 °C de V11P, pas une température d’incendie reconstituée.

À charge nominale et chauffage du quart central, à90 s : flèche42,4224 mm, U=2038,6084 J, ratio maximal0,716683, ratio barres/liaisons0,588483. La différence de chargement thermique spatial modifie fortement le premier garde-fou. Ne pas extrapoler au-delà de90 s ni qualifier la stabilité réelle.

Le contrôle froid V11F COLD_R02 àg=0,25 est préservé et comparé sans relance : écarts relatifs énergie6,052e-7, flèche5,979e-7, réaction3,372e-12. L’écart d’inertie continue est explicite, aucune ancienne matrice/histoire remplacée.

## Bilans et trois réserves numériques

Équilibre indépendant maximal9,703e-11 relatif. L’audit reconstruit forces de section, forces de ressort/barres, équilibre, contraintes à tous les nœuds thermiques et extrémités d’éléments, réactions, garde-fous, travail externe et thermique. Maximum d’écart du bilan de chaleur transférée1,118e-8 J.

La limite d’erreur incrémentale du travail est1e-7, plancher1 J. `TIME_S160` atteint9,174e-7, `TIME_S320`4,185e-7, `TIE_SOFT`3,954e-7 : changements d’ensemble de contacts actifs avec quadrature trapézoïdale. Défauts cumulés respectifs1,578e-6/4,178e-7/3,947e-7 J. Ils sont petits en absolu mais ne satisfont pas le seuil pré-déclaré. **Pas de tolérance relâchée, pas de dissipation fictive, pas de travail défini par différence d’énergie.** S640 et S1280 de référence passent. Résultats des trois variantes utilisables comme diagnostics de sensibilité, pas comme chemins pleinement qualifiés pour un transfert visuel.

Chaleur sensible du coupon et du composite reste séparée du travail mécanique. En référence au dernier état, composite−coupon = -33305,94 J ; à charge nominale toute longueur -29692,35 J. Ce décalage provient de la substitution de béton par les couches d’armatures et de leurs capacités thermiques ; aucun premier principe thermomécanique couplé n’est revendiqué.

## Suite V11S — avancer sur le blocage physique du panneau

Le blocage principal observé est **la limite du domaine élastique en traction du béton**, pas un besoin de nouveaux tests de dilatation. Préparer directement l’extension du panneau à une fissuration contrôlée avec historique et dissipation. Examiner seulement les lois V11E/F nécessaires ; ne pas modifier ni relancer leurs anciennes histoires. Une première extension à propriétés froides constantes pourrait servir de test constitutif exploratoire explicitement limité, mais **pas** être présentée comme une loi de béton à chaud validée. Déclarer E, ft, Gf, longueur caractéristique, déformations thermiques et historiques avant calcul ; conserver les bilans séparés, l’irréversibilité, les refus d’essais et le contrôle élastique V11R. Ne pas simplement retirer le garde-fou0,9 ou changer les propriétés d’un matériau déjà endommagé.

Maintenir la charge nominale et le témoin de chauffage localisé. Déclarer des arrêts sur compression, acier, liaisons, perte de tangente ou fissuration sortant du domaine vérifié. La localisation après fracture complète reste non validée. Si cette extension ne peut pas être qualifiée, produire le diagnostic précis et les données manquantes dans le même lot, sans prétendre à l’effondrement.

Pour les trois défauts de quadrature, privilégier les profils fins déjà sauvegardés et/ou une intégration des changements de contact explicitement justifiée ; aucune interpolation temporelle du champ thermique ni faux bilan couplé. Ne pas bloquer les13 chemins déjà qualifiés pour répéter tous les raffinements.

## Lecture minimale et visualisation

Configuration `wtc1_simulation_v8/data/v11r_integrated_panel.json`. Noyau `v11r_integrated_panel.py`, pilote `run_v11r_integrated_panel.py`, audit `audit_v11r_integrated_panel.py` dans `wtc1_simulation_v8/scripts/`. Le noyau réutilise l’assemblage V11I, remplace uniquement l’intégration de section par les intégrales exactes et met en cache les tangentes par ensemble de contacts actifs. Pas de ressort artificiel ni de stabilisation ajoutés.

Lire `results_v11r.json`, `rapport_v11r.md`, `cold_comparison.json`, `comparisons.json`. Chaque cas possède `CAS.json` (histoire engagée, essai refusé) et `CAS_inventory.json` (coordonnées, matrices d’interpolation, liaisons, capacités, poids). Profil source et pas thermique suffisent pour retrouver toutes les températures dans V11P. Pas de rescannage des archives.

**Figure à montrer : `synthese_v11r_final.png`**, avec les trois bilans non qualifiés en orange et une déformée issue des déplacements vérifiés. `synthese_v11r.png` est un premier rendu conservé mais remplacé visuellement : courbe mal cadrée et réserve énergétique insuffisamment visible. Les scripts et les deux rendus sont conservés. `render_metadata_final.json` trace le cadrage et les empreintes sources. Pas de Blender modifié ou relancé ; la vieille animation V10Z n’intègre toujours pas ce panneau.

Audit sans écriture : `python wtc1_simulation_v8/scripts/audit_v11r_integrated_panel.py --output wtc1_simulation_v8/output/v11r_integrated_panel --read-only`. Environnement `OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`. `release_audit_final.json` contient la relecture après ajout de la figure finale ; `release_audit.json` est la première relecture conservée.

## Limites permanentes

Un panneau équivalent et petits déplacements, pas la tour ; ferme/appuis/attaches froids ; exposition synthétique ; aucun feu calculé, dommage d’impact intégré ou couplage global validé. Localisation en flexion après fracture complète non validée. Blender reste une visualisation, crédit énergétique global nul.
