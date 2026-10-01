# WTC 1 — plan de faisabilité vers le 11 septembre 2026 (V10M)

Date de gel : 2 septembre 2026. Échéance visée : 11 septembre 2026. Fenêtre : 9 jours calendaires.

## Verdict de faisabilité

- **Livrable réaliste d’ici le 11 septembre :** une chaîne intégrée et reproductible de modèles réduits, avec scénarios d’incertitude, contrôles dimensionnels, critères explicites d’initiation/propagation et visualisation 3D pilotée par les sorties calculées.
- **Non réaliste dans cette fenêtre :** reconstruire et valider indépendamment un jumeau numérique haute fidélité des 110 niveaux, un Boeing 767 détaillé, les incendies CFD, la thermo-mécanique non linéaire et la propagation explicite complète. Les fichiers de production NIST décrits dans les rapports n’ont pas été localisés comme entrées réutilisables, et le NIST indique lui-même que son modèle des tours s’arrêtait à l’initiation.
- **Nature du verdict final :** le harnais pourra dire ce que produit chaque jeu de paramètres et où se situe la frontière effondrement/non-effondrement. Il ne transformera pas une plage synthétique en probabilité de l’événement réel.

## Chemin critique daté

| Date cible | Itération / livrable | Critère de sortie |
|---|---|---|
| 2 septembre | V10M — provenance et disponibilité | Sources officielles hachées ; modèle exact disponible ou manquant explicitement qualifié. |
| 3 septembre | V10N — ressources et graphe de couplage | CPU/RAM/GPU/solveurs inventoriés ; interfaces et unités gelées. |
| 4–5 septembre | Impact et dommage initial | Enveloppes d’impact bornées ; conservation masse/énergie/impulsion vérifiée ; aucune rupture non calibrée promue. |
| 5–6 septembre | Incendie et transfert thermique | Histoires thermiques bornées et provenance séparée ; tests de sensibilité au feu et au SFRM. |
| 6–7 septembre | Réponse structurelle et initiation | Modèle réduit global + sous-modèles de connexions ; critères d’instabilité et de non-convergence audités. |
| 7–8 septembre | Propagation / arrêt | Modèle de propagation explicitement distinct ; cas d’arrêt, progressif et global ; bilan d’énergie. |
| 8–9 septembre | Ensemble d’incertitude | Graines, plages et résultats complets ; frontière effondrement/non-effondrement, sans fréquence réelle. |
| 9–10 septembre | 3D liée aux résultats | Géométrie et animation lisent les états validés ; Blender reste une visualisation. |
| 11 septembre | Gel reproductible | Harnais PASS, registre, hashes, rapport final, limites et inconnues. |

## Portes qui interdisent une conclusion forte

1. Les 22 exigences mécaniques de source restent ouvertes : aucun texte de rapport ne remplace les tableaux, connexions, révisions et conditions aux limites exactes.
2. Aucun jeu d’entrée de production SAP2000, TrueGrid/LS-DYNA, ANSYS ou FDS du WTC 1 n’a été localisé dans V10M.
3. Une conclusion « effondrement impossible » exige que **toute** la plage crédible échoue à initier et propager ; un seul scénario stable ne suffit pas.
4. Une conclusion « effondrement démontré » exige des résultats robustes aux incertitudes, aux maillages/réductions et aux lois de rupture ; une animation ressemblante ne suffit pas.

## Politique de calcul long

Avant tout calcul estimé à plusieurs heures, annoncer la durée, les ressources, les fichiers d’entrée, le critère d’arrêt et le livrable attendu. V10M ne lance aucun solveur.
