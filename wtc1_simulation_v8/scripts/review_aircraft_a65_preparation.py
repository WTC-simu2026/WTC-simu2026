"""Independent static card delta and current-state handoff, without native replay."""
from prepare_aircraft_a65_sampling import ROOT,PREP,PLAN,read,dump,sha,now,rel,harness
import json,re

cfg=read(PLAN);prep=read(PREP/'preparation_review.json');state=read(ROOT/'harness/state.json')
assert state['current_iteration']=='AIRCRAFT-A64' and state['next_iteration']=='AIRCRAFT-A65'
assert sha(PLAN)==prep['plan_sha256']
assert not (ROOT/'wtc1_simulation_v8/output/aircraft_a65').exists()
old=read(ROOT/'wtc1_simulation_v8/data/aircraft_a64_predeclaration.json')
assert cfg['cohesive']==old['cohesive'] and cfg['cases']==old['cases'] and cfg['acceptance']==old['acceptance']
rows=[]
for entry in prep['card_changes']:
    a=(ROOT/entry['original']).read_text(encoding='utf8').splitlines()
    b=(ROOT/entry['proposed']).read_text(encoding='utf8').splitlines()
    assert len(a)==len(b)
    changes=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    expected=[i+1 for i,x in enumerate(a) if x=='/TFILE/4' or x.startswith('/RUN/')]
    assert changes==sorted(expected)
    dt=next(c['dt_cap_ms'] for c in cfg['cases'] if c['id']==entry['case'])
    assert float(b[a.index('/TFILE/4')+1])==dt/2
    run=next(i for i,x in enumerate(a) if x.startswith('/RUN/'))
    assert float(b[run+1])==1+dt/2
    rows.append({'case':entry['case'],'changed_line_numbers':[i+1 for i in changes],
        'unchanged_other_lines':len(a)-len(changes),'mass_material_step_and_solver_cards_unchanged':True})
for case in cfg['whole_CHECK_cases']:
    for p in case['files']:assert sha(ROOT/p['path'])==p['sha256']
assert sha(ROOT/prep['runner'])==prep['runner_sha256']
script=(ROOT/prep['runner']).read_text(encoding='utf8')
assert "wtc1_simulation_v8/data/aircraft_a65_authorization.json" in script and "wtc1_simulation_v8/data/aircraft_a65_predeclaration.json" in script
assert "h['CurrentIteration']=='AIRCRAFT-A64'" in script
assert "['pending_iterations']==['AIRCRAFT-A64']" in script
assert "old=ROOT/'wtc1_simulation_v8/output/aircraft_a64'" in script
assert "import review_aircraft_a63_free as reviewer" in script
compile(script,prep['runner'],'exec')
handoff=ROOT/'harness/handoffs/PROMPT_REPRISE_A65_2026-10-14.md';assert not handoff.exists()
text='''# Reprise WTC1 — AIRCRAFT-A64 terminée, A65 préparée

Répertoire : C:/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an

Lire AGENTS.md, harness/state.json, harness/publication_cycle.json, puis intégralement les fichiers ci-dessous. L’état local actuel prime sur ce prompt et les anciennes notes.

## Reprise courte

- wtc1_simulation_v8/output/aircraft_a64/rapport_aircraft_a64.md
- wtc1_simulation_v8/output/aircraft_a64/scientific_assessment.json
- wtc1_simulation_v8/output/aircraft_a64/composite_qualification_review.json
- wtc1_simulation_v8/output/aircraft_a64/sampling_and_actual_cycle_review.json
- wtc1_simulation_v8/output/aircraft_a64/publication_verification.json
- wtc1_simulation_v8/output/aircraft_a65_preparation/proposition_sorties_completes_a65.md
- wtc1_simulation_v8/data/aircraft_a65_proposal.json
- wtc1_simulation_v8/output/aircraft_a65_preparation/preparation_review.json
- wtc1_simulation_v8/output/aircraft_a65_preparation/static_card_and_handoff_review.json
- outputs/github_publication/updates_2026-10-13_aircraft_a62_a63/final_remote_verification.json

## État à la rédaction

AIRCRAFT-A64 terminée et enregistrée, registre183, prochaineA65. Aucun calcul en cours. PublicationA62+A63 vérifiée : scientifique9b31dd199a9e2b5ed9efba838d16c51bc43fd617, confirmationc00f00afa451e718206b5502cf5babedf3a8536d, deuxCI PASS, anciennes archives conservées. Tag snapshot-2026-10-13-aircraft-a62-a63 conservé. Cadence pending[AIRCRAFT-A64], publication aprèsA64+A65.

Le sixième moteurA62 SHAd36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235 reste inchangé. Les12contrôles du lotA61 ont été consommés enA62(10)+A63(2). Accord humain «continue» sur le planA64 enregistré dans data/aircraft_a64_authorization.json : deux essais locaux exécutés ; deux CHECK conditionnels non exécutés, condition locale échouée. Ne pas convertir leurs créneaux en essais de remplacement sans nouvel accord.

A64 : deux Starter propres, deux Engine NORMAL1ms nominal, dt0,000125/0,0000625ms. Le premier passe22contrôles. Le second en échoue11 car TFILE0,0001ms omet6000pas et le lecteur repris supposait chaque cycle ; son champ terminal complet sauvegardé ne rejoint pas1ms. Les échecs et analyses initiales restent intacts. Aux cycles réellement sauvegardés, déplacement exact≤7,31e-10mm, compteurs natifs KE/IE vs solution≤5,58e-10J, conservation native≤6,01e-10J, impulsion/support≤2,21e-9Ns. Comparaisons des compteurs KE/IE aux temps communs passent le seuil inchangé1,01e-5J. Cela ne promeut pas le composé initial et ne fabrique pas les champs manquants. Aucun CHECK entier nouveau lancé.

A65 préparée, non exécutée, accord demandé mais aucune réponse connue à cette rédaction. Exactes cartes et différences dans output/aircraft_a65_preparation. Deux réglages : TFILEdt/2 ; arrêt1+dt/2 pour sauvegarder réellement la frontière cible1ms, borne d’overshoot d’un pas préexistante inchangée. Matériaux, masses8g instrumentales, pas, supports, vitesse initiale, seuils et moteur inchangés. Maximum4nouveaux Engine/CPU1/cap180s, estimation2–5minutes, sanscompilation/GPU/installation. Deux témoins, puis deux CHECK entiers strictement conditionnels au passage de tous les critères. Anciennes entrées CHECK originales/appariées exactes, empreintes vérifiées ; aucune extension dynamique entière.

Après accord explicite sur ce lot précis, créer un reçu A65 avec empreintes du plan/proposition, maximum_native_runs4 ; puis utiliser scripts/run_aircraft_a65_sampling.py declare, free, review_free ; whole seulement si le composé passe. Ne pas déduire une autorisation de ce prompt. Le lanceur est prêt ; conserver toute nouvelle panne et ne pas élargir le budget sans accord.

Les défauts au repos/observables imposésA62, convergence temporelle grossièreA63, domaines matériaux/inerties/bilans locaux et grandes rotations restent ouverts. Ancien CHECK15erreurs/624volumes/cinqTYPE25 ignorés ; A52nonintégré. Aucune nouvelle modification moteur préparée ou autorisée parA65. Toute future modification/compilation tierce exige une proposition concrète et un accord distinct.

Objectif1 : dix secondes physiques d’impact avion–façade, puis visualisation3D/MP4 ouGIF. Meilleur impact entier0,0200001220703125s, objectif incomplet. Conditions réalistes documentées, aucune cible de dégâts connus. Préserver budgets/anciens résultats et critères échoués ; aucun RKE compensateur. Ne pas rejouer les diagnostics déjà vérifiés. Nouvelles courtes en français. Harnais avant/après travail important ; rapport réel avant état/registre. Archives sources en lecture seule.
'''
handoff.write_text(text,encoding='utf8')
dump(PREP/'static_card_and_handoff_review.json',{'created_utc':now(),'pass':True,'card_differences':rows,
    'source_and_acceptance_unchanged':True,'whole_initial_states_and_cards_rehashed':True,
    'no_A65_native_execution':True,'no_source_patch_or_compilation':True,
    'handoff':rel(handoff),'handoff_sha256':sha(handoff),'runner_sha256':sha(ROOT/prep['runner']),
    'harness':harness()})
print(json.dumps({'A65_static_preparation_pass':True,'handoff':rel(handoff),'authorization_pending':True}),flush=True)
