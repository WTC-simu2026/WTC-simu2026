# WTC1 — IMPACT-I02I-I : arrêt, décharge avec historique et retour

## 1. Faits directement observés ou transcrits

Quatre états neufs, 12 exécutables, 3.444373 s cumulées. Terminaison normale, aucune alerte starter, masse 0,2 g constante, aucun ajout de masse, une ligne TH par cycle. Le déplacement mobile Y est libre ; seul vY initial est prescrit, X/Z et rotations bloqués. OFF reste 1, aucun cas ne se sépare. Le gap reste positif après la ligne initiale : aucune compression dans la fenêtre calculée.

Les critères sont pré-déclarés dans impact_i02i_i_predeclaration.json après la référence indépendante et avant tout moteur. Résultat : **170/174 critères de cas, 16/16 comparaisons, 16/16 contrôles de référence**. Les quatre échecs concernent exclusivement retained_nonnegative : IE−U descend sous −1e−10 J dans chaque cas. Ils restent échoués ; le succès intégral des critères déclarés vaut false. Aucun seuil, temps ou signe n'est changé après résultat.

## 2. Résultats d'un modèle officiel

Aucun nouveau résultat NIST ni interprétation historique ajouté. La documentation TYPE8/H2 et TH issue des manifestes H/C est réutilisée comme définition logicielle. REACX/REACY est appelé force dans la documentation mais compatible ici avec une impulsion cumulative N ms, vérifiée par intégration de −Fy dt. Le centrage exact de la version TH installée reste non établi. Aucun décalage des séries n'est effectué.

## 3. Affirmations des archives locales

Aucune nouvelle assertion d'archive ni vidéo inspectée. 1869 fichiers précédents vérifiés depuis les inventaires sauvegardés, sans archive rescannée. H, les anciens résultats E/F/G, V11F froid, V11R et V11S différée sont conservés. Aucun ancien solveur relancé.

## 4. Hypothèses propres au modèle, propriétés, unités et historique

Liaison numérique TYPE8 à deux nœuds : aire 1 mm², masse mobile m_g=0,1 g, masse d'appui 0,1 g, inertie 0,001 g mm²/nœud, rotations bloquées. Kn=56000 N/mm, Kt=21500 N/mm, pic normal 495 N, Gf=30 N/mm hypothétique ; δ0=0,00883928571429 mm, δf=0,121212121212 mm, pente d'adoucissement ks=4404,97917319 N/mm. H2 normal/tangentiel ; aucune viscosité. La loi de désactivation complète est active mais n'est pas atteinte. Aucune modification de propriété endommagée, restart ou remise à zéro d'historique.

Unités d'entrée : g, mm, ms, N ; N=g mm/ms², N ms=g mm/ms. N mm=mJ et J=0,001 N mm. Une vitesse en mm/ms vaut numériquement celle en m/s ; v0=20 et √20≈4,472135955 concernent uniquement ces témoins, pas l'avion. Le nom delta_max désigne le maximum historique du gap, distinct de la masse m_g.

L'enveloppe est F_env=Knδ pour δ≤δ0, puis ks(δf−δ). En décharge : **F=max(0,F_env(delta_max)+Kn(δ−delta_max))**. delta_max ne décroît jamais. Travail de chargement W(delta_max)=∫F_env dδ ; énergie récupérable U=F²/(2Kn). Travail numérique non récupéré D=W(delta_max)−F_env(delta_max)²/(2Kn). Référence IE=D+U, KE=m_g v²/2 ; multiplier ces énergies N mm par 0,001 pour J. D est une partition de la loi numérique, sans identification à une chaleur, fissure réelle ou dissipation physique mesurée.

Référence d'arrêt : E0=20 N mm=0,02 J, P0=2 N ms ; supérieure au pic élastique mais inférieure aux 30 N mm de séparation. ω=√(Kn/m_g), λ=√(ks/m_g). Avant le pic : δ=v0 sin(ωt)/ω. En adoucissement, x=δf−δ=x0 cosh(λτ)−vpic sinh(λτ)/λ. À l'arrêt xturn=√(2(Gf A−E0)/ks), δturn=0.0538302498685 mm, Fturn=296.815739919 N. Décharge élastique depuis cet état : δ=δres+(Fturn/Kn)cos(ω(t−tturn)), avec δres=0.0485299687985 mm ; après annulation de force, δ=δres+vretour(t−tzero), vretour=-3.9663671635 mm/ms.

tturn=0.00568860945488 ms, tzero=0.00778767434034 ms. Fin demandée 0,012 ms, première compression prédite 0.0200230440875 ms : marge positive vérifiée avant moteur. Uturn=0.000786603423783 J ; après décharge IE=D=0.0192133965762 J, KE=Uturn, WE=0. La force nulle à gap positif provient de l'historique de décharge, sans OFF.

Contrôle sous pic : E0=0,001 J < 0,002187723214 J de pic élastique, P0=0,4472135955 N ms. Référence sinusoïdale réversible, δmax=0.00597614304667 mm, tturn=0.00209906488545 ms, D=0. Fin demandée 0,004 ms avant la première compression à 0.00419812977091 ms. Les deux caps sont 25/12,5 ns, contre 50/25 ns pour l'arrêt endommagé.

Référence contrôlée sans moteur : intégration RK4 directe de m_g δ̈=−F avec maximum historique, 4096/8192 pas ; quadrature indépendante du temps jusqu'à l'arrêt, 512/1024/2048/4096 subdivisions ; identité énergétique, équation du mouvement par différences finies, continuités, non-négativité et monotonie de D théorique. Le changement de variable δ=δturn−y² supprime la singularité intégrable du temps à l'arrêt. Tous ces contrôles passent avant déclaration.

Critères : gap/vitesse/force/momentum/impulsions brutes ≤1 % de l'amplitude déclarée ; IE, KE, travail intégré, U, D et bilan ≤0,5 % de E0 ; signe brut IE−U≥−1e−10 J. J_appui=m_g v−P0 ; le résidu audité est J1+J2+P0−P_global. Travail externe nul à l'appui stationnaire ; IE comparée séparément à l'intégrale Fy dδ et à IE(delta,delta_max). Retour repéré par changement de signe de la vitesse, sans ajuster le temps des séries. Comparaisons aux temps communs pré-déclarés couverts, sans extrapolation.

## 5. Résultats dérivés

| Cas | Gap maximal (mm) | Vitesse finale (mm/ms) | IE finale (J) | Résidu impulsion (%) | Bilan énergie (%) | Minimum IE−U (J) |
|---|---:|---:|---:|---:|---:|---:|
| NORMAL_ARREST_RETURN_050NS | 0.05383159 | -3.966255 | 0.01921344 | 0.618325 | 0.003825 | -1.940604e-10 |
| NORMAL_ARREST_RETURN_025NS | 0.05383066 | -3.966486 | 0.01921335 | 0.30908 | 0.000965 | -3.315714e-10 |
| NORMAL_SUBPEAK_RETURN_025NS | 0.005976403 | -4.416921 | 2.181157e-05 | 0.9354604 | 0.00875261 | -3.664722e-10 |
| NORMAL_SUBPEAK_RETURN_012P5NS | 0.005976207 | -4.419988 | 2.18197e-05 | 0.4677168 | 0.00219202 | -4.508014e-10 |

L'arrêt endommagé restitue environ 0,0007866 J et conserve environ 0,0192134 J de travail numérique. Sa force devient nulle après la décharge, OFF=1, puis son retour se poursuit librement dans le domaine positif. Le contrôle sous pic retrouve la référence réversible aux seuils d'amplitude et d'énergie. Réduire le pas réduit les résidus bruts d'impulsion approximativement de moitié ; maximum 0,935461 % dans le contrôle 25 ns. Les comparaisons entre caps passent à 0,5 %. Ces accords bornés ne ferment pas le critère strict de signe.

Diagnostic séparé, sauvegardé dans precision_diagnostic_r1.json : les minima négatifs, de −1,94060e−10 à −4,50801e−10 J, sont tous compatibles avec la borne de représentation issue du format CSV effectivement observé (.6e) et de TFILE/4 IEEE32 configuré. La borne comprend un demi-ULP binaire plus un demi-pas décimal sur IE et force, puis propage exactement l'erreur de force dans F²/(2Kn). Zéro appartient à l'intervalle de toutes les lignes négatives. **C'est une compatibilité conditionnelle avec l'arrondi, pas la preuve de l'algorithme interne ni une réussite du critère.** Les valeurs brutes restent sauvegardées sans clipping. L'étape J établira d'abord l'observabilité de IE−U à partir des sorties binaires existantes.

## 6. Contradictions et informations manquantes

Les quatre échecs de signe I restent ouverts, malgré de faibles amplitudes et une explication par arrondi plausible. Le sous-modèle n'est donc pas qualifié par l'ensemble des critères déclarés. Les cinq échecs mixtes OFF/FX de F, le réservoir tangentiel supprimé avec l'élément, les huit diagnostics historiques G, le centrage TH et les définitions REACX/REACY restent ouverts. Toutes sensibilités d'inertie/angle et couvertures E restent inchangées. Les deux conventions NASA ne sont pas identifiées ; Gf30 reste hypothétique et Gf15/60 différés.

Aucune plaque, onde de connexion réelle, mode mixte libre ou fracture physiquement calibrée n'est ajouté. L'impact complet Boeing/façade, l'incendie et l'effondrement réel restent non qualifiés. La localisation en flexion après fracture complète n'est pas validée ; température imposée ≠ incendie calculé. Blender reste une visualisation tant que sa dynamique n'est pas reliée à des états mécaniques vérifiés.

## Reproduction et reprise

Configuration JSON, graine 1102017 sans tirage, scripts, référence, decks, exécutables hachés, versions, journaux, T01, CSV, comparaison, diagnostic et rapport conservés. Actions : initialize, référence, declare, run, audit, diagnostic, prepare puis register. Les quatre échecs sont un résultat audité, pas un échec d'intégrité du harnais. Le brouillon de référence qui a échoué lors de la sérialisation d'un booléen NumPy est conservé dans development_r0 ; aucun moteur ni fichier de résultats n'avait été produit alors. La correction ne change aucune équation ou seuil.

Vérification sans moteur : complete_impact_i02i_free_return.py verify. Prochaine étape J : lecture indépendante des T01/CSV sauvegardés et diagnostic de précision avant nouveaux états mixtes. Publication autorisée H+I après contrôle d'intégrité, en conservant les échecs. Aucun message X.
