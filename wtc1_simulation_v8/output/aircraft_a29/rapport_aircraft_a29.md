# AIRCRAFT-A29 — branche volumique orthotrope explicite

**17 nouveaux calculs natifs complets**, deux tentatives Starter seulement et conservation des échecs. La branche LAW12 comporte15contrôles: réussis. Le montage peau/cœur, les attaches réelles et l'impact entier restent à qualifier. Aucun nouveau calcul entier ou vidéo10secondes.

## 1. Faits directement observés ou transcrits

Graine1102054, aucun tirage. Plaque10×10×0,5mm, volume50mm³, masse0,0915g; TYPE6 Isolid18, maillages6/12dans le plan et4éléments géométriques dans l'épaisseur. rho0,00183g/mm³, E11=E22=22000MPa, E33=10000MPa, G12=G23=G31=4000MPa, nu12=0,25. Aucune densité, masse ou inertie n'est compensée. Les RKE natives restent dans le bilan et sont nulles dans ces témoins.

w0 s'arrête au Starter: Ismstr4 est déconseillé avec Isolid18; aucun Engine. w1 demande0automatique et obtient2, mais le générateur a utilisé à tort X/Y comme entrées de /SKEW/FIX; les axes effectifs sontZ,Y,−X. Son premier calcul reste conservé en échec. w2 corrige Yprime/Zprime, obtient les bons axes, puis le lecteur de validation attend à tort le format TYPE22; arrêt avant Engine. w3 corrige seulement ce lecteur et confirme les axesY,−X,Z et les drapeaux18,2,3,2,0,0,0,0,0avant Engine. Son premier mode normal échoue à la référence3D; les contrôles suivants ne sont pas exécutés.

w4 est une nouvelle branche LAW12 déclarée avant ses15contrôles. Le repère et les propriétés sont vérifiés avant chaque Engine. Les17calculs terminent normalement, sans avertissement. Une erreur de chemin dans le résumé final est corrigée par un collecteur distinct qui lit seulement les15résultats déjà enregistrés; aucun calcul n'est relancé, le générateur original reste conservé. 51échantillons natifs passent les contrôles de finitude, géométrie avec borne d'impression et absence de suppression. Les cartes effectives sont vérifiées dans chaque entrée. Certains champs descriptifs de configuration hérités de vieux témoins sont périmés; configuration_metadata_addendum.json les identifie sans réécriture. Les cartes réellement exécutées, les références nouvelles et les lectures natives font foi. Préservation de21940fichiers précédents, 65.434Go; aucun ancien solveur relancé.

## 2. Résultats d'un modèle officiel

[TYPE6](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm) fournit Isolid18 pour solides orthotropes. [/SKEW/FIX](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/skew_fix_starter_r.htm) demandeYprime etZprime, puis reconstruitXprime. [LAW12](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law12_3d_comp_starter_r.htm) décrit l'élasticité orthotrope3D par les trois modules, trois coefficients de Poisson, trois cisaillements et leurs réciprocités. Ces définitions sont des références constitutives, sans recours au dommage connu du WTC1.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse de vidéo ou affirmation historique. Le fichier A20effectivement utilisé et sa LAW25/4 sont épinglés. La carte source est un témoin élastique, pas une mesure historique de résistance/rupture de Boeing. L'inventaire A25des24racines/144ancres est conservé, sans intégration nouvelle dans l'avion entier.

## 4. Hypothèses propres au modèle

La référence3D déclare S11=S22=1/22000, S33=1/10000, S12=−0,25/22000, S13=−0,25/10000, S23=−0,25/22000(MPa−1), puis inverseS et tourne les axes90°. Le tenseur est symétrique défini positif, valeur propre minimale4000MPa. Les cisaillements utilisent gamma ingénieur etG4000MPa, sans Ashear de coque. Les coefficients nu23=nu31=0,25de LAW12 sont **des hypothèses transverses explicites nouvelles**, pas des mesures historiques. Les modules,nu12etdensité source sont inchangés. LAW12n'est pas une équivalence automatique de l'ancienne LAW25; ses seuils géants1e12MPa maintiennent ces témoins élastiques.

Les6modes affines sont déclarés avant les mouvements libres et la flexion; arrêt au premier mode affine échoué. Les références utilisent0,5epsilon·C·epsilon·volume. La traction libre transverse suit la compliance indépendante. La flexion cylindrique imposeepsilon_y=0et sigma_z=0au premier ordre; contraction transverseCzx/Czzet D=(Cxx−Cxz²/Czz)t³/12. Les4éléments dans l'épaisseur représentent cette cinématique. Masse nodale obtenue par volumes physiques, inertie discrète distincte du tenseur continu. Seuils énergétiques et élastiques2%+1e−7J, invariants libres0,2%, inertie continue2%, raffinement spatial5% conservés. Aucune référence n'est estimée sur les sorties natives.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Résultat |
|---|---:|---|
| w1 / PATCH_NORMAL_X_N12 | 9.3228e-11 | **échoué**: independent_elastic_reference |
| w3 / PATCH_NORMAL_X_N12 | 1.93228e-10 | **échoué**: independent_elastic_reference |
| w4 / BENDING_N12 | 1.63584e-10 | réussi |
| w4 / BENDING_N6 | 2.5929e-10 | réussi |
| w4 / FREE_ROTATION_X_N12 | 5.89e-08 | réussi |
| w4 / FREE_ROTATION_Y_N12 | 5.45668e-08 | réussi |
| w4 / FREE_ROTATION_Y_N12_HALF | 5.554e-08 | réussi |
| w4 / FREE_ROTATION_Z_N12 | 1.7606e-07 | réussi |
| w4 / FREE_TRANSLATION_N12 | 0 | réussi |
| w4 / MEMBRANE_N12 | 1.403903e-10 | réussi |
| w4 / MEMBRANE_N6 | 1.461588e-10 | réussi |
| w4 / PATCH_NORMAL_X_N12 | 1.6535e-10 | réussi |
| w4 / PATCH_NORMAL_Y_N12 | 1.93347e-10 | réussi |
| w4 / PATCH_NORMAL_Z_N12 | 1.1635864e-10 | réussi |
| w4 / PATCH_SHEAR_XY_N12 | 2.83e-11 | réussi |
| w4 / PATCH_SHEAR_XZ_N12 | 3.304615e-11 | réussi |
| w4 / PATCH_SHEAR_YZ_N12 | 3.304615e-11 | réussi |

Le modeXde LAW25avec bon repère fournitIE=0.0005861244J, contre référence3D0.000640752111J; bilan complet réussi mais critère constitutif échoué. Cette réponse est proche du bloc plan, contrairement à la matrice3D déclarée. La mauvaise orientationw1est une erreur distincte et ne prouve pas cette contradiction. Aucun ancien bilan, matériau ou critère n'est révisé.

LAW12: 15ensembles individuels réussis sur15. Mouvements libres:True; six modes affines:True; traction:True; flexion:True. Pas temporel médian demi-pas/initial=0.5; différence de moment cinétique=1.79581674e-13kg·m²/s, énergie=1.03177164e-08J. Les écarts spatiaux et lectures natives sont détaillés dans composite_qualification_review.json. Au total17bilans complets sur17passent; 15ensembles individuels sur17passent. L'intégrité du dossier ne vaut pas qualification du montage entier.

## 6. Contradictions et informations manquantes

La carte LAW25source reste conservée et échoue au premier contrôle volumique3D avec orientation correcte. Son équivalence constitutive3D n'est pas établie. LAW12est une hypothèse de remplacement explicite uniquement pour les témoins; aucune pièce de l'avion entier n'est modifiée. La réussite locale éventuelle ne qualifie ni les coefficients historiques, ni la rupture, ni le cœur/sandwich, ni les attaches courbes. Les échecs A21–A28restent inchangés. Façade, gravité, intérieur porteur et contacts de fragments restent ouverts. Meilleur entierA20=20ms; vidéo10secondes physiques incomplète.

AIRCRAFT-A30 : reprendre la branche LAW12/TYPE6 Isolid18 à quatre éléments dans l’épaisseur, avec les propriétés source, les coefficients transverses explicitement hypothétiques et le repère natif vérifié. Si tous les témoins A29 passent, qualifier séparément le cœur LAW28 et un sandwich conformal peau/cœur à faces partagées, sans masse ou inertie ajoutée; les anciens raccords Spot5 restent conservés et ne sont pas remplacés implicitement. Tester masse, moments physiques, mouvements libres, travail/énergie et modes élastiques indépendants avec raffinements. Ensuite préparer les24racines/144ancres courbes A25 dans leur géométrie réelle et leur budget physique. Si un critère A29 échoue, le diagnostiquer avant le couplage. Aucune carte historique de rupture n’est qualifiée. Aucun état A21 prolongé; nouveau départ entier intact seulement après ces contrôles et estimation du coût. Objectif vidéo3D10secondes physiques incomplet, meilleur entier20ms. Publier A28+A29 avec tous les échecs; cadence suivante A30+A31 vérifiées. Aucun dommage connu comme cible, aucun terme RKE inventé.
