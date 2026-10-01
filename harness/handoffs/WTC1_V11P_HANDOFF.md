# WTC1 — passation V11P vers V11Q

Lire `AGENTS.md`, `harness/state.json`, puis cette passation. L’état local prévaut sur les anciennes reprises. Exécuter `harness/tools/Test-WtcHarness.ps1` avant/après les modifications importantes. Sources et anciennes itérations restent en lecture seule ; pas de relance des anciens pilotes complets.

## État vérifié

V11P terminée : **107/107 contrôles et 670/670 audits indépendants**, 15 calculs, 5117 états sauvegardés. Sorties : `wtc1_simulation_v8/output/v11p_nodal_heat/`, 24 fichiers identiques à `tmp/v11p_nodal_heat/attempt_001`. Durée du pilote environ 7,53 s ; Python 3.14.3, NumPy 2.4.6, graine 11016 sans tirage. Empreinte numérique `b4f72e77c95d4a99bd0831ef3f2c56bdb6624d7d95e7ccc9dd34ee5e5ed77a64`.

Le démarrage thermique nodal et ses bilans sont qualifiés sur les cas déclarés. **Ce n’est pas une qualification du raccord V11O**, qui reste incompatible avec les flux. Utiliser les nouveaux profils résolus V11P, pas le raccord reconstruit V11O. Les intégrales mécaniques exactes V11O restent réutilisables.

## Formulation et résultat décisif

Coupon 1 m², épaisseur 4,35 in × 0,0254 = 0,11049 m ; rho=2400 kg/m³, cp=900 J/(kg K), k=1 W/(m K), constants, non calibrés WTC. Masse inchangée 265,176 kg/m² ; capacité thermique inchangée 238658,4 J/(m² K).

N intervalles, N+1 températures nodales incluant les surfaces. Largeurs de contrôle dx à l’intérieur et dx/2 aux extrémités, somme L. Euler arrière et Newton avec dérivée exacte du rayonnement. La surface stocke la chaleur de sa demi-maille **déjà incluse dans le solide**, sans ajout de masse fictive.

En haut : `q_ext - k*(T_N-T_(N-1))/dx = rho*cp*(dx/2)*dT_N/dt`. Le gradient terminal fournit le flux à la première face **intérieure** du volume de contrôle ; il n’est pas tenu égal au flux extérieur lorsque ce demi-volume chauffe. Le profil linéaire par morceaux n’est pas prétendu satisfaire point par point la dérivée extérieure.

Cas principal : initial 20 °C partout, y compris aux surfaces, H=0. Gaz et rayonnement haut/bas 250/20 °C ; h haut/bas 25/10 W/(m² K), epsilon 0,7/0,8. À zéro : flux haut 8429,999306 W/m², flux intérieur nul, intégralement affecté à la dérivée initiale de stockage. Pour N256 : vitesse nodale initiale 18,085094 K/s. Elle est finie à maillage fixé mais croît avec N ; ne pas en déduire une dérivée temporelle finie dans la limite continue.

Chaleur `H=rho*cp*sum(width_i*(T_i-20))`, J/m². Chaque pas ferme `DeltaH=dt*sum(q_ext,nouveau)`. Pour les témoins initialement chauds, utiliser H−Hinitial. Résidu local maximal 4,543e-10 W/m² ; bilan cumulé maximal 5,960e-8 J/m².

## Raffinements et comparaisons

Principal 0–90 s : N64/128/256/512 à 640 pas ; N256 à 160/320/640/1280 pas. Tous les pas sont sauvegardés. `N` signifie intervalles, pas cellules centrées. Quatre références stationnaires convection/rayonnement/équilibre passent. Le mode propre Robin lisse montre un ordre spatial proche de 2, isolé par exponentielle de l’opérateur discret ; l’ordre temporel est proche de 1, contrôlé aussi par évolution modale Euler arrière indépendante.

À 90 s, N256/S640 : surface haute **72,192510302 °C**, H **661175,789058 J/m²**. Passer à N512/S640 : surface +0,006290351 K ; chaleur relative −0,00760074 %. Doubler les pas à N256/S1280 : surface +0,005664560 K ; chaleur relative +0,00354181 %. Les sensibilités du carré de température sont également conservées. Ces écarts mesurés ne sont pas des bornes rigoureuses d’erreur continue, surtout près de zéro.

Comparaison aux sorties V11M sauvegardées, mêmes temps 0 / 0,140625 / 45 / 90 s et 64/128/256 intervalles-cellules : à N256 et 90 s, surface V11P−V11M = −0,016768354 K ; H +134,011371 J/m². V11M a une surface algébrique déjà chaude à zéro ; V11P commence réellement froid. Aucun des deux n’est une observation du WTC.

## V11Q — étape suivante limitée

Transférer **directement les profils nodaux sauvegardés** aux intégrales exactes de section V11O, d’abord sur une plage élastique limitée avec garde-fou de résistance. Les profils P1 conservent exactement `m0=mean(DeltaT)`, `m1=mean((x/L-1/2)*DeltaT)`, `m2=mean(DeltaT²)` ; l’audit les vérifie par quadrature de Gauss indépendante. Ne pas remplacer m2 par le carré de la moyenne ni par une projection de fibres sous-résolue.

Vérifier froid, section libre/empêchée, déformations, réactions et travail thermique ; comparer les raffinements sauvegardés et les températures des armatures discrètes. Ne pas supposer qu’un profil à 90 s reste élastique. Arrêter ou borner l’exploitation quand le garde-fou est atteint ; aucune modification des propriétés d’un matériau endommagé.

Préserver V11F et comparer séparément la correction d’inertie continue V11O : par rapport à 160 fibres au milieu des bandes, écart de raideur de flexion d’environ 0,003826 %. Ne pas exiger ni déclarer une identité bit à bit du nouveau contrôle froid avec l’ancien. Ne pas avancer au panneau complet avant ce transfert de section vérifié.

Ne pas fabriquer de fractions de temps avant le premier pas : interpolation temporelle non qualifiée. On peut comparer les temps communs des calculs sauvegardés. Chaleur sensible du coupon et travail thermoélastique de la section restent deux bilans séparés ; l’écart de capacité thermique du composite doit rester explicite.

## Entrées et lecture minimale

Configuration `wtc1_simulation_v8/data/v11p_nodal_heat.json`. Scripts : `v11p_nodal_heat.py`, `run_v11p_nodal_heat.py`, `audit_v11p_nodal_heat.py` sous `wtc1_simulation_v8/scripts/`. Constantes et références héritées de `v11k_surface_exchange_predeclaration.json`.

Lire `results_v11p.json`, `rapport_v11p.md`, `sensitivities.json`, puis les profils nécessaires `N256_S640.json`, etc. Chaque fichier contient `summary`, `case`, `x_m`, `control_width_m`, `profiles` (températures en °C) et `history` (flux, stockage, chaleur, trois intégrales). `convergence.json` contient les références séparées. Sources et sorties sont couvertes par `offline_manifest.json`.

Audit sans écriture : `python wtc1_simulation_v8/scripts/audit_v11p_nodal_heat.py --output wtc1_simulation_v8/output/v11p_nodal_heat --read-only`. Environnement : `OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`.

## Limites permanentes

Exposition synthétique, propriétés constantes, conduction 1D, pas d’humidité/phase. Aucun nouveau panneau mécanique calculé, aucun incendie reconstruit, premier principe thermo-mécanique couplé non fermé. Pas de fissuration chaude ni d’effondrement validés ; localisation en flexion après fracture complète non validée. Contrôle froid V11F conservé par empreintes. Blender inchangé, visualisation seulement ; crédit énergétique global nul.
