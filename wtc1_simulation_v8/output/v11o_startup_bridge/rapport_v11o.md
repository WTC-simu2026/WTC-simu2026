# V11O — raccord faible initial et énergie de section

Contrôles : 41/41 ; statut PASS. Qualification numérique du raccord mécanique, pas d’un nouveau champ thermique physique.

## 1. Faits observés dans les fichiers

Les deux premiers états sauvegardés V11M encadrent 0 à 0,140625 s. La température de surface algébrique est positive dès zéro alors que les cellules sont froides. Sources V11M/N et contrôle V11F sont conservés par empreintes. Aucun solveur de conduction ni ancien pilote complet relancé.

## 2. Modèles officiels

Aucun nouveau résultat officiel importé.

## 3. Archives locales

Aucune nouvelle analyse d’archive, de photographie ou de vidéo.

## 4. Hypothèses et équations

Le raccord principal interpole les moyennes de cellules et les températures de face entre les deux états sauvegardés ; pour chaque fraction positive, il utilise la reconstruction conservative V11N. À zéro, le volume est froid presque partout et la face positive reste une sonde de mesure volumique nulle. Ce champ initial est discontinu : l’ancien rejet de reconstruction continue reste correct. Le témoin multiplie tout le premier profil positif par la fraction ; il conserve la chaleur mais viole la température de face intermédiaire. Il n’est pas retenu comme champ respectant cette condition.

La section intègre exactement le béton continu à propriétés constantes et conserve les armatures discrètes. Les trois intégrales sont m0=moyenne(DeltaT), m1=moyenne((y/h)*DeltaT), m2=moyenne(DeltaT²). U=1/2*qᵀKq−qᵀf+S/2, avec f=intégrale(E*alpha*DeltaT*B*dA) et S=intégrale(E*alpha²*DeltaT²*dA). B=(1,−y), q=(eps0,kappa). Réactions en N et N·m ; énergies par mètre longitudinal en J/m. Les contraintes sont calculées aussi aux faces, même lorsqu’elles ont une mesure volumique nulle.

Travail thermique incrémental : −(qancien+qnouveau)ᵀ*(fnouveau−fancien)/2+(Snouveau−Sancien)/2. Travail extérieur : (Rancien+Rnouveau)ᵀ*(qnouveau−qancien)/2. La chaleur sensible et l’écart de capacité thermique composite restent séparés ; aucun premier principe thermo-mécanique couplé n’est revendiqué.

Hypothèses héritées : épaisseur 0,11049 m ; largeur 80 in × 0,0254=2,032 m ; béton E=2500 ksi, alpha=1e-5/K, rho=2400 kg/m³, cp=900 J/(kg K) ; armatures E=200 GPa, alpha=1,2e-5/K, rho=7850, cp=600, fraction de section 0,002. Les conversions et constantes effectives figurent dans section_inventory.json et les configurations sources.

Cette intégration retire l’erreur de quadrature au milieu des fibres sur l’inertie du béton : DeltaK22=Ec*Ac*h²/(12*n²). Cet écart est mesuré séparément ; aucune ancienne raideur ni histoire V11F/H/N n’est réécrite. Le futur panneau devra comparer explicitement son contrôle froid.

## 5. Résultats dérivés

| Source | Liaison | Énergie au plus petit paramètre, raccord faible (J/m) | Témoin proportionnel (J/m) | Écart final (unités SI) |
|---|---|---:|---:|---:|
| C64_S640 | FREE | 3.30390864e-08 | 5.4804346e-13 | 0.000e+00 |
| C64_S640 | FULLY_RESTRAINED | 3.30390905e-08 | 5.52113903e-13 | 0.000e+00 |
| C128_S640 | FREE | 1.59869855e-08 | 3.28910459e-13 | 0.000e+00 |
| C128_S640 | FULLY_RESTRAINED | 1.59869897e-08 | 3.33093854e-13 | 0.000e+00 |
| C256_S640 | FREE | 6.8554216e-09 | 2.29980045e-13 | 0.000e+00 |
| C256_S640 | FULLY_RESTRAINED | 6.85542584e-09 | 2.34208137e-13 | 0.000e+00 |

12 chemins de section, 180 états. Résidu énergétique relatif maximal : 2.711e-19. Ratio maximal aux résistances froides (faces incluses) : 0.061617.

Pour 0≤T≤Tmax, |m1|≤m0/2 et m2≤Tmax*m0. Puisque m0 tend linéairement vers zéro, les charges thermiques et S tendent vers zéro ; déformations libres et réactions empêchées s’annulent. 0≤Ulibre≤Uempêchée=S/2. Les contraintes ponctuelles de face peuvent garder une limite non nulle. Le raccord est donc cohérent pour ces grandeurs intégrées, pas continu point par point en température.

Les deux raccords atteignent le même état final mais peuvent avoir des énergies très différentes dans l’intervalle. Une projection conservant moyenne et gradient peut manquer le terme moyen de température au carré : projection_square_diagnostics.json mesure cet écart sans engager ces projections dans le calcul de section.

## 6. Limites et informations manquantes

Les fractions de l’intervalle sont des coordonnées d’interpolation, pas des microsecondes thermiques nouvellement résolues. Le gradient du profil reconstruit à la surface ne reproduit pas en général le flux sauvegardé ; cet écart est mesuré dans flux_mismatch_diagnostics.json. La reconstruction n’est donc pas une nouvelle solution de l’équation de chaleur. La température algébrique initiale reste un effet du maillage thermique et de sa convention de surface sans masse.

Exemple décisif : à 256 cellules et fraction 1/65536 du premier pas, le gradient reconstruit donne environ 5,02e8 W/m² contre 8,38e3 W/m² dans le flux sauvegardé interpolé. Cet écart est un artefact de reconstruction, pas une exposition physique. Malgré les identités mécaniques réussies, la compatibilité thermique reste NON QUALIFIÉE et l’intégration au panneau est différée. La prochaine étape doit tester un démarrage thermique cohérent, par exemple des volumes de contrôle nodaux incluant la surface sans ajouter de masse.

Aucun nouveau panneau chargé, temps de rupture ou garde-fou global n’est calculé. Pas de dommage chaud, de modification d’historique endommagé, d’incendie réel ou d’effondrement validé. Localisation en flexion après fracture complète non validée. Blender inchangé, visualisation seulement ; crédit énergétique global nul.

## Suite

Qualifier une formulation thermique de démarrage cohérente avant le panneau : tester notamment des températures nodales de surface avec demi-volumes de contrôle, à masse et capacité thermique totales inchangées ; vérifier flux, enthalpie, état initial et raffinements, puis comparer aux sorties V11M sauvegardées. Conserver les intégrales exactes de température et de température au carré pour le futur transfert mécanique. Ne pas intégrer le raccord V11O comme une conduction validée.

Calcul CPU : 0.64 s ; graine 11015, sans tirage.
