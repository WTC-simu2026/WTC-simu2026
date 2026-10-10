"""Read-only curved-root inventory and native shell inertia diagnosis, without balance repair."""
from run_aircraft_a25 import *
import urllib.request

def main():
    guard();dest=OUT/'root_geometry_preparation.json';assert not dest.exists();m=read(SOURCE/'mesh.json');xyz=np.asarray(m['nodes_mm']);roots=[r for r in m['new_RBE2'] if r['role']=='root'];tn=m['original_triangle_node_ids'];ti=m['aircraft_triangle_ids'];tp=m['aircraft_triangle_part_ids'];rows=[]
    for r in roots:
        body=[{'element':i,'part':p,'nodes':n,'points_mm':xyz[np.asarray(n)-1].tolist()} for i,p,n in zip(ti,tp,tn) if r['host'] in n and p==1]
        assert body
        anchors=[]
        for ni in r['dependent_nodes']:
            skins=[{'element':q['id'],'part':q['part'],'facet':q['facet'],'side':q['side'],'nodes':q['nodes'],'points_mm':xyz[np.asarray(q['nodes'])-1].tolist(),'normal':m['radome_facets'][q['facet']-1]['normal']} for q in m['radome_skin_quads'] if ni in q['nodes']]
            assert skins
            anchors.append({'node':ni,'point_mm':xyz[ni-1].tolist(),'offset_from_host_mm':(xyz[ni-1]-xyz[r['host']-1]).tolist(),'candidate_main_skin_faces':skins})
        rows.append({'root_RBE2_to_replace_only_after_qualification':r['id'],'host':r['host'],'host_point_mm':xyz[r['host']-1].tolist(),'body_main_faces':body,'body_shell_thickness_mm':2.54,'skin_shell_thickness_mm':.5,'anchors':anchors})
    ids=[a['node'] for r in rows for a in r['anchors']];assert len(rows)==24 and len(ids)==144 and len(set(ids))==144
    dump(dest,{'created_utc':now(),'source':rel(SOURCE/'mesh.json'),'sha256':streamsha(SOURCE/'mesh.json'),'roots':rows,'root_count':24,'distinct_anchor_nodes':144,'prototype_flat_mass_g':.00556,'naive_144_flat_mass_g':.80064,'actual_root_mass_not_yet_defined':True,'geometry_not_as_built':True,'do_not_carry_flat_dsearch_blindly':True,'curved_native_controls_executed':False,'whole_source_not_modified':True,'whole_insertion_ready':False,'goal_complete':False})
    sources=[]
    for name,url in [('shell_mechanical_properties','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_element_mechanical_prop_r.htm'),('tshell','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type20_tshell_starter_r.htm'),('composite_material','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law25_compsh_starter_r.htm')]:
        q=OUT/'sources'/(name+'.html');assert not q.exists();q.write_bytes(urllib.request.urlopen(url,timeout=45).read());sources.append({'url':url,'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q),'redistribution':'exclude_third_party'})
    dump(OUT/'inertia_source_manifest.json',{'created_utc':now(),'files':sources})
    observed=[];shell_mass=.183+.139;physical_I=shell_mass*.5**2/12
    for ax in 'XYZ':
        d=PREV/'w3'/f'REFERENCE_FREE_ROTATION_S100_{ax}';g=read(d/'generation.json');H=histories(d/(g['name']+'T01.csv'));native=float(H['ROTATION ENERGY'][0]*.001);physical=.5*physical_I*100*.001 if ax!='Z' else 0;tol=.002*physical+1e-7
        observed.append({'axis':ax,'source_csv':rel(d/(g['name']+'T01.csv')),'source_csv_sha256':streamsha(d/(g['name']+'T01.csv')),'native_initial_RKE_J':native,'native_scalar_sum_I_g_mm2':native*2/(100*.001),'physical_thickness_initial_RKE_J':physical,'native_minus_physical_J':native-physical,'physical_initial_RKE_limit_J':tol,'physical_initial_RKE_pass':bool(abs(native-physical)<tol)})
    dump(OUT/'shell_inertia_diagnostic.json',{'created_utc':now(),'rows':observed,'all_physical_initial_RKE_pass':all(r['physical_initial_RKE_pass'] for r in observed),'native_RKE_preserved_in_balance':True,'no_scalar_RKE_subtracted_reconstructed_added_or_compensated':True,
      'derived_physical_thickness_I_g_mm2':physical_I,'known_nodal_geometry_mass_contribution_already_in_translation':True,
      'primary_theory':'Radioss shell inertia contains a spherical regularized area term m*(A/f+t²/12). This is a discretization term, not solely the physical inertia across thickness. Default f values from theory do not alone determine this composite/tied fixture nodal inertias.',
      'unproven':'The per-node native inertia and tied-core redistribution have not been read. The observed excess is not proof of the complete angular defect or A21 energy deficit. Zero initial offset alone is insufficient in A25.',
      'next':'Translation-only solid/thick-shell representation or controlled shell refinement with independent mass, tensor, membrane and bending tests; no unilateral inertia compensation. Keep old failed gates.',
      'A24_assessment_preserved':True,'whole_insertion_ready':False,'objective1_complete':False})
    dump(OUT/'generator_recovery.json',{'created_utc':now(),'initial_failure':'CG substitution matched center= instead of the actual conditional-expression np.array substring. Failure occurred before any case directory or native solve. Original script saved as generator_before_cg_substitution_fix.py.','native_solver_reruns':0,'configuration_unchanged':True,'axis_and_footprint_generation_retained':True,'github_source_read_404':'Two optional public repository API reads returned404; no source code downloaded, no result inferred from unavailable code. Altair primary theory and actual native histories used.'})
    print({'roots_prepared':24,'anchors':144,'initial_physical_shell_RKE_pass':False,'native_RKE_J':observed[0]['native_initial_RKE_J'],'physical_transverse_RKE_J':observed[0]['physical_thickness_initial_RKE_J']},flush=True)

if __name__=='__main__':main()
