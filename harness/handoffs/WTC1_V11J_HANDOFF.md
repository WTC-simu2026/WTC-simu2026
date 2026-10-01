# Passation WTC1 — V11J vers V11K

## État vérifié

- V11J est terminée et validée localement.
- Calcul : `PASS`, 31/31 contrôles, 5 cas de référence et 205 états sauvegardés.
- Audit indépendant des fichiers, sans importer le noyau de conduction : `PASS`, 23/23 contrôles.
- Contrôles hérités relus par empreinte : V11H `PASS` (27/27, 11 cas) et V11I `PASS` (32/32, 3 cas). Leurs anciens pilotes n'ont pas été relancés.
- Harnais avant enregistrement : `PASS`, 87 entrées de registre. Exécuter de nouveau `harness/tools/Test-WtcHarness.ps1` après la mise à jour de l'état et du registre.
- Sortie publiée, copiée octet pour octet depuis `tmp/v11j_transient_conduction/attempt_002` : `wtc1_simulation_v8/output/v11j_transient_conduction/` (17 fichiers).
- `attempt_001` est conservée comme tentative rejetée : les 31 contrôles numériques passaient, mais l'audit indépendant a refusé une phrase-limite absente mot pour mot du rapport. La physique n'a pas été changée entre les deux tentatives.

## Ce que V11J établit

V11J qualifie un coupon de conduction transitoire unidimensionnelle à travers une épaisseur équivalente de 4,35 in, soit 0,11049 m, par unité de surface de 1 m². Le maillage de référence comporte 64 volumes finis centrés et 1 600 pas. Euler implicite résout des propriétés constantes avec convention de flux positif vers l'intérieur.

Les propriétés du contrôle de référence sont `rho=2400 kg/m³`, `cp=900 J/(kg·K)` et `k=1,0 W/(m·K)`. `rho` et `cp` sont repris des hypothèses génériques V11H ; `k` est un ancrage numérique. La plage `0,5 / 1,0 / 1,3 W/(m·K)` est une sensibilité explicite, non une calibration de la dalle réelle.

Cas de référence :

- uniforme adiabatique : 60 °C conservés, flux et variation d'enthalpie exactement nuls ;
- profil linéaire stationnaire 20–120 °C : erreur L-inférieure à `2.843e-14 K`, flux de faces égaux et opposés ;
- mode sinus à faces 20 °C, 1 800 s : erreur L-inférieure à `0,011296 K`, erreur de moyenne `0,009801 K` ;
- flux supérieur entrant constant de 1 000 W/m² pendant 1 800 s, face basse adiabatique : apport et variation d'enthalpie `1,800000 MJ/m²`, température moyenne finale `27,542161 °C`, conforme à la référence analytique à `3.553e-14 K` ;
- palier supérieur synthétique à 120 °C pendant 1 800 s, face basse adiabatique : moyenne finale `49,472051 °C`, cellules basse/haute `21,369131/118,3122 °C`, erreur L-inférieure analytique `0,020169 K`, variation d'enthalpie `7,033753 MJ/m²`.

Le résidu incrémental absolu maximal du bilan flux–enthalpie vaut `4.103e-9 J/m²`, le résidu total absolu `2.524e-7 J/m²` et le maximum relatif sur les bilans non nuls `2.057e-13`. La violation maximale du principe du maximum vaut `1.421e-14 K`.

Le contrôle spatial, isolé par la valeur propre exacte de l'opérateur volumes finis sur le mode sinus, donne les ordres `1,994554 / 1,998641 / 1,999660`. Les raffinements temporels Euler implicite donnent `0,992242 / 0,988160 / 0,978365` sur le sinus et `0,992618 / 0,985131 / 0,970631` sur le palier, compatibles avec les ordres attendus 2 en espace et 1 en temps.

Sous le même palier synthétique de 1 800 s, les températures moyennes finales pour `k=0,5 / 1,0 / 1,3 W/(m·K)` valent `40,835222 / 49,472051 / 53,605009 °C`. Cette monotonie est un résultat conditionnel du coupon, pas une probabilité ni un scénario d'incendie.

## Sources primaires bornées

- NIST NCSTAR 1-5G : épaisseur équivalente 4,35 in, environ 16 éléments thermiques dans l'épaisseur et propriétés du béton léger variables avec la température dans le modèle officiel ; V11J ne reproduit pas ce modèle.
- NIST NCSTAR 1-5F, p. 52 : `k=1,0 W/(m·K)` dans la représentation de la dalle utilisée comme condition de bord du calcul de gaz ; le calcul détaillé de pénétration était séparé.
- NIST TN 1681, §4.2.1.1.1 : estimations constantes simples `0,5 W/(m·K)` pour béton léger et `1,3 W/(m·K)` pour béton courant, avec réserves sur densité, granulats, humidité et données d'essai.

Les URL, localisateurs, dates d'accès et limites d'emploi sont conservés dans `source_manifest.json` et `thermal_property_ledger.json`. Aucun PDF distant n'a été téléchargé et aucune archive locale n'a été rescannée.

## Limites obligatoires

- Le palier à 120 °C et le flux de 1 kW/m² sont des conditions synthétiques de vérification. V11J n'est pas un incendie WTC, une température de gaz ou une histoire thermique historique.
- Il n'y a ni convection, ni rayonnement, ni humidité ou chaleur latente, ni tôle de deck, armature, SFRM, résistance de contact ou propriété dépendante de la température.
- Le profil calculé n'est pas appliqué au panneau V11I. Aucune déformation thermique, contrainte, réaction mécanique, fissuration chaude, plasticité, rupture ou propriété d'un matériau endommagé n'est calculée ou modifiée.
- La localisation en flexion après fracture complète reste non validée. Ce coupon ne valide ni l'impact, ni l'incendie, ni l'initiation, l'arrêt ou la propagation d'un effondrement réel.
- L'enthalpie est locale et exprimée en J/m² ; le crédit énergétique global vaut exactement 0 J. Blender reste inchangé et sans crédit mécanique.

## Reprise V11K

1. Lire intégralement `AGENTS.md`, `harness/state.json` puis cette passation, et exécuter le contrôle du harnais.
2. Ne pas relancer V11H, V11I ou V11J ; vérifier leurs manifestes sauvegardés.
3. Pré-déclarer séparément des conditions de surface convectives et radiatives sur le coupon, avec unités, conventions de signe et paramètres synthétiques ou primaires clairement étiquetés.
4. Vérifier d'abord des références analytiques, manufacturées ou des limites exactes, puis le bilan de puissance de surface, la conservation et les raffinements espace–temps. Conserver V11J comme contrôle à propriétés constantes.
5. Ne relier aucune température de gaz, flux net ou courbe à un incendie WTC sans source primaire et sans traiter les incertitudes de SFRM, rayonnement, convection et exposition.
6. Conserver le coupon séparé du panneau tant que les conditions de surface ne sont pas qualifiées. Ne pas activer de fissuration chaude ni modifier une propriété endommagée sans énergie libre dépendant de la température et de l'historique, forces thermodynamiques, dissipation et irréversibilité.

## Livrables principaux

- Configuration : `wtc1_simulation_v8/data/v11j_transient_conduction_predeclaration.json`
- Noyau : `wtc1_simulation_v8/scripts/v11j_transient_conduction_model.py`
- Pilote : `wtc1_simulation_v8/scripts/run_v11j_transient_conduction.py`
- Tests : `wtc1_simulation_v8/scripts/test_v11j_transient_conduction.py`
- Audit : `wtc1_simulation_v8/scripts/audit_v11j_release.py`
- Rapport : `wtc1_simulation_v8/output/v11j_transient_conduction/rapport_v11j_conduction_transitoire.md`
- Résultats : `wtc1_simulation_v8/output/v11j_transient_conduction/results_v11j.json`
- Cas et profils : `conduction_cases.json`, `temperature_profiles.csv`, `boundary_flux_history.csv`.
- Bilans et raffinements : `energy_ledger.csv`, `space_time_convergence.json`, `space_time_convergence.csv`, `conductivity_sensitivity.json`, `conductivity_sensitivity.csv`.
- Contrôles et manifestes : `inherited_controls.json`, `thermal_property_ledger.json`, `numerical_audit.json`, `source_manifest.json`, `offline_manifest.json`, `release_audit.json`.

Empreinte numérique V11J : `e5a62e868a1448268eb389512a5ca90015d662316636c11342924122775513a4`.
