"""Audit immutable w0 and w1 native fields; no rerun or alteration of solver histories."""
from run_aircraft_a23 import *
import subprocess

def paired(revision):
    c=read(CFG if revision=='w0' else ROOT/'wtc1_simulation_v8/data/aircraft_a23_coupling_w1.json')
    duration=1 if revision=='w0' else 10
    rows=[]
    for axis in 'XYZ':
        rd=OUT/revision/f'REFERENCE_ROTATION_{axis}';cd=OUT/revision/f'CONNECTED_ROTATION_{axis}'
        ref=np.load(rd/'histories_SI.npz');con=np.load(cd/'histories_SI.npz');g=read(cd/'generation.json')
        T=con['time_ms'];mask=(T>=ref['time_ms'][0])&(T<=ref['time_ms'][-1]);tm=T[mask]
        q=np.asarray(g['nodes_mm'])[np.asarray(g['clip_node_ids'])-1];m=np.asarray(g['clip_known_nodal_masses_g'])
        X,V,a,w=rotation(q,tm/duration,axis);V/=duration
        expected=.5*np.sum(m[None,:,None]*V**2,axis=(1,2))*.001
        actual=con['KE_J'][mask]-np.interp(tm,ref['time_ms'],ref['KE_J'])
        diff=float(abs(actual-expected).max());tol=.02*float(expected.max())+1e-7
        rr=read(rd/'review.json');cr=read(cd/'review.json')
        time_shift=float(abs(T-ref['time_ms']).max())
        slope=float(abs(np.diff(ref['KE_J'])/np.diff(ref['time_ms'])).max())
        dx=con['positions_mm']-rotation(np.asarray(g['nodes_mm']),T/duration,axis)[0]
        dv=con['velocities_m_s']-rotation(np.asarray(g['nodes_mm']),T/duration,axis)[1]/duration
        cap=np.array([i for i in g['clip_node_ids'] if abs(abs(g['nodes_mm'][i-1][0])-2)<1e-12])-1
        interior=np.array([i for i in g['clip_node_ids'] if abs(abs(g['nodes_mm'][i-1][0])-2)>1e-12])-1
        checks={'reference_native_balance':rr['checks']['native_energy_balance'],
            'connected_native_balance':cr['checks']['native_energy_balance'],
            'known_added_KE':diff<tol,'declared_added_mass':abs(cr['native_mass_g']-rr['native_mass_g']-.00556)<1e-6*.00556,
            'time_alignment_error_bound':slope*time_shift<tol/10,
            'no_extrapolation':bool(len(tm)>990),'cap_velocity':bool(abs(dv[:,cap]).max()<.005)}
        rows.append({'axis':axis,'rotation_duration_ms':duration,'maximum_added_KE_error_J':diff,
          'expected_peak_clip_KE_J':float(expected.max()),'tolerance_J':tol,
          'maximum_native_timestamp_shift_ms':time_shift,'conservative_linear_interpolation_shift_bound_J':slope*time_shift,
          'common_rows':len(tm),'cap_velocity_error_m_s':float(abs(dv[:,cap]).max()),
          'interior_velocity_error_m_s':float(abs(dv[:,interior]).max()),'interior_position_error_mm':float(abs(dx[:,interior]).max()),
          'native_all_nodes_velocity_gate_pass':cr['checks']['all_node_velocity'],
          'checks':checks,'paired_pass':all(checks.values()),'original_reviews_unmodified':True})
    p=OUT/f'paired_{revision}_cached_audit.json';assert not p.exists()
    dump(p,{'created_utc':now(),'revision':revision,'pairs':rows,'paired_pass':all(r['paired_pass'] for r in rows),
      'all_original_case_gates_pass':all(read(OUT/revision/cid/'review.json')['pass'] for cid in c['cases']['primitive']+c['cases']['paired']),
      'sampling_correction_only':True,'native_samples_not_modified':True,'whole_impact_qualified':False})
    print({'cached_pairs':revision,'pass':all(r['paired_pass'] for r in rows)},flush=True)

def w0_extension():
    rows=[]
    for cid in ['CONNECTED_EXTENSION_N4','CONNECTED_EXTENSION_N8']:
        d=OUT/'w0'/cid;g=read(d/'generation.json');r=read(d/'review.json');H=histories(d/(g['name']+'T01.csv'))
        clip=next(v[-1]*.001 for k,v in H.items() if k.startswith('FINITE_METAL_CLIP') and k.strip().endswith('IE'))
        body=next(v[-1]*.001 for k,v in H.items() if k.startswith('HALF_MM_BACKING') and k.strip().endswith('IE'))
        # The Spot5 projected left cap at x=-2 receives .8 of the .004 backing boundary displacement.
        left=.0032;right=.004;expected=r['analytic_IE_J']*((right-left)/.004)**2
        h=np.load(d/'histories_SI.npz');xyz=np.asarray(g['nodes_mm']);caps={}
        for x in [-2,2]:
            ids=np.array([i-1 for i in g['clip_node_ids'] if abs(xyz[i-1,0]-x)<1e-12]);caps[str(x)]=(h['positions_mm'][-1,ids]-xyz[ids]).mean(axis=0).tolist()
        rows.append({'case':cid,'global_IE_J':r['last_IE_J'],'body_IE_J':float(body),'clip_IE_J':float(clip),
           'independent_clip_IE_for_actual_boundary_J':float(expected),'relative_error':float(abs(clip-expected)/expected),
           'actual_cap_displacements_mm':caps,'expected_left_right_x_mm':[left,right],
           'original_failed_global_IE_gate_retained':not r['checks']['independent_static_IE'],
           'cached_explanation_pass':bool(abs(clip-expected)<.02*expected+1e-7)})
    dump(OUT/'w0_boundary_diagnostic.json',{'created_utc':now(),'cases':rows,'no_new_native_solver':True,
      'cause':'x>=0 incorrectly moved both backing boundary nodes; global IE included backing. Existing control does not implement its intended fixed-backing reference.',
      'w1_declared_before_corrected_cases':True,'old_files_unchanged':True,'physical_strength_qualified':False})
    print({'cached_boundary_diagnostic':rows},flush=True)

def fields(revision):
    c=read(CFG if revision=='w0' else ROOT/'wtc1_simulation_v8/data/aircraft_a23_coupling_w1.json');rows=[]
    for cid in c['cases']['primitive']+c['cases']['paired']:
        d=OUT/revision/cid;g=read(d/'generation.json');n=g['name'];h={k:v for k,v in np.load(d/'histories_SI.npz').items()};xyz=np.asarray(g['nodes_mm'])
        native=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name))
        assert native
        ad=OUT/'native_field_audit'/revision/cid;ad.mkdir(parents=True,exist_ok=True)
        for p in [native[0],native[len(native)//2],native[-1]]:
            start=time.perf_counter();dest=ad/(p.name+'.vtk');reused=dest.exists()
            if not reused:
                proc=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120)
                dest.write_text(proc.stdout,encoding='utf-8')
            q=vtk(dest.read_text(encoding='utf-8'))
            order=np.argsort(q['NODE_ID']);ids=q['NODE_ID'].astype(int)[order];assert np.array_equal(ids,np.arange(1,len(xyz)+1))
            pts=q['points'].reshape(-1,3)[order];v=q['Velocity'].reshape(-1,3)[order];disp=q['Displacement'].reshape(-1,3)[order]
            tm=q['time'];covered=bool(h['time_ms'][0]<=tm<=h['time_ms'][-1]);pe=ve=None
            if covered:
                ex=np.array([np.interp(tm,h['time_ms'],h['positions_mm'][:,j,a]) for j in range(len(xyz)) for a in range(3)]).reshape(-1,3)
                ev=np.array([np.interp(tm,h['time_ms'],h['velocities_m_s'][:,j,a]) for j in range(len(xyz)) for a in range(3)]).reshape(-1,3)
                pe=float(abs(pts-ex).max());ve=float(abs(v-ev).max())
            checks={'native_node_ids':True,'all_finite':bool(np.isfinite(pts).all() and np.isfinite(v).all() and np.isfinite(disp).all()),
                'displacement_coordinate_identity':bool(abs(pts-xyz-disp).max()<2e-5),
                'no_native_element_deletion':bool(np.all(q['EROSION_STATUS']==1))}
            rows.append({'case':cid,'time_ms':tm,'native':rel(p),'native_sha256':streamsha(p),'vtk':rel(dest),'vtk_sha256':streamsha(dest),
              'native_history_support':covered,'no_extrapolation':True,'coordinate_vs_interpolated_TH_max_mm':pe,'velocity_vs_interpolated_TH_max_m_s':ve,
              'checks':checks,'pass':all(checks.values()),'reused_cached_conversion':reused,'reader_wall_s':time.perf_counter()-start,'fields':list(q)})
        print({'field_audit':revision,'case':cid,'samples_done':len(rows)},flush=True)
    dest=OUT/f'native_fields_{revision}_audit.json';assert not dest.exists();dump(dest,{'created_utc':now(),'revision':revision,'samples':rows,'pass':all(r['pass'] for r in rows),'old_solvers_rerun':0})
    print({'native_fields':revision,'samples':len(rows),'pass':all(r['pass'] for r in rows)},flush=True)

def summary_w1():
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a23_coupling_w1.json');rows=[read(OUT/'w1'/cid/'review.json') for cid in c['cases']['paired']]
    e4=read(OUT/'w1/CONNECTED_EXTENSION_N4/review.json')['last_clip_IE_J'];e8=read(OUT/'w1/CONNECTED_EXTENSION_N8/review.json')['last_clip_IE_J']
    checks={'all_w1_native_case_gates':all(r['pass'] for r in rows),'paired_added_KE_and_cap_velocity':read(OUT/'paired_w1_cached_audit.json')['paired_pass'],
      'elastic_mesh_change':abs(e4-e8)/e8<.05,'independent_free_tensor_A23_primitive':all(read(OUT/'w0'/('FREE_ROTATION_'+a)/'review.json')['pass'] for a in 'XYZ')}
    dump(OUT/'coupling_summary.json',{'created_utc':now(),'w1_cases':rows,'checks':checks,'pass':all(checks.values()),'elastic_mesh_relative_difference':abs(e4-e8)/e8,
       'all_w0_gates_pass':False,'w0_failures_preserved':True,'scope':'flat fixture and declared slower10ms rotation, primitive free tensor; actual curved root geometry, actual strength and whole impact not qualified',
       'ready_for_whole':False,'actual_geometry_controls_required':True,'physical_strength_or_fracture_qualified':False,'objective1_complete':False,'old_solver_reruns':0})
    print({'w1_summary':checks},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['pair_w0','pair_w1','boundary','fields_w0','fields_w1','summary_w1']);a=p.parse_args().action
    if a.startswith('pair_'):paired(a[5:])
    elif a.startswith('fields_'):fields(a[7:])
    elif a=='summary_w1':summary_w1()
    else:w0_extension()
