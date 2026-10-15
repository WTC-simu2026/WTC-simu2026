"""Record the direct human reply for the single A85 observation."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel

def main():
    plan=ROOT/'wtc1_simulation_v8/data/aircraft_a84_proposal.json'
    proposal=ROOT/'wtc1_simulation_v8/output/aircraft_a84_preparation/proposition_mesure_references_brutes_A85.md'
    proof=ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a82_a83/final_remote_verification.json'
    assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A84'
    assert read(proof)['pass']
    dump(ROOT/'wtc1_simulation_v8/data/aircraft_a85_authorization.json',{
        'created_utc':now(),'explicit_human_authorization':True,'answer':'Oui, exécuter l’observation A85',
        'question_item':'request_user_input_async/call_61565801d9904c9cb78dcc622dc9c5d6/0',
        'plan_path':rel(plan),'plan_sha256':sha(plan),'proposal':rel(proposal),'proposal_sha256':sha(proposal),
        'maximum_Engine':1,'maximum_Starter':0,'CPU_threads':1,'cap_s':180,
        'GPU':False,'source_patch':False,'compilation':False,'installation':False,'whole_dynamic_extension':False,
        'condition_publication_A82_A83_verified':True,'publication_proof_path':rel(proof),
        'prior_budgets_not_reset':True})
    print('A85 explicit human authorization recorded.',flush=True)

if __name__=='__main__':main()
