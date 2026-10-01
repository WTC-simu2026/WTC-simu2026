# V11N — reconstruction positive et conservative sur éprouvettes

Contrôles : 74/74, statut PASS. Aucun nouveau chemin du panneau ni temps de garde-fou.

## 1. Faits observés dans les fichiers

Trois historiques fins V11M (64, 128 et 256 cellules, 641 états chacun) sont relus ; la conduction n’est pas recalculée. Les contrôles hérités, dont V11F, sont conservés et vérifiés par empreintes.

## 2. Modèles officiels

Aucune nouvelle sortie officielle ni donnée physique importée.

## 3. Archives locales

Aucune nouvelle analyse d’archive ou de vidéo.

## 4. Hypothèses numériques, propriétés et unités

La nouvelle reconstruction impose les températures de face sauvegardées et conserve séparément la moyenne de chaque cellule. Les faces internes sont la moyenne des cellules voisines limitée à deux fois la plus petite. Dans chaque cellule, deux rampes symétriques bordent un plateau ; leur largeur assure une température non négative et l’intégrale exacte. Un champ affine reste affine. Cette forme sous-maille est une hypothèse, pas une solution spatiale exacte de l’équation de chaleur.

La projection utilise T_i=n*m0*exp(log(Tbrut_i)+beta*eta_i)/somme(exp(...)), eta=y/h. Beta impose le barycentre cible. Les zéros sont préservés ; un barycentre hors du support des fibres positives est rejeté. La moyenne et le gradient linéaire équivalent sont conservés comme en V11L : le moment absolu conserve l’écart connu de quadrature, enregistré dans les sorties.

Propriétés constantes héritées : épaisseur 0,11049 m ; béton rho=2400 kg/m³, cp=900 J/(kg K), alpha=1e-5/K ; armatures rho=7850, cp=600, alpha=1,2e-5/K. E, aires et positions exactes sont dans section_inventory.json. Les armatures remplacent 0,2 % du volume de béton et échantillonnent le champ continu sans correction.

eps=eps0−y*kappa ; eps_th=alpha*DeltaT ; sigma=E*(eps−eps_th). Énergies par mètre longitudinal, en J/m ; réactions N et N·m. U=1/2*somme(A*sigma²/E). Wth=−intégrale sigma*d(eps_th)*A ; Wext=intégrale(N*d eps0+M*d kappa). Les cycles d’amplitude vérifient U=Wth+Wext, pas un refroidissement calculé. L’enthalpie sensible reste distincte.

## 5. Résultats dérivés

| Cellules | Reconstruction | Fibres | États supportés / 641 | Rejets à t>0 |
|---:|---|---:|---:|---:|
| C64_S640 | legacy_mean_scaled | 160 | 641 | 0 |
| C64_S640 | legacy_mean_scaled | 320 | 641 | 0 |
| C64_S640 | legacy_mean_scaled | 640 | 641 | 0 |
| C64_S640 | surface_cell_conservative | 160 | 640 | 0 |
| C64_S640 | surface_cell_conservative | 320 | 640 | 0 |
| C64_S640 | surface_cell_conservative | 640 | 640 | 0 |
| C128_S640 | legacy_mean_scaled | 160 | 641 | 0 |
| C128_S640 | legacy_mean_scaled | 320 | 641 | 0 |
| C128_S640 | legacy_mean_scaled | 640 | 641 | 0 |
| C128_S640 | surface_cell_conservative | 160 | 639 | 1 |
| C128_S640 | surface_cell_conservative | 320 | 640 | 0 |
| C128_S640 | surface_cell_conservative | 640 | 640 | 0 |
| C256_S640 | legacy_mean_scaled | 160 | 640 | 1 |
| C256_S640 | legacy_mean_scaled | 320 | 641 | 0 |
| C256_S640 | legacy_mean_scaled | 640 | 641 | 0 |
| C256_S640 | surface_cell_conservative | 160 | 639 | 1 |
| C256_S640 | surface_cell_conservative | 320 | 640 | 0 |
| C256_S640 | surface_cell_conservative | 640 | 640 | 0 |

60 éprouvettes de section libre/empêchée et cycles algébriques. Résidu relatif énergétique maximal : 1.479e-15. Erreur de moyenne : 1.776e-15 K ; erreur du gradient équivalent : 3.322e-13 K ; erreur maximale par cellule reconstruite : 1.066e-13 K.

Les ratios aux résistances froides sont conservés pour chaque éprouvette. Une identité thermoélastique au-delà d’une résistance n’est pas un état matériel physique validé. Les énergies et réactions détaillées, ainsi que l’écart d’enthalpie composite moins coupon brut, figurent dans section_coupons.json.

## 6. Limites et informations manquantes

À t=0, la surface algébrique de V11M est déjà réchauffée alors que chaque cellule reste à 20 °C. Un champ continu non négatif de moyenne nulle ne peut satisfaire une face positive : la reconstruction est rejetée, sans écraser la température de face ni ajouter une chaleur fictive. Le contrôle tout-froid séparé n’efface pas cette incompatibilité de raccord initial.

Le raffinement des fibres et la projection positive ne prouvent pas une précision suffisante du champ sous-maille. La qualification porte sur les instants sauvegardés et les éprouvettes déclarées, pas sur tout instant arbitrairement proche de zéro ni sur une histoire mécanique du panneau. La projection peut avoir un barycentre inaccessible avec des fibres trop grossières.

Aucune propriété endommagée ou énergie historique n’est modifiée. Pas de fissuration chaude, de premier principe couplé fermé, d’incendie ou d’effondrement réel validé. La localisation en flexion après fracture complète reste non validée. Blender est inchangé et reste une visualisation ; crédit énergétique global nul.

## Suite

Définir et qualifier le raccord initial entre champ froid, températures de surface sans masse et transfert positif ; ensuite seulement intégrer la projection au panneau élastique avec contrôles froids et raffinements croisés. Réutiliser V11M/V11N, sans recalcul de conduction ni fissuration chaude.

CPU : 25.60 s ; graine 11014, sans tirage.
