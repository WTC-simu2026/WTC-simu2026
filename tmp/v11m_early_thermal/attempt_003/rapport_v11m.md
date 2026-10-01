# V11M — premières 90 secondes du coupon synthétique

Contrôles des sorties bornées : 53/53 ; statut PASS. Qualification du transfert : PARTIAL (10 chemins acceptés, 4 rejetés). Les rejets ne sont pas des calculs mécaniques validés.

## 1. Faits observés ou transcrits

Les fichiers V11L et les contrôles V11F/H/I/K sont vérifiés par empreintes. Six nouveaux historiques thermiques sont sauvegardés à chaque pas, de 0 à 90 s. Les anciens calculs complets ne sont pas relancés.

## 2. Modèles officiels

Aucun nouveau résultat officiel. Les références primaires de méthode et les constantes de vérification sont héritées de V11K, sans nouvelle calibration WTC.

## 3. Archives locales

Aucune nouvelle consultation d’archive, photographie ou vidéo.

## 4. Hypothèses, unités et méthode

Coupon 1 m², épaisseur 4,35 in × 0,0254 = 0,11049 m ; béton k=1 W/(m K), rho=2400 kg/m³, cp=900 J/(kg K). Initialement 20 °C. En haut : gaz et rayonnement 250 °C, h=25 W/(m² K), epsilon=0,7 ; en bas : 20 °C, h=10, epsilon=0,8. Ce palier est synthétique_non_WTC.

Conduction : volumes finis, Euler implicite, bilans de surface sans masse. q entrant=h(Tgaz−Ts)+epsilon*sigma[(Trad+273,15)^4−(Ts+273,15)^4]. H=rho*cp*dx*sum(T−20), en J/m² ; DeltaH=dt*(qbas+qhaut) à chaque pas.

Panneau élastique à petites déformations, précharge 0,25 gravité ; 4 subdivisions longitudinales, 160 fibres béton et 2 couches d’armatures. E et résistances sont ceux de V11H/I, conservés dans chaque état de section ; alpha béton=1e-5/K, acier=1,2e-5/K. Les treillis et assemblages restent froids.

Le coupon utilise rho*cp=2 160 000 J/(m³ K). Les armatures remplacent une fraction du volume béton et utilisent rho*cp=4 710 000 J/(m³ K). Leur différence d’enthalpie est conservée explicitement. Déformation totale : eps=eps0−y*kappa ; déformation thermique : eps_th=alpha*DeltaT. Le travail thermique est Wth=−intégrale(sigma*d eps_th*dV) ; U=Wext+Wth. Aucune modification d’un matériau endommagé ni fermeture du premier principe couplé.

Le diagnostic FACE ne change que les sondes aux deux surfaces : les fibres intérieures, la raideur, les réactions et l’énergie transférée conservent le modèle V11L. À t=0, la sonde mécanique reste à 20 °C ; le premier intervalle rejoint la première température de surface positive sauvegardée. Cette convention n’est pas une reconstruction continue validée.

Les changements mesurés sont conservés même défavorables. Une dernière paire sous 1 % est seulement un indicateur local, pas une borne d’erreur. Pas thermique, fréquence des profils et maillage en profondeur sont comparés séparément, avec un maillage mécanique fixe.

## 5. Résultats dérivés

| Cas | Pas thermique (s) | Profils utilisés (s) | Premier garde-fou (s) | DCR |
|---|---:|---:|---:|---:|
| C64_S80 | 1.125000 | 1.125000 | 61.897806823 | 0.899999995 |
| C64_S160 | 0.562500 | 1.125000 | 61.667144358 | 0.899999995 |
| C64_S320 | 0.281250 | 1.125000 | 61.538037300 | 0.899999995 |
| C64_S640 | 0.140625 | 1.125000 | 61.473404109 | 0.900000000 |
| SNAP_45.0 | 0.140625 | 45.000000 | 64.253571555 | 0.899999994 |
| SNAP_22.5 | 0.140625 | 22.500000 | 62.063882500 | 0.899999994 |
| SNAP_4.5 | 0.140625 | 4.500000 | 61.505036473 | 0.899999997 |
| SNAP_0.140625 | 0.140625 | 0.140625 | 61.471234202 | 0.899999999 |
| FACE_C64_S640 | 0.140625 | 1.125000 | 61.473404109 | 0.900000000 |
| COLD | 0.140625 | 1.125000 | 90.000000000 | 0.147129378 |

COLD atteint simplement 90 s sans garde-fou thermique. Les chiffres des autres lignes sont des seuils du modèle élastique, pas des temps de rupture.

| Sensibilité | Paire | Écart du garde-fou |
|---|---|---:|
| thermal_dt | C64_S80 → C64_S160 | 0.374044 % |
| thermal_dt | C64_S160 → C64_S320 | 0.209800 % |
| thermal_dt | C64_S320 → C64_S640 | 0.105140 % |
| thermal_depth | C64_S640 → C128_S640 | indéterminé : transfert rejeté |
| thermal_depth | C128_S640 → C256_S640 | indéterminé : transfert rejeté |
| saved_sampling | SNAP_45.0 → SNAP_22.5 | 3.528121 % |
| saved_sampling | SNAP_22.5 → SNAP_4.5 | 0.908618 % |
| saved_sampling | SNAP_4.5 → C64_S640 | 0.051457 % |
| saved_sampling | C64_S640 → SNAP_0.140625 | 0.003530 % |
| face_screen_only | C64_S640 → FACE_C64_S640 | 0.000000 % |
| face_screen_only | C128_S640 → FACE_C128_S640 | indéterminé : transfert rejeté |
| face_screen_only | C256_S640 → FACE_C256_S640 | indéterminé : transfert rejeté |

| Transfert rejeté | Première entrée planifiée rejetée (s) | Incrément thermique proposé minimal (K) |
|---|---:|---:|
| C128_S640 | 1.125000 | -2.56686363e-10 |
| C256_S640 | 1.125000 | -2.6059511e-08 |
| FACE_C128_S640 | 1.125000 | -2.56686363e-10 |
| FACE_C256_S640 | 1.125000 | -2.6059511e-08 |

V11L sauvegardée : 64.576253369 s. Nouvelle référence à 64 cellules : 61.473404109 s. Aucun temps de garde-fou n’est attribué aux transferts rejetés. Le temps physique calculé concerne uniquement ce coupon synthétique ; le seuil est interpolé entre ses pas sauvegardés.

Référence : U=272.419237609 J ; Wext=95.390435077 J ; Wth=177.028802530 J ; réaction verticale=35239.800130 N. Résidu mécanique relatif maximal=3.834e-11.

Enthalpie composite=16942780.514532 J ; coupon brut étendu=16976354.328461 J ; différence=-33573.813928 J. Cette différence est tracée, pas compensée.

## 6. Limites et informations manquantes

La première tentative s’est arrêtée sur le contrôle de positivité à 128 cellules. Ses entrées et ses sorties sont conservées. Les essais suivants réutilisent les six historiques thermiques et les chemins déjà terminés, tous relus et audités. Aucun seuil de positivité n’est relâché. Le contrôle d’identité V11L compare le même déplacement sauvegardé : il ne mélange plus deux arrêts de Newton différents.

La correction héritée T*(1+a+b*y/h) peut devenir négative dans les queues froides du profil. Plus fondamentalement, si le barycentre thermique cible dépasse celui de la fibre la plus proche de la surface, aucune distribution non négative sur ces fibres fixes ne peut conserver simultanément les deux moments demandés. Les diagnostics non engagés de chaque pas sont sauvegardés dans mapping_diagnostics.json. Une correction simplement tronquée détruirait les moments.

Exemple à 256 cellules et 0.140625 s : barycentre cible 0.497007140334, fibre extrême 0.496875000000. Ce certificat concerne la quadrature et les moments imposés, pas l’impossibilité physique d’un champ thermique positif.

Comparaisons purement thermiques à 90 s (distinctes des chemins mécaniques rejetés) : [{"a": "C64_S640", "b": "C128_S640", "time_s": 90.0, "top_surface_difference_k": -0.10115045123023947, "mean_difference_k": 0.003363188578681786, "enthalpy_relative_change": 0.0012145938663563522}, {"a": "C128_S640", "b": "C256_S640", "time_s": 90.0, "top_surface_difference_k": -0.025176563852454592, "mean_difference_k": 0.0008420359033465274, "enthalpy_relative_change": 0.00030400339013328804}]

Le diagnostic FACE ne remplace que les sondes de contrainte aux deux faces, de mesure volumique nulle. Il ne valide pas une nouvelle température continue ni sa compatibilité avec une quadrature de section. Le point initial mécanique reste froid malgré la réponse algébrique instantanée d’une surface sans masse : cette régularisation est limitée au premier intervalle sauvegardé.

Le raffinement de profondeur change aussi les positions des sondes intérieures du profil ; le nombre de fibres mécaniques et le maillage longitudinal restent fixes. Les sensibilités enregistrées ne sont donc pas une certification d’erreur globale. Pas de fissuration chaude, de dégradation de propriétés, de rétroaction thermodynamique, de flambement géométrique, de dynamique globale ou d’effondrement calculé. La localisation en flexion après fracture complète reste non validée. Une exposition thermique imposée n’est pas un incendie calculé. Blender est inchangé et reste une visualisation. Aucun résultat historique n’est présupposé.

## Suite

Qualifier une reconstruction conservative et positive incluant les températures de surface, et sa compatibilité avec les fibres mécaniques aux tout premiers instants ; croiser ensuite les raffinements thermiques et mécaniques avant toute fissuration chaude. Conserver V11F et les bilans séparés.

CPU : 5.35 s ; graine 11013, sans tirage.
