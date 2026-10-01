# THERMITE-CORPUS-V1 — audit documentaire WTC

Date : 29 août 2026  
Statut : **PASS documentaire**  
Périmètre : onze PDF et un schéma fournis par Jeremy, inspectés en lecture seule.  
Frontière : aucune modification de `harness/state.json`, du registre d'expériences, des entrées solveur ou de Blender.

## Conclusion courte

Ces pièces renforcent trois constats, mais ne ferment pas la démonstration thermitique :

1. des formulations thermitiques nanostructurées et des variantes génératrices de gaz existaient bien comme **capacité technologique générale** ;
2. plusieurs documents rapportent dans des poussières attribuées au WTC des **fragments rouges/gris réactifs**, des **sphérules riches en fer**, ainsi que des **anomalies environnementales et thermiques** qui méritent une explication ;
3. le corpus ne fournit pas la chaîne indispensable reliant ces observations à un dispositif dans les tours : identité chimique univoque, échantillonnage représentatif, masse initiale, placement, géométrie, initiation, pression, couplage à la structure, chronologie et produits distinctifs.

La conclusion probatoire correcte est donc : **hypothèse thermitique ouverte mais non établie**. Elle ne doit pas être introduite dans la simulation WTC1 comme un fait.

## 1. Méthode et intégrité

### FAITS DE PROCÉDURE

- 11 PDF, 119 pages au total, et une image JPEG ont été inventoriés.
- Les empreintes SHA-256 ont été calculées avant et après l'extraction.
- Les dix PDF possédant une couche texte ont été extraits page par page.
- Le brevet WO 03/044450 A1, dépourvu de couche texte, a été rendu et contrôlé visuellement sur ses 18 pages.
- Les pages centrales contenant les courbes DSC, les pics de COV, le tableau de températures, les essais LLNL, la table USGS et les points chauds USGS ont été contrôlées visuellement.
- Les onze PDF et le JPEG ont conservé exactement la même empreinte jusqu'au contrôle final : ils n'ont été ni copiés dans le dossier, ni renommés, ni déplacés, ni modifiés.
- Le chemin corrigé du schéma est `C:\Users\jeuxpc\Desktop\ARCH\11 septembre 2001\IMG\collape shematic.jpg`; ses dimensions sont 1000 × 738 px.

Les détails reproductibles se trouvent dans `source_inventory.json`, `evidence_matrix.csv` et `run_manifest.json`.

## 2. Séparation des niveaux de preuve

### FAITS DIRECTEMENT RAPPORTÉS DANS LE CORPUS

- Harrit et al. ont étudié des fragments rouges/gris provenant de quatre lots de poussière collectés par des particuliers. Ils rapportent une structure en couches, des éléments Al/Fe/O/Si/C, des pics DSC vers 415-435 °C en air, des énergies intégrées d'environ 1,5 à 7,5 kJ/g et des sphérules riches en fer après chauffage.
- Leur estimation d'environ 0,1 % concerne 1,74 mg de fragments retirés de 1,6 g d'une poussière dont des morceaux de verre et de béton avaient été ôtés manuellement. Elle ne constitue pas une fraction représentative du nuage ou de la masse des tours.
- Jones et al. rapportent des sphérules riches en fer et en silicates dans deux lots de poussière et discutent un acier oxydé/sulfuré.
- Ryan, Gourley et Jones compilent des pics de COV et d'autres séries environnementales provenant notamment de données EPA obtenues par FOIA.
- L'USGS mesure une poussière très hétérogène. Ses données AVIRIS du 16 septembre 2001 indiquent plus de trois douzaines de points chauds de surface dépassant 800 °F, certains dépassant 1300 °F; la plupart des feux observables depuis l'avion diminuent ou ne sont plus visibles le 23 septembre.
- Clapsaddle et al. décrivent en laboratoire des nanocomposites Al-Fe2O3-SiO2 et des variantes organofonctionnelles produisant du gaz et des éjections de particules chaudes.
- Le retour de carrière décrit des détonateurs électroniques I-Kon et le brevet décrit une architecture de détonateur électronique.

### AFFIRMATIONS DES AUTEURS OU DES ARCHIVES

- Harrit et al. concluent explicitement que la couche rouge est un matériau thermitique actif, nanotechnologique et hautement énergétique.
- Jones et al. infèrent des températures très élevées à partir des sphérules et privilégient une réaction chimique violente.
- Ryan et al. proposent les matériaux nanoénergétiques comme explication possible de plusieurs anomalies environnementales.
- Le texte 911facts.dk conclut au contraire que la thèse est fausse, non documentée et incohérente.
- Le schéma local propose une lecture en quatre phases de l'effondrement du WTC 1.

### RÉSULTATS DE CET AUDIT

- Les observations de Harrit et al. sont réelles **dans les lots et les conditions d'essai décrits**, mais leur spécificité est insuffisante pour identifier un dispositif au WTC.
- Un exotherme DSC en air ne sépare pas proprement une réaction thermitique d'une combustion/oxydation d'une matrice organique; les auteurs indiquent eux-mêmes que cette matière organique reste à identifier et appellent FTIR, TGA, NMR et GC-MS.
- Des sphérules et une composition XEDS ne donnent pas, à elles seules, une température de formation unique : phase minérale, alliages/eutectiques, cinétique, provenance et mécanismes concurrents doivent être mesurés.
- La chimie globale USGS n'était pas une recherche spécifique de fragments énergétiques. Son silence ne confirme ni n'exclut des traces de nanothermite.
- Les documents LLNL, de carrière et de brevet établissent des capacités générales, pas un usage événementiel.
- Aucun document fourni ne ferme un bilan quantitatif masse-énergie-pression-structure.

### INCONNUS DÉCISIFS

- identité de la phase aluminium dans les fragments exacts de Harrit et al.;
- identité de la matrice organique et contribution de l'air au pic DSC;
- comparaison aveugle aux revêtements, primaires et autres matériaux réellement présents au WTC;
- représentativité spatiale et massique des fragments;
- masse avant réaction et masse résiduelle après l'événement;
- formulation éventuelle, vitesse de réaction/détonation, pression et travail mécanique;
- emplacement, géométrie, initiation et chronologie d'un éventuel dispositif;
- signatures distinctives attendues et retrouvées de manière indépendante.

## 3. Lecture pièce par pièce

| Pièce | Apport réel | Limite déterminante | Valeur pour la simulation |
|---|---|---|---|
| Harrit et al. 2009 | Fragments réactifs caractérisés dans quatre lots; DSC et résidus | contrôles, chaîne de garde, spécificité et représentativité insuffisants | aucune force/source d'énergie ajoutée |
| Environmental anomalies | séries de COV, particules et métaux à expliquer | aucune attribution de source ou signature unique | branche post-effondrement uniquement |
| Extremely high temperatures | sphérules et matériaux altérés à caractériser | thermométrie et causalité non univoques | définir de futures prédictions de phases/résidus |
| LLNL 2005 | capacité réelle de nanocomposites et générateurs de gaz | aucun lien WTC, pression encore à caractériser | borne générique seulement |
| Hightower 2011 | bonnes exigences de formulation, vitesse, quantité et géométrie | essai non expérimental | cadre de falsification utile |
| Retour I-Kon | séquençage électronique civil réel | carrière, aucune trace WTC | aucune |
| 911facts.dk | objections sur contrôles, quantité et initiation | erreurs factuelles et raisonnement secondaire | aucune |
| USGS, trois pièces | chimie globale, hétérogénéité, points chauds de surface | méthodes non spécifiques à un énergétique | contraintes environnementales séparées |
| WO 03/044450 A1 | concept de détonateur électronique | priorité du 19 novembre 2001; ni thermite ni WTC | aucune |
| Schéma de Cole | question visuelle sur toit, destruction latérale et noyau visible | pas de cinématique ni de mécanique validée | protocole vidéo futur seulement |

## 4. Contradiction centrale : fragments thermitiques ou revêtement ?

Harrit et al. concluent à une nanothermite. Le principal contrôle indépendant trouvé pour cet audit est le **rapport préliminaire** de James Millette (2012), qui a examiné quatre autres poussières attribuées au WTC. Il a sélectionné des fragments rouges/gris correspondant aux critères initiaux de morphologie, aimantation et EDS, puis a rapporté une matrice époxy avec kaolin et pigment d'oxyde de fer, sans aluminium élémentaire discret :

https://aneta.org/911experiments_com/articles/Millette9119ProgressReport022912_rev1_030112webHiRes.pdf

Ce résultat a deux limites importantes :

- Millette n'a pas eu accès aux fragments exacts de Harrit et al.; il ne peut donc pas les réfuter directement;
- son document est un rapport préliminaire, pas un article de revue avec une identité commerciale finale du revêtement.

Mais il établit un point méthodologique fort : **les critères initiaux de sélection ne sont pas uniques à la nanothermite**. La seule résolution propre serait une étude multi-laboratoires, en aveugle, sur aliquotes identiques et avec contrôles de revêtements WTC documentés.

## 5. Deux erreurs importantes du document 911facts.dk

Le document secondaire conserve quelques contre-questions utiles, mais ne doit pas servir d'autorité :

1. il affirme que l'article Harrit ne conclut pas à la nanothermite, alors que sa conclusion finale le dit explicitement;
2. il traite l'absence de mention USGS comme une exclusion, alors que les méthodes USGS de chimie globale n'étaient pas conçues pour sélectionner et identifier des fragments énergétiques.

Il confond également la collecte des poussières en 2001 avec leur transfert ultérieur à l'équipe de Jones. Les critiques valides doivent être conservées; ces erreurs doivent être écartées.

## 6. Relation avec l'audit de poussières DUST-V1

L'audit antérieur reste inchangé :

- les trois dépôts Lioy contiennent 30 à 38 % de leur masse sous 75 µm;
- le seuil 100 µm n'a pas été mesuré; les moyennes de 40,074 % et 44,477 % sous 100 µm sont des interpolations conditionnelles, pas des observations;
- la fraction PM2,5 du tableau étudié est seulement de 0,88 à 1,30 % de la masse;
- une fraction de fragments dans une poussière sélectionnée ne peut pas être multipliée par une masse hypothétique de tours sans modèle de prélèvement, dépôt et représentativité.

Le proxy déjà calculé à partir de 0,1 % et 1,5-7,5 kJ/g donne 1,5-7,5 kJ par kg de poussière **séparée**, sous application littérale. Ce n'est ni une mesure de l'énergie totale, ni une preuve de fragmentation, ni une exclusion mathématique de toute contribution chimique.

## 7. Provenance et usage du schéma d'effondrement

L'image locale est la figure 3 de la discussion de Jonathan H. Cole publiée en juillet 2023 :

https://www.journalof911studies.com/wp-content/uploads/2023/07/Cole_Le-Bazant-JSE-Discussion_July-2023.pdf

Une version HTML est publiée par IC911 :

https://ic911.org/journal/articles/discussion-of-spontaneous-collapse-mechanism-of-world-trade-center-twin-towers-and-progressive-collapse-in-general-by-jia-liang-le-and-zdenek-bazant/

Le document indique que la discussion avait auparavant été refusée par le *Journal of Structural Engineering* pour contenu technique jugé insuffisant. Cette provenance n'annule pas la question visuelle, mais réduit le poids du schéma comme preuve mécanique.

Usage correct : traiter les quatre stades comme une **hypothèse de segmentation vidéo**. Il faudrait revenir aux vidéos sources, calibrer temps et géométrie, suivre avec incertitude le toit, les façades et les éléments du noyau, puis comparer ces courbes à des prédictions. Le dessin seul ne doit pas devenir une condition imposée au solveur.

## 8. Conséquence immédiate pour WTC1

**Aucune modification physique de la simulation.**

- L'état validé du harnais reste la référence.
- La prochaine itération structurelle reste celle déjà annoncée dans `harness/state.json`.
- Aucun « explosif », « thermite », « nanothermite » ou apport énergétique supplémentaire n'est introduit.
- Si un scénario thermitique est testé plus tard, il devra être une branche hypothétique distincte avec paramètres JSON, plage d'incertitude, bilan de masse-énergie, produits prédits et critères de rejet définis avant calcul.
- Blender reste une visualisation et ne peut valider ce mécanisme.

## 9. Expérience documentaire recommandée avant tout scénario thermitique

Le test décisif ne serait pas une animation 3D, mais un protocole matériel préenregistré :

1. sélectionner plusieurs poussières à provenance documentée et en aliquoter les mêmes particules entre laboratoires;
2. inclure en aveugle des primaires/revêtements WTC attestés, peintures époxy/kaolin/oxyde de fer et thermites de référence;
3. appliquer microscopie optique, SEM-EDS quantifié, FTIR/Raman, XRD et TEM-SAED;
4. distinguer aluminium élémentaire, aluminosilicate et autres phases;
5. effectuer DSC/TGA sous air **et sous atmosphère inerte**, avec analyse des gaz et produits;
6. mesurer vitesse de réaction, pression et résidus avec répétitions et incertitudes;
7. estimer la fraction massique par plan d'échantillonnage, pas par sélection manuelle;
8. publier données brutes, chaîne de garde et critères de décision avant interprétation événementielle.

Sans cela, une simulation de thermite ne ferait que montrer ce que produisent des paramètres choisis, pas ce qui s'est passé.

## 10. Livrables

- `assessment.json` : qualification complète et matrice des affirmations;
- `source_inventory.json` : chemins, dimensions/pages, empreintes et contrôle d'intégrité;
- `evidence_matrix.csv` : une ligne par pièce avec faits, affirmation, limites et effet sur la simulation;
- `claim_matrix.csv` : une ligne par proposition testée;
- `future_archive_sorting_notes.md` : proposition de classement futur, sans déplacement actuel;
- `build_audit.py` : validation reproductible et génération des matrices;
- `run_manifest.json` : empreintes des livrables et frontière avec le harnais.

## Verdict

Ces documents doivent être conservés dans le dossier parce qu'ils posent des questions expérimentales légitimes et rassemblent des données utiles. Leur poids cumulé ne permet toutefois pas d'affirmer qu'une nanothermite a été utilisée au WTC, encore moins d'en déduire quantité, disposition ou rôle structurel. La piste reste testable; elle n'est pas validée.
