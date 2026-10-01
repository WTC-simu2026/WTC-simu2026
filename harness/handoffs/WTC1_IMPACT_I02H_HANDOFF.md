# WTC1 — IMPACT-I02H vers IMPACT-I02I

## État et priorité

I02H terminée comme **campagne numérique bornée, propagation physique non qualifiée**. Prochaine étape : **IMPACT-I02I**, loi matériau et raideur cohésive séparée du raffinement. Le point de reprise V8H et l'ancien V11H sont périmés. Branche thermique différée : V11R terminée, V11S non réalisée ; contrôle froid V11F préservé.

Harnais avant clôture : PASS, 106 entrées. La publication doit ajouter uniquement `WTC1-IMPACT-I02H`, soit 107 entrées. Lire `wtc1_simulation_v8/output/impact_i02h_local_cohesive/publication_verification.json` pour le contrôle après enregistrement ; `release_audit.json` distingue intégrité de publication et validation scientifique. Ne pas confondre clôture et succès de tous les critères.

## Résultats à réutiliser, sans relance

Dossier : `wtc1_simulation_v8/output/impact_i02h_local_cohesive/`.

- 7 cas complets, 49/49 contrôles de cas ; campagne 9/10. Résidus max : énergie 0,04929 %, travail 0,06510 %, masse 0,00002737 %. Deux témoins ajoutés : faible déplacement 0,02 mm et liaison sans propagation, aucun avancement ; 311,36 s supplémentaires.
- Gf=30 N/mm hypothétique, tôle M(T) 76,2 × 300 × 2,3 mm, a0=12,7 mm, EPP ou TAB. Ce n'est ni une aile Boeing ni une façade.
- TAB local h=2,54/1,27/0,635 mm : première séparation 182,454/209,525/215,415 MPa. Grossier/moyen 12,920 % **échec** ; moyen/fin 2,734 % **pass**. Demi-pas moyen : écart 0,000305 % **pass**, limité par des sorties toutes les 0,01 ms.
- Fine : 8 avances, trois états CTOA admissibles dans la zone locale après Δa≥2,3 mm : Δa=2,8575/4,7625/6,6675 mm ; CTOA(B)=5,569/6,778/4,863°, CTOA(2B)=3,590/4,712/4,309°. Domaine accessible, **pas calibré**.
- Propagation non convergée : CTOA(B) moyen/demi-pas diffère de 21 % à même Δa=9,525 mm. Fine KE/IE maximum 6,956 % pendant un saut, malgré <0,00821 % au pic de force. Pas de propagation entièrement quasi statique démontrée.
- Avance finale 12,7 mm hors zone locale : sa limite est Δa=10,16 mm. Les sorties finales ne doivent pas servir de preuve de convergence locale.
- EPP moyen complet 36 ms : une seule avance 0,635 mm. EPP fin non lancé. TAB limité à 12 ms après difficulté de l'essai long ; fenêtre exploratoire a posteriori. À 12 ms déplacement ≈1,55556 mm, pas 6 mm.

## Corrections d'interprétation importantes

1. NASA/CR-2006-214281 table 15 imprime 0,15/0,4 ; son jeu d'entrée imprime 0,015/0,04. Vérification visuelle PDF p.181/196, copie et SHA dans `source_manifest.json`. Des écarts psi existent aussi. La convention nominale/vraie n'est pas établie : la conversion actuelle reste une hypothèse.
2. EPP→TAB change E, ν, limite et écrouissage, donc aussi les ressorts : **pas une sensibilité au seul écrouissage**. Ne jamais remplacer une loi dans un état déjà endommagé.
3. Kn=E/h et Kt=G/h : changer h change la raideur de liaison. Fixer cette raideur pour isoler le maillage dans I02I.
4. Ishell=24 est QEPH, malgré le mauvais ancien libellé « FULLY_INTEGRATED ». Pas de modification rétroactive des anciens jeux.
5. Force utile = somme FY de section cohésive ; somme brute REACY du mors écartée, travail non fermé. À ne pas présenter comme réaction de support exacte pendant l'inertie.

## I02I proposée

1. Vérifier convention source et carte de coque ; traction élémentaire LAW36 neuve, comparaison analytique/table sur états et énergie. Si la convention source reste indéterminée, tester explicitement les deux interprétations au lieu de choisir celle qui ressemble au résultat voulu.
2. Créer une configuration distincte avec Kn/Kt fixes et trois résolutions locales ; sensibilités de pénalité et matériau séparées, témoin sans rupture conservé.
3. Comparer l'historique à déplacement/avance communs, pas seulement le premier seuil ; sorties plus fines autour des sauts, puis sensibilité de vitesse si nécessaire. Préserver les échecs de I02H.
4. Tester Gf15/30/60 sans ajustement aux comparateurs lorsque la carte et la pénalité sont fixées. Contrôler domaine local, coût et énergie avant toute extension.
5. Ne pas construire/transférer l'avion ou la façade complets comme résultat physique tant que matériau et propagation ne sont pas qualifiés. Une animation générique peut seulement être étiquetée diagnostic.

## Fichiers de travail

- Rapport : `wtc1_simulation_v8/output/impact_i02h_local_cohesive/rapport_impact_i02h.md`.
- `summary_i02h.json`, `comparisons.json`, `campaign_audit.json`, `additional_diagnostics.json`, `warning_audit.json`, `synthese_impact_i02h.png`.
- Configuration de base immuable : `wtc1_simulation_v8/data/impact_i02h_local_cohesive.json` ; complément : `impact_i02h_completion_r1.json`.
- Générateur/auditeur de base : `scripts/run_impact_i02h.py`, `scripts/audit_impact_i02h.py` ; nouveaux scripts : `complete_impact_i02h.py`, `summarize_impact_i02h.py`.
- `verification_r1/` : nouveaux réaudits, aucun audit ancien écrasé. `preservation_before_finalization.json` protège 282 fichiers antérieurs ciblés, V11F/V11R/I02G inclus.

Conserver les préflights rejetés et `G30_L127_TAB_DT90_R1` interrompu (28,07 ms, pas de terminaison normale, durée complète non enregistrée). Le générateur/config EPP ancien n'est plus identique au courant ; ses jeux solveur sauvegardés restent la référence. Les quatre TAB retenus correspondent aux empreintes de base actuelles. Les témoins ont chacun une configuration effective.

Limites inchangées : flexion après fracture non validée ; température imposée ≠ incendie calculé ; test numérique ≠ validation historique ; Blender ≠ solveur validé. Lire AGENTS.md et l'état, contrôler le harnais avant/après ; sources et anciens dossiers en lecture seule.
