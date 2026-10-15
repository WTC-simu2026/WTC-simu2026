"""Record the direct authorization for the single second-trial observation."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel

def main():
    plan=ROOT/'wtc1_simulation_v8/data/aircraft_a88_proposal.json'
    proposal=ROOT/'wtc1_simulation_v8/output/aircraft_a88_preparation/proposition_observation_second_essai_A89.md'
    assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A88'
    assert read(ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a86_a87/final_remote_verification.json')['pass']
    dump(ROOT/'wtc1_simulation_v8/data/aircraft_a89_authorization.json',{'created_utc':now(),'explicit_human_authorization':True,
        'answer':'Oui, exécuter l’observation A89','question_item':'request_user_input_async/call_983cb4f571c74eff9c7f88cff44ed49d/0',
        'plan':rel(plan),'plan_sha256':sha(plan),'proposal':rel(proposal),'proposal_sha256':sha(proposal),
        'maximum_Engine':1,'maximum_Starter':0,'CPU_threads':1,'cap_s':180,'GPU':False,'source_patch':False,
        'compilation':False,'installation':False,'whole_dynamic_extension':False,'prior_budgets_not_reset':True})
    print('A89 explicit authorization recorded.',flush=True)

if __name__=='__main__':main()
