# Reprise — IMPACT-I02A terminé ; prochaine étape IMPACT-I02B

Lire `AGENTS.md`, puis `harness/state.json`. L'état local prime sur les anciens points de reprise. Branche thermique : V11R terminée, V11S différée ; contrôle froid V11F préservé. Ne pas relancer I01/I02A : utiliser les sorties sauvegardées.

## Ce qui est maintenant disponible

- Configuration : `wtc1_simulation_v8/data/impact_i02a_structured_wing.json`.
- Rapport : `wtc1_simulation_v8/output/impact_i02a_structured_wing/rapport_impact_i02a.md`.
- Trois cas acceptés : `FREE_M050_R1`, `CONTACT_M050_R1`, `CONTACT_DT045_R1` ; tous terminent normalement, zéro avertissement Starter, zéro érosion, zéro mass scaling significatif.
- Audit campagne : PASS, 17 contrôles. Impulsion nominale 4378,6703 N·s au temps commun 1,195058 ms ; demi-pas 4377,5390 N·s, écart 0,02584 %. I01 au même temps : 6016,6042 N·s ; écart -27,2236 % à masse presque identique.
- Blender lié à 25 états exacts : `wtc1_3d_v4/output/impact_i02a/IMPACT_I02A_SOLVER_STATES.blend`. Réouverture : 21 920 sommets × 25, 22 074 faces, erreur de coordonnées 0 m, topologie et pièces identiques, interpolation constante, aucune dynamique Blender.
- Animation : `wtc1_3d_v4/renders/impact_i02a/IMPACT_I02A_solver_states.gif`, 25 états, 960×620, 5 s ; l'intervalle physique est 1,2 ms, sans interpolation géométrique.

## Modèle et limites obligatoires

Section rectangulaire hypothétique 3,0 × 2,0 × 0,4 m : deux peaux de 2,54 mm, deux longerons, quatre nervures, raidisseurs en Z de dimensions typiques NIST. Longerons/nervures à 3,175 mm = hypothèse. Dix raidisseurs **par peau** = interprétation de figure ; faire la sensibilité cinq/par peau. Peaux proxy 2024-T3 clad et internes proxy 7075-T6, lois élasto-plastiques parfaites sans vitesse ni dommage.

Les jonctions sont des nœuds fusionnés indestructibles. Les maxima epsilon-p finaux atteignent 2,2586 dans les peaux et 2,7484 dans les longerons : les formes tardives sortent clairement du domaine constitutif crédible. Ne jamais présenter l'absence d'érosion comme une aile intacte. Pas de géométrie Boeing as-built, rivets qualifiés, carburant, moteur, fuselage, panneau exact WTC1, étage complet ou tour globale. Le B762 graphique I02-GEOM conserve un crédit mécanique nul.

## Prochaine étape bornée IMPACT-I02B

1. Garder I01 et I02A inchangés comme témoins non érodants.
2. Construire un coupon peau-raidisseur/rivet ou une interface tiebreak vérifiable avant la section complète. Expliciter force-déplacement, travail de séparation et bilan énergétique.
3. Dériver des plages basse/base/haute depuis les essais de rivet et équations documentés dans NCSTAR 1-2B ; ne pas transformer l'ajustement NIST en mesure Boeing.
4. Exiger une dissipation objective ou régularisée et une sensibilité spatiale au moins 50→25 mm. Préserver l'historique et l'énergie si un matériau est endommagé.
5. Rejouer ensuite une section rompable avec sensibilités 5/10 raidisseurs par peau et épaisseurs longerons/nervures. Ne pas ajuster les paramètres pour reproduire une vidéo.

Sources déjà ciblées, ne pas rescanner le PDF entier : `work/official_sources/ncstar1-2bv1.pdf`, PDF 172, 174–179 et 214–221 (imprimé 74, 76–81 et 116–123). Valeurs aluminium statiques typiques : USAF/NAVAIR TO 1-1A-1 tableau 4-4. Une température imposée n'est pas un incendie calculé ; la localisation en flexion après fracture complète reste non validée ; aucune conclusion d'effondrement réel ne découle de ces contrôles.

