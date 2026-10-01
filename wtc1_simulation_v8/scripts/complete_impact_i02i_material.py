"""Prepare report, preservation audit and compact handoff; register only verified artifacts."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02i_material'
CFG=ROOT/'wtc1_simulation_v8/data/impact_i02i_material_predeclaration.json'
SUMMARY=OUT/'verification_r4/summary_i02i_material.json'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_A_HANDOFF.md'
REPORT=OUT/'rapport_impact_i02i_material.md'
NOW=lambda:datetime.now(timezone.utc).isoformat()
def dump(p,v): Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def rel(p): return Path(p).relative_to(ROOT).as_posix()
def validated():
    s=json.loads(SUMMARY.read_text()); old=json.loads((OUT/'preservation_before.json').read_text()); ref=json.loads((OUT/'reference_checks.json').read_text())
    assert s['campaign_pass'] and ref['pass'] and s['finite_checks_passed']==s['finite_checks_total']==145
    assert len(s['cases'])==10 and all(r['checks']['normal_termination'] for r in s['cases'].values())
    failures=[e['path'] for e in old['files'] if sha(ROOT/e['path'])!=e['sha256']]
    assert not failures,failures
    return s,old
def sources():
    cfg=json.loads(CFG.read_text()); src=OUT/'source_snapshots'; src.mkdir(exist_ok=False)
    entries=[]
    for item in cfg['sources']:
        if 'path' in item:
            assert sha(ROOT/item['path'])==item['sha256']; entries.append(item); continue
        url=item['url']; path=src/(item['id']+'.html'); row=dict(item,accessed_utc=NOW())
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'WTC1 research harness bounded source audit'})
            with urllib.request.urlopen(request,timeout=20) as response:
                payload=response.read(1000001)
                if len(payload)>1000000: raise ValueError('1 MB source gate')
            path.write_bytes(payload); row.update(path=rel(path),bytes=len(payload),sha256=sha(path),status='saved_read_only_primary_page')
        except Exception as exc: row.update(status='fetch_failed_web_tool_read_used',error=str(exc))
        entries.append(row)
    for identity,url in [('OPENRADIOSS_REACTION_867','https://github.com/orgs/OpenRadioss/discussions/867'),('OPENRADIOSS_REACTION_2773','https://github.com/orgs/OpenRadioss/discussions/2773')]:
        path=src/(identity+'.html'); row={'id':identity,'url':url,'accessed_utc':NOW(),'use':'maintainer explanation: T01 reaction channels are impulses unless converter differentiates with titles'}
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'WTC1 research harness'}),timeout=20) as response: data=response.read(1000001)
            if len(data)>1000000: raise ValueError('1 MB gate')
            path.write_bytes(data); row.update(path=rel(path),bytes=len(data),sha256=sha(path),status='saved')
        except Exception as exc: row.update(status='fetch_failed_web_tool_read_used',error=str(exc))
        entries.append(row)
    dump(OUT/'source_manifest.json',{'created_utc':NOW(),'sources':entries,'bounded_NASA_pages':[178,179,180,181,182,196],'NASA_convention':'indeterminate in pages actually inspected; no global absence claim','external_writes':False,'archive_modified':False,'live_web_read_date':'2026-10-01'})

def prepare():
    s,old=validated(); sources(); finite=[r for r in s['cases'].values() if r['case']['shell']=='finite']
    metrics={key:max(r['metrics'][key] for r in finite) for key in ['stress_reference_error_fraction','global_energy_residual_fraction','internal_stress_work_error_fraction','independent_boundary_work_error_fraction','plastic_work_reference_error_fraction','maximum_kinetic_to_internal_significant_window']}
    rows=[]
    for name,r in s['cases'].items():
        m=r['metrics']; rows.append(f"| {name} | {m['final_stress_MPa']:.6f} | {m['final_thickness_mm']:.6f} | {m['final_plastic_strain']:.7f} | {m['final_external_work_J']:.8f} | {m['stress_reference_error_fraction']*100:.6f} % | {'pass' if r['pass_all_checks'] else 'échec'} |")
    report=f'''# IMPACT-I02I-A : traction élémentaire LAW36 et conventions

Date : 1er octobre 2026. Étape A numérique terminée ; convention NASA et propagation physique restent non qualifiées. I02I-B, raideurs cohésives fixes, reste à réaliser. Cette étape suit l'état local IMPACT-I02H et ne rejoue pas l'ancien V11H. Branche thermique conservée : V11R vers V11S ; contrôle froid V11F inchangé.

## 1. Faits directement observés / transcriptions

Dix cas neufs d'un élément de coque ont terminé normalement, sans avertissement du préprocesseur ni du moteur. Sept variantes explicites passent 145/145 contrôles ; ensemble des témoins : 193/203. Les dix échecs appartiennent aux trois témoins legacy/small, ils sont conservés. Huit contrôles de campagne passent ; ce total vérifie la clôture bornée et conserve les échecs des témoins.

333 fichiers antérieurs épinglés par les manifestes I02H sont vérifiés inchangés, dont les références ciblées V11F/V11R/I02G. Aucune relance de ces calculs, aucun examen de vidéo ou nouvelle exploration d'archive. L'archive source n'a pas été parcourue. Les copies sources locales sont lues seulement.

## 2. Sources primaires / résultats de modèles officiels

Les pages PDF 178–182 et 196 du [manuel NASA STAGS](https://ntrs.nasa.gov/api/citations/20060008654/downloads/20060008654.pdf) ont été examinées ; la page 181 a aussi été revue visuellement dans le rendu sauvegardé. Table 15 imprime 0,15/0,4 ; le jeu imprime 0,015/0,04. Aucun texte de ces pages ne spécifie explicitement nominal/vrai. On conserve les valeurs MPa d'I02H et les décimales du jeu ; la différence entre MPa arrondis et psi reste ouverte. Le panneau de ce manuel est distinct du coupon générique utilisé ici. Aucun résultat de modèle officiel du WTC n'est ajouté.

La [caractérisation Altair](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tensile_test_example_law_characterization_r.htm) explique la transformation nominale/vraie et la soustraction de la part élastique. La [définition de coque](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type1_shell_starter_r.htm) distingue QEPH, petites/grandes déformations, épaisseur et plasticité plane. [LAW36](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law36_plas_tab_starter_r.htm) fournit la syntaxe de l'écrouissage tabulé. Ces sources définissent une méthode numérique ; elles n'identifient pas un matériau de production Boeing.

Les explications des développeurs OpenRadioss [discussion 867](https://github.com/orgs/OpenRadioss/discussions/867) et [discussion 2773](https://github.com/orgs/OpenRadioss/discussions/2773) identifient les impulsions stockées dans T01. Un fichier sans /TH/TITLE présente des colonnes génériques et n'entraîne pas leur dérivation automatique. Les réactions brutes de ces essais sont donc J(t) en N·ms. La force moyenne d'intervalle est ΔJ/Δt en N. Ce constat est vérifié numériquement ici, sans extrapoler aveuglément ce diagnostic à tous les types d'éléments.

## 3. Affirmations issues des archives

Aucune nouvelle affirmation d'archive, identification de mécanisme, de composant ou d'alliage du WTC n'est introduite. Les entrées historiques gardent leurs propres réserves.

## 4. Hypothèses, propriétés et unités

Patch homogène générique 10 × 10 × 2,3 mm ; masse 0,6394 g, volume initial 230 mm³. E = 71 400 MPa ; ν = 0,3 ; ρ = 0,00278 g/mm³. Unités du solveur : g–mm–ms, N, MPa, N·mm ; 1 N·mm = 0,001 J. Les cinq couples source sont (0,00483 ; 345), (0,015 ; 390), (0,04 ; 430), (0,1 ; 470), (0,16 ; 491), avec déformation sans unité et contrainte en MPa. Graine 1102009, aucun tirage.

Deux hypothèses neuves restent séparées :

- interprétation nominale : e = ln(1 + εnom), σ = σnom(1 + εnom), p = max(0, e − σ/E) ;
- interprétation vraie totale : e = εsource, σ = σsource, p = max(0, e − σ/E).

Le premier p est légèrement négatif (arrondis et choix de E), puis ramené à zéro explicitement dans `generation.json`. Cela introduit une petite modification au voisinage du premier point ; aucun point postélastique n'est ajusté. Le plateau ajouté à p=1 est une continuation de syntaxe seulement : aucun essai ne dépasse le dernier point source plastique. La formule de conversion nominale/vraie suppose une déformation uniforme et un volume approximativement conservé ; le changement élastique de volume explique une partie du faible écart nominal. Elle ne reconstitue pas la striction d'un essai réel.

Coque QEPH Ishell=24, cinq points en épaisseur. Options explicites : Ismstr=4, Ithick=1, Iplas=1. Témoin hérité : Ismstr=-1, champs épaisseur/plasticité omis ; le listing résout Ismstr=2, ITHK=0, IPLAS=0. Témoin petit déplacement : Ismstr=1, Ithick=2, Iplas=2. Il s'agit d'une comparaison de groupes d'options : elle n'isole pas individuellement Iplas et Ithick. Les essais explicites qualifient seulement la combinaison déclarée dans ce patch homogène.

Appui x nul à gauche ; déplacement x imposé à droite ; un nœud bloque la translation y ; contraction y libre, mouvement hors plan et rotations bloqués. Rampes quintiques à vitesse nulle aux jonctions, segments 2 ms, paliers 0,2 ms ; un témoin à durée double et un à facteur de pas 0,45 au lieu de 0,9. Aucun ajout de masse ni rupture. Cycle élastique 0 → 0,002 → 0 ; cycles plastiques : charge jusqu'au dernier point, décharge visant environ 50 MPa, recharge au même maximum. La loi et son historique ne sont jamais remplacés.

## 5. Résultats dérivés et vérification

La référence uniaxiale résout σ = E(e − p) et σ = f(p) par segments linéaires. p est engagé irréversiblement ; en décharge la réponse est élastique à p constant. Quatre contrôles analytiques indépendants passent : traction/cycle parfaitement plastique, écrouissage linéaire et reproduction des nœuds source pour les deux interprétations.

| Cas | σ finale MPa | épaisseur mm | p finale | Wext finale J | erreur σ / pic référence | marque |
|---|---:|---:|---:|---:|---:|---|
{chr(10).join(rows)}

À même allongement nominal de 10 %, les deux interprétations explicites donnent 516,998 contre 466,934 MPa : sensibilité d'environ 9,7 %, pas choix d'une vérité mesurée. Le témoin ENG_LEGACY atteint 548,560 au lieu d'environ 569,560 MPa, avec p=0,119519 contre 0,140443. Le bilan global ferme pourtant : la fermeture énergétique seule ne qualifie pas la réponse constitutive. Les résultats I02H sont préservés mais leur carte/options héritées ne doivent plus recevoir un crédit de matériau qualifié.

### Travail, réactions et dissipation

Trois calculs indépendants sont confrontés : énergie globale du solveur ; travail intérieur reconstruit depuis les contraintes et les changements du Jacobien du patch ; travail des appuis depuis les seules impulsions nodales et déplacements. Le travail intérieur d'un intervalle utilise la contrainte moyenne, sym(ΔJgéom·Jgéom_moy⁻¹) et le volume courant moyen. En petites déformations, Jacobien et volume initiaux sont utilisés. Les contraintes sont projetées depuis le repère de coque. Le travail des appuis vaut Σn (ΔJn/Δt)·Δun ; les degrés bloqués ont un déplacement nul. Pas de multiplication directe de l'impulsion par le déplacement.

La référence de dissipation plastique est ∫σ(p) V(p) dp, avec V(p) = V0 exp[(1−2ν)σ(p)/E] pour l'état uniaxial explicite, ou V0 dans le témoin small. Cette correction élastique de volume appartient au modèle de référence et n'est pas une mesure réelle. La part stockée sauvegardée vaut IE − travail plastique ; elle n'est pas confondue avec Gf ni une énergie de fissure.

ENG_FINITE : Wext = 16,312730 J, IE = 16,312330 J, travail plastique = 15,786080 J, part stockée par différence = 0,526250 J. Référence plastique = 15,786107 J ; travail des appuis dérivé = 16,313556 J. En recharge, le travail plastique final reste 15,786080 J ; aucun accroissement de p lors de la décharge/recharge sous le maximum. L'essai élastique retourne à p=0 et conserve un petit résidu numérique ; sa normalisation utilise le pic d'énergie du cycle, pas son travail net presque nul.

Maximum des sept cas explicites, normalisé par leur pic de référence ou leur excursion énergétique propre :

- contrainte : {metrics['stress_reference_error_fraction']*100:.6f} % ;
- bilan Wext − IE − KE : {metrics['global_energy_residual_fraction']*100:.6f} % ;
- travail intérieur reconstruit : {metrics['internal_stress_work_error_fraction']*100:.8f} % ;
- travail indépendant des appuis : {metrics['independent_boundary_work_error_fraction']*100:.6f} % (cycle élastique, faible énergie) ;
- travail plastique de référence : {metrics['plastic_work_reference_error_fraction']*100:.6f} % ;
- KE/IE dans la fenêtre IE > 1 % du pic : {metrics['maximum_kinetic_to_internal_significant_window']*100:.6f} %.

À déformation commune, demi-pas : écart σ/pic 0,002576 % ; durée double : 0,012267 %. L'impulsion brute finale est multipliée par {s['comparisons']['raw_reaction_duration_ratio']:.6f} quand la durée double, tandis que contrainte et travail restent proches. Cela confirme son caractère cumulatif. Les réactions dérivées sont des moyennes d'intervalle ; leur précision instantanée reste limitée par l'échantillonnage. Les sorties demandées tous les 0,002 ms sont émises aux cycles du solveur (jusqu'à environ 0,003 ms), et le dernier échantillon précède légèrement la fin demandée. Aucun saut de fracture n'est simulé.

## 6. Contradictions, informations manquantes et prochaine étape

Convention NASA : indéterminée dans la lecture bornée ; la différence Table 15/jeu n'est pas effacée. Le témoin à petites déformations et les deux témoins hérités échouent à la référence constitutive ; ils ne sont pas promus. La combinaison explicite passe dans un élément homogène, sans qualifier torsion, flexion, grandes rotations, localisation ou fracture.

Les préflights ENG_FINITE_R1 et R2 sont conservés avec leurs configurations/générateurs : champs de contrainte par couche non disponibles dans ce runtime isotrope et colonnes réservées/Istrain incompatibles. Aucun moteur lancé. R3 omet Istrain, le listing confirme son défaut actif ; il utilise les contraintes moyennes F1/F2/F12. Leur ordre de stockage canonique est vérifié par les valeurs initiales, l'épaisseur, la cinématique E1 et l'énergie IEM. Les diagnostics de lecture partiels verification_r1/r2 et la sortie r3 avant correction du journal final sont conservés. R4 est l'audit publié, sans relance solveur.

Next : IMPACT-I02I-B. Utiliser des états neufs avec options explicites et deux conventions séparées ; fixer Kn/Kt par unité d'aire indépendamment du maillage et du matériau ; trois résolutions locales, témoin sans propagation. Pré-déclarer domaines communs de déplacement/avance, énergie, inertie, fréquence de sortie, coûts et arrêts. Sensibilités Gf=15/30/60 restent hypothétiques. Examiner les historiques au-delà du seul premier seuil. Vérifier chaque canal force/impulsion avant de l'intégrer ; ne modifier aucune sortie historique.

Une température imposée n'est pas un incendie calculé. Flexion/localisation après fracture complète non validées. Aucun résultat ne démontre pénétration réelle, état d'une aile Boeing, stabilité ou effondrement du WTC1. Blender reste une visualisation ; il n'a pas été exécuté.

## Reproductibilité et livrables

Configuration : `wtc1_simulation_v8/data/impact_i02i_material_predeclaration.json`. Pilote, auditeur, tests de référence et clôture sous `wtc1_simulation_v8/scripts/`, suffixe `impact_i02i_material.py`. Dix dossiers R3 contiennent les jeux, T01, CSV bruts, journaux et temps ; 18,475445 s de solveur/conversion au total (CPU un thread). Python 3.14.3, NumPy 2.4.6, Pillow 12.2.0 ; runtime OpenRadioss local v20260728-win64, empreintes des trois exécutables dans chaque `execution.json`.

L'audit publié est `verification_r4/summary_i02i_material.json`, avec historiques et réactions par intervalle dans les sous-dossiers. Synthèse : `verification_r4/synthese_i02i_material.png`. Les empreintes des entrées, anciens fichiers ciblés et sorties sont dans `artifact_manifest.json` et `publication_verification.json`. Pour revérifier le cache, utiliser le mode `--verify` du script de clôture. Ne relancer aucun solveur ; une réanalyse de CSV doit utiliser un nouveau dossier avec `--output`.
'''
    REPORT.write_text(report,encoding='utf-8',newline='\n')
    HANDOFF.write_text('''# WTC1 : IMPACT-I02I-A terminée, prochaine IMPACT-I02I-B

Lire AGENTS.md puis harness/state.json, ce fichier et la publication_verification.json indiquée ci-dessous. L'état local fait autorité. V8H/V11H sont historiques ; branche thermique préservée V11R → V11S, contrôle froid V11F inchangé. Pas de reprise du feu ici.

## Acquis bornés à réutiliser

- Dix tractions neuves homogènes d'une coque QEPH ; 7 variantes explicites, 145/145 critères pass ; 193/203 avec les trois témoins rejetés. Campagne 8/8. Quatre contrôles analytiques de référence passent. Pas de fracture, avion ou façade.
- Options explicites vérifiées : Ishell=24, Ismstr=4, Ithick=1, Iplas=1, cinq points en épaisseur. Déformation vraie, contraction/épaisseur variables. Ce groupe d'options est qualifié uniquement pour la traction homogène testée ; les contributions individuelles des options ne sont pas isolées.
- Erreur σ max 0,028203 % ; énergie globale 0,002790 % ; travail intérieur 0,00007141 % ; travail indépendant des appuis 0,213157 % (cycle élastique à faible énergie). Demi-pas σ 0,002576 % ; durée double 0,012267 %.
- ENG_LEGACY hérite des champs I02H : σ finale 548,560 vs 569,560 MPa ; p 0,119519 vs 0,140443. Bilan énergétique fermé mais réponse constitutive non qualifiée. Préserver I02H, ne pas le promouvoir.
- Convention NASA toujours indéterminée. Hypothèses nominale et vraie totale testées séparément ; à 10 % nominal, σ=516,998 / 466,934 MPa. Ne choisir aucune branche par ressemblance au comparateur. Décimales .015/.04 du jeu retenues, différence MPa/psi ouverte.
- Les REAC bruts de ces CSV sans TH/TITLE sont des impulsions N·ms. Force d'intervalle = ΔJ/Δt ; travail = Σ(ΔJ/Δt)·Δu, bilans vérifiés indépendamment. L'impulsion double avec la durée. Ne pas appliquer aveuglément cette correction à tout canal/type d'élément : vérifier chaque sortie.

## Prochaine IMPACT-I02I-B

1. États entièrement neufs, options explicites et deux interprétations séparées. Ne changer ni E ni la loi dans un état endommagé.
2. Fixer Kn/Kt par unité d'aire indépendamment de h et du matériau ; trois maillages locaux + témoin sans propagation. Pré-déclarer domaines communs de déplacement/avance, critères d'énergie/inertie, fréquence de sortie et arrêt à la frontière raffinée.
3. Comparer forces, travail et CTOA à déplacement/avance communs, puis pas/vitesse au-delà du premier seuil. Gf15/30/60 restent des sensibilités, aucune calibration cachée.
4. Déclarer le coût avant une campagne longue. Pas de transfert physique à l'avion/façade tant que matériau et propagation restent non qualifiés.

## Chemins et contrôle rapide

Dossier : wtc1_simulation_v8/output/impact_i02i_material/.
Rapport : rapport_impact_i02i_material.md. Audit final : verification_r4/summary_i02i_material.json ; historiques/forces d'intervalle sous verification_r4/<cas>/ ; source_manifest.json ; artifact_manifest.json ; publication_verification.json.
Configuration : wtc1_simulation_v8/data/impact_i02i_material_predeclaration.json.
Scripts : run_impact_i02i_material.py, audit_impact_i02i_material.py, test_impact_i02i_material.py, complete_impact_i02i_material.py.

```powershell
./harness/tools/Test-WtcHarness.ps1
$env:PYTHONDONTWRITEBYTECODE='1'
& C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_material.py --verify
```

333 anciens fichiers ciblés conservés, aucune relance I02H/V11F/V11R. Préflights R1/R2 rejetés et diagnostics d'audit conservés ; R3 accepté, audit R4 publié. Solveur/conversion : 18,475445 s. Archives/sources en lecture seule. Température imposée ≠ incendie calculé ; flexion/localisation après fracture complète non validées ; tests numériques ≠ événement réel ; Blender reste visualisation.
''',encoding='utf-8',newline='\n')
    dump(OUT/'release_audit.json',{'pass':True,'created_utc':NOW(),'checks':{'bounded_campaign':True,'reference_checks':True,'previous_hashes':True,'report_present':REPORT.exists(),'handoff_present':HANDOFF.exists()},'previous_files_verified':len(old['files']),'scientific_limits':{'source_convention_verified':False,'propagation_qualified':False,'I02I_B_complete':False},'rejected_attempts':['ENG_FINITE_R1','ENG_FINITE_R2','verification_r1','verification_r2'],'verification_r3_note':'complete saved output, console JSON serialization failed; corrected r4 replay only CSV, no solver rerun'})
    print(json.dumps({'prepared':True,'previous_files_verified':len(old['files'])}))

def manifest():
    paths=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ['artifact_manifest.json','publication_verification.json']]
    paths += [CFG,HANDOFF,ROOT/'wtc1_simulation_v8/scripts/run_impact_i02i_material.py',ROOT/'wtc1_simulation_v8/scripts/audit_impact_i02i_material.py',ROOT/'wtc1_simulation_v8/scripts/test_impact_i02i_material.py',ROOT/'wtc1_simulation_v8/scripts/extract_impact_i02i_source_pages.py',Path(__file__).resolve()]
    entries=[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(paths))]
    dump(OUT/'artifact_manifest.json',{'created_utc':NOW(),'files':entries,'exclusions':['artifact_manifest.json self-hash','publication_verification.json post-registration audit'],'scope':'new artifacts, raw accepted/rejected attempts, cached verification outputs and source snapshots; historical protected files in preservation_before.json'})
def harness():
    exe='pwsh.exe'
    script="& './harness/tools/Test-WtcHarness.ps1' | ConvertTo-Json -Depth 5"
    p=subprocess.run([exe,'-NoProfile','-Command',script],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
    if p.returncode: raise RuntimeError(p.stderr or p.stdout)
    data=json.loads(p.stdout); assert data['Status']=='PASS'; return data
def register():
    s,old=validated(); assert REPORT.exists() and HANDOFF.exists() and json.loads((OUT/'release_audit.json').read_text())['pass']
    before=harness(); dump(OUT/'harness_after_artifacts_before_registration.json',before)
    statepath=ROOT/'harness/state.json'; regpath=ROOT/'harness/experiments/registry.jsonl'
    assert sha(statepath)==sha(OUT/'before_state.json') and sha(regpath)==sha(OUT/'before_registry.jsonl'),'Concurrent state/registry changes; do not overwrite'
    state=json.loads(statepath.read_text()); assert state['current_iteration']=='IMPACT-I02H' and state['next_iteration']=='IMPACT-I02I'
    manifest()
    when=NOW(); record={'experiment_id':'WTC1-IMPACT-I02I-A','registered_at':when,'status':'completed_bounded_material_stage_with_unresolved_source_convention_and_deferred_fixed_penalty_campaign','configuration':rel(CFG),'report':rel(REPORT),'results':rel(SUMMARY),'handoff':rel(HANDOFF),'source_manifest':rel(OUT/'source_manifest.json'),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'release_audit':rel(OUT/'release_audit.json'),'publication_verification':rel(OUT/'publication_verification.json'),'cases':10,'finite_cases':7,'finite_checks_passed':145,'finite_checks_total':145,'all_case_checks_passed':193,'all_case_checks_total':203,'campaign_checks_passed':8,'campaign_checks_total':8,'old_files_preserved':333,'source_convention_verified':False,'physical_propagation_qualified':False,'cold_V11F_preserved':True,'thermal_V11R_preserved':True,'next_iteration':'IMPACT-I02I-B','caveat':'Only fresh homogeneous explicit QEPH tension qualified. Three inherited/small controls retain ten failed constitutive gates. NASA nominal/true convention remains ambiguous. Fixed-penalty mesh/propagation and Gf campaign not performed.'}
    prefix=regpath.read_bytes(); assert prefix.endswith(b'\n')
    with regpath.open('ab') as f: f.write((json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8'))
    state.update(updated_at=when,current_iteration='IMPACT-I02I-A',current_status=record['status'],next_iteration='IMPACT-I02I-B',next_objective='À partir d’états neufs, utiliser les options QEPH explicites vérifiées (Ismstr4, Ithick1, Iplas1) et deux interprétations NASA séparées ; fixer Kn/Kt par unité d’aire indépendamment de h et du matériau ; comparer trois maillages locaux avec contrôle sans propagation à déplacement/avance communs. Pré-déclarer énergie, inertie, pas/vitesse, domaine raffiné et coût. Gf15/30/60 restent hypothétiques ; convention source et propagation physique non qualifiées. Vérifier les canaux force/impulsion avant intégration. Branche thermique V11R/V11S et contrôle froid V11F préservés.')
    state['impact_i02i_a_key_results']={k:record[k] for k in ['cases','finite_cases','finite_checks_passed','finite_checks_total','all_case_checks_passed','all_case_checks_total','campaign_checks_passed','campaign_checks_total','old_files_preserved','source_convention_verified','physical_propagation_qualified','cold_V11F_preserved','thermal_V11R_preserved']}
    state['impact_i02i_a_key_results'].update(maximum_stress_reference_error_fraction=0.0002820295103029352,maximum_global_energy_residual_fraction=0.000027895286535161967,raw_reaction_is_impulse_in_untitled_unit_test_CSV=True,I02I_B_performed=False,solver_execution_seconds=s['accepted_solver_execution_seconds'],source_interpretations_at_nominal_0p10_mpa=s['comparisons']['interpretations_at_engineering_strain_0p10'])
    va=state['validated_artifacts']; va['latest_material_translation_configuration']=rel(CFG); va['latest_material_translation_report']=rel(REPORT); va['latest_material_translation_summary']=rel(SUMMARY); va['latest_material_translation_handoff']=rel(HANDOFF); va['latest_material_translation_publication_verification']=rel(OUT/'publication_verification.json')
    limitation='I02I-A fresh uniaxial checks reveal that inherited I02H default plane-stress/thickness options fail the simple constitutive reference despite energy closure; only explicit Ismstr4/Ithick1/Iplas1 passes this homogeneous patch. NASA nominal/true convention remains indeterminate and fixed-penalty propagation has not been performed. Old outputs remain immutable numerical diagnostics.'
    if limitation not in state['open_limitations']: state['open_limitations'].append(limitation)
    temp=ROOT/'harness/state_i02i_a_pending.json'; dump(temp,state); temp.replace(statepath)
    check=verify(write=True); print(json.dumps(check,indent=2))
def verify(write=False):
    s,old=validated(); ma=json.loads((OUT/'artifact_manifest.json').read_text()); failures=[v['path'] for v in ma['files'] if sha(ROOT/v['path'])!=v['sha256']]
    state=json.loads((ROOT/'harness/state.json').read_text()); reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes(); oldreg=(OUT/'before_registry.jsonl').read_bytes(); newlines=reg[len(oldreg):].decode().splitlines(); records=[json.loads(v) for v in reg.decode().splitlines() if v.strip()]
    hv=harness(); oldstate=json.loads((OUT/'before_state.json').read_text()); oldkeys=['v11f_key_results','v11r_key_results','deferred_thermal_branch','impact_i02h_key_results','source_archive','evidence_policy']
    checks={'manifest_hashes':not failures,'old_files_preserved':True,'registry_prefix_preserved':reg.startswith(oldreg),'exactly_one_new_record':len(newlines)==1 and json.loads(newlines[0])['experiment_id']=='WTC1-IMPACT-I02I-A','single_registry_record':sum(v['experiment_id']=='WTC1-IMPACT-I02I-A' for v in records)==1,'correct_state':state['current_iteration']=='IMPACT-I02I-A' and state['next_iteration']=='IMPACT-I02I-B','cold_thermal_prior_results_preserved':all(state[k]==oldstate[k] for k in oldkeys),'harness_pass':hv['Status']=='PASS','bounded_science':s['campaign_pass'] and not s['source_convention_verified'] and not s['physical_propagation_qualified'],'report_handoff_exist':REPORT.exists() and HANDOFF.exists()}
    result={'created_utc':NOW(),'pass':all(checks.values()),'checks':checks,'manifest_files_checked':len(ma['files']),'manifest_failures':failures,'prior_files_checked':len(old['files']),'harness':hv,'scientific_case_checks':'145/145 finite; 193/203 all; three rejected constitutive controls retained','source_convention_verified':False,'physical_propagation_qualified':False,'next_iteration':'IMPACT-I02I-B'}
    if write: dump(OUT/'publication_verification.json',result)
    assert result['pass'],result; return result
def main():
    p=argparse.ArgumentParser(); g=p.add_mutually_exclusive_group(required=True); g.add_argument('--prepare',action='store_true'); g.add_argument('--register',action='store_true'); g.add_argument('--verify',action='store_true'); a=p.parse_args()
    if a.prepare: prepare()
    elif a.register: register()
    else: print(json.dumps(verify(),indent=2))
if __name__=='__main__': main()
