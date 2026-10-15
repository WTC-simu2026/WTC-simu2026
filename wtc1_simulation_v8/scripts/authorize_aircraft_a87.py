"""Record direct authorization of the exact A86 patch and bounded A87 lot."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel

def main():
    plan=ROOT/'wtc1_simulation_v8/data/aircraft_a86_proposal.json';p=read(plan)
    proposal=ROOT/'wtc1_simulation_v8/output/aircraft_a86_preparation/proposition_criteres_relatifs_exactement_nuls_A87.md'
    assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A86'
    assert read(ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a84_a85/final_remote_verification.json')['pass']
    dump(ROOT/'wtc1_simulation_v8/data/aircraft_a87_authorization.json',{
        'created_utc':now(),'explicit_human_authorization':True,
        'answer':'Oui, appliquer le correctif A86, compiler et exécuter A87',
        'question_item':'request_user_input_async/call_a7e8e12bd9604e8ea2f8c1de6ddb4d3f/0',
        'plan':rel(plan),'plan_sha256':sha(plan),'proposal':rel(proposal),'proposal_sha256':sha(proposal),
        'patch_sha256':p['patch']['patch_sha256'],'proposed_source_sha256':p['patch']['proposed_sha256'],
        'maximum_build_s':3600,'CPU_build':6,'maximum_Engine':4,'maximum_Starter':0,'CPU_native':1,'each_native_cap_s':180,
        'GPU':False,'installation':False,'whole_dynamic_extension':False,'prior_budgets_not_reset':True,
        'case_order_and_conditional_gates_approved':True})
    print('Exact A86 patch/A87 build and conditional control authorization recorded.',flush=True)

if __name__=='__main__':main()
