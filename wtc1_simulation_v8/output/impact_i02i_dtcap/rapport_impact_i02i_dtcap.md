# WTC1 — IMPACT-I02I-F : pas plafonné après désactivation

## 1. Faits directement observés ou transcrits

Huit témoins neufs terminent normalement, leurs 24 exécutables étant sauvegardés : 32.190214 s, plafond 600 s/campagne et 90 s/cas. Aucune alerte starter n'est acceptée. Les colonnes TIME STEP enregistrent exactement les plafonds 200, 100 ou 50 ns avant et après la désactivation. Une ligne TH correspond à chaque cycle ; les derniers états restent ceux enregistrés. Aucun point terminal n'est extrapolé, même si certaines dernières lignes précèdent la fin demandée d'un pas. Aucun ajout de masse mesuré.

La [documentation primaire /DTIX](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/dtix_engine_r.htm) donne les pas initial et maximal du run. Une copie datée et son SHA-256 sont dans `wtc1_simulation_v8/output/impact_i02i_dtcap/source_manifest.json` ; ce document sous copyright est exclu de la redistribution. Il n'est pas utilisé pour affirmer le phasage exact de l'algorithme interne.

## 2. Résultats d'un modèle officiel

Aucun résultat NIST ou calcul officiel du WTC1 n'est ajouté. /DTIX est une définition de logiciel, pas une preuve concernant l'événement. Les deux interprétations NASA de E demeurent conservées et non identifiées ; aucun matériau avion n'est choisi à partir de ces tests.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d'archive n'est évaluée. 1453 fichiers antérieurs sont contrôlés par leurs inventaires sauvegardés. D et E sont réutilisés sans ancien solveur relancé ; aucune archive source n'est rescannée ou modifiée. L'administration GitHub reste séparée des sorties scientifiques.

## 4. Hypothèses propres au modèle, propriétés, unités et critères

Deux nœuds coïncidents reliés par un TYPE8, aire initiale 1 mm², masse totale 0,2 g répartie 0,1 g/nœud, inertie de rotation 0,001 g mm² et rotations bloquées. Kn=56000 N/mm et Kt=21500 N/mm ; pic normal hypothétique 495 N, Gf=30 N/mm pour l'aire de référence, δ0=495/56000 mm, δf=60/495≈0,121212 mm. Lois H2 normale et tangentielle inchangées, aucune viscosité, aucune masse ajoutée, aucun état endommagé repris. L'énergie normale intégrée de séparation vaut 30 N mm=0,03 J ; cisaillement à 0,02 mm : U=Kt δ²/2=4,3 N mm=0,0043 J.

Unités : g, mm, ms, N ; N mm=mJ, J=0,001 N mm ; impulsion N ms=g mm/ms. Un pas 0,0002 ms vaut 200 ns, 0,0001 ms vaut 100 ns, 0,00005 ms vaut 50 ns. La même loi H2 définit le déchargement, U=Fn²/(2Kn)+Ft²/(2Kt) hors ligne de transition ; IE−U demeure un travail numérique non récupéré, pas une énergie de fracture mixte mesurée.

Nœud 1 fixé ; déplacement X/Y du nœud 2 imposé par trajectoires quintiques tabulées, 800 subdivisions par segment de 1 ms. Les cas reprennent les trajectoires D : cisaillement fixé avant rupture normale, mouvement proportionnel, cisaillement après rupture normale et retour élastique sans rupture. L'intervalle TH demandé 0,000001 ms est inférieur au pas résolu ; TIME STEP et nombre de cycles confirment l'échantillonnage. Les fichiers ne décalent ni OFF, ni force, ni impulsion, ni vitesse.

Critères pré-déclarés : force/travail/énergie hérités ≤0,5 %, masse relative ≤1e-5, absence de masse ajoutée ≤1e-12 g ; pas sauvegardé ≤plafond×(1+1e-5), différences de temps CSV avec tolérance déclarée 0,000002 ms ; couverture de fin à deux pas sans extrapolation. Somme signée des impulsions d'appuis comparée au momentum global, résidu brut ≤1 % du plus grand des pics d'impulsions d'appuis ; momentum nodal m1v1+m2v2 comparé au global ≤1 % de son pic. Le résidu rapporté au petit momentum net est aussi conservé sans correction de quantification ; il ne remplace pas ces normalisations.

Les contrôles additionnels aux temps communs demandés 1,1/1,25/1,5/1,75/1,9/2 ms sont inscrits dans la configuration avant solveur. La première déclaration et le script associé sont conservés avant cet alignement administratif. Génération par fonction D immuable sur états entièrement neufs, puis nom F et /DTIX ; la sortie et la configuration redirigées dans ce processus ne modifient aucun fichier D. Les fonctions de chargement, les versions et leurs SHA-256 sont sauvegardés.

## 5. Résultats dérivés

217/222 critères de cas et 10/10 comparaisons passent. Cinq critères stricts OFF/FX sur la même ligne demeurent échoués, sans relaxation. La passation d'intégrité est distincte du succès scientifique global.

| Cas | Max pas résolu ns | Lignes/cycles | Résidu énergie % | Erreur travail appuis % | Résidu impulsion X / pic appui % | IE finale J | Critères échoués |
|---|---:|---:|---:|---:|---:|---:|---|
| FIXED_CAP200NS | 200 | 15011 | 7.66172e-05 | 0.015133 | 1.92136e-05 | 0.0343 | strict_same_row_OFF_FX |
| FIXED_CAP100NS | 100 | 30020 | 5.31627e-05 | 0.00760218 | 1.84902e-05 | 0.0343 | strict_same_row_OFF_FX |
| FIXED_CAP050NS | 50 | 60041 | 3.86818e-05 | 0.00385174 | 1.92147e-05 | 0.0343 | strict_same_row_OFF_FX |
| PROP_CAP100NS | 100 | 10021 | 4.28836e-05 | 0.00853673 | 7.1077e-05 | 0.03390071 | strict_same_row_OFF_FX |
| PROP_CAP050NS | 50 | 20041 | 3.67394e-05 | 0.0043161 | 7.74512e-05 | 0.03390057 | strict_same_row_OFF_FX |
| AFTER_CAP100NS | 100 | 20021 | 4.42261e-05 | 0.0107388 | 0.192454 | 0.03 | aucun |
| AFTER_CAP050NS | 50 | 40040 | 3.90262e-05 | 0.00542317 | 0.192454 | 0.03 | aucun |
| RETURN_CAP100NS | 100 | 20021 | 5.06359e-05 | 0.0285669 | 2.85002e-05 | 3.568333e-17 | aucun |

| Cas | OFF ms | Retard lignes | Retard ns | FX sur ligne OFF N | U tangent avant J | ΔIE avant→stabilisé J | ΔKE avant→stabilisé J | ΔWE avant→stabilisé J |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FIXED_CAP200NS | 1.8142 | 1 | 200 | 430 | 0.0043 | 0 | 0 | 0 |
| FIXED_CAP100NS | 1.8142 | 1 | 100 | 430 | 0.0043 | 0 | 0 | 0 |
| FIXED_CAP050NS | 1.8142 | 1 | 50 | 430 | 0.0043 | 0 | 0 | 0 |
| PROP_CAP100NS | 0.8142 | 1 | 100 | 409.5343 | 0.0038998647 | 8.5e-07 | 0 | 8.5e-07 |
| PROP_CAP050NS | 0.8142 | 1 | 50 | 409.5343 | 0.0039001466 | 4.2e-07 | 0 | 4.2e-07 |
| AFTER_CAP100NS | 0.8142 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| AFTER_CAP050NS | 0.8142 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Le témoin de cisaillement après rupture avait dans D un résidu brut X de 14.20517 % du pic d'impulsion d'appui. F : 100 ns=0.1924542 %, 50 ns=0.1924542 %. Les six temps communs sont tous couverts et l'impulsion y coïncide à la précision des sorties ; cela reste un test imposé, pas un corps libre. La borne passe mais le plateau non nul subsiste.

Diagnostic ajouté après pré-déclaration, sans nouveau critère : maximum X à t=1.7875 ms, exactement sur un point de la trajectoire tabulée, résidu -7.217e-06 N ms aux deux pas. Momentum nodal à gauche 0.001687452, à droite 0.001673019, moyenne 0.0016802355 N ms ; momentum global 0.001680236, écart à cette moyenne 5e-10 N ms. Cela suggère un centrage temporel de sortie au changement de pente ; l'algorithme interne exact et une causalité unique ne sont pas établis. Aucune correction ni translation temporelle des données n'est appliquée.

Les cas de cisaillement fixé conservent IE=0,0343 J aux trois pas ; les 0,0043 J tangents récupérables avant désactivation ne deviennent pas une hausse de KE à la précision enregistrée, et leur suppression ne réduit pas IE. Ce modèle stocke ce travail dans IE, sans identifier une dissipation physique. Le cas proportionnel ajoute pendant la ligne de transition ≈0,85 µJ à 100 ns et ≈0,42 µJ à 50 ns, avec travail extérieur correspondant et KE inchangée à la précision enregistrée. Le retour élastique termine près de zéro IE, conformément à la restitution attendue.

Les grandes impulsions opposées limitent aussi la lecture du petit momentum net : cas fixé, résidu X≈2,8–2,9 % du pic net, somme d'ULP float32≈3,26 % de ce pic. Ce diagnostic ne démontre pas que toute l'erreur vient de la quantification ; le phasage peut intervenir. Les valeurs brutes et les normalisations figurent dans chaque audit, et aucune de ces limites ne qualifie une libération libre.

Revue E sauvegardée : ENG domaine max KE/IE=10.9577 %, CTOA domaine écart=19.6798 %, CTOA pénalité moitié écart=10.7074 %. Toutes les couvertures et tous les échecs E demeurent ouverts dans `wtc1_simulation_v8/output/impact_i02i_dtcap/cached_E_sensitivity_review.json`. F ne répare pas une avancée ou un déplacement absent.

## 6. Contradictions, informations manquantes et suite

Le critère strict de force sur la même ligne OFF échoue dans cinq cas, avec retard d'un cycle dont la durée se réduit 200→100→50 ns. Le centrage exact des grandeurs du moteur n'est pas établi par un code primaire vérifié. Une bonne fermeture énergie/impulsion sous déplacement imposé ne valide pas la libération d'un corps libre ni une énergie de fracture mixte physique. Gf réel, convention NASA, sensibilité spatiale E et ses couvertures restent non identifiés.

G : plan `wtc1_simulation_v8/data/impact_i02i_g_plan_from_f.json`. Étudier d'abord 1600/3200 subdivisions de la trajectoire sur témoins neufs, puis un oscillateur élastique libre à référence analytique avec momentum initial inclus, après vérification des mots-clés primaires. Conserver les sorties F ; ne pas relancer huit cas pour les lire. Pré-déclarer les critères avant tout nouveau solveur. Aucun transfert à un impact libre avec fracture avant ces contrôles. Gf15/60 différés.

V11F froid et V11R/V11S différée préservés. Température imposée ≠ incendie calculé ; localisation en flexion après fracture complète non validée ; tests numériques ≠ validation d'un effondrement réel ; Blender reste une visualisation. Aucun Boeing complet, façade ou pénétration historique qualifié. F=1/2 pour GitHub ; publication F+G après une G vérifiée, compte WTC-simu2026, sans post X.
