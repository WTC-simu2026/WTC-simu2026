# WTC 1 — V11B : départ, masse et limite finale du modèle réduit

## Résultat de cette étape

V11B corrige le début du mouvement : départ à déplacement nul et vitesse nulle, résistance active pendant le premier parcours, temps de ce parcours compté. Le demi-étage de masse absent de V10Y est désormais accré­té explicitement. La fin au dernier niveau est appelée **limite inférieure du modèle atteinte avec mouvement résiduel**, et non débris stabilisés ou effondrement complet résolu.

Les 729 scénarios de grille et trois scénarios nommés sont inchangés. Les paramètres, seuils thermiques, températures et dommages de référence ont été comparés au cache V10Y. Aucun ajustement n'a été fait pour obtenir un effondrement, l'empêcher, ou rejoindre la chronologie observée. Les contrôles passent : 75/75.

## 1. Faits directement vérifiés

L'inspection du code V10Y montre que son temps de propagation zéro contient déjà un déplacement f·h et une vitesse sqrt(2gfh), sans résistance pendant ce premier parcours. Après accrétion des niveaux inférieurs, sa masse représente 109,5 étages et non 110. Ces constats sont des faits de logiciel, pas des observations sur la tour.

V10Y et V10Z ont été laissées intactes. Leurs empreintes, les entrées utilisées et le master Blender sont vérifiés avant/après. L'ancien calcul de propagation est reproduit par appel de sa fonction pure, sans relancer son programme de publication ni écraser un résultat.

## 2. Résultats de modèles officiels réutilisés

La carte simplifiée de dommages et les enveloppes de température restent celles reprises des modèles NIST dans V10P/V10Q/V10Y. **V11B ne lance pas encore un avion contre une structure détaillée et ne résout pas encore les incendies.** Le calcul actuel explore la réponse à ces entrées. Le polynôme E(T) de V11A n'est pas utilisé ici ; l'ancienne prolongation exploratoire de la loi Fy(T) de V10Y reste inchangée, y compris ses limites de domaine.

Le seuil de capacité de V10Y est également inchangé. Son franchissement ne devient pas une vitesse imposée. Si la résistance dynamique constante reste supérieure au poids du bloc, les deux sous-modèles ne décrivent pas une transition compatible : cette situation reçoit une catégorie explicite, pas une correction cachée.

## 3. Éléments des archives locales

Aucune nouvelle consultation de l'archive source n'a été nécessaire. Les sections, treillis et appuis de V11A restent disponibles mais ne fournissent pas encore la résistance énergétique de toute la tour. Leur somme de forces ou de travaux de ressorts isolés n'est pas injectée dans cette progression 1D.

## 4. Hypothèses et équations conservées ou corrigées

Le modèle reste une pile uniforme de 110 étages de 3,6576 m ; elle ne devient pas la géométrie hétérogène de 416,9664 m par une correction de comptabilité. Au seuil situé au niveau i, M0=(110−i+α)m avec α=0,5, comme en V10Y. La fraction de parcours f reste indépendante de α : lier les deux aurait changé des masses initiales. Cette séparation est une convention de masses concentrées, pas une reconstruction de densité spatiale.

Premier intervalle : d=f·h, résistance F=R_i/h, travail Fd=fR_i. Après ce parcours, capture de (1−α)m, puis capture de m à chaque parcours complet i−1…1. Les R_i, leur gradient vers le bas et leur réduction au temps du seuil ne changent pas.

Pendant un intervalle : a=g−F/M ; v_−²=v0²+2ad ; Δt=2d/(v0+v_−). Si l'énergie s'épuise avant ou exactement à la fin, arrêt avec x=K0/(F−Mg), Δt=−v0/a, sans capture ni perte de choc fictive. À l'arrêt initial, F est une capacité disponible : si F≥Mg, la réaction mobilisée est Mg, l'accélération réalisée est zéro, et il n'y a pas de départ.

À la capture d'une masse immobile μ : v_+=Mv_−/(M+μ), perte=½Mμ/(M+μ)·v_−². L'impulsion et l'énergie sont vérifiées séparément. Le bilan global part de K0=0 : Kfinal=Wg−WR−Σ pertes. Le travail gravitaire initial figure une seule fois.

La masse « du bloc » désigne la masse affectée ou capturée, même à vitesse nulle. La masse non accré­tée reste inscrite. La variante finale a masse du bloc + masse non accré­tée = 110m à chaque événement. Deux variantes de diagnostic gardent délibérément la demi-masse omise dans un compte séparé, uniquement pour isoler les corrections.

Après un arrêt, les températures restent figées au seuil : ni chauffage ultérieur ni redémarrage ne sont résolus. À la dernière frontière, la vitesse et l'énergie demeurent explicitement présentes ; il n'y a ni modèle de fondation ni loi de dépôt des débris.

## 5. Résultats dérivés

### Effet séparé des corrections — 729 cas de grille

La colonne « temps seul » garde exactement les issues V10Y ; elle ajoute seulement le temps de la chute libre supposée. Les colonnes suivantes ajoutent la résistance initiale, puis la masse manquante.

| Issue dans le modèle | Temps seul | + résistance initiale | + masse complète V11B |
|---|---:|---:|---:|
| Pas de seuil franchi | 297 | 297 | 297 |
| Seuil franchi, sans départ | 0 | 90 | 90 |
| Mouvement puis arrêt | 144 | 73 | 54 |
| Limite basse atteinte | 288 | 269 | 288 |

Les nombres décrivent cette grille déterministe, jamais des probabilités de l'événement historique. « Seuil franchi, sans départ » n'est pas un verdict de stabilité réelle : la résistance constante et le critère de capacité sont deux hypothèses encore insuffisamment couplées.

L'ajout de la résistance initiale fait passer 19 anciens cas progressants à l'arrêt ; l'accrétion de la demi-masse manquante leur permet ensuite de progresser à nouveau dans ce modèle. Le total final de 288 arrivées à la frontière basse est donc identique au total ancien, sans que les deux corrections soient individuellement neutres. Les 90 cas sans départ faisaient auparavant partie des cas arrêtés après une vitesse initiale supposée.

### Cas nommés et ancien cas animé

| Scénario | Seuil après impact (s) | Issue V11B | Durée depuis le repos (s) | Énergie finale (GJ) |
|---|---:|---|---:|---:|
| RESISTANT_ENVELOPE | — | Pas de seuil franchi | — | 0.000 |
| CENTRAL_EXPLORATORY | 1730.000 | Limite basse atteinte | 19.501 | 266.894 |
| VULNERABLE_ENVELOPE | 320.000 | Limite basse atteinte | 14.467 | 386.659 |
| GRID-0119 | 5810.000 | Limite basse atteinte | 15.048 | 329.835 |

GRID-0119 est conservé parce qu'il pilotait déjà le film V10Z, pas parce qu'il serait le meilleur cas après correction. Son seuil reste à 5810 s. Sa durée passe de 14.126 s (temps initial absent) à 15.048 s depuis le repos. Masse finale : 350.400 → 352.000 millions de kg. L'énergie finale de 329.835 GJ et la vitesse de 43.290 m/s ne sont pas annulées artificiellement.

### Vérifications

75 tests, dont : intervalle accéléré et capture à solution analytique, arrêt à l'intérieur et exactement en frontière, résistance passive au repos, chute libre, vitesse constante, pile indépendante de deux étages, bornes 1/110, conservation de la demi-masse quel que soit f, paramètres inchangés et répétition exacte.

- Résidu relatif maximal d'énergie : 7.209e-16.
- Résidu relatif maximal d'impulsion : 1.517e-16.
- Résidu relatif maximal d'inventaire de masse : 0.000e+00.
- Erreur max du diagnostic « temps ajouté = temps de chute libre » : 6.456e-14 s.
- 29 évaluations thermiques distinctes mises en cache pour les 732 scénarios ; répétition numérique exacte. Exécution CPU : 2.89 s, Python 3.14.3. Aucun GPU, Blender ou logiciel installé.

Une relecture indépendante a confirmé les équations et ajouté une distinction entre capacité de résistance et résistance réellement mobilisée au repos, ainsi qu'un contrôle analytique à deux étages. Les tests qualifient ces équations et leur exécution, pas le bâtiment réel.

## 6. Limites, avion, incendies et réutilisation pour WTC2

L'objectif demandé reste : tour initialement en équilibre → impact d'un 767 → dommages calculés → incendie et transfert thermique → réponse structurelle, avec arrêt ou progression possibles. « Au point documenté » doit conserver les tolérances de position, d'angle, de vitesse et de masse ; ce ne sont pas des valeurs historiquement connues sans erreur. La dégradation de l'isolation, les ouvertures, le combustible et la ventilation relient impact et incendie : le feu n'est donc pas un effet visuel ajouté à la fin.

Le moteur de calcul pourra être commun aux deux tours. Les configurations devront rester distinctes : noyau orienté E–O pour WTC1, N–S pour WTC2, variations de dimensionnement/modifications, sections et événement d'impact propres à chaque tour. Voir [NIST NCSTAR1-1 p.8](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-1.pdf) et [NCSTAR1-2A tableau2-1 p.13](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2a.pdf). Ce n'est pas une nouvelle configuration WTC2 validée, ni une promesse de durée.

L'estimation vidéo des conditions d'impact doit rester distincte des valeurs choisies dans un cas de calcul : par exemple, 542±24 mph estimés pour UA175 versus 546 mph dans le cas de base du modèle officiel. Voir [présentation NIST sur les impacts](https://www.nist.gov/system/files/documents/2017/05/09/WTC_Symp_ARA_2.pdf) et [NCSTAR1-2B vol.2 tableau9-2 p.198](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2bv2.pdf).

Prochaine V11C : établir un panneau de plancher avec dalle, appuis déformables, liaisons et ruptures explicites à partir de V11A ; le vérifier au froid puis sous température/effets imposés, avant couplage à la structure spatiale. Garder séparés le modèle réduit, le solveur de structure et la visualisation. Aucune issue historique n'est imposée, et V10Z n'est pas remplacée par une animation dont le couplage serait présenté comme déjà complet.

## Fichiers

`comparison_cases.csv` : les 732 comparaisons ; `variant_summaries.csv` : les trois variantes ; `outcome_transitions.csv` : migrations entre issues ; `detailed_energy_mass_momentum_ledger.csv` et `detailed_motion_timeline.csv` : les trois cas nommés et GRID-0119 ; `corrected_driver.json` : interface de visualisation étiquetée, non appliquée à Blender ; `source_manifest.json`, `numerical_audit.json`, `offline_manifest.json` : entrées, contrôles et empreintes.
