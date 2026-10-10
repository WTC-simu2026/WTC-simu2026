"""Source and saved-output audit; no model, acceptance or ledger modification."""
from pathlib import Path
import numpy as np
from run_aircraft_a14 import OUT,ROOT,read,dump,now,streamsha,rel,CFG

commit='0168ab344bd743051e996d90c7c8d80728bb04a8'
paths=['engine/source/output/th/thnod.F','engine/source/assembly/velocity.F','engine/source/output/th/thkin.F','engine/source/output/th/hist1.F','engine/source/output/th/hist2.F','engine/source/engine/resol.F','engine/source/constraints/general/bcs/bcs10.F','engine/source/output/outfile/collect.F','engine/source/output/sortie_main.F','engine/source/output/reaction_forces_th.F','engine/source/assembly/asspar_sub_poff.F','engine/source/elements/shell/coque/cbilan.F']
assert not (OUT/'timing_audit.json').exists()
sources=[]
for q in paths:
    p=OUT/'sources'/Path(q).name
    sources.append({'path':rel(p),'url':f'https://raw.githubusercontent.com/OpenCourant/OpenCourant/{commit}/{q}','commit':commit,'bytes':p.stat().st_size,'sha256':streamsha(p),'redistribution':'exclude_third_party'})
evidence=[{'file':'thnod.F','lines':[126,154],'finding':'TH/NODE global-coordinate branch writes D,V,A,VR,AR arrays directly; this routine does not center velocities.'},
          {'file':'velocity.F','lines':[57,64],'finding':'Velocity update V=V+DT12*A then clears A. Source statement is verified; full mapping of DT12 and output call order to installed binary remains unproven.'},
          {'file':'hist2.F','lines':[308,324],'finding':'Global histories write ENCIN, XMOMT, DT2, ENROT and contact energies independently of direct TH/NODE.'},
          {'file':'reaction_forces_th.F','lines':[65,74],'finding':'Reaction buffer accumulates IFLAG*MS*A*DT12. Saved native output is cumulative impulse; it is not reintegrated as force.'},
          {'file':'cbilan.F','lines':[175,194],'finding':'Quad kinetic energy/momentum use sums of nodal or element-local velocities. Complete trace of these velocities relative to TH/NODE not established.'},
          {'file':'resol.F','lines':[1318,1324],'finding':'Source explicitly notes SORTIE_MAIN before integration of accelerations; this supports distinct recording phases, but does not establish binary equivalence.'}]
config=read(CFG);a=config['acceptance'];summary=read(OUT/'plate_review.json');rows=[]
for r in summary['cases']:
    z=np.load(OUT/'r0'/r['case']['id']/'balance_history_SI.npz');P=z['momentum_Ns'];J=z['impulse_Ns'];S=z['support_Ns'];ph=r['phase_candidates']
    rows.append({'case':r['case']['id'],'maximum_global_contact_balance_error_Ns':float(np.max(np.linalg.norm(P-P[0]+J,axis=1))),
        'maximum_global_support_balance_error_Ns':float(np.max(np.linalg.norm(P-P[0]-S,axis=1))),
        'maximum_contact_support_balance_error_Ns':float(np.max(np.linalg.norm(J+S,axis=1))),
        'actual_step_range_ms':[float(z['timestep_ms'].min()),float(z['timestep_ms'].max())],
        'phase_candidates':[{**p,'diagnostic_KE_limit_J':a['phase_centered_KE_fraction_initial']*22.24,'diagnostic_momentum_limit_Ns':a['phase_centered_momentum_fraction_initial']*.2224,
        'diagnostic_KE_pass':p['max_KE_change_error_J']<=a['phase_centered_KE_fraction_initial']*22.24,'diagnostic_momentum_pass':p['max_momentum_change_error_Ns']<=a['phase_centered_momentum_fraction_initial']*.2224} for p in ph],
        'all_prior_failed_checks_retained':True})
proof={'created_utc':now(),'source_commit':commit,'source_binary_equivalence_established':False,'full_phase_call_chain_proven':False,'source_files':sources,'source_evidence':evidence,'saved_output_diagnostics':rows,
    'raw_output_and_ledgers_unchanged':True,'only_predeclared_factors_tested':[0,-.5,.5],
    'conclusion':'Plus-half-step acceleration strongly reduces nodal/global KE and momentum mismatch, but does not qualify global/contact timestamp alignment. No recentered ledger, no added energy and no retroactive case credit.',
    'A15_required':'Fresh temporal/gap controls with an explicitly declared output-phase contract; retain native and analytic comparisons separately.'}
dump(OUT/'timing_audit.json',proof);print({'source_files':len(sources),'cases':len(rows),'binary_equivalence':False})
