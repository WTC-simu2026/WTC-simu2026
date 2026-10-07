"""Independent saved-history review and integrity sealing of bounded A10 diagnostics."""
import argparse, copy, json, re, shutil, subprocess, time
from pathlib import Path
import numpy as np
from run_aircraft_a10 import ROOT, OUT, CFG, SRC, RUNTIME, COMMIT, read, dump, sha, rel, now, harness, guard, preserved, cases, case_dir, records, histories

REPORT=OUT/'rapport_aircraft_a10.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A10_HANDOFF.md'
NEXT=('AIRCRAFT-A11 : conserver le témoin A10 et ses échecs. Avant tout transfert vers l’avion, '
      'vérifier le ledger local RKE des triangles/poutres et l’attribution native des inerties, '
      'puis ajouter au témoin un contrôle spatial et un contrôle contact/formulation à raideur déclarée. '
      'Stfac1 avec dt_scale0.05/0.025 satisfait seulement le témoin contraint 1D : ne pas le promouvoir comme contact avion qualifié. '
      'Les déficits Stfac0.01/0.001 persistent au pas réduit ; cause non identifiée. '
      'Les REACX bruts T-file de ce build sont des impulsions cumulées ; ne pas les réintégrer. '
      'Maintenir A09 immuable, V11F/V11R préservées et V11S/I02I-M différées. '
      'Publication A08+A09 déjà vérifiée ; prochaine paire A10+A11 après vérification, aucun X/Yoremi.')

def native_check(d,g,H):
    v=np.column_stack(list(H.values()));r=records(d/(g['name']+'T01'));nr=g['history_records_per_frame'];n=len(v);header=len(r)-n*nr;assert header>0
    frames=[r[header+i*nr:header+(i+1)*nr] for i in range(n)];sizes=[len(q) for q in frames[0]]
    assert sizes[0]==4 and sizes[1]==88 and all([len(q) for q in f]==sizes for f in frames)
    raw=np.array([np.concatenate([np.frombuffer(q,dtype='>f4') for q in f]) for f in frames]);a=read(CFG)['acceptance']
    assert raw.shape==v.shape and np.allclose(raw,v,rtol=a['native_binary_csv_relative'],atol=a['native_binary_csv_absolute'])
    return {'all_channels_match':True,'header_records':header,'records_per_frame':nr,'sizes_bytes':sizes,'frames':n}

def review():
    guard();assert not (OUT/'authoritative_review.json').exists();c=read(CFG);a=c['acceptance'];results=[];spin=[]
    for case in cases():
        d=case_dir(case['id']);g=read(d/'generation.json');H=histories(d/(g['name']+'T01.csv'));T=H['time'];keys=list(H);proof=native_check(d,g,H);nd=[k for k in keys if k.startswith('NODES')];assert len(nd)==48
        def nod(i,ch):return H[nd[(i-1)*6+['DX','VX','VRX','VRY','VRZ','REACX'].index(ch)]]
        partR=H[next(k for k in keys if k.startswith('MOVING_QUAD') and k.strip().endswith('RKE'))]*.001
        if 'spin_form' in case:
            form=case['spin_form'];M=.00278*400;omega=case['omega_rad_ms']
            if form=='QUAD':inertia=M*(400/12+1/12)
            elif form=='TRIA':inertia=M*(200/4.5+1/12)
            else:
                em=.00278*20/2;inertia=4*max(1.2*em*(1.2*20)**2/12+.00278*(20/2)*(1/12),.00278*20/2*(1/6))
            ref=.5*inertia*omega**2*.001;nat=float(H['ROTATION ENERGY'][0]*.001);part=float(partR[0]);tol=read(OUT/'extension_predeclaration.json')['spin_initial_energy_relative_allowance']
            checks={'binary_integrity':True,'normal_termination':'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace').upper(),'initial_global_RKE_matches_native_inertia':abs(nat-ref)/ref<=tol,'initial_part_RKE_matches_global':abs(part-nat)/ref<=tol,'initial_angular_velocity_matches':max(abs(nod(i,'VRZ')[0]-omega) for i in range(1,5))<=1e-8,'initial_translation_zero':max(abs(nod(i,'VX')[0]) for i in range(1,5))<=1e-10}
            checks={k:bool(v) for k,v in checks.items()}
            row={'case':case,'checks':checks,'failed_checks':[k for k,v in checks.items() if not v],'native_binary':proof,'initial_global_RKE_J':nat,'initial_part_RKE_J':part,'predicted_inertia_sum_g_mm2':inertia,'runtime_effective_inertia_sum_g_mm2':2*nat/(omega**2*.001),'reference_RKE_J':ref,'global_relative_error':abs(nat-ref)/ref,'part_relative_error':abs(part-nat)/ref,'scope':'Initial-state inertia/output test, translations fixed; no rigid-body physical spin or large-rotation qualification'}
            np.savez_compressed(d/'spin_history_corrected_SI.npz',time_ms=T,global_RKE_J=H['ROTATION ENERGY']*.001,part_RKE_J=partR,angular_velocity_rad_ms=np.column_stack([nod(i,'VRZ') for i in range(1,5)]))
            dump(d/'authoritative_review_corrected.json',row);spin.append(row);continue
        old=read(d/'review.json');row=copy.deepcopy(old);support=sum(nod(i,'REACX') for i in range(5,9))*.001;Pg=H['X-MOMENTUM']*.001;err=Pg-Pg[0]-(support-support[0]);P0=c['analytical_reference']['initial_Px_Ns'];e=float(np.max(abs(err)))/P0
        row['support_momentum_relative']=e;row['support_final_momentum_relative']=float(abs(err[-1]))/P0;row['checks']['support_momentum']=e<=a['support_momentum_relative'];row['support_raw_units']='Cumulative native impulse g mm/ms, convert *0.001 to N s; no second integration'
        VX=np.column_stack([nod(i,'VX') for i in range(1,5)]);ke=.5*(.001112/4)*np.sum(VX**2,axis=1);native=H['KINETIC ENERGY']*.001
        row['independent_translation_KE_max_error_J']=float(np.max(abs(ke-native)));row['checks']['independent_translation_KE']=row['independent_translation_KE_max_error_J']<=1e-9
        row['all_checks_pass']=all(row['checks'].values());row['failed_checks']=[k for k,v in row['checks'].items() if not v];row['original_review_retained']=rel(d/'review.json');row['native_binary']=proof
        z=dict(np.load(d/'balance_history_SI.npz'));z['support_cumulative_impulse_Ns']=support;z['independent_translation_KE_J']=ke;np.savez_compressed(d/'authoritative_balance_corrected_SI.npz',**z)
        dump(d/'authoritative_review_corrected.json',row);results.append(row)
    comparisons=[]
    by={r['case']['id']:r for r in results}
    for label,pairs in [('original_half_dt',[(k+'_DT080',k+'_DT040') for k in ['K1','K01','K001']]),('fine_half_dt',[('K1_DT0050','K1_DT0025')]),('fourfold_time_refinement',[(k+'_DT010',k+'_DT0025') for k in ['K1','K01','K001']])]:
        for aa,bb in pairs:
            za=np.load(case_dir(aa)/'authoritative_balance_corrected_SI.npz');zb=np.load(case_dir(bb)/'authoritative_balance_corrected_SI.npz');tm=min(za['time_ms'][-1],zb['time_ms'][-1]);ja=np.interp(tm,za['time_ms'],za['raw_contact_impulse_Ns']);jb=np.interp(tm,zb['time_ms'],zb['raw_contact_impulse_Ns']);diff=float(abs(ja-jb)/max(abs(ja),abs(jb),1e-30));en=abs(by[aa]['max_energy_residual_fraction']-by[bb]['max_energy_residual_fraction'])
            comparisons.append({'type':label,'cases':[aa,bb],'common_time_ms':float(tm),'impulse_difference_fraction':diff,'maximum_energy_residual_change_fraction_of_initial':en,'impulse_pass':diff<=a['half_dt_impulse_relative'],'energy_change_pass':en<=a['half_dt_energy_residual_change_relative_to_initial'],'both_cases_individually_pass':by[aa]['all_checks_pass'] and by[bb]['all_checks_pass']})
    s={'created_utc':now(),'iteration':'AIRCRAFT-A10','cases':results,'spin_controls':spin,'comparisons':comparisons,'integrity_only_pass':True,'all_declared_checks_pass':all(r['all_checks_pass'] for r in results) and all(all(r['checks'].values()) for r in spin),'qualified_1D_numerical_contact_cases':[r['case']['id'] for r in results if r['case']['contact'] and r['all_checks_pass']],'whole_aircraft_cases':0,'main_solver_jobs':len(cases()),'old_solver_reruns':0,'native_global_initial_inertias_identified_for_tested_forms':all(r['checks']['initial_global_RKE_matches_native_inertia'] for r in spin),'native_part_RKE_ledger_qualified':False,'spatial_convergence_tested':False,'contact_option_transferred_to_aircraft':False,'energy_cause_identified':False,'physical_impact_qualified':False,'next_iteration':'AIRCRAFT-A11'}
    dump(OUT/'authoritative_review.json',s);print({'reviewed':len(results),'spin':len(spin),'qualified_1D_cases':s['qualified_1D_numerical_contact_cases'],'all_checks_pass':s['all_declared_checks_pass']},flush=True)

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists();s=read(OUT/'authoritative_review.json');assert s['integrity_only_pass'];v=harness();dump(OUT/'harness_after_calculations.json',v)
    start=time.perf_counter();count=preserved();dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'files':count,'seconds':time.perf_counter()-start})
    table='\n'.join(f"|{r['case']['id']}|{r['last_saved_time_ms']:.6f}|{100*r['max_energy_residual_fraction']:.5f}|{r['final_velocity_m_s'][0]:.7f}|{r['final_raw_contact_impulse_Ns']:.9f}|{100*min(r['momentum_plus_relative'],r['momentum_minus_relative']):.5f}|{100*r['support_momentum_relative']:.5f}|{','.join(r['failed_checks']) or 'aucun'}|" for r in s['cases'])
    rot='\n'.join(f"|{r['case']['spin_form']}|{r['predicted_inertia_sum_g_mm2']:.9g}|{r['initial_global_RKE_J']:.9g}|{r['initial_part_RKE_J']:.9g}|{100*r['global_relative_error']:.7f}|{','.join(r['failed_checks']) or 'aucun'}|" for r in s['spin_controls'])
    comp='\n'.join(f"|{' / '.join(r['cases'])}|{r['type']}|{100*r['impulse_difference_fraction']:.5f}|{100*r['maximum_energy_residual_change_fraction_of_initial']:.5f}|{r['impulse_pass']}/{r['energy_change_pass']}|" for r in s['comparisons'])
    jobs=[read(p) for p in OUT.glob('r*/**/*.execution.json')];sec=sum(j['seconds'] for j in jobs);dump(OUT/'execution_journal.json',{'created_utc':now(),'python':__import__('sys').version,'numpy':np.__version__,'native_software':'OpenRadioss Windows double precision build2026-07-28 (unchanged runtime)','threads':2,'GPU':False,'summed_recorded_stage_seconds':sec,'main_engine_jobs':s['main_solver_jobs'],'rejected_starter_only_jobs':1,'old_solver_reruns':0,'native_execution_records':[rel(p) for p in OUT.glob('r*/**/*.execution.json')],'source_commit':COMMIT,'source_binary_equivalence_established':False,'generator':rel(ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a10.py'),'reviewer':rel(Path(__file__))})
    REPORT.write_text(f'''# AIRCRAFT-A10 — témoin isolé et inerties natives

A10 est terminée comme diagnostic numérique limité : 17 Engine neufs (13 contacts, un libre, trois rotations initiales), un Starter initial rejeté et conservé, zéro ancien Engine. Les critères ne sont pas tous satisfaits. Une réduction de pas suffit à fermer les bilans du témoin contraint pour Stfac1 aux facteurs0,05/0,025, mais les contacts plus souples gardent un déficit. Aucun réglage n’est transféré à l’avion. A09 et ses échecs restent inchangés.

## 1. Faits directement observés et transcriptions

Plaque carrée20×20×1mm, façade témoin fixe40×40×1mm, distance initiale1,01mm et gap1mm. Déplacement libre uniquement suivantX, rotations bloquées pour le contact, aucune RBE3/ADMAS/rupture/masse ajoutée. LAW1, rho0,00278g/mm³, E70000MPa, nu0,3 sont des valeurs synthétiques déclarées. Masse mobile1,112g, vitesse1mm/ms =1m/s, K0=0,000556J, P0=0,001112N·s ; rebond conservatif attendu |J|=0,002224N·s et vx=-1m/s. L’énergie de contact fait partie du bilan pendant l’engagement.

Configuration principale et deux extensions horodatées avant leurs nouveaux calculs ; graine1102035, aucun tirage. Les dossiersr0/r1/r2 et chaque générateur sauvegardé rendent les tentatives traçables. Le Starterr0 signale1084 (LAW1 N5 devientN0), puis s’arrête avant Engine ; une déclaration de correction distincte imposeN0 pourr1/r2. Les critères restent inchangés. Les libellés natifs PART sont les noms des pièces, et NODE/INTER utilisent des indicesvar : premières erreurs de lecture conservées et corrections uniquement dans des relectures séparées. Tous les canaux CSV sont comparés aux records binaires T01 float32 natifs, sans modifier le CSV.

Les docs [TH/PART](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_part_starter_r.htm) distinguentRKE etRKERB. Dans le code primaire [{COMMIT}](https://github.com/OpenCourant/OpenCourant/tree/{COMMIT}), hist2.F écrit PARTSAV(22) pourRKE. cinmas.F donne, pour QEPH sans offset, I_nodal=(m/4)(A/12+t²/12) ; c3inmas.F utilise I_element=m(A/(9/2)+t²/12), distribué par les angles/pi. Cette dernière expression diffère de2A/6 utilisée en A09. pmass.F emploie une inertie sphérique stabilisée, dépendant de la longueur et des inerties de section, et pas seulement une inertie géométrique. Les valeurs sont testées ci-dessous à t0 ; l’équivalence intégrale du commit source et du binaire installé n’est pas démontrée.

BCS1TH accumule FTHREAC += (-a)·m·DT12 : sansTH/TITLE, REACX brut représente une impulsion cumulée, pas une force instantanée. Le témoin non nul confirme son égalité avec la variation finale de quantité de mouvement globale, à l’arrondi sauvegardé. La documentation générale la désigne comme force, ce qui ne suffit pas à lire le T-file brut de ce build. Les intégrales de force erronées restent dans review.json ; authoritative_review.json utilise directement l’impulsion et conserve les écarts intermédiaires dus au décalage temporel. A09 n’est pas réécrit.

## 2. Résultats d’un modèle officiel

Aucun résultat WTC/NIST n’est une cible, un critère, ou une donnée ajustée dans ces témoins. Les seules sorties officielles utilisées ici sont celles du solveur natif. Elles constituent des tests numériques, pas des résultats du modèle historique officiel.

## 3. Affirmations des archives locales

Aucune nouvelle lecture d’archive, photographie ou vidéo. Le suivi local A09 et la preuve de publication A08+A09 sont réutilisés. {count} fichiers antérieurs épinglés parSHA256 sont vérifiés inchangés, comprenant les chaînes de préservation héritées. V11F/V11R restent préservées ; V11S/I02I-M différées.

## 4. Hypothèses propres aux témoins

Ces plaques, les matériaux, la vitesse, l’absence de rupture et les appuis sont des choix de vérification. Un mouvement contraint1D ne reproduit ni un moteur, ni une aile, ni un avion traversant une tour. TYPE7 Istf4 etStfac1/0,01/0,001 sont des sensibilités ; aucune sélection en fonction de dégâts historiques. Le Starter confirme friction0, amortissement normal1e-20, friction visqueuse1 sans friction active, gap constant1 etN0 ; les champs natifs effectifs sont documentés, plutôt que supposés égaux à tous les noms de la déclaration initiale. La rotation initiale des témoins SPIN a les translations fixes et omegaZ=0,01rad/ms ; seuls l’état initial et les canaux d’inertie sont qualifiés, pas une rotation rigide physique.

Critères : résidu énergétique maximal≤1%K0, quantité de mouvement contact≤1%P0, appuis≤2%P0, vitesse finale±1%, variation d’impulsion demi-pas≤1%, variation de résidu demi-pas≤0,5%K0. Les fenêtres échantillonnées sont conservées ; l’intervalle demandé0,0001ms ne force pas une résolution plus fine que le pas réel.

## 5. Résultats dérivés

|Cas|Dernier échantillon ms|Max résidu %K0|vx final m/s|J brut N·s|Erreur contact %P0|Erreur appuis %P0|Critères échoués corrigés|
|---|---:|---:|---:|---:|---:|---:|---|
{table}

Le libre garde exactement K0 etvx aux sorties sauvegardées. La reconstruction indépendante des KE par masses nodales et vitesses est vérifiée. Rotation, énergie interne, hourglass et amortissement de contact sont nuls dans les témoins de translation ; aucun déficit n’est comblé par une énergie hypothétique.

|Paire|Comparaison|ΔJ %|Δmax résidu %K0|Critères J/E|
|---|---|---:|---:|---|
{comp}

|Rotation initiale|Somme inerties prévue g·mm²|RKE global J|RKE pièce J|Erreur global %|Critères échoués|
|---|---:|---:|---:|---:|---|
{rot}

Les trois RKE globaux initiaux sont reproduits par les inerties natives déclarées. Le RKE par pièce est différent pourTRIA et nul pourBEAM alors que le global est positif. La signification globaleRKE est donc bornée par ces essais, mais le ledger localRKE reste non qualifié. NiRKE niRKERB ne doivent être ajoutés arbitrairement au bilan global. Les scripts, sorties complètes et unités sont sauvegardés ; temps cumulé des étapes natives et convertisseurs : {sec:.3f}s, CPU2threads, pasGPU.

## 6. Contradictions, données manquantes et suite

Les anciens échecs, le passage automatiqueN5→N0, l’ambiguïté force/impulsion brute et les désaccordsRKE par pièce sont conservés. Les contacts plus souples présentent des pertes finales et maximales qui persistent sous raffinement temporel ; leur cause algorithmique n’est pas identifiée. Le bon bilan àStfac1 ne qualifie qu’un témoin simple à translation contraint1D, sans convergence spatiale ni problème de fracture. Aucune explication exhaustive du déficit A09 n’est établie.

{NEXT}

Impact et écrasement historiques non qualifiés ; localisation en flexion après fracture complète non validée ; température imposée distincte d’un incendie calculé ; tests numériques distincts d’une validation de l’effondrement réel ; Blender reste une visualisation. Aucun Blender, aucune publication et aucun envoi externe n’ont été réalisés dansA10.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Passation AIRCRAFT-A10 → A11

Lire AGENTS.md, harness/state.json, cette passation, puis harness/publication_cycle.json. A10 terminée comme diagnostic limité, état local prioritaire. Résultats : wtc1_simulation_v8/output/aircraft_a10/authoritative_review.json et rapport_aircraft_a10.md ; configuration aircraft_a10_predeclaration.json + syntax_correction_predeclaration.json + extension_predeclaration.json + half_dt_extension_predeclaration.json. Graine1102035, aucun tirage. 17 nouveaux Engine (13contacts, 1libre, 3rotation initiale), un Starterr0 rejeté1084 conservé ; zéro ancien Engine, {count} fichiers antérieurs épinglés inchangés.

Témoin LAW1 quad20×20×1mm contrequad fixe40×40×1mm, rho0,00278g/mm³,E70000MPa,nu0,3, vx1m/s, contact àgap1mm depuisx=-1,01mm. Masse1,112g,K0=0,000556J,P0=0,001112N·s. SansRBE3/ADMAS/rupture/GPU. r1/r2 utilisentN0 explicitement ; r0N5, premières erreurs de lecteurs et anciens review.json conservés. authoritative_review.json fait foi ; tous CSV comparés aux T01 binaires.

Libre : énergie etv constantes exactement à la précision sauvegardée. Stfac1 : maxrésidu18,238% àdt0,8,4,780% à0,4,0,466% à0,1,0,181% à0,05,0,142% à0,025. Demi-pas0,05/0,025 passe les critères du témoin. Stfac0,01/0,001 conservent maxrésidus≈1,195%/3,713% à0,025 : cause non identifiée, aucune compensation inventée. Convergence spatiale non testée, aucune option transférée à l’avion.

Rotation t0 : globalQUAD/TRIA/BEAM reproduit par les inerties natives. QUAD I_n=m/4(A/12+t²/12) ; TRIA I_e=m(2A/9+t²/12), angles/pi ; BEAM inertie sphérique stabilisée (pmass.F). RKE pièceTRIA diffère duglobal, BEAMRKEpièce0 malgréglobal>0. ledger local non qualifié. Source commit{COMMIT} ; équivalence intégrale source/binaire non démontrée. Ne pas ajouter desRKE pour fermer un déficit.

REACX brut T-file sansTH/TITLE = impulsion cumulée, BCS1TH accumule(-a)mDT12 ; témoin non nul confirmé à la fin. Ne pas réintégrer comme force. Écarts intermédiaires de décalage temporel restent visibles ; ancienne lecture dansreview.json conservée. A09 reste intacte.

{NEXT}

PublicationA08+A09 déjà vérifiée : outputs/github_publication/updates_2026-10-06_aircraft_a08_a09/final_remote_verification.json. A10 seule en attente après enregistrement, paireA10+A11 suivante ; ne pas republierA08+A09, pasX niYoremi. V11F/V11R intactes, V11S/I02I-M différées. Impact/écrasement historiques et effondrement réel non qualifiés ; température imposée≠incendie calculé ; Blender visualisation. Aucun scan archive ni nouveau calcul ancien.
''',encoding='utf-8')
    # Seal every new source, input, script, rejected attempt and result; mutable state is verified separately.
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[p for p in SRC.rglob('*') if p.is_file()]+[CFG,ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a10.py',Path(__file__),HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(paths))]})
    print({'prepared':True,'old_files_verified':count,'report':rel(REPORT),'manifest_files':len(paths)},flush=True)

def register():
    guard();s=read(OUT/'authoritative_review.json');assert REPORT.exists() and HANDOFF.exists();state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');assert state['current_iteration']=='AIRCRAFT-A09' and cycle['pending_count']==0;assert harness()['Status']=='PASS';verify_artifacts();t=now()
    record={'experiment_id':'WTC1-AIRCRAFT-A10','registered_at':t,'status':'completed_isolated_elastic_contact_and_native_inertia_diagnostic_with_retained_failed_gates','configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'authoritative_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'integrity_only_pass':True,'all_declared_checks_pass':s['all_declared_checks_pass'],'branch_iteration_count':10,'whole_aircraft_iteration_count':9,'whole_aircraft_cases':0,'main_solver_jobs':17,'old_solver_reruns':0,'old_files_preserved':read(OUT/'preservation_verification.json')['files'],'qualified_1D_contact_cases':s['qualified_1D_numerical_contact_cases'],'native_global_initial_inertias_identified':True,'native_part_RKE_ledger_qualified':False,'spatial_convergence_tested':False,'energy_cause_identified':False,'contact_option_transferred_to_aircraft':False,'physical_impact_qualified':False,'engine_crushing_qualified':False,'next_iteration':'AIRCRAFT-A11','NIST_outcomes_used_as_target':False}
    prefix=(OUT/'before_registry.jsonl').read_bytes();assert (ROOT/'harness/experiments/registry.jsonl').read_bytes()==prefix
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A10',next_iteration='AIRCRAFT-A11',current_status=record['status'],next_objective=NEXT,updated_at=t);state['aircraft_a10_key_results']=record
    state['validated_artifacts'].update(aircraft_a10_report=rel(REPORT),aircraft_a10_results=rel(OUT/'authoritative_review.json'),aircraft_a10_handoff=rel(HANDOFF))
    state['user_steering_2026_10_05']['next']='AIRCRAFT-A11';cycle.update(pending_iterations=['AIRCRAFT-A10'],pending_count=1,next_publication_after='After verified A11, publish A10+A11; A08+A09 already published',updated_at=t)
    dump(ROOT/'harness/state.json',state);dump(ROOT/'harness/publication_cycle.json',cycle);verify(write=True)

def verify_artifacts():
    m=read(OUT/'artifact_manifest.json');bad=[r['path'] for r in m['files'] if sha(ROOT/r['path'])!=r['sha256']];assert not bad,bad;return len(m['files'])

def verify(write=False):
    guard();n=verify_artifacts();old=preserved();before=read(OUT/'before_state.json');s=read(ROOT/'harness/state.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();cy=read(ROOT/'harness/publication_cycle.json');v=harness()
    protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_artifacts_verified':True,'old_files_unchanged':old==read(OUT/'preservation_verification.json')['files'],'prior_evidence_and_A09_unchanged':all(s[k]==before[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A10','state_route':s['current_iteration']=='AIRCRAFT-A10' and s['next_iteration']=='AIRCRAFT-A11','publication_cadence':cy['pending_iterations']==['AIRCRAFT-A10'] and cy['pending_count']==1 and cy['last_published_iteration']=='AIRCRAFT-A09','A08_A09_publication_evidence_preserved':read(ROOT/'outputs/github_publication/updates_2026-10-06_aircraft_a08_a09/final_remote_verification.json')['pass'],'all_failed_checks_visible':not read(OUT/'authoritative_review.json')['all_declared_checks_pass'],'report_and_handoff_exist':REPORT.exists() and HANDOFF.exists(),'harness_pass':v['Status']=='PASS'}
    result={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':old,'harness':v,'physical_impact_qualified':False,'contact_option_transferred_to_aircraft':False,'next_iteration':'AIRCRAFT-A11'};assert result['pass'],result
    if write:dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['review','prepare','register','verify']);globals()[p.parse_args().action]()
