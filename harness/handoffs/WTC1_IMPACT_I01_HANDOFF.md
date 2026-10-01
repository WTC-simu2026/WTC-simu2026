# Reprise WTC1 — IMPACT-I01 vers IMPACT-I02

Lire AGENTS.md puis harness/state.json. Priorité explicitement changée par Jeremy le 10 septembre 2026 : premier contact avion/façade, pas poursuite thermique immédiate. V11R demeure terminée, V11S différée (passation WTC1_V11R_HANDOFF.md). Ne pas suivre le vieux marqueur V8H. Ni archives ni anciennes itérations modifiées.

## Livré

IMPACT-I01 : sept cas OpenRadioss réellement terminés. Caisson aluminium générique 3 × 2 × 0,4 m, peau 4/8 mm, 172,8/345,6 kg ; trois colonnes représentatives et une allège ; vitesse de référence 198,03072 m/s, arrondie à 198,031 dans les decks. Durée 1,2 ms. Pas Boeing complet, pas aile as-built, pas carburant, pas rupture, pas auto-contact/arête-arête. Le gel V9M de qualification physique n'est pas levé.

- Résultats et rapport : `wtc1_simulation_v8/output/impact_i01_first_contact/`.
- Configuration : `wtc1_simulation_v8/data/impact_i01_first_contact.json`.
- Scripts : `run_impact_i01.py`, `audit_impact_i01.py`, `export_impact_i01.py`, `release_impact_i01.py` dans scripts de simulation ; `build_impact_i01.py`, `present_impact_i01.py` dans scripts 3D.
- Livrable animé final : `wtc1_3d_v4/renders/impact_i01/final/impact_i01_contact_final.mp4` et GIF ; fichier `wtc1_3d_v4/output/IMPACT_I01_CONTACT_DIAGNOSTIC_FINAL.blend`.
- 24 états calculés M050 de 0 à 1,15078 ms, montrés en 6 s, sans interpolation de déformation ni amplification. Rouge = plasticité >2 %, pas rupture. Couleurs neutres dans le blend. Les rendus sans suffixe final sont des essais de cadrage conservés.

## Résultats et échecs à conserver

À temps commun 1,15 ms : impulsions M100 7084,31 ; M050 5874,20 ; M025 4925,54 ; M0125 4769,82 N·s. Écarts 100→50 : 20,60 % ; 50→25 : 19,26 % (échecs seuil 10 %) ; 25→12,5 : 3,26 % (passe ce seul scalaire). Dernier raffinement ajouté après échec initial. Demi-facteur de pas : écart 1,44 %. Aucun élément érodé ni mass scaling significatif ; contrôle sans contact nul en plasticité.

Défaut strict KE configuration/sortie à 1 ppm : échec de 2,731 ppm expliqué par vitesse arrondie dans le deck ; contrôle contre le deck passe. Ne pas remplacer l'échec par un PASS global. Trois avertissements 100214/champs obsolètes par cas, plus 477/jeu versus taille de maille sur M0125. Plasticité max caisson 1,074 sur M050, 3,122 sur M0125 : états tardifs non qualifiés physiquement. Animation M050 reste diagnostic malgré coordonnées vérifiées.

Bilan ordinaire max <2,655 %, seuil exploratoire 5 %. M050 fin : résidu étendu −45506 J après ajout contact et TH/PART HE QEPH, pas bilan exactement fermé. Ne pas lire seulement HE global. T01 sans TH/TITLE conserve l'impulsion cumulée FNZ, pas une force à intégrer ; voir discussions OpenRadioss 2451/867. Contrôle final impulsion/Δp projectile <2 % ; réactions d'appuis pas encore instrumentées séparément.

## Prochain lot IMPACT-I02

Réutiliser les historiques, pas de relance des sept cas. Corriger précision d'écriture et champs obsolètes dans une nouvelle itération ; instrumenter réactions et contact et examiner le rapport jeu/maillage. Construire dans ce lot une section d'aile peaux/longerons/nervures à partir de données primaires ciblées, avec plages explicites là où les épaisseurs exactes manquent. Contrôler les formulations de contact pour plis avant exploitation tardive, puis rupture avec énergie et sensibilité de maillage, I01 non érodant conservé comme témoin. Ne pas calibrer pour ressembler à Evidence1.

NIST NCSTAR 1-2B pages imprimées31–33 : données publiques MIL-HDBK-5F/Aerospace Structural Metals Handbook, pas d'essais matériaux avion spécifiques NIST ; source disponible en lecture seule `work/official_sources/ncstar1-2bv1.pdf`. Une carte aluminium générique n'est pas celle de l'aile Boeing. Pas de nouvelle analyse Evidence2 : sa question visuelle est hors priorité et l'audit vidéo précédent demeure distinct.

Avant et après modifications importantes : harnais. Actualiser registre et état uniquement après vérification des nouvelles sorties. Préserver V11F froid, V11R et réserves post-fracture. Ne pas conclure qu'une aile reste intacte parce que le caisson non érodant le reste ; un résultat numérique insuffisant ne prouve ni ne réfute une projection holographique.
