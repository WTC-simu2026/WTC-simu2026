# Passation compacte — IMPACT-I02B → IMPACT-I02C

12 septembre 2026. Lire AGENTS.md puis `harness/state.json` et cette passation. L'état local fait autorité sur les anciennes mentions V8H/V11H. Vérifier `harness/tools/Test-WtcHarness.ps1` avant toute modification importante. Sources en lecture seule ; anciennes itérations conservées.

## Livré

- I02B : connecteur uniaxial séparable TYPE4 H2, glissement permanent et drapeau de rupture irréversible ; pas encore de plaques déformables ni de mode mixte. 13 cas acceptés, 231 contrôles élémentaires ; campagne PASS (17 marques incluant les 13 agrégations). Rejetés R0 et mouvements imposés R1 conservés. Cas imposés acceptés R2, cas libres R1.
- Base normale : Fp = 11 392 N, d0 = 0,02 mm, df = 0,5 mm, K = 569 600 N/mm, G = 2,848 J. d0, df et loi de décharge sont des hypothèses. G bas/haut = 1,1392/5,696 J. Masse mobile 100 g, pas une masse de rivet. SHEAR est un substitut axial de capacité 6 528 N, pas un test géométrique de cisaillement.
- À 10 m/s et 5 J : G bas/central donnent rupture, G haut arrêt puis retour partiel. Énergies cinétiques finales 3,860818 / 2,152020 / 0,01420363 J. À 5 m/s et G central : pas de rupture. Résidu énergétique max 8,707865e-7 en fraction ; erreur impulsion max 0,00467950. Cycle partiel : glissement conservé 0,1875 mm ; aucune cicatrisation après séparation.
- Rangée uniforme 200 mm, poids h/25,4 avec h=50/25/12,5 mm : énergie conservée à 3,5674e-7 près en fraction. Ce n'est PAS une convergence spatiale de plaques.
- 21,217 s cumulées pour les 13 séquences acceptées, 1 fil ; pas de long calcul. Aucun ancien calcul relancé.

## Entrées ciblées / précautions techniques

Source NIST NCSTAR 1-2B v1, PDF176–177 / imprimées78–79, figure4-21 : environ Fn=4,45 kN et Fs=2,55 kN pour les rivets expérimentaux reproduits. D² vers 1/4 pouce est NOTRE hypothèse ; la trace force-déplacement, l'énergie, le mode mixte post-pic et la dépendance au taux ne sont pas identifiés. SHA de la copie locale : `1504c598adcd9e492bc126530b593b2d467b7c01a7324913b221a5cb9e128ab4`. Ne pas rescanner l'archive.

Unités natives g/mm/ms/N ; énergie Nmm × 0,001 = J. REACX dans T01 converti = impulsion cumulée Nms, ne pas la réintégrer. Les canaux nœuds sont réordonnés par ID. Après suppression de liaison, masse de pièce nulle possible mais masse nodale globale conservée ; ne pas détruire sa quantité de mouvement ou sa dissipation. Décharge H2 plastique avec jeu, PAS cohésive vers l'origine. Compression hors domaine (ouverture acceptée ≥ 0).

## Fichiers à utiliser

- Config : `wtc1_simulation_v8/data/impact_i02b_joint_coupon.json`.
- Résultats : `wtc1_simulation_v8/output/impact_i02b_joint_coupon/` ; lire `campaign_audit.json`, `rapport_impact_i02b.md`, `release_audit.json`, puis seulement les `results.json`/`history_si.json` nécessaires.
- Scripts conservés : `run_impact_i02b.py`, `audit_impact_i02b.py`, `present_impact_i02b.py`, `release_impact_i02b.py` dans `wtc1_simulation_v8/scripts/`. L'audit relit les résultats sans solveur ; éviter de le régénérer après clôture sauf besoin justifié et nouvelle itération.
- Courbes : `wtc1_simulation_v8/output/impact_i02b_joint_coupon/synthese_impact_i02b.png`.
- Vidéo nouvelle mais états ANCIENS I02A : `wtc1_3d_v4/renders/impact_i02b/I02A_etats_verifies.mp4`, 5 s, H264. Rupture désactivée ; ne pas l'étiqueter simulation d'aile rompable I02B.
- ParaView : `wtc1_3d_v4/output/impact_i02b/paraview_i02a/I02A_solver_states_ms.pvd`, 25 états en mm/ms, VTP vérifiés exactement ; pas d'interpolation temporelle. Source NPZ I02A non modifiée.
- FFmpeg sur PATH et ParaView `C:/Program Files/ParaView 6.2.0/bin/pvpython.exe` fonctionnent ; ce dernier annonce 6.2.0-RC1. Python `C:/Python314/python.exe` suffit aux scripts I02B. Aucun nouveau plugin requis pour la prochaine petite éprouvette.

## Prochaine étape réalisable : IMPACT-I02C

1. Créer une petite peau–raidisseur/longeron à deux pièces élastiques et connecteurs séparables, sans encore relancer l'aile entière. Géométrie/matériaux explicitement hypothétiques quand non documentés.
2. Vérifier ouverture normale et vrai cisaillement séparément, repères/rotation, rigidité parasite, traction–relâchement–recharge, travail des frontières, dissipation et masse après séparation. Ne pas étendre automatiquement TYPE4 axial au mode mixte.
3. Tester une libération dynamique à énergie faible/haute et G bas/central/haut ; comparer plaques avec au moins deux résolutions réelles et pondération d'énergie/longueur constante. Exporter les positions réellement calculées vers une courte vue 3D.
4. Seulement après ces contrôles, intégrer un petit tronçon rompable à I02A et comparer au témoin à nœuds fusionnés. Le balayage 5/10 raidisseurs et le raffinement d'aile 50→25 mm restent ouverts, sans prétendre qu'I02B les a fermés.

## Limites à maintenir

I01/I02A non érodants, V11F froid et V11R thermique préservés ; V11S différée à la demande utilisateur. Pas d'intégrité d'aile réelle prouvée par le témoin sans rupture. Pas de qualification physique Boeing, de rupture mixte ni de convergence spatiale du joint. Le B762 graphique garde zéro masse/raideur/résistance mécanique créditée. Une température imposée n'est pas un incendie calculé ; localisation en flexion post-fracture non validée. Ni un échec numérique ni une ressemblance vidéo ne tranchent un mécanisme historique. Actualiser registre/état uniquement après rapport, sorties et audit vérifiés.
