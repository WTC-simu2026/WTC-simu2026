# Instantané AIRCRAFT-A22+AIRCRAFT-A23 — 10 octobre 2026

A22 exécute21contrôles de six poutres finies aux offsets réels d'une racine. Les21bilans énergétiques passent mais l'inertie physique reste échouée, notamment enY; la contribution native RKE est scalaire. A23 exécute26contrôles d'un solide3D et de sa transmission à une peau métallique et au sandwich A20. Les26bilans passent; le solide isolé conserve le tenseur physique en rotation libre. Les neuf témoins corrigés w1 passent leurs critères individuels, mais la comparaison avec/sans connecteur échoue à l'énergie cinétique globale ajoutée surXYZ. Aucun connecteur n'est inséré dans l'avion entier, aucune compensation de masse ou de RKE n'est utilisée.

Le [rapport A23](wtc1_simulation_v8/output/aircraft_a23/rapport_aircraft_a23.md) distingue l'inertie propre correcte du solide et celle du montage encore biaisée. Il conserve les erreurs du témoin de traction initial, les post-traitements corrigés par lecture en cache, les contrôles d'arrondi des champs natifs et les échecs. Le [rapport A22](wtc1_simulation_v8/output/aircraft_a22/rapport_aircraft_a22.md) prépare dix familles d'écrouissage acier sans les adopter; le début de striction n'est pas un seuil de rupture.

L'objectif vidéo3D des **dix premières secondes physiques** demeure incomplet. Le dernier aperçu entier A20 couvre **20millisecondes physiques**. Aucun ancien état invalide n'est prolongé ni ajusté à un dommage observé. Les géométries, capacités, rupture à grand taux, gravité, intérieur porteur et contacts des fragments restent à qualifier. Publication d'intégrité, sans validation historique de l'impact ou de l'effondrement.


Chaque rapport sépare faits observés, modèles officiels, archives, hypothèses, résultats dérivés et lacunes.


9 archives complémentaires ; 100 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
