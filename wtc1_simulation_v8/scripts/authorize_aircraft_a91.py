"""Record direct authorization for the exact projected-null source patch and A91 lot."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel

def main():
    plan=ROOT/'wtc1_simulation_v8/data/aircraft_a90_proposal.json';p=read(plan)
    proposal=ROOT/'wtc1_simulation_v8/output/aircraft_a90_preparation/proposition_correction_libre_projetee_A91.md'
    assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A90'
    assert read(ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a88_a89/final_remote_verification.json')['pass']
    dump(ROOT/'wtc1_simulation_v8/data/aircraft_a91_authorization.json',{'created_utc':now(),'explicit_human_authorization':True,
        'answer':'Oui, appliquer le correctif A90, compiler et exécuter A91',
        'question_item':'request_user_input_async/call_eb3cec6ec1704469a8b062d90392f066/0',
        'plan':rel(plan),'plan_sha256':sha(plan),'proposal':rel(proposal),'proposal_sha256':sha(proposal),
        'patch_sha256':p['patch']['patch_sha256'],'proposed_source_sha256':p['patch']['proposed_sha256'],
        'maximum_build_s':3600,'CPU_build':6,'maximum_Engine':4,'maximum_Starter':0,'CPU_native':1,'each_native_cap_s':180,
        'GPU':False,'installation':False,'whole_dynamic_extension':False,'prior_budgets_not_reset':True,
        'case_order_and_conditional_gates_approved':True})
    print('Exact A90 patch/A91 build and conditional lot explicitly authorized.',flush=True)

if __name__=='__main__':main()
