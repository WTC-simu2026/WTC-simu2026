# Reprise WTC 1 — V11G terminée, prochaine V11H

## Reprise courte

Lire intégralement `AGENTS.md`, puis `harness/state.json` et ce document. L'état fait autorité ; le point V8H d'AGENTS est historique. Exécuter `harness/tools/Test-WtcHarness.ps1` depuis la racine active :

`C:\Users\jeuxpc\Documents\Codex\2026-08-13\referenced-chatgpt-conversation-this-is-an`

Archives et `work/official_sources/` restent en lecture seule. Ne pas relire toute l'histoire, rescanner les archives ou analyser des vidéos sans besoin ciblé. Jeremy demande un prototype réaliste avec hypothèses explicites, pas une conclusion pré-écrite ; l'absence de données parfaites ne bloque pas tout calcul exploratoire.

## Ajout V11G

Un benchmark longitudinal à une seule fissure sélectionnée vérifie l'énergie de fracture et sa régularisation au maillage. Une relecture des forces de V11F vérifie en parallèle l'équilibre local de la dalle. La mécanique et les sorties V11F, le calcul global V11B et Blender restent inchangés. La stratégie à fissure sélectionnée n'a PAS été intégrée comme rupture complète du panneau.

81/81 contrôles numériques passent ; 16 parcours de barre, 3 920 états de référence, répétition exacte et demi-pas. Huit témoins de dommage uniforme forcé sont rejetés comme interprétation d'une seule fissure. Les 42 états terminaux de panneau (14 cas × 3 maillages) ont été relus. Les 14 cas au maillage fin passent les seuils locaux choisis. Un audit des fichiers, sans importer le noyau mécanique, apporte 43 contrôles supplémentaires.

## Six catégories de preuve

1. **Constats / transcriptions** : résultats, charges et efforts V11F relus avec leurs empreintes ; pas de nouvel examen d'archive, PDF ou média.
2. **Résultats officiels / méthode** : aucun résultat historique officiel nouveau. Les héritages NIST du panneau conservent leurs limites. Les deux pages primaires DIANA/OpenSees citées au rapport concernent la largeur de bande et l'équilibre faible ; aucun de ces logiciels n'est exécuté.
3. **Archives** : aucune nouvelle affirmation ou identification de mécanisme introduite.
4. **Hypothèses** : barres génériques de 2 m et 8 m, section 0,01 m², 20 °C. Une seule cellule centrale peut fissurer ; le reste est élastique. Géométrie de test, pas composants WTC identifiés. Béton E = 2500 ksi, ft = 1 MPa, Gf = 100 J/m² hérité de V11E ; fc = 3 ksi conservé mais aucune compression appliquée. Pas d'armature ou de chaleur.
5. **Résultats dérivés** : chaque fissure sélectionnée consomme 1 J jusqu'à séparation complète, sur les quatre maillages 9 / 17 / 33 / 65 cellules. Courbes, cycles et bilan de travail sont indépendants du maillage dans les tolérances annoncées.
6. **Inconnues / limites** : la position et le nombre de fissures sont choisis, pas prédits. La localisation en flexion, l'adhérence, les fissures multiples et la fracture complète du panneau restent non validées. Aucun résultat local ne donne une conclusion d'effondrement ou de non-effondrement de la tour.

## Formulation et résultats à conserver

La cellule centrale a h = L/n ; les maillages impairs conservent le plan de fissure à L/2. Le matériau V11E est inchangé. On résout sa compatibilité avec l'ouverture inélastique w = h(ε − σ/E), depuis le dernier état engagé, par Newton encadré. Les autres cellules ont ε = σ/E ; la reconstruction en série impose une même force et vérifie les résidus nodaux.

Comparateur fermé : wc = 2Gf/ft = 0,2 mm ; σ = ft(1 − w/wc) sur l'enveloppe ; P = Aσ ; Δ = Lσ/E + w. Décharge/recharge sécante jusqu'à l'ouverture maximale historique. À séparation complète : énergie stockée nulle, dissipation et travail extérieur net = AGf = 1 J.

Lcrit = 2EGf/ft² = 3,447378647 m. Après le pic, la barre de 2 m poursuit son déplacement total croissant ; celle de 8 m retourne en déplacement (snapback). L'ouverture est un paramètre numérique de continuation, pas un actionneur intérieur au travail oublié. Suivre cette branche d'équilibre ne démontre pas sa stabilité sous un chargement physique libre ou sa dynamique.

Parcours : préchargement élastique au pic, puis monotone 0 / wc / 1,1wc ; cycle 0 / 0,75wc / 0 / 0,75wc / wc / 1,1wc. Les sommets sont inclus. Le travail est calculé par P·dΔ indépendamment de l'identité matériau W = U + D. Normalisations physiques : force Aft, déplacement wc, énergie AGf, sans plancher arbitraire de 1 J.

Maximum sur référence, répétition et demi-pas :

- écart force au comparateur / Aft : 3,783497959e−16 ;
- écart déplacement / wc : 4,336808690e−15 ;
- résidu d'équilibre nodal / Aft : 1,509761205e−14 ;
- identité d'énergie / AGf : 2,775557562e−15 ;
- écart du travail extérieur / AGf : 8,437694987e−15.

L'audit de relecture reconstruit cette fois l'intégralité du travail extérieur de la barre depuis les historiques force/déplacement : écart au registre sauvegardé nul, écart Wext − U − D au plus 8,430756093e−15 relatif à AGf. Ce n'est pas une validation expérimentale externe.

### Témoin de fissuration uniforme forcée

Toutes les cellules partagent une déformation homogène et leurs g points d'intégration partagent le même champ axial. Avec Lch = L/(n·g), la dissipation totale vaut n·g·AGf : 9 / 18 / 17 / 34 / 33 / 66 / 65 / 130 J dans les huit témoins. L'énergie de chaque bande est correcte, mais leur somme ne représente pas une seule fissure. Deux points de Gauss dans une même cellule ne sont pas automatiquement deux fissures physiques.

Ce témoin ne prédit pas une localisation spontanée : il impose volontairement une branche homogène. La réussite du cas à fissure centrale ne prouve pas non plus que la fissure du plancher réel serait centrale ou unique. Ne pas transférer sa dissipation comme résistance globale.

### Équilibre local du panneau V11F

Sur la dalle : forces opposées à celles des ressorts de contact et d'attaches ; couple −e·F pour chaque attache horizontale ; gravité uniforme ; réaction d'actionneur seulement pour un actionneur appliqué à la dalle. Ne jamais appliquer une seconde fois à la dalle l'actionneur du treillis.

À une coupe x : N = −ΣFx à gauche ; M = ΣFy(x − xi) − ΣC + qx²/2. Comparer ces efforts équilibrés aux N/M constitutifs aux mêmes points de Gauss. Reconstruire séparément l'équilibre faible aux nœuds et les trois bilans globaux de dalle. Les efforts récupérés ne remplacent pas les contraintes constitutives et n'apportent aucune énergie supplémentaire.

Écart axial maximal, divisé par le pic du champ N équilibré, sur les maillages 2 / 4 / 8 : 2,331305 % / 1,497616 % / 0,813986 %. Tous les cas sont sous le seuil déclaré de 5 % au maillage fin. Le résidu nodal maximal reconstruit vaut 7,379007919e−12. Les cas sont comparés à leur état terminal propre, pas exactement au même déplacement final.

**Attention à l'échantillonnage des moments.** Les erreurs M aux points de Gauss sont presque nulles par construction : avec q constant, le moment quadratique équilibré et son interpolant linéaire coïncident aux deux Gauss. Cela ne valide pas les moments entre les points. Leur écart aux extrémités vaut |q|·dx²/12 et atteint 353,001201 / 88,250300 / 22,062575 N·m aux trois maillages. C'est un diagnostic d'interpolation, PAS une contrainte postfissurée réelle récupérée entre les points. Le test supplémentaire et cet avertissement ont été ajoutés après le premier calcul, sans modifier les seuils ni les barres.

## Livrables, empreintes et reprise rapide

Sorties : `wtc1_simulation_v8/output/v11g_localization/`, avec rapport `rapport_v11g_localisation.md`, résultats `results_v11g.json` et figure `synthese_v11g_localisation.png`. Historique complet dans `bar_paths.json` et `bar_half_step_paths.json` ; témoins dans `uniform_damage_controls.json` ; comparaison locale complète dans `panel_equilibrium_recovery.json` ; unités dans `material_input_ledger.json`.

Configuration : `wtc1_simulation_v8/data/v11g_localization_predeclaration.json`. Scripts, sous `wtc1_simulation_v8/scripts/` : `v11g_localization_model.py`, `run_v11g_localization.py`, `test_v11g_localization.py`, `audit_v11g_release.py`.

Empreinte numérique complète finale : `e3c1098f7377909d8bf56471258e6a5f872108282f6f5415342127fef37b4011`.

Calcul final 6,2958577 s sur CPU ; Python 3.14.3, NumPy 2.4.6, Pillow 12.2.0, `OPENBLAS_NUM_THREADS=1`. Graine 1101007, aucun tirage. `attempt02` est publié byte-identiquement, 12 fichiers. Le manifeste vérifie 10 sorties et 43 entrées/protégés ; il exclut sa propre empreinte et l'audit de relecture ajouté ensuite, épinglés par le registre avec le handoff.

`tmp/v11g_localization/attempt01` est conservé avant l'ajout du diagnostic entre points de Gauss et du 81e contrôle. Les quatre fichiers de barre/demi-pas/témoins/unités sont identiques aux fichiers finaux ; l'empreinte globale change car la sortie de panneau est enrichie. Les empreintes de code initiales ne correspondent plus au pilote final. Ne pas le promouvoir ni le supprimer.

```powershell
./harness/tools/Test-WtcHarness.ps1
$env:PYTHONDONTWRITEBYTECODE='1'
& C:/Python314/python.exe wtc1_simulation_v8/scripts/audit_v11g_release.py --directory wtc1_simulation_v8/output/v11g_localization
```

Une reproduction complète, si nécessaire, utilise le pilote avec un nouveau `--output tmp/v11g_localization/<nom_inexistant>` et `OPENBLAS_NUM_THREADS=1`. Préférer la vérification du cache ; les anciens dossiers sont refusés. Pas d'installation, GPU, publication externe, revue multi-agent ou Blender dans V11G.

## Prochaine V11H : commencer la thermomécanique bornée

Commencer par dilatation libre/empêchée et gradient de dalle, avec déformations thermiques, unités, propriétés et bilans explicites. Préserver V11F comme référence froide. Une température imposée est un essai thermomécanique, pas un incendie calculé ; le calcul du feu et du transfert de chaleur spatial reste une étape distincte.

Ne pas modifier simplement E ou ft dans la loi fissurée en oubliant les historiques et l'énergie. Vérifier la limite isotherme, les cycles thermiques et le travail des appuis ; si nécessaire, borner d'abord ce couplage au domaine élastique pour qualifier la dilatation et les gradients avant d'étendre la fissuration chauffée. La localisation en flexion après fracture complète reste non validée. Ensuite : géométrie non linéaire/postflambement, assemblages avec colonnes/allèges, impact calculé du 767 et feux résolus spatialement, sans issue prédéfinie.
