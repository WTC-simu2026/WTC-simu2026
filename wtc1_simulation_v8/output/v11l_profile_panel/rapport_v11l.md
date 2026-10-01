# V11L — transfert de profils thermiques vers le panneau élastique

Résultat : PASS, 33/33 contrôles.

## 1. Faits observés dans les fichiers

V11K fournit 41 profils espacés de 45 s sur 1800 s. Les contrôles sauvegardés V11F, V11H, V11I et V11K sont vérifiés par empreintes. Le palier est synthétique_non_WTC.

## 2. Résultats de modèles officiels

Aucun nouveau résultat officiel importé. Les hypothèses héritées restent celles des configurations V11H/V11I/V11K.

## 3. Archives locales

Aucune nouvelle analyse d’archive, de vidéo ou de photographie.

## 4. Hypothèses et unités

Linear interpolation between saved thermal cell centres, one-sided linear extrapolation to the two faces; multiplicative rescaling conserves the original FV mean while preserving zero-temperature-rise zones. Discrete concrete fiber corrections T*(a+b*y/h) conserve that mean and the equivalent linear gradient M1/I; this retains exact affine fields on V11H midpoint quadrature and rejects any below-reference mapped temperature. Reinforcement evaluates the rescaled continuous profile. Save correction and quadrature moment discrepancy. Linear interpolation in saved time only, including the initial zero field. This heating-only adapter is not a general mixed heating/cooling remapper.

Preserve gross-coupon sensible heat by mean. Panel concrete occupies 0.998 of gross area; reinforcement has its own rho*cp and interpolated temperature. Report panel sensible minus gross-coupon sensible as an explicit transfer discrepancy; there is no combined first-law closure or feedback to conduction. Thermoelastic work is -integral sigma*d(eps_th)*dV, external work plus thermal work equals change in stored elastic energy. No damage/dissipation; zero global energy credit.

Le panneau est préchargé à 0,25 gravité. La dalle utilise eps=eps0-y*kappa et eps_th=alpha*DeltaT. E, alpha, rho, cp restent constants : béton alpha=1e-5/K, rho=2400 kg/m³, cp=900 J/kg/K ; armatures alpha=1,2e-5/K, rho=7850 kg/m³, cp=600 J/kg/K. Le treillis et les assemblages restent au contrôle froid.

Les contraintes sont évaluées dans les fibres, aux nœuds du profil reconstruit, aux extrémités des éléments et aux points de Gauss. Les propriétés E, aires, y, alpha, rho et cp effectivement utilisées sont conservées pour chaque calcul dans panel_runs.json.

## 5. Résultats dérivés

| Cas | Coordonnée du profil (s) | DCR | Énergie élastique (J) | Réaction verticale (N) |
|---|---:|---:|---:|---:|
| cold | 1800.000000000 | 0.14712938 | 123.54242536 | 35239.800130 |
| uniform_control | 1800.000000000 | 0.50224742 | 1831.68510042 | 35239.800130 |
| linear_control | 1800.000000000 | 0.58910617 | 131.14925097 | 35239.800130 |
| profile | 64.576253369 | 0.90000000 | 275.42355628 | 35239.800130 |
| uniform | 1800.000000000 | 0.21583832 | 350.62099915 | 35239.800130 |

Profil courbe : arrêt au garde-fou à la coordonnée interpolée 64.576253369 s, dans l’intervalle sauvegardé [45.0, 90.0]. Ce nombre ne constitue pas un temps d’échauffement résolu ni un temps de rupture.

Travail extérieur cumulé 94.287547063 J ; travail thermoélastique 181.136009210 J ; énergie stockée 275.423556279 J. Résidu maximal relatif 4.376e-11. Retour mécanique : écart de déplacement 5.426e-15 m.

Enthalpie brute du coupon étendu au panneau : 17689070.887464 J ; enthalpie composite : 17655062.545166 J ; écart déclaré : -34008.342297 J. Cette différence n’est pas corrigée par une énergie fictive.

| Comparaison | Coordonnée au garde-fou (s) | Écart relatif |
|---|---:|---:|
| half_step | 64.576253369 | 0 |
| mesh | 64.436100572 | 0.00217035 |
| fibers | 64.576366022 | 1.74449e-06 |

## 6. Limites et informations manquantes

An interpolated guard coordinate inside a 45 s saved interval is not a resolved heating or failure time. Halving interpolation steps tests the adapter only, not thermal time accuracy. Reverse traversal is a synthetic mechanical reversibility test, not solved cooling.

La reconstruction des températures de face utilise les cellules et n’impose pas les températures des surfaces sans masse de V11K. Leur différence est sauvegardée. Le transfert conserve la moyenne et le gradient linéaire équivalent ; le moment absolu conserve l’erreur de quadrature de V11H. La différence d’enthalpie due aux armatures empêche de déclarer un bilan thermodynamique couplé fermé.

Correction maximale des fibres : 0.0846635 K. La première tentative utilisait une correction additive créant un sous-dépassement froid de 0,02 K : elle est conservée mais écartée de la publication. La correction multiplicative vérifiée préserve les zones froides. Les numéros de tentatives et les changements d’audit sont consignés dans la passation.

Une température imposée n’est pas un incendie calculé. Le garde-fou DCR=0,9 fondé sur des propriétés froides génériques ne constitue pas une température critique réelle. Pas de dégradation, fissuration chaude, dynamique, flambement géométrique, effondrement calculé ni preuve de survie. La localisation en flexion après fracture complète reste non validée. Blender reste une visualisation inchangée. Crédit énergétique global nul.

## Suite

Résoudre et sauvegarder finement les premières minutes thermiques, notamment entre 45 et 90 s, pour mesurer la sensibilité du premier garde-fou au pas thermique, au maillage en profondeur et à la reconstruction de surface ; conserver le couplage unidirectionnel élastique et expliciter l’écart de capacité thermique du matériau composite.

Calcul CPU : 8.24 s. Graine 11012 sans tirage.
