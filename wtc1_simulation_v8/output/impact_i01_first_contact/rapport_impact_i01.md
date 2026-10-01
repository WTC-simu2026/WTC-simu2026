# IMPACT-I01 — premier contact 3D calculé, diagnostic de composant

Date : 10 septembre 2026. Branche prioritaire demandée par Jeremy : impact initial WTC1. La branche thermique reste V11R terminée, V11S différée. Aucun calcul ancien n'a été relancé. Le gel V9M de la qualification physique de rupture n'est pas levé.

## Résultat livré

Sept cas OpenRadioss ont effectivement terminé normalement. Une animation de 6 secondes montre 24 états sauvegardés, de 0 à 1,15078 milliseconde mécanique, du cas M050. La vitesse seule est initialisée ; les déplacements après contact viennent du solveur. Blender ne calcule pas une seconde dynamique et n'impose pas la pénétration. Il affiche des états discrets, sans interpolation temporelle des déformations.

**Il ne s'agit pas encore d'une simulation du Boeing 767 complet ni d'une aile reconstruite.** C'est un caisson creux générique contre un secteur de façade représentatif. Sa rupture est volontairement désactivée : on ne peut donc tirer de sa continuité aucune conclusion sur la survie d'une aile réelle. L'objectif de ce lot est d'obtenir une chaîne calcul-contact-export-3D vérifiable, puis de situer ses limites avant d'ajouter une structure d'aile documentée.

Livrables finaux : `wtc1_3d_v4/renders/impact_i01/final/impact_i01_contact_final.mp4`, GIF homonyme, `impact_i01_apercu_final.png`, et `wtc1_3d_v4/output/IMPACT_I01_CONTACT_DIAGNOSTIC_FINAL.blend`. Les versions sans suffixe final et les premiers rendus sont des essais de cadrage conservés, pas les livrables à utiliser.

## 1. Faits directement lus ou observés

- Les sept historiques et journaux du solveur existent, avec fin normale, sans érosion d'éléments et sans ajout significatif de masse. Les bilans de masse des pièces correspondent au bilan global.
- Les géométries initiales sont séparées : distance entre surfaces physiques 44,03125 mm pour la peau 4 mm, 42,03125 mm pour 8 mm. L'absence de message de pénétration initiale ne remplace pas ce contrôle géométrique.
- Le témoin sans contact conserve son énergie et sa quantité de mouvement ; sa plasticité reste nulle. Ce témoin traverse géométriquement la façade désactivée, ce qui est attendu et ne représente pas un impact.
- Les images de cette livraison sont des états numériques, pas des observations de l'événement historique. Les vidéos Evidence1/2 n'ont pas été réanalysées dans ce lot ; leur audit antérieur est conservé séparément.

## 2. Sources primaires et modèle officiel : ce qui est réutilisable

La vitesse de référence héritée V8S est 443 mph, soit 198,03072 m/s (facteur 0,44704), attribuée à l'estimation vidéo AA11 du NIST. Elle n'est pas extraite des captures Evidence1/2. La carte représentative de façade et ses hypothèses viennent de V8V, avec références de provenance inchangées ; ce n'est pas le relevé exact des tôles du panneau frappé.

Le rapport [NIST NCSTAR 1-2B](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2bv1.pdf), pages imprimées 31–33, explique l'emploi de courbes publiques MIL-HDBK-5F et Aerospace Structural Metals Handbook, notamment pour des alliages 2024/7075, leur conversion en courbes vraies/plastiques et la difficulté des données de vitesse de déformation. Il précise ne pas avoir réalisé d'essais spécifiques sur les matériaux de l'avion pour ces paramètres. Ces données permettent d'avancer, mais ne fournissent pas à elles seules les épaisseurs, assemblages et capacités de chaque pièce d'un appareil donné. Reprendre une hypothèse ou une calibration de ce modèle devra être marqué comme dépendance, pas comme validation indépendante. [Notice officielle du rapport](https://www.nist.gov/publications/analysis-aircraft-impacts-world-trade-center-towers-chapters-1-2-3-4-5-6-7-8).

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d'archive n'est utilisée comme entrée physique. La suggestion de projection holographique n'est ni une donnée de calcul ni une conclusion. Une silhouette masquée par une façade ne mesure pas l'intégrité des structures à l'intérieur ; un échec du présent modèle ne départage pas à lui seul les mécanismes historiques.

## 4. Hypothèses, unités et propriétés

Système solveur : g, mm, ms, MPa. Une unité de force vaut 1 N ; une unité d'impulsion vaut 0,001 N·s ; une unité d'énergie vaut 0,001 J. La vitesse en mm/ms a la même valeur numérique qu'en m/s. Il n'y a ici ni température ni déformation thermique, ni modification de matériau endommagé.

| Composant | Géométrie et propriétés utilisées | Statut |
|---|---|---|
| Façade | Trois colonnes creuses carrées 355,6 mm, centres espacés de 1016 mm ; un niveau de 3657,6 mm ; allège métallique de hauteur 1320,8 mm ; tôles colonnes 7,9375 mm, allège 9,525 mm | Représentation héritée, pas un panneau as-built certifié |
| Acier | rho 7860 kg/m³ ; E 200 GPa ; nu 0,30 ; limite élastique 427,656 MPa ; résistance ultime 601,566 MPa ; déformation nominale à UTS 0,15 ; coefficient de vitesse 0,016, référence 0,001/ms | Carte V8V représentative, même carte pour ces pièces |
| Caisson | 3 × 2 × 0,4 m, six faces fermées, peau uniforme 4 mm ; variante 8 mm | Dimensions entièrement hypothétiques, pas une section Boeing |
| Aluminium | rho 2700 kg/m³ ; E 70 GPa ; nu 0,33 ; limite élastique 300 MPa ; UTS 450 MPa ; déformation nominale à UTS 0,12 ; coefficient de vitesse nul | Hypothèse isotrope générique, pas une carte identifiée 2024/7075 |

Les paramètres UTS alimentent la variante simplifiée de LAW2 ; ils ne constituent pas des critères de rupture. La déformation de rupture est mise à 1e30 pour supprimer l'érosion. Pas de longerons, nervures, flèche d'aile, carburant, moteurs, fuselage ou masse empruntée à l'avion entier. Les masses du caisson proviennent de la surface médiane × épaisseur × densité : 172,8 kg ou 345,6 kg.

Les extrémités des colonnes sont bloquées en translation et rotation. Les assemblages sont des nœuds communs parfaits, sans boulons ni soudures destructibles. Pas de précharge gravitaire, planchers, noyau ou réaction de la tour complète. Contact TYPE7 unilatéral nœuds du caisson/surfaces de façade, frottement nul ; ni auto-contact ni contact arête-arête. Ces exclusions limitent particulièrement les plis tardifs. [Documentation TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm).

Coques QEPH 24, cinq points dans l'épaisseur, aucun mass scaling ; durée demandée 1,2 ms. Maillages nominaux 100/50/25/12,5 mm ; facteur de pas 0,9 et témoin 0,45. Graine 9112001, aucun tirage. La variante 8 mm change simultanément masse et rigidité : ce n'est pas un essai de résistance seule à énergie fixée.

## 5. Résultats dérivés et contrôles

### Comparaison à temps commun 1,15 ms

Les valeurs suivantes sont interpolées linéairement entre enregistrements scalaires voisins, sans création d'états mécaniques pour l'animation.

| Cas | Maillage nominal | Impulsion sur caisson, N·s | Écart maximal du bilan d'énergie ordinaire / énergie initiale |
|---|---:|---:|---:|
| FREE50, contact désactivé | 50 mm | 0 | 0 % |
| M100 | 100 mm | 7084,31 | 2,654 % |
| M050 | 50 mm | 5874,20 | 2,431 % |
| M025 | 25 mm | 4925,54 | 2,304 % |
| M0125, ajout diagnostique | 12,5 mm | 4769,82 | 2,319 % |
| DT045, facteur de pas divisé par deux | 50 mm | 5790,67 | 2,468 % |
| SKIN008 | 50 mm | 10669,50 | 2,148 % |

L'écart relatif est rapporté au second cas : 100→50 mm **20,60 %**, 50→25 mm **19,26 %** (échecs du seuil 10 %) ; 25→12,5 mm **3,26 %** (passe ce critère scalaire seulement). Le raffinement 12,5 mm a été déclaré après l'échec initial, qui reste conservé. Le contrôle de pas donne **1,44 %**, sous 5 %. Les fins d'historiques n'étant pas exactement au même instant, leurs impulsions finales ne doivent pas servir à cette comparaison.

L'écart final entre impulsion de contact et variation de quantité de mouvement du caisson est inférieur à 2 % dans les cas avec contact. Il s'agit du contrôle sur le projectile, pas d'une validation indépendante des réactions aux appuis de la façade ; ces réactions ne sont pas enregistrées séparément dans I01. Les appuis fixes ne font pas de travail, mais échangent de la quantité de mouvement.

Attention au format : les fichiers T01 bruts stockent ici une impulsion cumulée ; sans `/TH/TITLE`, le convertisseur ne la dérive pas en force. L'accord avec Δp confirme cette lecture. Ne pas intégrer à nouveau cette colonne. [Explications des mainteneurs OpenRadioss](https://github.com/orgs/OpenRadioss/discussions/2451), [métadonnées et conversion](https://github.com/orgs/OpenRadioss/discussions/867).

### Bilan énergétique M050

Configuration : Ecin0 = 3 388 276,7479 J. Le format du fichier de calcul arrondit la vitesse à 198,031 m/s : Ecin0 de cette entrée = 3 388 286,3294 J ; CSV = 3 388 286 J. L'écart configuration/CSV de 2,731 ppm fait échouer le contrôle strict initial à 1 ppm, **échec conservé**. Le contrôle additionnel contre la vitesse effectivement écrite passe, sans relever le seuil ni modifier les sorties. Le prochain générateur devra conserver davantage de chiffres.

Au dernier enregistrement M050, 1,199236 ms : énergie cinétique 2 574 324 J, interne 749 007 J, rotation 10 809,98 J, contact élastique 1337,75 J, travail extérieur 0. Le résidu ordinaire (cinétique + interne + rotation − énergie initiale − travail extérieur) vaut −54 145,02 J. La somme des énergies numériques QEPH des pièces vaut 7300,90528 J ; ajouter cette somme et le contact une seule fois laisse **−45 506,36472 J**, soit environ −1,343 %.

Ce résidu n'est pas remplacé par une dissipation inventée. L'énergie numérique QEPH doit être lue dans TH/PART HE, pas uniquement dans le champ global HE ; l'énergie d'amortissement TYPE7 n'est pas fournie via CE_DAMP. Cela constitue une limite de fermeture, pas une preuve que tout le résidu provient de cet amortissement. Le maximum du résidu ordinaire respecte le seuil exploratoire 5 % dans tous les cas ; l'énergie numérique des pièces reste sous 1 %. [Documentation des historiques et bilans](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/time_histories_overview_starter_r.htm).

### Transfert 3D vérifié

Les identifiants de nœuds, éléments et pièces et la connectivité du convertisseur ont été comparés au maillage généré. Coordonnées = positions initiales + déplacements à 0,05 mm près, tolérance de quantification du convertisseur. Blender reproduit les coordonnées converties avec un écart maximal inférieur à 1e-5 m (mesuré environ 7,45e-9 m). Déformations non amplifiées. La couleur rouge signale une plasticité équivalente supérieure à 2 %, **repère arbitraire, pas déformation de rupture** ; elle appartient aux rendus annotés, tandis que le fichier Blender conserve les couleurs neutres et les états géométriques.

La séquence représente M050, dont la convergence 50→25 mm échoue : elle est livrée comme diagnostic visuel explicitement non qualifié. Les deux états extrêmes des autres cas sont aussi exportés. Le maximum de plasticité du caisson au dernier état sauvegardé atteint 1,074 pour M050 et 3,122 pour M0125 ; ces valeurs très grandes ne sont pas interprétables comme réponse physique fiable avec ce matériau non endommageable et sans auto-contact.

## 6. Contradictions, avertissements et suite

Chaque lancement produit trois avertissements 100214 sur un ancien champ Istrain de propriété coque ; la relecture du listing confirme les épaisseurs et les cinq points d'intégration attendus. M0125 ajoute l'avertissement 477 : jeu variable maximal 6,7625 mm supérieur à la moitié de la plus petite arête principale. Le texte prévient notamment d'un raidissement artificiel en auto-contact ; ce pilote n'en utilise pas, mais la sensibilité jeu/maillage doit être examinée avant qualification. La réussite scalaire 25→12,5 mm ne supprime pas cet avertissement. Le message Blender de miniature de cache non écrite ne concerne pas les PNG et le fichier final sauvegardés ; les artefacts livrés sont contrôlés séparément.

**Bilan : livraison reproductible de diagnostic, pas PASS physique global.** Les contrôles échoués restent visibles dans `campaign_audit.json`. Pas de conclusion sur pénétration complète, maintien des ailes, hologramme, incendie ou effondrement. Les réserves antérieures sur localisation post-fracture restent applicables. Le contrôle froid V11F et la branche V11R sont préservés ; le harnais et l'audit de livraison vérifient les fichiers, pas l'événement réel.

Suite IMPACT-I02, par lot utile : corriger la précision d'entrée et les champs obsolètes ; instrumenter aussi les réactions et le jeu de contact, comparer les formulations adaptées aux plis ; construire une section d'aile avec peaux, longerons et nervures à partir de données primaires ciblées, en donnant des plages explicites aux dimensions manquantes. Introduire ensuite une loi de rupture avec bilan et sensibilité de maillage contrôlés, en gardant I01 non érodant comme témoin. Ne pas régler une déformation de rupture pour obtenir l'image souhaitée. La géométrie du Boeing entier ne doit pas masquer une incertitude mécanique de la section frappée.

## Reproductibilité et reprise

Configuration : `wtc1_simulation_v8/data/impact_i01_first_contact.json`. Génération/exécution : `run_impact_i01.py` ; audits d'historiques : `audit_impact_i01.py` ; extraction des états : `export_impact_i01.py` ; rendu et annotation : `wtc1_3d_v4/scripts/build_impact_i01.py`, `present_impact_i01.py`. Chaque cas conserve decks, journaux, exécutions horodatées et empreintes des exécutables, données de maillage et historiques. OpenRadioss local v20260728-win64, Python 3.14.3, Blender 5.2.0 LTS, encodeur FFmpeg installé existant. Le cas le plus fin a pris environ 304,36 s pour le moteur, plus 3,17 s de préparation ; aucun calcul de plusieurs heures.

Réutiliser `campaign_audit.json`, `history_comparisons.json`, `animation_export_audit.json`, `render_audit.json`, `presentation.json` et `release_audit.json`. Ne pas relancer les solveurs pour reprendre la discussion. Lire la passation `harness/handoffs/WTC1_IMPACT_I01_HANDOFF.md` après l'état local.
