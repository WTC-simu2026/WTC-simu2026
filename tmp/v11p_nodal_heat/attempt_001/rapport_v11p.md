# V11P — conduction nodale avec stockage aux surfaces

107/107 contrôles ; 15 calculs, 5117 états sauvegardés.

## 1. Faits observés dans les fichiers

V11O signalait un raccord reconstruit incompatible avec les flux. V11P résout de nouveaux profils thermiques et compare uniquement des sorties V11M sauvegardées. V11F et les anciennes itérations sont protégés par empreintes ; aucun ancien pilote complet relancé.

## 2. Modèles officiels

Aucun nouveau résultat officiel importé. Les références de méthode et de constantes restent celles de la configuration V11K ; il ne s’agit pas d’une reproduction de l’incendie du WTC.

## 3. Archives locales

Aucune nouvelle affirmation ni inspection d’archive.

## 4. Hypothèses, unités et équations

Coupon de 1 m², épaisseur 4,35 in × 0,0254 = 0,11049 m ; rho=2400 kg/m³, cp=900 J/(kg K), k=1 W/(m K), propriétés constantes, sans humidité ni changement de phase. Masse 265,176 kg/m² ; capacité thermique 238658,4 J/(m² K). Ces valeurs sont des paramètres de vérification hérités, non une calibration WTC.

N intervalles donnent N+1 nœuds, dont les deux surfaces. Largeurs de contrôle dx à l’intérieur et dx/2 à chaque extrémité : somme L. C_i=rho*cp*largeur_i en J/(m² K). Euler arrière : C_i*(Tnouveau−Tancien)/dt=somme des flux entrants, en W/m². Newton emploie la dérivée exacte du rayonnement.

qconv=h*(Tgaz−Tsurface), qrad=epsilon*sigma*((Trad+273,15)^4−(Tsurface+273,15)^4), sigma=5,670374419e−8 W/(m² K⁴). Exposition synthétique principale : gaz/rayonnement 250 °C en haut, 20 °C en bas ; h=25/10 W/(m² K), epsilon=0,7/0,8 (haut/bas).

The end-segment conductive gradient gives flux at the first INTERIOR control-volume face, not necessarily the exterior surface flux. At the upper half-volume: q_environment - k*(T_last-T_previous)/dx = rho*cp*(dx/2)*dT_last/dt. Their difference is explicitly stored heat, not an unbalanced massless boundary. A piecewise-linear nodal temperature interpolant is not claimed to satisfy the exterior derivative condition pointwise.

Initial temperatures are 20 C everywhere, including the surfaces, with zero sensible heat for the step case. At t=0 a nonzero environmental flux produces the semi-discrete initial temperature rate of the boundary half-volume; no temperature or energy jump is imposed. Positive-time profiles are solved steps, not a rescaled V11M field. Time interpolation between saved steps would still require a separate accuracy qualification.

H=rho*cp*sum(largeur_i*(T_i−20)) en J/m². Chaque incrément égale dt fois les quatre flux extérieurs au nouveau pas. Pour les contrôles initialement chauds, le bilan porte sur H−Hinitial. Les intégrales du profil linéaire par morceaux m0=mean(DeltaT), m1=mean((x/L−1/2)*DeltaT), m2=mean(DeltaT²) sont exactes, sans projection sur des fibres. Le profil représente une approximation discrète ; son gradient terminal n’est pas une condition extérieure exacte.

## 5. Résultats dérivés

| Maillage/pas | Surface à 90 s (°C) | H à 90 s (J/m²) |
|---|---:|---:|
| N64_S640 | 72.065356972 | 662178.159589 |
| N128_S640 | 72.167286251 | 661376.673884 |
| N256_S640 | 72.192510302 | 661175.789058 |
| N512_S640 | 72.198800654 | 661125.538626 |
| N256_S160 | 72.158532101 | 661035.390292 |
| N256_S320 | 72.181182476 | 661128.967835 |
| N256_S1280 | 72.198174863 | 661199.207510 |

Résidu local maximal : 4.543e-10 W/m² ; résidu global cumulé maximal : 5.960e-08 J/m².

Ordres spatiaux sur mode propre Robin lisse : [2.0004482394066145, 2.000115630196828, 2.000029084261751]. Ordres temporels contre exponentielle du même opérateur discret : [0.9980865434621264, 0.9990420359488574, 0.9995207005267652]. Ces tests isolent les deux erreurs ; ce ne sont pas des bornes d’erreur du démarrage non linéaire.

Les quatre références stationnaires sont maintenues. La température initiale des surfaces vaut maintenant 20 °C, sans saut ni chaleur initiale. La vitesse initiale de chauffage est finie pour chaque maillage mais augmente avec son raffinement : elle ne prouve pas une dérivée temporelle finie dans la limite continue. Le stockage du demi-volume ferme explicitement l’écart entre flux extérieur et flux intérieur.

Comparaisons V11M aux instants 0, 0,140625, 45 et 90 s : voir cached_comparisons.json. Raffinements séparés et sensibilité du carré de la température : voir sensitivities.json. Les écarts ne sont pas assimilés à une probabilité ni à une validation physique.

## 6. Limites et informations manquantes

Qualification numérique bornée de conduction 1D à propriétés constantes. Aucun panneau mécanique chargé dans V11P, aucune fissuration chaude ou modification d’historique endommagé. Pas d’incendie calculé, de premier principe thermo-mécanique couplé fermé, de temps d’effondrement ni de preuve de l’événement réel. Localisation en flexion après fracture complète non validée. Blender inchangé, visualisation ; crédit énergétique global nul. Les premières fractions de pas ne sont plus fabriquées par le raccord V11O, et leur interpolation éventuelle reste à qualifier.

## Suite

Transférer directement les profils nodaux V11P aux intégrales exactes de section V11O sur une plage élastique limitée ; vérifier froid, dilatations, réactions et travail thermique avec garde-fou de résistance. Comparer raffinements spatiaux/temporels et carré de température. Ne pas interpoler avant le premier pas sans qualification ; ne pas engager de matériau endommagé ni confondre chaleur sensible et travail thermoélastique.

Durée CPU/murale mesurée du pilote : 7.532 s ; Python 3.14.3, NumPy 2.4.6, graine 11016 sans tirage.
