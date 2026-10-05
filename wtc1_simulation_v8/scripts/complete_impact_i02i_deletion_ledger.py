"""L faithful bounded ledger, registration and solver-free final verification."""
from __future__ import annotations
import argparse,json,shutil
from pathlib import Path
import run_impact_i02i_deletion_ledger as run
h=run.h;ROOT,OUT,CFG=run.ROOT,run.OUT,run.CFG
read=run.read
SUMMARY=OUT/'verification_r1/summary.json'
REPORT=OUT/'rapport_impact_i02i_deletion_ledger.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_L_HANDOFF.md'
MPLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_m_plan_from_l.json'
OBJECTIVE='M : vérifier la référence conditionnelle de rétention de Ux avec quatre états neufs X/Y libres jusqu’à suppression normale complète, vx5/10 et vy30 mm/ms, caps25/12,5ns. D’abord contrôler la référence L, les frontières de temps et le devenir explicite de l’énergie, puis pré-déclarer tous les critères et lancer seulement des états neufs. Conserver les signaux bruts à la transition OFF/FX et tout échec, sans déphasage, clipping, restitution artificielle ni modification de matériau endommagé. La rétention est une hypothèse de comptabilité numérique, pas une rupture mixte physique. L=1/2 GitHub ; prochaine paire L+M après vérification. E/F/G/I/J, NASA/Gf30 hypothétique/Gf15/60 et V11F/V11R/V11S préservés. Impact Boeing/façade, feu et effondrement non qualifiés.'

def preservation():
    rows=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in rows if h.sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad;return len(rows)

def prepare():
    assert not REPORT.exists() and not HANDOFF.exists() and not MPLAN.exists(),'Keep iterations'
    s=read(SUMMARY);cfg=read(CFG);ref=read(OUT/'reference_verification.json');count=preservation();hv=h.harness()
    assert s['all_declared_checks_pass'] and s['case_checks_passed']==s['case_checks_total']==186
    assert s['comparison_checks_passed']==s['comparison_checks_total']==12 and s['reference_checks_passed']==s['reference_checks_total']==26
    assert s['total_rows']==215216 and s['total_values']==8823856 and s['solver_jobs']==0
    plan={'id':'IMPACT-I02I-M_PLAN_FROM_L','created_utc':h.NOW(),'seed':1102021,'random_draws':0,
        'saved_L_summary':{'path':h.rel(SUMMARY),'sha256':h.sha(SUMMARY)},
        'saved_L_conditional_reference':{'path':h.rel(OUT/'reference_verification.json'),'sha256':h.sha(OUT/'reference_verification.json')},
        'scope':'Fresh two-node free XY normal whole-element deletion with explicitly retained X reserve; numerical witness only',
        'cases_proposed':[{'family':'FREE_X5_NORMAL_SEPARATION','vx0_mm_per_ms':5.,'vy0_mm_per_ms':30.,'E0_J':.04625,'end_ms':.012,'maximum_dt_ms':[.000025,.0000125]},
                          {'family':'FREE_X10_NORMAL_SEPARATION','vx0_mm_per_ms':10.,'vy0_mm_per_ms':30.,'E0_J':.05,'end_ms':.012,'maximum_dt_ms':[.000025,.0000125]}],
        'reference_parameters':{name:r['parameters'] for name,r in ref['cases'].items()},
        'properties':cfg['connector'],'boundary_conditions':'node1 fixed; node2 X/Y free, Z/rotations blocked; initial velocity only',
        'energy_policy':'Before normal deletion: IE=Wn+Ux. After: IE=Garea+Ux(tf), forces zero and velocities continuous; no invented KE jump or energy source.',
        'before_engine':['Verify cached reference and independent ODE/quadrature guards; record all source/runtime hashes',
            'Predeclare amplitudes/impulses/energy per axis, P0 per axis, mass, work, exact binary intervals and time coverage',
            'At discontinuous X force, preserve every raw row and strict same-row OFF/FX result; any failed raw criterion remains failed',
            'Predeclare any limited pre/post observation windows around analytic tf, separately from complete raw traces; never fit phase or use windows to override an old gate',
            'Check IE retains deleted Ux, terminal ballistic velocity/momentum and two-axis support impulses; compare caps at common covered times',
            'Keep retention interpretation conditional; data can refute it, and never impose a material change on an old damaged state'],
        'cost':{'maximum_case_wall_seconds':90,'maximum_campaign_wall_seconds':600,'announce_before_engine':True},
        'unchanged':['Five strict F OFF/FX failures','Eight G strict diagnostics','E sensitivity and coverage',
            'Four I signs','Three J raw endpoints','REAC/TH and exact engine/converter provenance','NASA conventions',
            'Gf30 hypothetical;15/60 deferred','V11F/V11R/V11S'],
        'not_qualified':['Released X-energy law','Physical mixed fracture','Plate/contact/waves','Boeing/facade/fire/collapse'],
        'publication':'L pending1/2; publish L+M only after M audited, including any failures; preserve J+K baseline'}
    h.dump(MPLAN,plan)
    table=[]
    for name,r in s['cases'].items():
        e=r['event']
        if e:
            q=e['raw_changes_J'];table.append(f"| {name} | {e['pre_Ux_J']:.10g} | {e['post_IE_J']:.12g} | {e['post_IE_minus_normal_work_J']:.10g} | {q['IE']:.7g} | {q['KE']:.7g} | {q['WE']:.7g} | {e['raw_force_lag_rows']} |")
    refs=[]
    for name,r in ref['cases'].items():
        p=r['parameters'];refs.append(f"| {p['vx0_mm_ms']:g} | {p['E0_J']:.10g} | {p['Ux_at_deletion_J']:.12g} | {p['vx_at_deletion_mm_ms']:.10g} | {p['retained_IE_after_J']:.12g} | {p['free_KE_after_J']:.12g} |")
    REPORT.write_text(f'''# WTC1 — IMPACT-I02I-L : registre énergétique à suppression complète

## 1. Faits directement observés ou transcrits

Huit essais F sauvegardés relus : **215216 lignes, 8823856 valeurs**. Toutes les valeurs binaires reproduisent exactement les CSV .6e ; deux lecteurs indépendants concordent, IE globale/SPRING ENERGY/IE liaison identiques bit pour bit. Analyse13,181737s, budget120s ; zéro job de solveur ou convertisseur relancé. La référence conditionnelle propre ajoute20 contrôles mécaniques, sans moteur.

Nouveaux contrôles L : **186/186 de cas,12/12 comparaisons,26/26 références**. Ces comptes sont ceux du diagnostic L. Les cinq critères stricts OFF/FX de F restent échoués et all_scientific_checks_pass de F reste false. L vérifie leur préservation et reproduit le retard d’une ligne ; elle ne promeut pas la qualification des anciens essais.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat NIST ou modèle du WTC. La [documentation primaire TYPE8](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type8_spr_gene_starter_r.htm) décrit des modes indépendants et les options de rupture. La [documentation /TH/SPRING](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm) définit OFF, les composantes de force et IE ; elle ne fournit pas ici une répartition de l’énergie supprimée en chaleur, fracture et mouvement. Deux snapshots sont conservés comme preuves documentaires, avec copyright et exclusion de redistribution.

Le chemin interne de cette énergie dans l’exécutable et le centrage TH ne sont pas identifiés. Le code du convertisseur et le schéma binaire officiel demeurent indisponibles ; le lecteur propre n’est accepté que sur sa signature3040 déclarée et ses blocs/codes contrôlés. L’égalité avec les CSV et les deux lecteurs vérifie ces fichiers, pas le solveur entier.

## 3. Affirmations des archives locales

Aucune nouvelle assertion d’archive, image ou vidéo examinée ; aucune archive rescannée. {count} fichiers antérieurs épinglés depuis les inventaires K et précédents, inchangés. Source et anciennes itérations restent en lecture seule. Les propriétés et résultats H/K servent de références sauvegardées, sans relance. La preuve locale confirme la publication J+K et pending0 avant L ; après L enregistrée,pending1/2, prochaine paire L+M.

## 4. Hypothèses propres au diagnostic, unités et histoire

F : deux nœuds avec masse totale0,2g (0,1g chacun), nœud1fixe, déplacements X/Y du nœud2 imposés. Kn56000N/mm,Kt21500N/mm,picnormal495N,aire1mm²,Gf30N/mm hypothétique. H2 sur X et Y ; la courbe X est linéaire symétrique de penteKt, donc élastique dans ces essais. Rupture tangentielle désactivée et rotations bloquées. Aucun restart ni propriété d’un état endommagé modifiée.

Unités g/mm/ms/N, énergie de sortie Nmm=mJ puis ×0,001J, impulsionNms. Garea=30Nmm=0,03J ; réserve élastique X à0,02mm : Ux=Kt x²/2=4,3Nmm=0,0043J. Ux=Fx²/(2Kt),Uy=Fy²/(2Kn) sont des réserves **inférées de la loi** sur les lignes cohérentes. D=IE−Ux−Uy est un registre de travail non récupéré ; il n’identifie pas un canal physique de dissipation.

Sélection avant analyse : première transition OFF1→0 à la lignej, ligne avantj−1 et ligne aprèsj+2 fixées. Les six lignesj−2…j+3 sont conservées sur leurs temps originaux. Aucune partition récupérable n’est affirmée àj ouj+1, où OFF/force peuvent différer ; les valeurs brutes restent affichées. Le premier zéro des deux forces est un diagnostic séparé et ne sert pas à déplacer les signaux ou à choisir un meilleur résidu. Des vues CSV clairsemées portent les indices originaux ; les histoires complètes F restent épinglées.

Cellules binaires32 au plus proche, avec milieux exacts entre voisins, arithmétique rationnelle pour les cellules IE/KE/WE/F et les carrés. Aux lignes sélectionnées, calculer les intervalles exacts de ΔIE,ΔKE,ΔWE,ΔUx,ΔUy,ΔD et du bilan. Hypothèse d’arrondi explicite, sans accès aux doubles internes ; les cellules sont prises indépendamment, sans covariance supposée. Le signe et la valeur bruts ne sont jamais corrigés. L’intervalle du résidu ΔD−(Uavant−Uaprès)−(ΔWE−ΔKE) est descriptif et en grande partie une identité de registre ; son inclusion de0 **ne démontre pas le mécanisme de transfert**.

Seuils avant analyse :0,5% des échelles fixes d’énergie/réserve,force zéro1e−5N ; contrôle masse sans ajout. La compatibilité du registre retenu est testée contre IEaprès≈Garea+Uxavant+ΔWE−ΔKE, complétée par contrôles sans réserve et retour élastique. Elle reste une compatibilité numérique conditionnelle.

## 5. Résultats dérivés

| Cas sauvegardé | Ux avant (J) | IE après (J) | IE après−0,03J (J) | ΔIE (J) | ΔKE (J) | ΔWE (J) | Retard force/lignes |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table)}

FIXED : à200/100/50ns, réserve≈0,0043J avant,forces nulles après et IE≈0,0342999992371J. L’excès au-delà du travail normal≈0,0042999992371J correspond à la réserve tangente. ΔKE brute=0 et son intervalle≈±2,91e−14J contient0 ; ΔWE brute=0 aussi. Le très petit ΔIE à200ns (≈3,81e−9J) apparaît en binaire malgré les CSV arrondis ; il est conservé et sa cellule admet0. ΔD vaut≈+0,0043J : la réserve cesse d’être récupérable d’après la force mais reste dans IE. Le gain cinétique enregistré ne vaut pas cette réserve dans ce protocole contraint.

PROP : réserve avant≈0,0038999/0,0039001J et petit travail imposé supplémentaire≈8,43e−7/4,23e−7J pendant la transition. Le bilan conserve cet apport ; aucun modèle de suppression instantanée à temps ajusté n’est utilisé. Les résidus du registre retenu sont≈−8,98e−10/−3,18e−9J, bien plus petits que la réserve.

AFTER : aucune réserve X avant la rupture,IE=0,03J après, même quand X est déplacé ensuite. RETURN sans OFF : la réserve maximale≈0,0043J revient à une IE finale≈3,568e−17J. Ces deux familles distinguent réserve préalable supprimée et énergie récupérée par retour élastique.

Les sept cellules exactes de bilan à l’événement admettent0. Les trois comparaisons de quantités par paire de pas passent12/12, sans alignement temporel ni extrapolation. Cinq Fx sur la ligne OFF demeurent non nulles :430N pour FIXED,≈409,5343N pour PROP, puis zéro une ligne plus tard. Les deux AFTER ont zéro dès OFF. La diminution de durée du retard avec le pas est conservée ; le centrage interne demeure inconnu.

### Référence conditionnelle pour une future séparation libre

Réutiliser le mouvement normal H (vy0=30mm/ms,m0,1g,Garea0,03J) et X indépendant jusqu’à tf=0,00561201925604ms. Àtf, déclarer **pour la comptabilité numérique** forcesX/Ynulles,vitesses continues,IEaprès=Garea+Ux(tf). Le mouvement suivant est balistique. IE reste continue ; le registre D acquiert la réserve Ux supprimée. Quadrature indépendante du travail/impulsionX,RK4 directe jusqu’àtf,continuité et conservation totale passent20/20 contrôles. Cela ne calibre pas une fracture mixte.

| vx0 (mm/ms) | E0 (J) | Ux(tf) (J) | vx(tf) (mm/ms) | IE après retenue (J) | KE après (J) |
|---|---:|---:|---:|---:|---:|
{chr(10).join(refs)}

Contrefactuel : si IEaprès est remplacée par0,03J tout en conservant les mêmes vitesses, le bilan perd exactement Ux(tf), soit0,00032976554/0,00131906216J. Une vraie restitution exigerait un canal d’énergie et une dynamique d’impulsion explicites ; augmenter arbitrairement une vitesse ou effacer l’énergie ne fournit pas ce mécanisme. Aucune politique de restitution physique complète n’est construite ici et aucun de ces cas n’est exécuté dans OpenRadioss en L.

## 6. Contradictions et informations manquantes

L confirme la compatibilité du registre de rétention sur des **déplacements imposés** et dérive une référence conditionnelle libre ; elle ne vérifie pas encore une séparation mixte libre. Le destin interne des0,0043J n’est pas identifié et aucune température/chaleur/énergie de fissuration n’en est déduite. Au point OFF, les sorties force/flag ne donnent pas une partition synchrone ; les cinq échecs F restent ouverts.

M proposera quatre états neufs libres,vx5/10,vy30,caps25/12,5ns,avec politique de rétention explicitée avant moteur. Tout échec brut à la transition restera échoué ; un contrôle de mouvement ou de bilan sur une fenêtre pré-déclarée ne le remplacera pas. Les références peuvent être réfutées par les sorties. Aucun matériau ancien endommagé ne sera reconfiguré.

Conserver les huit diagnostics G,sensibilités/couvertureE,quatre signesI,trois fins brutesJ,REAC/centrage TH,schéma officiel et provenance exacte du moteur non identifiés. NASA non résolu,Gf30hypothétique/Gf15/60différés,V11Ffroid et V11R→V11S conservés. Impact complet Boeing/façade,incendie et effondrement réel non qualifiés. Localisation en flexion après fracture complète non validée,température imposée≠incendie calculé,Blender visualisation.

## Reproduction et reprise

Pré-déclaration JSON1102020,zéro tirage,scripts,référence,histoires F épinglées,snapshots documentaires,intervalles exacts,comparaisons,rapport et passation conservés. Une erreur de syntaxe du brouillon de préparation a arrêté Python avant initialisation ou analyse ; brouillon conservé dans development_r0, correction de syntaxe uniquement. Aucun moteur ni ancien fichier modifié. Vérifier sans solveur avec complete_impact_i02i_deletion_ledger.py verify. L seule pending1/2 ; publier L+M après M vérifiée, pas de publication X.
''',encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# Passation compacte — IMPACT-I02I-L vers M

Lire AGENTS.md,harness/state.json (prioritaire),cette passation puis impact_i02i_m_plan_from_l.json. L terminée → M. Lpending1/2 ; publication L+M après M vérifiée. J+K est la base distante vérifiée et ne doit pas être reconstruite.

L : huit F sauvegardés,215216lignes,8823856valeurs reproduisent les CSV,deux lecteurs concordants ;186/186 nouveaux contrôles,12/12 comparaisons,26/26 références. Diagnostic13,181737s,zéro moteur/convertisseur. {count} anciens fichiers épinglés. Rapport/audits/configuration dans impact_i02i_deletion_ledger ; vérifier sans moteur via complete_impact_i02i_deletion_ledger.py verify.

FIXED : Uxavant≈.0043J,IEaprès≈.0342999992371J,forces nulles,ΔKE/WE enregistrées0 ; réserve devenue non récupérable dans le registre IE−U, sans canal physique identifié. PROPapport imposé pendant la transition conservé ; AFTERsans réserveIE.03J ; RETURNsans OFF récupère l’énergie. Cinq OFF/FX F demeurent échoués,retard une ligne non corrigé. Sélectionj−1/j+2 déclarée,cellsIEEE32conditionnelles exactes ; aucune partition affirmée àj/j+1 et aucune phase déplacée.

Référence conditionnelle pour M : vy30,m.1g,tf.00561201925604ms ; Xoscillateur avanttf,puisforces0 etvitesses continues,IE=Garea+Ux(tf). Pourvx5/10 : Ux(tf)=.000329765540/.001319062160J ;20contrôles mécaniques/quadrature/RK4passent. Politique numérique de rétention,pas fracture mixtephysique. Restitution non définie : effacer Ux avec vitesses inchangées perdrait cette énergie.

M : quatre états neufs X/Ylibres,Z/rotations bloqués,vx5/10,vy30,caps25/12,5ns,fin.012ms. Vérifier références et pré-déclarer critères/limites temporelles avant moteur. Préserver toutes lignes brutes et tout échec OFF/FX ; pas ajustementphase/clipping/saut KEinventé/changementpropriétéendommagée. Annoncerbudget90s/cas,600stotal. Tester si IE/mouvement/impulsions soutiennent ou réfutent la référence retenue.

Conserver E/F/G/I/J,REAC/TH/schéma/provenance,NASA,Gf30hypothétique/Gf15/60différés,V11F/V11R/V11S. Aucun impactBoeing/façade/feu/effondrement qualifié,flexionpost-fracture nonvalidée,Blender visualisation. Aucun postX ni actionYoremi.
''',encoding='utf-8',newline='\n')
    draft=ROOT/'tmp/impact_i02i_l_development_r0/runner.py'
    if draft.exists():
        dest=OUT/'development_r0';dest.mkdir();shutil.copy2(draft,dest/'runner.py')
        h.dump(dest/'failure.json',{'stage':'Python parsing before initialization','error':'SyntaxError: expected else after if expression; missing space before literal1',
            'solver_jobs':0,'diagnostic_run':False,'old_files_modified':False,'correction':'Syntax only, no criterion/equation altered'})
    h.dump(OUT/'release_audit.json',{'created_utc':h.NOW(),'pass':True,'old_files_preserved':count,'harness':hv,'summary_sha256':h.sha(SUMMARY),
        'scope':'Integrity and bounded ledger; old failures unchanged, not physical qualification'})
    h.dump(OUT/'harness_after_artifacts.json',h.harness())
    scripts=[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_impact_i02i_deletion_ledger.py','reference_impact_i02i_deletion_ledger.py','audit_impact_i02i_deletion_ledger.py','complete_impact_i02i_deletion_ledger.py']]
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,MPLAN,HANDOFF]+scripts
    h.dump(OUT/'artifact_manifest.json',{'created_utc':h.NOW(),'files':[{'path':h.rel(p),'bytes':p.stat().st_size,'sha256':h.sha(p)} for p in sorted(set(paths))],
        'exclusions':['self','post-registration verification','mutable harness administration']})

def register():
    assert REPORT.exists() and HANDOFF.exists() and MPLAN.exists() and (OUT/'artifact_manifest.json').exists();count=preservation();s=read(SUMMARY)
    for name in h.g.f.ADMIN:assert h.sha(ROOT/'harness'/name)==h.sha(OUT/('before_'+Path(name).name)),'Concurrent state change'
    state=read(ROOT/'harness/state.json');cadence=read(ROOT/'harness/publication_cycle.json')
    assert state['current_iteration']=='IMPACT-I02I-K' and state['next_iteration']=='IMPACT-I02I-L' and cadence['pending_iterations']==[]
    status='completed_bounded_deletion_energy_ledger_with_conditional_retention_reference';when=h.NOW()
    keys=['case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','reference_checks_passed','reference_checks_total',
        'all_declared_checks_pass','runtime_seconds','total_rows','total_values','old_F_same_row_failures_preserved','solver_jobs','old_solver_rerun',
        'numeric_retention_ledger_compatible','internal_transfer_route_identified','free_mixed_separation_tested','release_policy_complete',
        'physical_fracture_calibrated','physical_propagation_qualified','aircraft_impact_qualified']
    record={'experiment_id':'WTC1-IMPACT-I02I-L','registered_at':when,'status':status,'configuration':h.rel(CFG),'report':h.rel(REPORT),
        'results':h.rel(SUMMARY),'handoff':h.rel(HANDOFF),'M_plan':h.rel(MPLAN),'artifact_manifest':h.rel(OUT/'artifact_manifest.json'),
        'source_manifest':h.rel(OUT/'source_manifest.json'),'publication_verification':h.rel(OUT/'publication_verification.json'),
        **{key:s[key] for key in keys},'old_files_preserved':count,'mixed_mode_qualified':False,'source_convention_verified':False,
        'E_sensitivities_resolved':False,'next_iteration':'IMPACT-I02I-M','github_pending_iterations':1}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='IMPACT-I02I-L',current_status=status,next_iteration='IMPACT-I02I-M',next_objective=OBJECTIVE,updated_at=when)
    state['impact_i02i_l_key_results']={k:v for k,v in record.items() if k not in ['experiment_id','registered_at','status','configuration','report','results','handoff','M_plan','artifact_manifest','source_manifest','publication_verification','next_iteration']}
    state['validated_artifacts'].update(impact_i02i_l_report=h.rel(REPORT),impact_i02i_l_results=h.rel(SUMMARY),impact_i02i_l_handoff=h.rel(HANDOFF),
        impact_i02i_l_publication_verification=h.rel(OUT/'publication_verification.json'),impact_i02i_m_plan=h.rel(MPLAN))
    cadence.update(pending_iterations=['IMPACT-I02I-L'],pending_count=1,next_publication_after='L+M after M audited; retain all failures and J+K baseline',updated_at=when)
    h.dump(ROOT/'harness/publication_cycle.json',cadence);temp=ROOT/'harness/state_i02il_pending.json';h.dump(temp,state);temp.replace(ROOT/'harness/state.json');verify(write=True)

def verify(write=False):
    count=preservation();manifest=read(OUT/'artifact_manifest.json');bad=[r['path'] for r in manifest['files'] if h.sha(ROOT/r['path'])!=r['sha256']]
    state=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cadence=read(ROOT/'harness/publication_cycle.json');s=read(SUMMARY);cfg=read(CFG)
    prefix=(OUT/'before_registry.jsonl').read_bytes();reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();extra=reg[len(prefix):].decode('utf-8').splitlines()
    protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy','open_limitations']
    hv=h.harness();before=read(OUT/'before_publication_cycle.json');checks={'artifact_hashes':not bad,'old_pins_preserved':True,
        'registry_prefix':reg.startswith(prefix),'one_L_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-L',
        'state_L_to_M':state['current_iteration']=='IMPACT-I02I-L' and state['next_iteration']=='IMPACT-I02I-M',
        'prior_states_preserved':all(state[k]==old[k] for k in protected),'harness_pass':hv['Status']=='PASS',
        'report_handoff_plan_exist':REPORT.exists() and HANDOFF.exists() and MPLAN.exists(),
        'cadence_L_one_pending':cadence['pending_iterations']==['IMPACT-I02I-L'] and cadence['pending_count']==1,
        'J_K_baseline_preserved':all(cadence[k]==before[k] for k in ['last_published_iteration','last_published_commit','last_published_release']),
        'config_predeclared':h.sha(CFG)==read(OUT/'declaration_guard.json')['config_sha256'],
        'cached_reference_hashes':all(h.sha(ROOT/v['path'])==v['sha256'] for v in cfg['cached_references'].values()),
        'L_counts_unchanged':s['all_declared_checks_pass'] and s['case_checks_passed']==s['case_checks_total']==186 and s['comparison_checks_passed']==12 and s['reference_checks_passed']==26,
        'five_F_failures_retained':len(state['impact_i02i_f_key_results']['strict_same_row_OFF_FX_failed_cases'])==5 and s['old_F_same_row_failures_preserved']==5,
        'I_J_failures_retained':not state['impact_i02i_i_key_results']['all_declared_checks_pass'] and state['impact_i02i_j_key_results']['raw_failures_preserved']==3,
        'physical_limits_retained':not s['physical_propagation_qualified'] and not s['physical_fracture_calibrated'] and not s['free_mixed_separation_tested'] and not s['internal_transfer_route_identified'],
        'no_solver_rerun':s['solver_jobs']==0 and not s['old_solver_rerun']}
    v={'created_utc':h.NOW(),'pass':all(checks.values()),'scope':'Integrity and conditional saved-output ledger, not physical qualification',
        'checks':checks,'manifest_files_checked':len(manifest['files']),'manifest_failures':bad,'old_files_checked':count,'harness':hv,
        'case_checks':'186/186','comparison_checks':'12/12','reference_checks':'26/26','old_failures_retained':True,'physical_propagation_qualified':False,
        'next_iteration':'IMPACT-I02I-M','github_pending_iterations':cadence['pending_count']}
    assert v['pass'],v
    if write:h.dump(OUT/'publication_verification.json',v)
    print(json.dumps(v,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);a=p.parse_args();globals()[a.action]()
