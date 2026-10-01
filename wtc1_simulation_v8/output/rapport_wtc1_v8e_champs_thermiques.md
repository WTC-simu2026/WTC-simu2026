# WTC 1 — V8E : champs thermiques spatiaux corrélés, niveaux 94–99

## Résultat

V8E remplace la température uniforme par 200 champs spatiaux lisses pour chaque combinaison. Chaque champ atteint exactement les extrema publiés par NIST au niveau considéré. Les fractions ci-dessous décrivent uniquement la robustesse de cet ensemble synthétique; elles ne sont pas des probabilités de l’événement réel.

### À 100 minutes — perte d’équilibre d’au moins un niveau

| Extrapolation E au-dessus de 600 °C | Répartition thermique | Fraction des 200 champs | Niveaux défaillants médians |
|---|---:|---:|---:|
| E maintenu à E600 (borne haute) | diffuse, γ=0,5 | 92.5 % | 4.0 |
| E maintenu à E600 (borne haute) | linéaire, γ=1 | 71.0 % | 2.0 |
| E maintenu à E600 (borne haute) | localisée, γ=2 | 45.0 % | 0.0 |
| E maintenu à E600 (borne haute) | très localisée, γ=4 | 21.5 % | 0.0 |
| E décroît vers 5 % à 1000 °C | diffuse, γ=0,5 | 92.5 % | 4.0 |
| E décroît vers 5 % à 1000 °C | linéaire, γ=1 | 71.0 % | 2.0 |
| E décroît vers 5 % à 1000 °C | localisée, γ=2 | 45.0 % | 0.0 |
| E décroît vers 5 % à 1000 °C | très localisée, γ=4 | 21.5 % | 0.0 |

### Localisation par niveau à 100 minutes

| Niveau | Champs γ=1 sans équilibre | Champs très localisés γ=4 sans équilibre |
|---:|---:|---:|
| 94 | 34.0 % | 0.0 % |
| 95 | 68.0 % | 20.5 % |
| 96 | 47.0 % | 2.0 % |
| 97 | 45.0 % | 1.0 % |
| 98 | 0.0 % | 0.0 % |
| 99 | 0.0 % | 0.0 % |

### Enveloppes déterministes à 100 minutes

| Champ | Équilibre conservé aux six niveaux | Niveaux sans équilibre |
|---|---:|---|
| minimum uniforme (borne froide) | oui | aucun |
| milieu uniforme, non médian NIST | non | 95 |
| maximum uniforme (borne chaude irréaliste) | non | 94, 95, 96, 97 |
| foyer centré sur la zone endommagée | oui | aucun |
| foyer nord | oui | aucun |
| foyer sud | non | 95 |
| foyer ciblant les colonnes les plus sollicitées | non | 97 |

## Ce que V8E établit — et n’établit pas

- Il mesure la sensibilité à l’information thermique manquante sans présenter un champ inventé comme le champ réel.
- Une perte d’équilibre dans ce réseau signifie que la règle locale de redistribution ne trouve plus de portance; ce n’est pas encore une simulation dynamique de la tour.
- Les planchers, poutres du noyau, façades, connexions, hat truss, fluage et transfert vertical post-rupture restent absents.
- Le résultat le plus important est la séparation entre cas robustes et cas dépendant fortement de l’emplacement du foyer.
