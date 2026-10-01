# V11K — convection et rayonnement de surface sur coupon 1D

## Résultat

V11K passe 41/41 contrôles numériques. Six cas synthétiques couplent une surface sans masse au coupon constant V11J : q entrant = h(Tgaz−Ts) + εσ(Trad,K⁴−Ts,K⁴), puis conduction dans la demi-maille. Les contributions convective et radiative sont conservées séparément en W/m² et J/m².

Cette qualification ne calcule pas un incendie. Les températures ambiantes, coefficients d'échange et émissivités ne sont pas attribués au WTC1. Aucun champ V11K n'est appliqué au panneau mécanique V11I.

## 1. Faits directement observés ou transcrits

NIST TN 1681 donne la relation convective simple Qc=h·As·(Ts−Tf), indique une plage typique d'environ 10 à 30 W/(m²·K) dans un compartiment en feu, et additionne convection et rayonnement comme condition de bord de la conduction. V11K inverse seulement le signe pour déclarer positif ce qui entre dans le coupon.

Le rapport technique FDS NISTIR 6902 formule également le flux net reçu par un solide comme somme des termes convectif et radiatif, couplée à une conduction unidimensionnelle. La table NIST/CODATA 2022 donne σ=5,670374419×10⁻⁸ W/(m²·K⁴), valeur exacte dans le SI de 2019.

## 2. Résultats d'un modèle officiel

Ces documents décrivent des équations et conventions de modèles officiels. V11K ne relance ni FDS ni le modèle thermique NIST du WTC ; aucun champ de gaz, facteur de vue, flux de flamme ou résultat officiel n'est importé.

## 3. Affirmations provenant des archives locales

Aucune archive locale, photographie, vidéo ou nouvelle page de PDF archivée n'est analysée. Les références méthodologiques proviennent directement des publications NIST en ligne consignées dans le manifeste.

## 4. Hypothèses propres au modèle

Le coupon homogène a L=0.11049 m et A=1 m². Les constantes V11J sont inchangées : k=1.0 W/(m·K), ρ=2400 kg/m³ et cp=900 J/(kg·K). Il n'y a ni deck, armature, humidité, chaleur latente, SFRM, contact ni dépendance en température.

Chaque surface a une capacité nulle. Le rayonnement emploie Ts+273,15 et Trad+273,15 en kelvins absolus. Euler implicite et Newton résolvent simultanément la conduction et les deux équilibres de surface. Le bilan stocké est ΔH=∫(qconv,bas+qrad,bas+qconv,haut+qrad,haut)dt, par mètre carré.

Les valeurs h=10 à 50 W/(m²·K), ε=0 à 0,9 et les environnements de 20 à 250 °C sont des essais de vérification et de sensibilité. Ce ne sont ni des mesures, ni des probabilités, ni des scénarios d'incendie WTC.

## 5. Résultats dérivés

| Cas | T moyenne finale (°C) | Ts bas / haut (°C) | qconv haut (W/m²) | qrad haut (W/m²) | ΔH (MJ/m²) | ∫q dt (MJ/m²) | Erreur L∞ (K) |
|---|---:|---:|---:|---:|---:|---:|---:|
| COMBINED_EQUILIBRIUM_CONTROL | 60.000000 | 60.0000 / 60.0000 | 0.0000 | 0.0000 | 0.000000 | 0.000000 | 0 |
| CONVECTION_STEADY_TWO_SIDED | 76.139960 | 50.6998 / 101.5801 | 460.4970 | 0.0000 | 0.000000 | 0.000000 | 0 |
| CONVECTION_EIGENMODE_TRANSIENT | 76.189567 | 60.4362 / 60.4362 | -808.7238 | -0.0000 | -3.251359 | -3.251359 | 0.00233678 |
| RADIATION_STEADY_TWO_SIDED | 149.868454 | 115.8510 / 183.8859 | 0.0000 | 615.7565 | 0.000000 | 0.000000 | 0 |
| COMBINED_STEADY_TWO_SIDED | 158.120503 | 92.1463 / 224.0947 | 647.6324 | 546.5788 | 0.000000 | -0.000000 | 0 |
| COMBINED_STEP_TRANSIENT | 56.460784 | 20.8987 / 163.5059 | 2162.3531 | 1530.1332 | 8.701672 | 8.701672 | — |

Le résidu maximal d'équilibre d'une surface vaut 1.774e-11 W/m² ; le résidu non linéaire global 7.594e-11 W/m². Newton demande au plus 3 itérations par pas. Le résidu énergétique total maximal est 5.378e-08 J/m², soit 8.965e-13 relativement pour les cas à bilan non nul.

Les contrôles d'équilibre et les trois profils stationnaires restent invariants. Pour la convection seule, le débit stationnaire est aussi recalculé par la résistance fermée 1/hbas+L/k+1/hhaut. Le mode propre de Robin fournit la référence transitoire continue.

### Raffinement indépendant

| Diagnostic | Erreurs L∞ successives (K) | Ordres observés |
|---|---|---|
| Opérateur spatial, temps exact | 0.026959 / 0.00686315 / 0.00173102 / 0.000434645 | 1.973827 / 1.987252 / 1.993708 |
| Euler implicite, 256 cellules | 0.0152324 / 0.00765893 / 0.0038684 / 0.00197219 | 0.991933 / 0.985406 / 0.971939 |

### Sensibilités du palier combiné à 1 800 s

| Paramètre | Valeur | h haut (W/m²K) | ε haut | T moyenne (°C) | ΔH (MJ/m²) | Convection cumulée (MJ/m²) | Rayonnement cumulé (MJ/m²) |
|---|---:|---:|---:|---:|---:|---:|---:|
| top_h_w_m2_k | 10.000 | 10.000 | 0.700 | 47.474215 | 6.556952 | 2.658301 | 3.898651 |
| top_h_w_m2_k | 25.000 | 25.000 | 0.700 | 56.457973 | 8.701001 | 5.322457 | 3.378544 |
| top_h_w_m2_k | 50.000 | 50.000 | 0.700 | 64.980096 | 10.734878 | 7.992273 | 2.742604 |
| top_emissivity | 0.000 | 25.000 | 0.000 | 47.613634 | 6.590226 | 6.591092 | -0.000866 |
| top_emissivity | 0.500 | 25.000 | 0.500 | 54.208880 | 8.164237 | 5.650852 | 2.513384 |
| top_emissivity | 0.900 | 25.000 | 0.900 | 58.502586 | 9.188966 | 5.019727 | 4.169238 |

L'énergie reçue augmente monotoniquement avec h haut lorsque ε est fixé, et avec ε haut lorsque h est fixé. Cette réponse est conditionnelle au coupon et aux autres paramètres inchangés.

## 6. Contradictions, limites et informations manquantes

Une température de gaz ou radiative imposée n'est pas un incendie calculé. Il manque un historique primaire de flux net ou de températures environnantes, les facteurs de vue, la composition des gaz, l'état local du SFRM, le deck, l'humidité, les propriétés thermiques variables et leurs incertitudes. La plage de h n'est qu'un encadrement méthodologique général.

Le coupon reste unidimensionnel et sans mécanique. Il ne modifie aucune propriété d'un matériau endommagé, n'accorde aucune énergie à une rupture et ne traite ni fissuration chaude, ni localisation après fracture, ni impact, ni initiation, arrêt ou propagation d'effondrement. Des tests numériques réussis qualifient ce sous-modèle, pas le comportement réel de la tour. Blender reste inchangé et purement visuel.

## Suite bornée

V11L : effectuer un premier couplage unidirectionnel, limité et réversible, d'un profil transitoire V11K sauvegardé vers le panneau thermoélastique non endommagé V11I. Vérifier interpolation, dilatation libre/empêchée, réactions, travail thermique et bilan énergétique contre les contrôles V11H/V11I ; conserver le palier synthétique explicitement non-WTC et ne traiter ni fissuration chaude ni propriété dégradée avant une formulation d'histoire et d'énergie dédiée.

## Sources primaires utilisées

- [NIST_TN_1681](https://nvlpubs.nist.gov/nistpubs/technicalnotes/nist.tn.1681.pdf) — Section 7.1.3.1, report p.184; Primary NIST guidance states the simple convection relation Qc=h*As*(Ts-Tf), notes typical fire-compartment h values of about 10 to 30 W/(m2 K), and treats convection plus radiation as the surface boundary for conduction. V11K reverses the sign to report heat into the coupon.
- [NISTIR_6902_FDS_TECHNICAL_REFERENCE](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir6902.pdf) — Section 3.6, report pp.43-46; Primary NIST FDS technical reference describes net solid-surface heat flux as convective plus radiative contributions and couples it to one-dimensional solid conduction. V11K uses only the stated idealized boundary structure, not an FDS fire field.
- [NIST_CODATA_2022](https://physics.nist.gov/cuu/pdf/all.pdf) — 2022 CODATA recommended values, Stefan-Boltzmann constant; Primary NIST constants table gives sigma=5.670374419...e-8 W m-2 K-4, exact in the 2019 SI.

Exécution : 32.996 s sur CPU ; Python 3.14.3, NumPy 2.4.6, Pillow 12.2.0. Graine 1101111, sans tirage. Empreinte numérique : 5bc22ccf518507450a550200b5ce53ab544d76dfa2e2edfbaa04ad768263fb80. Aucun GPU, solveur externe, Blender ou rescannage d'archive.
