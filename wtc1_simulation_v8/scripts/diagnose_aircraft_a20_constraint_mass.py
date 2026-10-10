"""Additional Starter listing only; unchanged mechanics, no additional impact."""
from run_aircraft_a20_whole import *

def main():
    whole_guard();o=D/'constraint_mass_listing';assert not o.exists();o.mkdir()
    source=D/(N+'_0000.rad');pins=streamsha(source)
    dump(o/'declaration.json',{'declared_utc':now(),'only_change':'IOFLAG Ipri6, print nodal masses and RBE2 hierarchy','mechanical_inputs_unchanged':True,'new_engine_run':False,'source_deck_sha256':pins,
        'goal':'Reconcile the new1.145kg animation mass sum discrepancy against native constraint mass transfers, without assuming a physical added mass or subtracting an invented term.',
        'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/ioflag_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe2_starter_r.htm']})
    b=blocks(source.read_text().splitlines());assert not any(x[0]=='/IOFLAG' for x in b)
    lines=[line for block in b if block[0]!='/END' for line in block]+['/IOFLAG',ii(6)+' '*20+ii(-1,0,0,0),'/END']
    (o/source.name).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    assert execute(RUNTIME/'starter_win64.exe',['-i',source.name,'-np','1'],o,'starter.log',180,env());assert streamsha(source)==pins
    text=(o/(N+'_0000.out')).read_text(errors='replace');dump(o/'completion.json',{'created_utc':now(),'source_deck_unchanged':True,'listing_bytes':len(text.encode()),'no_engine_run':True,'new_source_deck_sha256':streamsha(o/source.name)})
    print({'listing_created':rel(o/(N+'_0000.out')),'source_deck_unchanged':True},flush=True)

def analyze():
    whole_guard();o=D/'constraint_mass_listing';assert not (o/'nodal_mass_crosscheck.json').exists()
    s=(o/(N+'_0000.out')).read_text(errors='replace');tail=re.split(r'\n\s*NODAL MASSES\s*\n',s)[-1];nodes={}
    for line in tail.splitlines():
        if not re.match(r'\s*\d+\s+[\d.E+\-]+',line):
            if nodes:break
            continue
        x=line.split();assert len(x)%2==0
        for j in range(0,len(x),2):nodes[int(x[j])]=float(x[j+1].replace('D','E'))
    q=fast(D/'initial_diagnostic'/(N+'A001'));assert len(nodes)==len(q['nid'])
    nm=np.array([nodes[int(i)] for i in q['nid']]);diff=q['node_mass_g']-nm;M=read(D/'native_insertion_gate.json')['mass_CG_new'][0];m=read(D/'mesh.json')
    deps={i for r in m['new_RBE2'] if r['role']=='root' for i in r['dependent_nodes']};depmass=sum(nodes[i] for i in deps)
    r={'created_utc':now(),'Starter_nodal_mass_count':len(nodes),'Starter_nodal_mass_sum_g':float(nm.sum()),'Starter_physical_mass_g':M,'RBE2_root_dependent_mass_g':depmass,
        'Starter_nodal_sum_minus_root_dependents_g':float(nm.sum()-depmass),'Starter_duplicate_mass_residual_g':float(nm.sum()-depmass-M),'initial_animation_sum_g':float(q['node_mass_g'].sum()),
        'animation_minus_Starter_nodal_sum_g':float(diff.sum()),'nodes_mass_field_changed_above_.01g':[int(i) for i,e in zip(q['nid'],diff) if abs(e)>.01],
        'physical_added_mass_explanation_proven':False,'input_density_ADMAS_unchanged':True,'no_mass_term_subtracted_from_energy_or_momentum':True,'complete_constraint_nodal_mass_semantics_qualified':False}
    dump(o/'nodal_mass_crosscheck.json',r);print({k:v for k,v in r.items() if not isinstance(v,list)},flush=True)

def interpret():
    whole_guard();o=D/'constraint_mass_listing';p=o/'constraint_mass_interpretation.json';assert not p.exists();r=read(o/'nodal_mass_crosscheck.json')
    M=r['Starter_physical_mass_g'];dup=r['RBE2_root_dependent_mass_g'];rounding=r['animation_minus_Starter_nodal_sum_g'];checks={
        'printed_nodal_sum_equals_physical_mass_plus_root_dependents':abs(r['Starter_duplicate_mass_residual_g'])<.001,
        'animation_and_printed_mass_sum_within_float32_quantization':abs(rounding)<np.finfo(np.float32).eps*M,
        'input_density_ADMAS_unchanged':r['input_density_ADMAS_unchanged'],'no_energy_or_momentum_term_adjusted':r['no_mass_term_subtracted_from_energy_or_momentum']}
    checks={k:bool(v) for k,v in checks.items()}
    result={'created_utc':now(),'checks':checks,'pass':all(checks.values()),'physical_mass_g':M,'duplicated_root_dependent_mass_g':dup,'printed_balance_residual_g':r['Starter_duplicate_mass_residual_g'],
        'float32_animation_sum_rounding_g':rounding,'interpretation':'The Starter NODAL MASSES sum retains root dependent masses while the RBE2 main nodes carry their transferred mass. This field sum is not a physical material-mass total. Subsequent TYPE2 redistribution may change individual fields, so subtracting the current secondary animation masses is not a justified physical reconstruction.',
        'original_raw_animation_mass_sum_gate_preserved':True,'all_original_checks_pass':False,'no_nodal_KE_or_momentum_correction_applied':True,
        'root_rotational_inertia_and_dynamic_energy_qualified':False,'added_physical_material_mass_detected':False,'physical_impact_qualified':False}
    dump(p,result);print(result,flush=True);assert result['pass']

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['main','analyze','interpret'],default='main',nargs='?');globals()[p.parse_args().action]()
