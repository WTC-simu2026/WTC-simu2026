# V11M — premières 90 secondes du coupon synthétique

Contrôles des sorties bornées : 52/53 ; statut FAIL. Qualification du transfert : PARTIAL (10 chemins acceptés, 4 rejetés). Les rejets ne sont pas des calculs mécaniques validés.

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

Conduction conserves gross rho*cp=2160000 J/m3/K. The separate composite panel subtracts reinforcement volume from concrete and uses steel rho*cp=4710000 J/m3/K. Preserve and report their sensible-energy difference, not a fictitious correction. eps=eps0-y*kappa; eps_th=alpha*DeltaT; U=Wext-Wintegral(sigma*d eps_th). No history or damaged-material properties are edited; no coupled first-law closure.

Replace only zero-measure face stress probes by interpolated massless boundary temperatures. Bulk fiber temperatures, strains, stiffness, forces and energy transfer remain exactly V11L. This measures surface-screen sensitivity, NOT validation of a continuous boundary-consistent conservative remap. At t=0 the mechanical face increment remains zero; the first resolved interval joins it to the first positive-time boundary value. Store this regularization explicitly.

Report measured changes without imposing a favorable trend. A final pair below 1 percent is a bounded small-change indicator, not an error bound or formal convergence proof. Thermal solve time step, stored-profile sampling and depth mesh are varied separately. Fixed structural mesh and fiber count remain inherited limits.

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

V11L sauvegardée : 64.576253369 s. Nouvelle référence à 64 cellules : 61.473404109 s. Aucun temps de garde-fou n’est attribué aux transferts rejetés. Le temps physique calculé concerne uniquement ce coupon synthétique ; le seuil est interpolé entre ses pas sauvegardés.

Référence : U=272.419237609 J ; Wext=95.390435077 J ; Wth=177.028802530 J ; réaction verticale=35239.800130 N. Résidu mécanique relatif maximal=3.834e-11.

Enthalpie composite=16942780.514532 J ; coupon brut étendu=16976354.328461 J ; différence=-33573.813928 J. Cette différence est tracée, pas compensée.

## 6. Limites et informations manquantes

La première tentative s’est arrêtée sur le contrôle de positivité à 128 cellules. Ses entrées et ses sorties sont conservées. La présente publication réutilise ses six historiques thermiques et quatre chemins terminés, tous relus et audités. Aucun seuil de positivité n’est relâché.

La correction héritée T*(1+a+b*y/h) peut devenir négative dans les queues froides du profil. Plus fondamentalement, si le barycentre thermique cible dépasse celui de la fibre la plus proche de la surface, aucune distribution non négative sur ces fibres fixes ne peut conserver simultanément les deux moments demandés. Les diagnostics non engagés de chaque pas sont sauvegardés dans mapping_diagnostics.json. Une correction simplement tronquée détruirait les moments.

Comparaisons purement thermiques à 90 s (distinctes des chemins mécaniques rejetés) : [{"a": "C64_S640", "b": "C128_S640", "time_s": 90.0, "top_surface_difference_k": -0.10115045123023947, "mean_difference_k": 0.003363188578681786, "enthalpy_relative_change": 0.0012145938663563522}, {"a": "C128_S640", "b": "C256_S640", "time_s": 90.0, "top_surface_difference_k": -0.025176563852454592, "mean_difference_k": 0.0008420359033465274, "enthalpy_relative_change": 0.00030400339013328804}]

Le diagnostic FACE ne remplace que les sondes de contrainte aux deux faces, de mesure volumique nulle. Il ne valide pas une nouvelle température continue ni sa compatibilité avec une quadrature de section. Le point initial mécanique reste froid malgré la réponse algébrique instantanée d’une surface sans masse : cette régularisation est limitée au premier intervalle sauvegardé.

Le raffinement de profondeur change aussi les positions des sondes intérieures du profil ; le nombre de fibres mécaniques et le maillage longitudinal restent fixes. Les sensibilités enregistrées ne sont donc pas une certification d’erreur globale. Pas de fissuration chaude, de dégradation de propriétés, de rétroaction thermodynamique, de flambement géométrique, de dynamique globale ou d’effondrement calculé. La localisation en flexion après fracture complète reste non validée. Une exposition thermique imposée n’est pas un incendie calculé. Blender est inchangé et reste une visualisation. Aucun résultat historique n’est présupposé.

## Suite

Qualifier une reconstruction conservative et positive incluant les températures de surface, et sa compatibilité avec les fibres mécaniques aux tout premiers instants ; croiser ensuite les raffinements thermiques et mécaniques avant toute fissuration chaude. Conserver V11F et les bilans séparés.

CPU : 14.27 s ; graine 11013, sans tirage.
