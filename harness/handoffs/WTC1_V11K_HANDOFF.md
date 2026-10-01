# Passation WTC1 — V11K vers V11L

## État vérifié

- Itération achevée : `V11K`.
- Prochaine itération : `V11L`.
- V11K qualifie un coupon homogène 1D à propriétés constantes avec surfaces sans masse, convection et rayonnement couplés à la conduction.
- Exécution validée : `41/41` contrôles, `6` cas, `246` états sauvegardés.
- Audit indépendant des fichiers finaux : `24/24`, sans importer le noyau V11K.
- Contrôle V11J sauvegardé : `PASS`, sans relancer son pilote.
- Contrôle final du harnais après actualisation : `PASS`, `89` entrées, `98` fichiers requis, état `V11K -> V11L`, `8` empreintes de sources vérifiées.

## Reprise minimale

Lire intégralement, dans cet ordre :

1. `AGENTS.md` ;
2. `harness/state.json` ;
3. ce fichier.

Puis exécuter `harness/tools/Test-WtcHarness.ps1`. L'état local prévaut sur tout ancien point de reprise.

## Résultat borné V11K

Convention par mètre carré, positive vers le coupon :

`q_in = q_conv,in + q_rad,in = h (T_gaz - T_surface) + epsilon sigma (T_rad,K^4 - T_surface,K^4)`

La surface sans masse satisfait aussi `q_in = 2 k (T_surface - T_cellule) / dx`. Les puissances radiatives utilisent `T_K=T_C+273.15` et `sigma=5.670374419e-8 W/(m2 K4)`.

Paramètres constants hérités de V11J : `L=0.11049 m`, `A=1 m2`, `k=1.0 W/(m K)`, `rho=2400 kg/m3`, `cp=900 J/(kg K)`. Ils restent des hypothèses de vérification, pas un matériau WTC calibré.

Cas sauvegardés :

- équilibre combiné uniforme à `60 C` : flux et variation d'enthalpie nuls ;
- convection stationnaire `20/120 C` : débit `460.497029794 W/m2`, identique à la résistance fermée ;
- mode propre transitoire de Robin : erreur de champ finale `0.00233678 K`, erreur moyenne `0.00403725 K` ;
- rayonnement stationnaire `20/220 C` : débit `615.756496688 W/m2` ;
- convection-rayonnement stationnaire `20/250 C` : débit `1194.211225433 W/m2` ;
- palier combiné synthétique `20/250 C`, `1800 s` : moyenne finale `56.4607844 C`, surface haute `163.505877 C`, enthalpie reçue `8.70167246 MJ/m2`.

Diagnostics maximaux : équilibre de surface `1.7735e-11 W/m2`, résidu Newton `7.5943e-11 W/m2`, trois itérations Newton, résidu énergétique total `5.3784e-8 J/m2`, résidu relatif des bilans non nuls `8.9649e-13`. Ordres spatiaux `1.97383-1.99371` et temporels `0.97194-0.99193`. L'énergie reçue augmente monotoniquement dans les sensibilités séparées `h_haut=10/25/50 W/(m2 K)` et `epsilon_haut=0/0.5/0.9`.

Empreinte numérique : `5bc22ccf518507450a550200b5ce53ab544d76dfa2e2edfbaa04ad768263fb80`.

## Tentatives conservées

- `tmp/v11k_surface_exchange/attempt_001` : rejetée parce que le critère relatif avait été appliqué à tort à un bilan nul ; les seuils physiques n'étaient pas en cause.
- `tmp/v11k_surface_exchange/attempt_002` : calcul `41/41`, mais audit `23/24` rejeté sur une assertion textuelle trop littérale du rapport.
- `tmp/v11k_surface_exchange/attempt_003` : calcul `41/41` et audit `24/24`, source des fichiers calculés publiés. L'audit final a été régénéré dans le dossier final.

## Fichiers principaux

- Configuration : `wtc1_simulation_v8/data/v11k_surface_exchange_predeclaration.json`
- Noyau : `wtc1_simulation_v8/scripts/v11k_surface_exchange_model.py`
- Pilote : `wtc1_simulation_v8/scripts/run_v11k_surface_exchange.py`
- Tests : `wtc1_simulation_v8/scripts/test_v11k_surface_exchange.py`
- Audit : `wtc1_simulation_v8/scripts/audit_v11k_release.py`
- Résultats : `wtc1_simulation_v8/output/v11k_surface_exchange/results_v11k.json`
- Cas et historiques : `wtc1_simulation_v8/output/v11k_surface_exchange/surface_exchange_cases.json`
- Bilan d'énergie : `wtc1_simulation_v8/output/v11k_surface_exchange/energy_ledger.csv`
- Raffinement : `wtc1_simulation_v8/output/v11k_surface_exchange/space_time_convergence.json`
- Sensibilités : `wtc1_simulation_v8/output/v11k_surface_exchange/surface_exchange_sensitivity.json`
- Rapport : `wtc1_simulation_v8/output/v11k_surface_exchange/rapport_v11k_surface_exchange.md`
- Manifeste : `wtc1_simulation_v8/output/v11k_surface_exchange/offline_manifest.json`
- Audit final : `wtc1_simulation_v8/output/v11k_surface_exchange/release_audit.json`

## Limites à conserver

- Les températures de gaz et radiatives, `h` et `epsilon` sont synthétiques. Une température imposée n'est pas un incendie calculé.
- Aucun champ V11K n'est encore appliqué au panneau V11I.
- Aucun deck, SFRM, humidité, changement de phase, facteur de vue, propriété dépendante de la température ou incertitude matérielle n'est résolu.
- Aucune propriété d'un matériau endommagé n'est modifiée ; aucune fissuration chaude ni énergie de rupture n'est calculée.
- La localisation en flexion après fracture complète reste non validée.
- Les tests numériques qualifient le sous-modèle, pas l'effondrement réel. Impact, initiation, arrêt et propagation globale restent non résolus.
- Blender est inchangé et reste une visualisation sans état mécanique V11K.
- Crédit énergétique global : `0 J`.

## Prochaine étape V11L

Effectuer un premier couplage **unidirectionnel, limité et réversible** d'un profil transitoire V11K sauvegardé vers le panneau thermoélastique non endommagé V11I. Commencer par `DeltaT=0`, puis une température uniforme reconstruite et enfin le profil transitoire dans la dalle. Vérifier explicitement :

- interpolation du maillage thermique vers les fibres de dalle et conservation des moyenne/gradient ;
- dilatation libre et empêchée contre V11H ;
- réactions et équilibre contre V11I ;
- travail thermoélastique, énergie stockée et enthalpie sensible, maintenus dans des registres séparés ;
- pas de validation au-delà du premier garde-fou élastique froid.

Le palier transféré doit rester étiqueté `synthétique_non_WTC`. Ne pas introduire fissuration chaude, dégradation, plasticité thermique ou effacement d'histoire avant une formulation dédiée de l'état interne et de l'énergie.

## Sources méthodologiques primaires ajoutées

- NIST TN 1681, section 7.1.3.1, p. 184 : convection simple et addition convection-rayonnement.
- NISTIR 6902, section 3.6, pp. 43-46 : flux net vers solide et conduction 1D.
- NIST/CODATA 2022 : constante de Stefan-Boltzmann.

Aucune archive locale n'a été rescannée et aucun fichier source distant n'a été téléchargé.
