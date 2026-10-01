"""Derived GPLv2 graphics scene, exact source GLB vertices; no collision or rigid-body physics."""
import bpy,json,numpy as np,hashlib,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]; cfg=json.loads((ROOT/'wtc1_simulation_v8/data/impact_i02_geom.json').read_text()); base=ROOT/cfg['output_directory']; out=base/'final'; out.mkdir(parents=True,exist_ok=True); render=ROOT/'wtc1_3d_v4/renders/impact_i02_geom/final'; render.mkdir(parents=True,exist_ok=True)
data=np.load(base/'source_geometry.npz'); pts=data['points_m']; original_tris=data['triangles']; ids=data['primitive_ids']; audit=json.loads((base/'geometry_audit.json').read_text())
areas=np.linalg.norm(np.cross(pts[original_tris[:,1]]-pts[original_tris[:,0]],pts[original_tris[:,2]]-pts[original_tris[:,0]]),axis=1)/2
keep=areas>=1e-12; tris=original_tris[keep]; ids=ids[keep]
np.savez_compressed(out/'retained_triangle_indices.npz',source_triangle_indices=np.flatnonzero(keep),removed_triangle_indices=np.flatnonzero(~keep))
bpy.ops.wm.read_factory_settings(use_empty=True); scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
col=bpy.data.collections.new('B762_VISUAL_ONLY_ZERO_MECHANICAL_CREDIT'); scene.collection.children.link(col)
mat=bpy.data.materials.new('Neutral_visual_surface_NOT_mechanical_aluminum'); mat.diffuse_color=(.63,.69,.76,1); mat.use_nodes=True
node=mat.node_tree.nodes.get('Principled BSDF'); node.inputs['Base Color'].default_value=(.63,.69,.76,1); node.inputs['Metallic'].default_value=.2; node.inputs['Roughness'].default_value=.5
parts=[]; errors=[]
for k in np.unique(ids):
    faces=tris[ids==k]; used,inv=np.unique(faces,return_inverse=True)
    mesh=bpy.data.meshes.new(f'visual_primitive_{k:03d}'); mesh.from_pydata(pts[used].tolist(),[],inv.reshape(-1,3).tolist()); mesh.update()
    obj=bpy.data.objects.new(f'B762_primitive_{k:03d}',mesh); col.objects.link(obj); obj.data.materials.append(mat)
    obj['source_primitive']=int(k); obj['scope']='GRAPHICS_ONLY'; obj['mechanical_mass_kg']=0.; obj['mechanical_strength_credit']=0.
    co=np.empty(len(used)*3,dtype=np.float32); mesh.vertices.foreach_get('co',co); errors.append(float(np.max(np.abs(co.reshape(-1,3)-pts[used])))); parts.append(obj)
assert max(errors)<1e-5
scene['scope']='Boeing 767-200 labelled third-party graphics asset; NOT a mechanical reconstruction or impact simulation'
scene['source_repository']=cfg['repository']; scene['source_commit']=cfg['commit']; scene['license']='GPL-2.0; see THIRD_PARTY_NOTICES.md and bundled source LICENSE'
scene['scaling']='No scaling: length and span disagree with Boeing planning dimensions; see report'
scene.render.engine='BLENDER_WORKBENCH'; scene.render.resolution_x=1200; scene.render.resolution_y=800; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGB'
scene.world=bpy.data.worlds.new('World'); scene.world.color=(.07,.095,.13)
shade=scene.display.shading; shade.light='STUDIO'; shade.color_type='MATERIAL'; shade.background_type='WORLD'; shade.show_shadows=True; shade.show_cavity=True; shade.cavity_type='BOTH'
scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'
camdata=bpy.data.cameras.new('Inspection camera'); cam=bpy.data.objects.new('Inspection camera',camdata); scene.collection.objects.link(cam); scene.camera=cam; camdata.type='ORTHO'; camdata.clip_end=1000
center=(pts.min(axis=0)+pts.max(axis=0))/2; center[2]=6
def view(name,offset,scale):
    cam.location=Vector(center)+Vector(offset); cam.rotation_euler=(Vector(center)-cam.location).to_track_quat('-Z','Y').to_euler(); camdata.ortho_scale=scale
    scene.render.filepath=str(render/(name+'.png')); bpy.ops.render.render(write_still=True)
view('perspective',(-62,-62,42),72)
view('plan',(0,0,90),78)
view('front',(-90,0,0),60)
cam.location=Vector(center)+Vector((-62,-62,42)); cam.rotation_euler=(Vector(center)-cam.location).to_track_quat('-Z','Y').to_euler(); camdata.ortho_scale=72
notice=bpy.data.texts.new('READ_ME_GEOMETRY_ONLY'); notice.write('Derived 2026-09-10 from Flightradar24/fr24-3d-models commit '+cfg['commit']+' under GPLv2. Source and license retained alongside package. Neutral graphics materials; no thickness, strength, fuel, physical joints or damage law assigned. Exact source vertex geometry, axis permutation only. No collision simulation. Source scale discrepancies retained.')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'B762_GEOMETRY_ONLY.blend'),check_existing=False)
for obj in scene.objects: obj.select_set(False)
for obj in parts: obj.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.export_scene.gltf(filepath=str(out/'B762_GEOMETRY_ONLY.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
result={'blender':bpy.app.version_string,'source_npz_sha256':hashlib.sha256((base/'source_geometry.npz').read_bytes()).hexdigest(),'objects':len(parts),'triangles':len(tris),'original_triangles':len(original_tris),'removed_zero_area_triangles':int((~keep).sum()),'cleanup_tolerance_area_m2':1e-12,'source_original_preserved':True,'max_vertex_transfer_error_m':max(errors),'source_scale_unchanged':True,'physics_enabled':False,'bounds_m':{'min':pts.min(axis=0).tolist(),'max':pts.max(axis=0).tolist()},'source_dimensions_m':np.ptp(pts,axis=0).tolist(),'boeing_length_m':48.51,'boeing_span_m':47.57,'relative_length_difference':float(np.ptp(pts,axis=0)[0]/48.51-1),'relative_span_difference':float(np.ptp(pts,axis=0)[1]/47.57-1),'outputs':['B762_GEOMETRY_ONLY.blend','B762_GEOMETRY_ONLY.glb']}
(out/'integration_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2))
