"""Map cached curved attachment surfaces without inventing a connector footprint."""
from run_aircraft_a31 import *
CFGROOT=ROOT/'wtc1_simulation_v8/data/aircraft_a31_root_mapping_preparation.json'
SOURCE=ROOT/'wtc1_simulation_v8/output/aircraft_a25/root_geometry_preparation.json'

def closest_triangle(p,a,b,c):
    # Voronoi-region projection; retain barycentric coordinates of the real face.
    ab=b-a;ac=c-a;ap=p-a;d1=ab@ap;d2=ac@ap
    if d1<=0 and d2<=0:return a,np.array([1.,0,0])
    bp=p-b;d3=ab@bp;d4=ac@bp
    if d3>=0 and d4<=d3:return b,np.array([0.,1,0])
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0:
        v=d1/(d1-d3);return a+v*ab,np.array([1-v,v,0])
    cp=p-c;d5=ab@cp;d6=ac@cp
    if d6>=0 and d5<=d6:return c,np.array([0.,0,1])
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0:
        w=d2/(d2-d6);return a+w*ac,np.array([1-w,0,w])
    va=d3*d6-d5*d4
    if va<=0 and d4-d3>=0 and d5-d6>=0:
        w=(d4-d3)/((d4-d3)+(d5-d6));return b+w*(c-b),np.array([0.,1-w,w])
    den=1/(va+vb+vc);v=vb*den;w=vc*den;return a+ab*v+ac*w,np.array([1-v-w,v,w])

def main():
    guard();dest=OUT/'curved_root_surface_mapping.json';assert not CFGROOT.exists() and not dest.exists();source_before=streamsha(SOURCE)
    c={'iteration':'AIRCRAFT-A31','declared_utc':now(),'seed':1102056,'random_draws':0,'scope':'Cached geometric preparation of24real roots/144distinct anchors, source A25. No new native case, no actual-as-built identification.',
       'source':rel(SOURCE),'source_sha256':source_before,'method':'For every source skin-face candidate and both physical shell sides, nearest point on every body triangle offset by +/-half its actual2.54mm thickness. Skin0.5mm thickness used unchanged. Retain all candidates and barycentric coordinates; deterministic minimum distance. Local right-handed frame axis1 is gap direction, axis2 longest body-edge projection, axis3 crossproduct.',
       'choice_status':'Geometry-only nearest-face selection, not proof of a connector, joint, contact or strength. No footprint or clipping width assumed.',
       'budget':'No finite connector volume/mass allocated; old flat .00556g and144*.00556g cannot be used as an actual curved-root budget.',
       'acceptance':{'source_unchanged':True,'root_count':24,'distinct_anchors':144,'barycentric_min':-1e-10,'reconstruction_mm':1e-8,'frame_tolerance':1e-10,'finite_positive_gap':True},'whole_source_changed':False,'whole_insertion_ready':False,'physical_strength_or_fracture_qualified':False}
    dump(CFGROOT,c);dump(OUT/'root_mapping_declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFGROOT),'before_mapping':True});root=read(SOURCE);rows=[]
    for r in root['roots']:
        anchors=[]
        for anchor in r['anchors']:
            candidates=[];p=np.asarray(anchor['point_mm'])
            for skinface in anchor['candidate_main_skin_faces']:
                sn=np.asarray(skinface['normal']);sn=sn/np.linalg.norm(sn)
                for ss in [-1,1]:
                    ps=p+ss*.5*r['skin_shell_thickness_mm']*sn
                    for bodyface in r['body_main_faces']:
                        X=np.asarray(bodyface['points_mm']);bn=np.cross(X[1]-X[0],X[2]-X[0]);bn=bn/np.linalg.norm(bn)
                        for bs in [-1,1]:
                            Y=X+bs*.5*r['body_shell_thickness_mm']*bn;q,bary=closest_triangle(ps,*Y);gap=ps-q;length=float(np.linalg.norm(gap));assert length>0
                            eu=gap/length;edges=[Y[1]-Y[0],Y[2]-Y[0],Y[2]-Y[1]];projections=[e-(e@eu)*eu for e in edges];v=max(projections,key=lambda e:e@e);ev=v/np.linalg.norm(v);ew=np.cross(eu,ev);frame=np.array([eu,ev,ew]);err=float(abs(q-bary@Y).max())
                            candidates.append({'skin_face':skinface['element'],'skin_part':skinface['part'],'skin_facet':skinface['facet'],'skin_named_side':skinface['side'],'skin_physical_side_sign':ss,'skin_surface_point_mm':ps.tolist(),'body_face':bodyface['element'],'body_part':bodyface['part'],'body_nodes':bodyface['nodes'],'body_physical_side_sign':bs,'body_offset_face_points_mm':Y.tolist(),'body_surface_point_mm':q.tolist(),'body_barycentric':bary.tolist(),'gap_mm':length,'frame_rows_global':frame.tolist(),'checks':{'finite':bool(np.isfinite(frame).all() and np.isfinite(length)),'barycentric':bool(bary.min()>=-1e-10 and abs(bary.sum()-1)<1e-10),'reconstruction':err<1e-8,'orthonormal':bool(np.allclose(frame@frame.T,np.eye(3),atol=1e-10,rtol=0)),'right_handed':bool(abs(np.linalg.det(frame)-1)<1e-10)}})
            best=min(range(len(candidates)),key=lambda i:candidates[i]['gap_mm']);anchors.append({'source_anchor_node':anchor['node'],'source_midplane_point_mm':anchor['point_mm'],'candidate_count':len(candidates),'selected_candidate_index':best,'selected':candidates[best],'all_candidates':candidates,'no_connector_footprint_assumed':True})
        rows.append({'source_RBE2':r['root_RBE2_to_replace_only_after_qualification'],'source_host':r['host'],'source_host_point_mm':r['host_point_mm'],'anchors':anchors})
    selected=[a['selected'] for r in rows for a in r['anchors']];ids=[a['source_anchor_node'] for r in rows for a in r['anchors']];checks={'source_unchanged':streamsha(SOURCE)==source_before,'roots':len(rows)==24,'anchors':len(ids)==144 and len(set(ids))==144,'all_selected_geometry_checks':all(all(x['checks'].values()) for x in selected)}
    dump(dest,{'created_utc':now(),'configuration_sha256':streamsha(CFGROOT),'roots':rows,'checks':checks,'pass':all(checks.values()),'gap_range_mm':[min(x['gap_mm'] for x in selected),max(x['gap_mm'] for x in selected)],'actual_connector_volume_mm3':None,'actual_connector_mass_g':None,'physical_capacity_identified':False,'native_curved_attachment_tested':False,'whole_insertion_ready':False,'whole_source_changed':False,'unresolved':'Nearest-face geometry does not define an attachment footprint, adhesive/fastener, capacity or failure. Those need explicit hypotheses and sensitivity, source-supported where available.'});assert all(checks.values());print({'curved_roots':24,'anchors':144,'geometry_checks':checks,'gap_range_mm':read(dest)['gap_range_mm'],'connector_budget_defined':False},flush=True)

if __name__=='__main__':main()
