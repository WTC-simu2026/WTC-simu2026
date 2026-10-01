# Passation — IMPACT-I02D → IMPACT-I02E

13 septembre 2026. Lire AGENTS.md, l'état local, puis cette passation. Les anciens labels V8H/V11H sont périmés. Harnais avant/après ; archives et anciennes itérations en lecture seule.

## Livré

13 cas R5, 226 contrôles de cas et 13 marques de campagne PASS ; 320,970 s cumulées de séquences acceptées. Aucun ancien solveur relancé. Vérifier `wtc1_simulation_v8/output/impact_i02d_lap_joint/release_audit.json`.

- Deux bandes 45 × 25,4 mm, épaisseurs 2/3 mm, recouvrement 10 mm, surfaces moyennes distantes de 2,5 mm ; masse 15,4305 g. E=70 000 MPa, ν=0,33, ρ=0,0027 g/mm³. Coques élastiques, pas de déchirure.
- TYPE43/LAW117, BK=1 et γ=1 ; Imass=1 : masse SURFACIQUE numérique 10⁻¹² g/mm², total 2,54×10⁻¹⁰ g. Le nom `joint.rho_g_mm3` est impropre pour cette quantité, expliqué en config. `True_thickness=0` conserve le bras géométrique courant.
- Une connexion équivalente répartie sur 254 mm² : Fn=11 392 N, Ft=6 528 N, d0=0,02 mm, df=0,5 mm ; Gn=2,848 J, Gt=1,632 J. Ne pas multiplier la capacité par les 12/44 cellules. Pics hérités d'I02B ; énergie, distribution et mélange hypothétiques.
- Conserver maximum de séparation κ ET maximum de dommage d. Cisaillement signé à raideur dégradée, sans guérison. Compression cohésive élastique avant suppression complète ; contact TYPE7 distinct ensuite. Les deux compressions peuvent agir en parallèle avant rupture : non calibré.
- Coupons purs, combiné 45°, changement de mode, inversion, fermeture après rupture. Travaux finaux 2,848 / 1,632 / 2,405029 / 2,575413 J selon chemin. U=½F·δ par tractions ; D=IE−U non décroissante dans la tolérance.
- Fermeture imposée −0,02 mm : contact ≈67 742 N contre 0 sans contact ; énergie maximale 0,675606 J puis rendue. Contrôle de pénalité, pas force réelle de matage ni rebond libre validé.
- Recouvrement : six DOF intérieurs libres ; prises orientées et contrôlées. Déplacement droit 1,2 mm en x et 4 mm en z sur 4 ms, maintien 1 ms. **Pas un impact balistique.**
- Cas fin : pic 6 371,269 N, travail de liaison 1,651691 J ; première/totale suppression échantillonnées à 1,598/1,602 ms. À 4,99805 ms : tôles 0,00904575 J et cinétique 0,03118305 J. Bandes encore vibrantes, pas équilibre final.
- Maillage 5→2,5 mm, 108→396 coques : pic 0,4236 %, travail 0,09318 %, cinétique commune 0,9377 %. Demi-pas : pic 0,002309 %, travail identique, cinétique commune 0,001457 %. Rotation initiale 90° : coordonnées inverses à 10⁻⁶ mm.
- Résidus maximaux : énergie 0,01144 %, travail des prises 0,24665 %, impulsion 0,33943 %. Moments statiques aux prises vérifiés. Moment cinétique dynamique orbital seulement : **spin absent**, bilan complet non qualifié. Deux maillages ≠ convergence asymptotique.

## Pièges conservés

R2, épaisseur imposée 1 mm : moments incorrects malgré forces/énergie plausibles ; cisaillement ≈74,95 % de résidu angulaire. R4, bras constant 2,5 mm : encore incorrect en mode combiné si l'ouverture change. R0–R4 conservées ; deux séries interrompues. Certaines cartes R2 diagnostiques ont été générées pendant les révisions : aucune n'est promue. R5 possède sa configuration complète et l'empreinte du générateur.

BRIC T01 réordonne **OFF, IE, LSX, LSY, LSZ, LSXY, LSYZ, LSXZ**. NODE : D3, V3, VR3, REAC translation3, REAC rotation3 ; trier par identifiant. REAC est une impulsion cumulée N·ms / N·mm·ms, ne pas réintégrer. Global : cinétique translation colonne2, rotation8, contact11, travail9. Anciennes erreurs de lecture et de reconstruction κ conservées ; aucun pic, G ou seuil ajusté.

Avertissement94 autorisé uniquement pour deux ensembles de coques disjoints : gap supérieur à une demi-arête, mise en garde pour auto-contact. Pas de réduction artificielle du gap. Ne pas réinitialiser les propriétés ou l'histoire à la volée.

## Fichiers utiles

Configuration : `wtc1_simulation_v8/data/impact_i02d_lap_joint.json`.
Dossier : `wtc1_simulation_v8/output/impact_i02d_lap_joint/` — rapport, campagne, source_manifest, release et cas R5 avec cartes, raw, history, results, computed_frames.

Scripts run/audit/summarize/present/cross/sources/release_impact_i02d dans `wtc1_simulation_v8/scripts/` ; transfert ParaView dans `wtc1_3d_v4/scripts/paraview_impact_i02d.py`. Générateur : argument explicite `--revision R5` ; les dossiers existants sont protégés. Préférer les caches.

Film : `wtc1_3d_v4/renders/impact_i02d/I02D_recouvrement_calcule.mp4`, 6,2 s, 31 états sans amplification ni interpolation mécanique.
PVD : `wtc1_3d_v4/output/impact_i02d/I02D_lap_ms.pvd`, mm/ms ; Threshold Active≥0,5 masque les éléments supprimés. VTU relus exactement ; 31 animations natives recoupées à des temps légèrement différents du film.

## I02E réalisable

Intégrer **une seule zone peau–raidisseur remplaçable** à un petit tronçon de la topologie I02A. Comparer fusionné / liaison sans rupture / liaison rompable en conservant masses, offsets et aires tributaires. Courte fenêtre d'abord ; ne pas étendre à toute l'aile si énergie supprimée ou domaine des matériaux restent incontrôlés. Vérifier ensuite le premier contact de cette zone avec la façade. Les grandes contraintes du témoin I02A non érodant ne sont pas un état matériau qualifié.

I01/A/B/C et V11F/V11R préservés ; V11S différée. Aucun crédit mécanique B762 ; ni incendie calculé, ni conclusion historique ; localisation en flexion après fracture complète non validée. Ne pas rescanner l'archive. Actualiser état et registre seulement après sorties et audits vérifiés.
