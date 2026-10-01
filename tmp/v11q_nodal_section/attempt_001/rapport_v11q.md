# V11Q — transfert nodal direct vers une section élastique

7406/7406 contrôles ; 14 chemins ; 7357 états engagés ; 7 premiers essais refusés.

## 1. Faits observés dans les fichiers

V11P fournit les profils nodaux et la chaleur sensible sauvegardés. V11Q les lit sans relancer la conduction. Les anciens résultats, le contrôle froid V11F et le master Blender sont protégés par empreintes.

## 2. Modèles officiels

Aucun nouveau résultat officiel importé.

## 3. Archives locales

Aucune nouvelle analyse d’archive.

## 4. Hypothèses et équations

Section de largeur 80 in × 0,0254=2,032 m, épaisseur 4,35 in × 0,0254=0,11049 m ; béton E=2500 ksi × 6,894757293168361e6 Pa/ksi, alpha=1e-5/K, ft20=1 MPa, fc20=3 ksi ; armatures E=200 GPa, alpha=1,2e-5/K, fy=400 MPa, fraction totale 0,002, deux couches symétriques à 25 mm des faces. Propriétés constantes héritées, pas une loi validée à chaud.

Sections planes : eps(y)=eps0−y*kappa, déformation thermique alpha*DeltaT, contrainte E*(eps−alpha*DeltaT). q=(eps0 sans unité,kappa en 1/m), R=Kq−f en N et N·m ; réaction conventionnelle aux blocages −R. Libre : q=K^-1*f ; entièrement empêchée : q=0. Les signes des réactions suivent cette convention de section et ne sont pas encore des forces nodales de panneau.

Le béton est intégré exactement sur chaque segment linéaire du profil : m0=mean(DeltaT), m1=mean((y/h)*DeltaT), m2=mean(DeltaT²). Les armatures reçoivent une interpolation spatiale aux couches physiques du sous-modèle. K reste celle de la section continue V11O ; aucun raccord initial V11O n’est utilisé.

Section U=0.5*q^T*K*q-q^T*f+0.5*S in J/m. Increment thermal work=-0.5*(q_old+q_new)^T*(f_new-f_old)+0.5*(S_new-S_old). External work=0.5*(R_old+R_new)^T*(q_new-q_old), R=Kq-f. Support reaction convention=-R. These endpoint identities hold for the constant-K section; they do not qualify an inter-step thermal path or close a coupled thermodynamic first law. Coupon sensible heat and composite sensible heat are distinct ledgers.

Chaleur sensible du béton : Ac*rho_c*cp_c*m0 ; armatures : sum(As*rho_s*cp_s*Ts), en J/m. rho_c=2400, cp_c=900 ; rho_s=7850, cp_s=600, en unités SI. Le coupon thermique homogène vaut largeur*H_V11P ; la différence composite−coupon est enregistrée, sans être absorbée dans un bilan fictif.

Garde-fou : maximum des ratios traction béton/ft20, compression béton/fc20 et acier/fy20 ≤0,9. Les contraintes du béton sont contrôlées à tous les nœuds et aux faces, ce qui couvre les extrema de chaque segment linéaire. Le premier essai dépassant 0,9 est isolé, non engagé ; le chemin s’arrête. Cet arrêt n’est ni une rupture calculée, ni une chronologie du WTC.

## 5. Résultats dérivés

| Source | Liaison | Dernier temps engagé (s) | Premier essai refusé (s) |
|---|---|---:|---:|
| N64_S640 | FREE | 63.0 | 63.140625 |
| N64_S640 | FULLY_RESTRAINED | 90.0 | aucun à 90 s |
| N128_S640 | FREE | 63.0 | 63.140625 |
| N128_S640 | FULLY_RESTRAINED | 90.0 | aucun à 90 s |
| N256_S640 | FREE | 63.0 | 63.140625 |
| N256_S640 | FULLY_RESTRAINED | 90.0 | aucun à 90 s |
| N512_S640 | FREE | 63.0 | 63.140625 |
| N512_S640 | FULLY_RESTRAINED | 90.0 | aucun à 90 s |
| N256_S160 | FREE | 63.0 | 63.5625 |
| N256_S160 | FULLY_RESTRAINED | 90.0 | aucun à 90 s |
| N256_S320 | FREE | 63.0 | 63.28125 |
| N256_S320 | FULLY_RESTRAINED | 90.0 | aucun à 90 s |
| N256_S1280 | FREE | 62.9296875 | 63.0 |
| N256_S1280 | FULLY_RESTRAINED | 90.0 | aucun à 90 s |

Résidu énergétique relatif maximal 1.202e-15 ; écart chaleur du transfert 3.492e-10 J/m² ; ratio engagé maximal 0.899773599.

Correction relative de raideur de flexion par rapport à 160 fibres au milieu des bandes : 3.82625067e-05. Le contrôle froid exact est nul ; l’ancienne raideur n’est pas remplacée et l’ancien panneau V11F n’est pas relancé.

Les comparaisons spatiales et temporelles utilisent le dernier temps sauvegardé commun à tous les chemins de même liaison. Aucun temps de franchissement n’est ajusté ou interpolé. Voir comparisons.json pour q, réactions, énergie, carré de température et garde-fou.

## 6. Limites et informations manquantes

Sections isolées sans charge de gravité ni contraintes de compatibilité du panneau. Une section libre peut développer des contraintes autoéquilibrées sous un gradient non linéaire ; libre ne signifie pas partout sans contrainte. Les seuils restent froids et ne constituent pas une validation thermomécanique à chaud. Pas de plasticité, fissuration, fluage, endommagement, fermeture du premier principe couplé ou effondrement validés. Localisation après fracture complète toujours non validée. Exposition synthétique, pas incendie calculé ; Blender inchangé, visualisation seulement.

## Suite

Préparer une intégration bornée des profils nodaux V11P dans le panneau élastique, avec intégrales exactes de section, contrôle froid comparé et garde-fou local avant engagement. Pré-déclarer une fenêtre thermique commune sous le garde-fou, vérifier charges mécaniques et conventions de travail/réactions, conserver séparément chaleur sensible et travail thermoélastique. Aucun prolongement au-delà du garde-fou ni dommage chaud sans formulation et validation nouvelles.

Durée 3.693 s ; graine 11017 sans tirage.
