# V11H — socle thermomécanique élastique borné

## Résultat

V11H passe 27/27 contrôles. Elle qualifie une section élastique à température prescrite pour dilatation libre, dilatation empêchée et gradient linéaire dans l'épaisseur. Les propriétés, unités, déformations thermiques, réactions, travail thermoélastique, énergie stockée et enthalpie sensible sont enregistrés à chaque état.

Le contrôle froid V11F est conservé octet par octet : 132/132 contrôles, 14 cas et son empreinte numérique antérieure sont retrouvés. Aucun état V11F n'est recalculé ou modifié. V11H ne couple pas encore le champ thermique au panneau V11F et n'introduit aucune loi de fissuration à chaud.

## 1. Faits directement observés ou transcrits

Le dossier local vérifié indiquait V11G terminée et V11H suivante. Les fichiers V11F/V11G déclarés par leurs manifestes ont été relus par empreinte, sans rescanner l'archive source. La géométrie de section reprend le ruban équivalent V11E/V11F : largeur 2,032 m, épaisseur équivalente 0,11049 m et portée de référence 18,1102 m.

## 2. Résultats d'un modèle officiel

Aucun nouveau résultat officiel n'est utilisé. Les résultats historiques déjà transcrits dans les étapes antérieures ne sont ni étendus ni réinterprétés ici.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation d'archive, mesure de température, séquence d'incendie ou identification de mécanisme n'entre dans V11H.

## 4. Hypothèses propres au modèle

Petites déformations et sections planes : ε(y)=ε₀−yκ. La déformation thermique est εth=α(T−20 °C), la déformation mécanique εm=ε−εth et la contrainte σ=Eεm. Les résultantes sont N=ΣAσ et M=−ΣAyσ.

Les coefficients constants sont αc=1.000e-05 K⁻¹ et αs=1.200e-05 K⁻¹. Les propriétés calorifiques constantes sont ρc=2400 kg/m³, cp,c=900 J/(kg·K), ρs=7850 kg/m³ et cp,s=600 J/(kg·K). Ce sont des hypothèses génériques, pas des propriétés mesurées du béton ou des armatures du WTC1.

E et les résistances à 20 °C sont hérités sans dégradation. Il n'y a ni conduction, convection, rayonnement, flux incident, protection projetée calculée, fluage, plasticité, fissuration, écrasement, glissement d'adhérence, non-linéarité géométrique ou contact. Le gradient est imposé, non calculé. La température maximale de 120 °C est un palier numérique de qualification, pas une reconstitution d'incendie.

L'énergie mécanique par mètre longitudinal est U=1/2 ΣAE εm². Le travail thermoélastique conjugué est −∫ΣAσ dεth. Le travail mécanique généralisé est ∫(N dε₀+M dκ). Pour les appuis idéaux présents, les coordonnées bloquées ne bougent pas et les coordonnées libres ont une résultante nulle : le travail mécanique d'appui vaut donc zéro même si les réactions ne sont pas nulles. L'enthalpie sensible H=ΣρcpAΔT est inventoriée séparément ; aucune équation de chaleur n'est résolue.

## 5. Résultats dérivés

| Cas | Cinématique | T basse/haute au pic (°C) | ε₀ | κ (m⁻¹) | Réaction N (kN) | Réaction M (kN·m) | U (kJ/m) | H sensible (MJ/m) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| COLD_R02_FREE | FREE | 20.0/20.0 | 0.000000e+00 | 0.000000e+00 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| PLAIN_UNIFORM_FREE | FREE | 120.0/120.0 | 1.000000e-03 | 3.465278e-19 | 0.000000 | 0.000000 | 0.000000 | 48.495387 |
| PLAIN_UNIFORM_FULLY_RESTRAINED | FULLY_RESTRAINED | 120.0/120.0 | 0.000000e+00 | 0.000000e+00 | 3869.952805 | 0.000000 | 1.934976 | 48.495387 |
| PLAIN_GRADIENT_FREE | FREE | 20.0/120.0 | 5.000000e-04 | -9.050593e-03 | 0.000000 | 0.000000 | 0.000000 | 24.247693 |
| R02_COMMON_ALPHA_GRADIENT_FREE | FREE | 20.0/120.0 | 6.000000e-04 | -1.086071e-02 | 0.000000 | 0.000000 | 0.000000 | 24.304945 |
| R02_UNIFORM_FREE | FREE | 120.0/120.0 | 1.004545e-03 | -3.679825e-18 | 0.000000 | 0.000000 | 0.001755 | 48.609890 |
| R02_UNIFORM_AXIAL_RESTRAINED | AXIAL_RESTRAINED_ROTATION_FREE | 120.0/120.0 | 0.000000e+00 | -1.813925e-18 | 3969.980426 | 0.000000 | 1.995767 | 48.609890 |
| R02_GRADIENT_FREE | FREE | 20.0/120.0 | 5.022724e-04 | -9.087665e-03 | 0.000000 | 0.000000 | 0.000571 | 24.304945 |
| R02_GRADIENT_FULLY_RESTRAINED | FULLY_RESTRAINED | 20.0/120.0 | 0.000000e+00 | 0.000000e+00 | 1984.990213 | -36.452156 | 0.664706 | 24.304945 |
| R02_UNIFORM_RESTRAINED_CYCLE | FULLY_RESTRAINED | 120.0/120.0 | 0.000000e+00 | 0.000000e+00 | 3969.980426 | -0.000000 | 1.995767 | 48.609890 |
| R02_GRADIENT_FREE_CYCLE | FREE | 20.0/120.0 | 5.022724e-04 | -9.087665e-03 | 0.000000 | 0.000000 | 0.000571 | 24.304945 |

À +100 K uniforme, le cas composite libre donne un allongement au centroïde de 18.192508 mm. Le même cas axialement empêché donne une réaction de 3969.980426 kN et stocke 1.995767 kJ/m.

Pour un gradient imposé de 20 à 120 °C, le cas composite libre donne κ=-9.087665150e-03 m⁻¹ et une flèche cinématique petites pentes de 0.372571 m. Le blocage complet donne des réactions de 1984.990213 kN et -36.452156 kN·m. Cette flèche n'est pas un calcul du panneau V11F.

Le résidu relatif maximal de l'identité énergétique est 1.208e-13; le résidu maximal des résultantes libres est 3.395e-15. Les deux cycles reviennent à l'état de référence sans dissipation. Le passage de 160 à 320 fibres donne un écart maximal de 2.858e-05, et le demi-pas conserve les états terminaux à 3.406e-13.

Les rapports aux résistances froides ft, fc et fy sont uniquement des écrans de domaine. Un dépassement n'autoriserait pas l'emploi de l'élasticité : il indiquerait au contraire que ce cas doit s'arrêter avant une interprétation physique ou être repris avec une loi thermodynamique complète et un historique cohérent.

## 6. Contradictions, limites et informations manquantes

Une température imposée n'est pas un incendie calculé. Il manque les flux thermiques, échanges de surface, propriétés variables, humidité, état de la protection, températures spatiales et leur validation. Il manque aussi une énergie libre dépendant de T et de l'endommagement, les forces thermodynamiques, l'irréversibilité et une loi de fissuration/écrasement/plasticité à chaud avant de modifier E, ft, fc ou fy.

La localisation en flexion après fracture complète reste non validée. Le succès de ces coupons numériques ne valide ni le panneau chauffé, ni la tour, ni l'impact, ni l'incendie, ni l'initiation ou la propagation d'un effondrement réel. Blender reste inchangé et sans crédit mécanique.

## Suite bornée

V11I : injecter les pré-déformations et courbures thermiques élastiques qualifiées dans un seul panneau V11F borné, avec contrôle ΔT=0, température uniforme puis gradient imposé, réactions et travail des appuis ; arrêter avant toute fissuration chauffée ou limite de domaine. Formuler ensuite l'énergie libre et l'historique du matériau endommagé avant d'autoriser une loi fissurée à chaud.

Exécution finale : 0.360 s sur CPU ; Python 3.14.3, NumPy 2.4.6, Pillow 12.2.0. Graine 1101008, sans tirage aléatoire. Empreinte numérique : a7a39e9a1a4f00709e390da28766c66806b81e9696a25eae1a5b82effa616f8e. Aucune installation, analyse vidéo, relecture d'archive, solveur externe, GPU ou modification Blender.

## Livrables

results_v11h.json, section_paths.json, section_paths.csv, section_fiber_states.csv, section_mesh_comparison.csv, mesh_convergence.json, energy_ledger.csv, thermal_material_ledger.json, cold_v11f_control.json, v10w_bar_replay.json, numerical_audit.json, source_manifest.json, offline_manifest.json et synthese_v11h_thermomecanique.png. L'audit de relecture séparé est ajouté dans release_audit.json avant publication locale.
