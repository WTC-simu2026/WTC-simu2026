"""H durable report/summary, compact I handoff, registration and integrity."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import run_impact_i02i_free_fracture as h
ROOT,OUT=h.ROOT,h.OUT
SUMMARY=OUT/'verification_r1/summary.json'
REPORT=OUT/'rapport_impact_i02i_free_fracture.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_H_HANDOFF.md'
IPLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_i_plan_from_h.json'

def read(p):return json.loads(p.read_text(encoding='utf-8'))

def preservation():
    rows=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in rows if h.sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad;return len(rows)

def prepare():
    assert not REPORT.exists() and not HANDOFF.exists() and not IPLAN.exists() and not SUMMARY.exists(),'Keep artifacts'
    e=read(OUT/'elastic_verification_r1/summary.json');n=read(OUT/'fracture_verification_r1/summary.json');ref=read(OUT/'reference_verification.json')
    cfg=read(h.FRACCFG);ecfg=read(h.ELCFG);hv=h.harness();count=preservation()
    assert e['all_checks_pass'] and e['strict_raw_1pct_all_pass'] and ref['pass'] and n['all_checks_pass']
    assert h.sha(OUT/'elastic_verification_r1/summary.json')==cfg['elastic_guard_sha256']
    assert h.sha(OUT/'reference_verification.json')==cfg['reference_verified_sha256']
    ex=[r for p in OUT.glob('*/execution.json') for r in read(p)]
    assert len(ex)==12 and all(r['returncode']==0 for r in ex)
    runtime=sum(r['seconds'] for r in ex);assert runtime<=600
    assert all(sum(r['seconds'] for r in read(p))<=90 for p in OUT.glob('*/execution.json'))
    r=ref['parameters'];cases={**e['cases'],**n['cases']}
    s={'iteration':'IMPACT-I02I-H','created_utc':h.NOW(),'cases':cases,
        'case_checks_passed':e['case_checks_passed']+n['case_checks_passed'],
        'case_checks_total':e['case_checks_total']+n['case_checks_total'],
        'comparison_checks_passed':e['comparison_checks_passed']+n['comparison_checks_passed'],
        'comparison_checks_total':e['comparison_checks_total']+n['comparison_checks_total'],
        'reference_checks_passed':sum(ref['checks'].values()),'reference_checks_total':len(ref['checks']),
        'all_declared_checks_pass':True,'strict_raw_elastic_1pct_pass':True,
        'numerical_free_normal_witness_verified':True,'post_failure_numerical_ballistic_verified':True,
        'physical_fracture_calibrated':False,'free_fracture_physically_qualified':False,
        'mixed_mode_qualified':False,'aircraft_impact_qualified':False,'physical_propagation_qualified':False,
        'E_sensitivities_resolved':False,'source_convention_verified':False,'exact_TH_centering_verified':False,
        'runtime_seconds':runtime,'old_solvers_rerun':False,'reference':r,
        'elastic_summary':h.rel(OUT/'elastic_verification_r1/summary.json'),'elastic_summary_sha256':h.sha(OUT/'elastic_verification_r1/summary.json'),
        'normal_summary':h.rel(OUT/'fracture_verification_r1/summary.json'),'normal_summary_sha256':h.sha(OUT/'fracture_verification_r1/summary.json'),
        'configs_sha256':{h.rel(p):h.sha(p) for p in [h.ELCFG,h.FRACCFG]},
        'cached_G_strict_1pct_failures_preserved':8,
        'cached_F_same_row_OFF_FX_failures_preserved':['FIXED_CAP200NS','FIXED_CAP100NS','FIXED_CAP050NS','PROP_CAP100NS','PROP_CAP050NS'],
        'cached_E_review':h.rel(h.g.f.OUT/'cached_E_sensitivity_review.json'),'cached_E_review_sha256':h.sha(h.g.f.OUT/'cached_E_sensitivity_review.json'),
        'qualification':'Four fresh two-node numerical controls; no real joint, plate wavefield, mixed fracture, material calibration or aircraft/facade conclusion'}
    SUMMARY.parent.mkdir();h.dump(SUMMARY,s)
    # I is only a proposed fresh-history follow-up; no I declaration or solve.
    m,k,peak,soft=r['moving_mass_g'],r['k_N_per_mm'],r['peak_N'],r['softening_N_per_mm']
    E20=.5*m*20**2;xturn=math.sqrt(2*(r['normal_total_work_N_mm']-E20)/soft)
    dturn=r['deltaf_mm']-xturn;fturn=soft*xturn;residual=dturn-fturn/k;Uturn=fturn**2/(2*k)
    plan={'id':'IMPACT-I02I-I_PLAN_FROM_H','created_utc':h.NOW(),'seed':1102017,'random_draws':0,
        'saved_H_summary':h.rel(SUMMARY),'saved_H_sha256':h.sha(SUMMARY),
        'scope':'Verify non-separation, history-dependent unloading and rebound before mixed-mode or plate integration',
        'proposed_cases':[
            {'family':'NORMAL_ARREST_RETURN','initial_vY_mm_per_ms':20.,'initial_energy_J':E20*.001,
                'maximum_dt_ms':[.00005,.000025],'proposed_end_ms':.012,
                'expected_no_deactivation':True,'turning_gap_mm':dturn,'force_at_turn_N':fturn,'positive_residual_gap_mm':residual,
                'recoverable_energy_at_turn_J':Uturn*.001,'ideal_release_velocity_mm_per_ms':-math.sqrt(2*Uturn/m),
                'retained_numerical_IE_after_unloading_J':(E20-Uturn)*.001,
                'history':'m=max historical positive gap; unloading F=max(0,F(m)+Kn*(delta-m)), while delta stays positive; derive crossing times and stop before compression'},
            {'family':'NORMAL_SUBPEAK_RETURN','initial_vY_mm_per_ms':math.sqrt(20.),'initial_energy_J':.001,
                'maximum_dt_ms':[.000025,.0000125],'proposed_end_ms':.004,'expected_no_deactivation':True,
                'reason':'Initial energy below elastic-peak energy; reversible elastic return, positive-gap window before first negative gap'}],
        'before_engine':['Derive and independently verify piecewise unloading/zero-force times and energy identities',
            'Verify entire proposed record remains positive gap before compression; shorten end before declaration if needed',
            'Declare raw velocity/force/impulse <=1%, global energy/work <=0.5%; retain actual histories with initial P',
            'Fresh states only, never modify a damaged property or relabel old failed gates'],
        'cost':{'maximum_case_wall_seconds':90,'maximum_campaign_wall_seconds':600,'announce_before_run':True},
        'unchanged':['Both NASA conventions','Gf30 hypothetical, Gf15/60 deferred','All E inertia/angle/coverage limitations',
            'F OFF/FX mixed-phase mismatch','TH/REACX labeling and exact centering unresolved','V11F/V11R and deferred V11S'],
        'deferred':['Mixed-mode free separation','Plate/connection wavefield and physical fracture calibration','Boeing/façade/fire/collapse'],
        'publication':'H pending 1/2; publish H+I after verified I and remote digest/CI checks; F+G baseline preserved'}
    h.dump(IPLAN,plan)
    erows=[];nrows=[]
    for name,v in e['cases'].items():
        a=v['metrics'];erows.append(f"| {name} | {a['maximum_solver_dt_ms']*1e6:g} | {100*a['displacement_fraction']:.7g} | {100*a['nodal_velocity_fraction']:.7g} | {100*a['raw_initial_momentum_impulse_fraction']:.7g} | {100*a['energy_residual_fraction']:.7g} |")
    for name,v in n['cases'].items():
        a=v['metrics'];nrows.append(f"| {name} | {a['OFF_time_ms']:.9g} | {a['final_IE_J']:.9g} | {a['final_KE_J']:.9g} | {a['final_velocity_mm_per_ms']:.9g} | {100*a['raw_impulse_fraction']:.7g} | {100*a['energy_residual_fraction']:.7g} |")
    report=f'''# WTC1 — IMPACT-I02I-H : précision libre et séparation normale libre

## 1. Faits directement observés ou transcrits

Quatre états neufs, 12 exécutables sauvegardés, {runtime:.6f} s cumulées ; limites 90 s/cas et 600 s/campagne respectées. Aucune alerte starter, terminaison normale, pas réel sauvegardé plafonné et une ligne TH par cycle, aucun ajout de masse. Les deux contrôles élastiques sont exécutés et audités avant déclaration des cas de rupture. Le garde dans fracture_declaration_guard.json prouve que leur audit strict et la référence vérifiée existaient avant les deux nouveaux calculs de rupture. Aucun déplacement imposé sur le degré de liberté mobile ; uniquement une vitesse initiale, contraintes transversales et nœud fixe.

Tous les {s['case_checks_total']} critères de cas et {s['comparison_checks_total']} comparaisons déclarés passent, ainsi que les {s['reference_checks_total']} contrôles de référence. Les anciennes sorties de G à 100/50 ns sont réutilisées, sans les recalculer ni changer leurs huit diagnostics stricts échoués.

La définition primaire de /INIVEL, /TH/NODE, /DTIX et TYPE8 est réutilisée depuis les manifestes sources sauvegardés G/F/D ; aucune donnée matérielle précise ajoutée. La documentation appelle REACX/REACY une force alors que cette sortie de la version installée est compatible avec une impulsion cumulative. Les deux lectures et le contrôle indépendant par intégrale de force sont conservés. Le phasage exact du code TH n'est toujours pas établi, aucune série n'est décalée pour réussir un critère.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle NIST/WTC ajouté. La documentation Radioss définit des options de logiciel et non une explication historique. Les deux conventions NASA précédentes restent non identifiées et aucune branche n'est choisie à partir de H.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d'archive, aucune vidéo inspectée. {count} fichiers précédents contrôlés à partir des inventaires sauvegardés, sans archive rescannée ni ancien solveur relancé. V11F froid, V11R et V11S différée conservés. F+G publiée et vérifiée reste la base publique ; le dépôt n'est pas modifié pour H seule.

## 4. Hypothèses propres au modèle, propriétés, unités et références

Deux nœuds coïncidents reliés par une seule liaison TYPE8, aire de référence 1 mm², masse totale 0,2 g répartie 0,1 g/nœud, inertie de rotation 0,001 g mm² et rotations bloquées. Les cartes sont neuves à chaque cas, sans restart, viscosité, ajout de masse ou substitution de propriété endommagée.

Élastique X : Kt=21500 N/mm, v0=1 mm/ms, u0=0, X libre et Y/Z bloqués. Même référence que G : ω=√(k/m), T≈0,0135506659245 ms, durée huit périodes, E0=0,00005 J, P0=0,1 N ms. Tous les champs bruts amplitude/impulsion sont désormais limités à 1 %, énergie/période à 0,5 %. Ratios d'erreur par rapport à G 50 ns attendus en h² pour déplacement/momentum global/énergie, h pour vitesse/impulsion, tolérance relative 10 %. Seuils fixés avant moteur, sans phase ajustée.

Rupture normale Y : Kn=56000 N/mm, pic hypothétique 495 N, Gf=30 N/mm pour aire 1 mm² ; δ0={r['delta0_mm']:.12g} mm, δf={r['deltaf_mm']:.12g} mm. F=kδ jusqu'à δ0 puis F=ks(δf−δ), ks={r['softening_N_per_mm']:.12g} N/mm, jusqu'à désactivation complète. X/Z bloqués, Y libre, v0=30 mm/ms=30 m/s ; cette vitesse appartient au témoin, pas au Boeing. E0=45 N mm=0,045 J > travail normal 30 N mm=0,03 J, garantissant une ouverture monotone dans la référence. Il n'y a aucun réservoir de cisaillement dans cet essai.

Unités : g, mm, ms, N ; N=g mm/ms², N ms=g mm/ms, N mm=mJ, J=0,001 N mm. Dans v(δ)=√(v0²−2W/m), W est en N mm, jamais en J sans conversion. Énergies IE/KE/WE du solveur sont converties par ×0,001. Bilans bruts : J1+J2+P0−P, avec P0=mv0 ; E0+WE−IE−KE, avec U récupérable=F²/(2Kn) en phase active, IE−U rapporté comme travail numérique non récupéré. Aucune dissipation physique mesurée n'est identifiée par IE.

Référence propre : mδ̈=−F(δ). Branche élastique δ=v0 sin(ωt)/ω. Au pic t0={r['peak_time_ms']:.12g} ms, vpic={r['peak_velocity_mm_per_ms']:.12g} mm/ms. Pour τ=t−t0, x=δf−δ=x0 cosh(λτ)−vpic sinh(λτ)/λ, λ=√(ks/m). La séparation survient à tf=t0+atanh(λx0/vpic)/λ={r['failure_time_ms']:.12g} ms. Après séparation : F=0, v=√(v0²−2Gf A/m)={r['post_failure_velocity_mm_per_ms']:.12g} mm/ms et déplacement linéaire. Référence indépendante par quadrature t(δ)=∫dδ/√(v0²−2W(δ)/m), 512/1024/2048/4096 subdivisions par branche. Équation du mouvement, dérivée dW/dδ=F, continuités et énergie contrôlées ; erreur maximale d'identité énergétique {ref['maximum_energy_identity_error_J']:.6g} J.

Critères de rupture déclarés après ces gardes et avant moteur : champs bruts 1 % de leurs amplitudes, bilan et travail 0,5 %, OFF à moins de deux pas du temps analytique, forces nulles après deux lignes, vitesse post-rupture à 1 % et momentum constant, aucun travail externe. Fin demandée 0,012 ms ; dernières lignes 0,012 ms et 0,011975 ms conservées sans extrapolation.

## 5. Résultats dérivés

### Contrôles libres élastiques

| Cas | Pas (ns) | Déplacement (%) | Vitesse nodale (%) | Impulsion brute (%) | Bilan énergie (%) |
|---|---:|---:|---:|---:|---:|
{chr(10).join(erows)}

Les champs bruts passent maintenant tous le seuil 1 % dans ces deux cas neufs. Le résidu d'impulsion décroît encore comme h et les erreurs déplacement/momentum global/énergie approximativement comme h² aux tolérances déclarées. Ce résultat ne réécrit pas les diagnostics de G, ne prouve pas l'algorithme exact de centrage et ne ferme pas les essais mixtes OFF/FX de F.

### Séparation normale libre

| Cas | OFF (ms) | IE finale (J) | KE finale (J) | Vitesse finale (mm/ms) | Impulsion brute (%) | Bilan énergie (%) |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(nrows)}

À 50 ns : momentum final 1,732244 N ms, impulsion d'appui −1,267756 N ms ; leur somme avec P0=3 est compatible. À 25 ns : 1,732142 et −1,267858 N ms. WE=0, masse conservée. Après OFF, forces nulles et vitesse/momentum constants : le mouvement post-séparation est calculé, sans trajectoire prescrite. IE tend vers 0,03 J et KE vers 0,015 J, comme la référence de la loi hypothétique ; vitesse finale à environ 0,011154/0,005265 % de la référence. Les événements OFF suivent tf à moins d'un pas dans les sorties observées, sans forcer leur temps.

L'écart entre IE et le travail de F intégré sur le déplacement est inférieur à 0,000026 % du travail normal. Le bilan énergétique global maximal vaut 0,001698 % puis 0,000429 % de E0. Le résidu brut d'impulsion reste non nul (0,412/0,206 %), mais passe les seuils. Les tableaux près d'OFF sont conservés, sans interpréter leur partition comme une dissipation physique.

Il s'agit d'une vérification numérique locale de séparation normale libre et de mouvement ensuite sans force, pour une unique liaison et ces paramètres. Aucun rivet réel, déchirure de plaque ou effondrement ne peut être déduit de cet accord.

## 6. Contradictions et informations manquantes

Restent ouverts : les cinq critères mixtes OFF/FX de F, le réservoir élastique tangentiel supprimé avec l'élément, la définition exacte de REACX/REACY et du centrage TH, toutes les limitations d'inertie/angle/couverture de E, l'identification nominal/vrai NASA et la calibration physique de Gf30. Gf15/60 restent différés. Aucun contact post-fracture, état de plaque ou mode mixte n'est qualifié par H.

I testera d'abord l'arrêt et la restitution lors d'une ouverture qui n'atteint pas la séparation, avec historique de décharge H2. Le plan proposé contient un cas énergie 0,02 J (v0=20 mm/ms) dans l'adoucissement et un retour sous pic à 0,001 J. Avant tout moteur I, dériver/vérifier les références et vérifier que la fenêtre reste en ouverture positive sans compression. Rien n'est exécuté en I ici.

La localisation en flexion après fracture complète n'est pas validée ; température imposée ≠ incendie calculé. Blender reste une visualisation. Impact complet Boeing/façade, incendie et effondrement réel restent non validés.

## Reproduction et reprise

Deux pré-déclarations JSON immuables, scripts, référence analytique, graines sans tirage, decks, journaux/versions/empreintes d'exécutables, CSV et rapports sauvegardés. Les étapes exécutées sont declare_elastic, run_elastic, audit elastic, référence verify, declare_fracture, run_fracture, audit fracture ; la seconde déclaration vérifie les SHA-256 des deux gardes. Le harnais est contrôlé avant/après et l'état n'est actualisé qu'après présence et contrôle de ces artefacts.

Contrôle sans solveur : `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_free_fracture.py verify`. Publication : H seule pending 1/2, H+I après une I vérifiée, avec contrôle distant des archives et CI. Aucun envoi X.
'''
    REPORT.write_text(report,encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# Passation WTC1 — H terminée, I suivante

Lire AGENTS.md, harness/state.json (prioritaire), ce fichier et data/impact_i02i_i_plan_from_h.json. Vérifier le harnais avant/après. G reste réutilisée, aucune archive rescannée ni ancien solveur relancé.

H : quatre états neufs, 12 jobs, {runtime:.3f} s ; {s['case_checks_passed']}/{s['case_checks_total']} critères de cas, {s['comparison_checks_passed']}/{s['comparison_checks_total']} comparaisons et {s['reference_checks_passed']}/{s['reference_checks_total']} contrôles de référence. Élastique libre à 25/12,5 ns : impulsion brute 0,579655/0,289821 %, tous champs bruts ≤1 %. Les huit anciens diagnostics G échoués restent conservés.

Première séparation normale libre numérique : Y libre, m mobile 0,1 g, v0=30 mm/ms, Kn=56000 N/mm, pic495 N, aire1 mm², Gf30 hypothétique ; E0=0,045 J, Wséparation≈0,03 J, KE finale≈0,015 J. Référence propre vérifiée par quadrature et équations avant déclaration du moteur : tf=0,00561201925604 ms, vf=√300≈17,320508 mm/ms. Cas 50/25 ns : OFF0,00565/0,005625 ms, vf17,32244/17,32142, résidu impulsion0,412173/0,206106 %, bilan énergie0,001698/0,000429 %. Après OFF : forces nulles, mouvement libre calculé, momentum constant. Ce témoin ne calibre pas la fracture physique ni le mode mixte.

I : états neufs d'arrêt/retour sans séparation ; proposition énergie0,02 J/v0Y20 mm/ms dans l'adoucissement et retour sous pic0,001 J. Dériver puis vérifier référence de décharge H2 avec maximum historique, temps de retournement/force nulle et bilans. Vérifier la fenêtre de gap positif, arrêter avant compression. Pré-déclarer critères bruts1 %, énergie/travail0,5 %, pas/couverture et budget90 s/cas600 s total. Ne jamais modifier une propriété sur état endommagé.

Sorties : wtc1_simulation_v8/output/impact_i02i_free_fracture/rapport_impact_i02i_free_fracture.md et verification_r1/summary.json ; référence reference_verification.json, audits elastic_verification_r1 et fracture_verification_r1. {count} anciens fichiers épinglés. Vérification sans moteur : complete_impact_i02i_free_fracture.py verify.

Conserver les cinq échecs OFF/FX F, REACX/REACY et centrage exact non établis, toutes sensibilités et couvertures E, deux conventions NASA, Gf15/60 différés. Aucun transfert vers avion/façade ou Blender dynamique ; flexion post-fracture non validée, température imposée ≠ incendie, effondrement non validé. V11F/V11R/V11S conservés.

GitHub : F+G publiée/vérifiée, H seule pending1/2 ; publier H+I après I vérifiée selon harness/publication_cycle.json. Aucun post X.
''',encoding='utf-8',newline='\n')
    h.dump(OUT/'release_audit.json',{'created_utc':h.NOW(),'pass':True,'definition':'Integrity of bounded fresh numerical elastic and normal free controls, unresolved physical limitations retained',
        'old_files_preserved':count,'harness':hv,'summary_sha256':h.sha(SUMMARY),'report_sha256':h.sha(REPORT),'handoff_sha256':h.sha(HANDOFF),
        'physical_fracture_calibrated':False,'physical_propagation_qualified':False})
    h.dump(OUT/'harness_after_artifacts.json',h.harness())
    scripts=[ROOT/'wtc1_simulation_v8/scripts'/name for name in ['run_impact_i02i_free_fracture.py','reference_impact_i02i_free_fracture.py','audit_impact_i02i_free_fracture.py','complete_impact_i02i_free_fracture.py']]
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[h.ELCFG,h.FRACCFG,IPLAN,HANDOFF]+scripts
    h.dump(OUT/'artifact_manifest.json',{'created_utc':h.NOW(),'files':[{'path':h.rel(p),'bytes':p.stat().st_size,'sha256':h.sha(p)} for p in sorted(set(paths))],
        'exclusions':['self','post-registration verification','mutable harness administration']})

def register():
    assert REPORT.exists() and HANDOFF.exists() and IPLAN.exists() and (OUT/'artifact_manifest.json').exists()
    count=preservation();s=read(SUMMARY)
    for name in h.g.f.ADMIN:assert h.sha(ROOT/'harness'/name)==h.sha(OUT/('before_'+Path(name).name)),'Concurrent state change'
    state=read(ROOT/'harness/state.json');cadence=read(ROOT/'harness/publication_cycle.json')
    assert state['current_iteration']=='IMPACT-I02I-G' and state['next_iteration']=='IMPACT-I02I-H' and cadence['pending_iterations']==[]
    when=h.NOW();status='completed_bounded_strict_elastic_and_free_normal_separation_controls'
    record={'experiment_id':'WTC1-IMPACT-I02I-H','registered_at':when,'status':status,
        'configurations':[h.rel(h.ELCFG),h.rel(h.FRACCFG)],'report':h.rel(REPORT),'results':h.rel(SUMMARY),'handoff':h.rel(HANDOFF),
        'artifact_manifest':h.rel(OUT/'artifact_manifest.json'),'source_manifest':h.rel(OUT/'source_manifest.json'),
        'publication_verification':h.rel(OUT/'publication_verification.json'),'I_plan':h.rel(IPLAN),'cases':4,
        'case_checks_passed':s['case_checks_passed'],'case_checks_total':s['case_checks_total'],
        'comparison_checks_passed':s['comparison_checks_passed'],'comparison_checks_total':s['comparison_checks_total'],
        'reference_checks_passed':s['reference_checks_passed'],'reference_checks_total':s['reference_checks_total'],
        'runtime_seconds':s['runtime_seconds'],'old_files_preserved':count,
        'strict_raw_elastic_1pct_pass':True,'numerical_free_normal_witness_verified':True,
        'post_failure_numerical_ballistic_verified':True,'physical_fracture_calibrated':False,
        'physical_propagation_qualified':False,'mixed_mode_qualified':False,'E_sensitivities_resolved':False,'source_convention_verified':False,
        'normal_final_velocity_mm_per_ms':{n:v['metrics']['final_velocity_mm_per_ms'] for n,v in s['cases'].items() if v['case']['stage']=='normal'},
        'normal_raw_impulse_fractions':{n:v['metrics']['raw_impulse_fraction'] for n,v in s['cases'].items() if v['case']['stage']=='normal'},
        'next_iteration':'IMPACT-I02I-I','github_pending_iterations':1}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as file:file.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='IMPACT-I02I-H',current_status=status,next_iteration='IMPACT-I02I-I',updated_at=when,
        next_objective='Réutiliser H : précision libre brute ≤1 % vérifiée à 25/12,5 ns et témoin numérique de séparation normale libre vérifié à 50/25 ns, sans calibration physique. I : pré-déclarer états neufs d arrêt/retour H2 sans séparation après référence de décharge avec historique et contrôle du gap positif avant compression. Conserver échecs OFF/FX F, diagnostics G antérieurs, sensibilités/couvertures E, conventions NASA, Gf30 hypothétique et Gf15/60 différés. H=1/2 GitHub ; publication H+I après I vérifiée. V11F/V11R/V11S préservés.')
    state['impact_i02i_h_key_results']={k:record[k] for k in ['cases','case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','reference_checks_passed','reference_checks_total','runtime_seconds','old_files_preserved','strict_raw_elastic_1pct_pass','numerical_free_normal_witness_verified','post_failure_numerical_ballistic_verified','physical_fracture_calibrated','physical_propagation_qualified','mixed_mode_qualified','E_sensitivities_resolved','source_convention_verified','normal_final_velocity_mm_per_ms','normal_raw_impulse_fractions','github_pending_iterations']}
    state['validated_artifacts'].update(impact_i02i_h_report=h.rel(REPORT),impact_i02i_h_results=h.rel(SUMMARY),impact_i02i_h_handoff=h.rel(HANDOFF),impact_i02i_h_publication_verification=h.rel(OUT/'publication_verification.json'),impact_i02i_i_plan=h.rel(IPLAN))
    cadence.update(pending_iterations=['IMPACT-I02I-H'],pending_count=1,next_publication_after='Publish H+I only after verified I, retaining F+G baseline and unresolved physical limitations',updated_at=when)
    h.dump(ROOT/'harness/publication_cycle.json',cadence);temp=ROOT/'harness/state_i02ih_pending.json';h.dump(temp,state);temp.replace(ROOT/'harness/state.json')
    verify(write=True)

def verify(write=False):
    count=preservation();m=read(OUT/'artifact_manifest.json');bad=[r['path'] for r in m['files'] if h.sha(ROOT/r['path'])!=r['sha256']]
    state=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cadence=read(ROOT/'harness/publication_cycle.json')
    reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();extra=reg[len(prefix):].decode('utf-8').splitlines()
    s=read(SUMMARY);hv=h.harness();cfg=read(h.FRACCFG)
    protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy','open_limitations']
    checks={'artifact_hashes':not bad,'old_pins_preserved':True,'registry_prefix':reg.startswith(prefix),
        'one_H_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-H',
        'state_H_to_I':state['current_iteration']=='IMPACT-I02I-H' and state['next_iteration']=='IMPACT-I02I-I',
        'prior_states_preserved':all(state[k]==old[k] for k in protected),'harness_pass':hv['Status']=='PASS',
        'report_handoff_plan_exist':REPORT.exists() and HANDOFF.exists() and IPLAN.exists(),
        'cadence_H_one_pending':cadence['pending_iterations']==['IMPACT-I02I-H'] and cadence['pending_count']==1,
        'F_G_publication_baseline_preserved':all(cadence[k]==read(OUT/'before_publication_cycle.json')[k] for k in ['last_published_iteration','last_published_commit','last_published_release']),
        'strict_elastic_guard':read(OUT/'elastic_verification_r1/summary.json')['all_checks_pass'],
        'fracture_reference_guard':read(OUT/'reference_verification.json')['pass'],
        'guard_hashes':h.sha(OUT/'elastic_verification_r1/summary.json')==cfg['elastic_guard_sha256'] and h.sha(OUT/'reference_verification.json')==cfg['reference_verified_sha256'],
        'all_H_gates_pass':s['all_declared_checks_pass'],
        'prior_G_and_F_failures_retained':s['cached_G_strict_1pct_failures_preserved']==8 and len(s['cached_F_same_row_OFF_FX_failures_preserved'])==5,
        'physical_limits_retained':not s['physical_fracture_calibrated'] and not s['physical_propagation_qualified'] and not s['mixed_mode_qualified'] and not s['E_sensitivities_resolved'],
        'no_old_solver_rerun':not s['old_solvers_rerun']}
    result={'created_utc':h.NOW(),'pass':all(checks.values()),'checks':checks,'manifest_files_checked':len(m['files']),
        'manifest_failures':bad,'old_files_checked':count,'harness':hv,'cases':4,
        'case_checks':f"{s['case_checks_passed']}/{s['case_checks_total']}",'comparison_checks':f"{s['comparison_checks_passed']}/{s['comparison_checks_total']}",
        'reference_checks':f"{s['reference_checks_passed']}/{s['reference_checks_total']}",
        'numerical_free_normal_witness_verified':True,'physical_fracture_calibrated':False,'physical_propagation_qualified':False,
        'next_iteration':'IMPACT-I02I-I','github_pending_iterations':1}
    assert result['pass'],result
    if write:h.dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);a=p.parse_args();globals()[a.action]()
