"""Display exact solver node coordinates, no Blender dynamics or interpolated states."""
import bpy, json, sys, time, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
src=ROOT/'wtc1_simulation_v8/output/impact_i01_first_contact/M050/computed_frames.npz'
out=ROOT/'wtc1_3d_v4/renders/impact_i01/final'; out.mkdir(parents=True,exist_ok=True)
data=np.load(src); pts=data['points_mm'][:,:,[0,2,1]]/1000; quads=data['quads']; parts=data['parts']; times=data['times_ms']; strains=data['epsp']
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1000; scene.render.resolution_y=650; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGB'
scene.world=bpy.data.worlds.new('World'); scene.world.color=(.12,.12,.12)
shade=scene.display.shading; shade.light='STUDIO'; shade.studiolight_rotate_z=.4
shade.color_type='MATERIAL'; shade.show_shadows=True; shade.show_cavity=True; shade.cavity_type='BOTH'
shade.background_type='WORLD'; shade.show_specular_highlight=True
scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'
mesh=bpy.data.meshes.new('Computed_shell_nodes'); mesh.from_pydata(pts[0].tolist(),[],quads.tolist()); mesh.update()
obj=bpy.data.objects.new('NUMERICAL_ONLY_GENERIC_BOX_AND_COLUMNS',mesh); scene.collection.objects.link(obj)
for name,color in [('steel',(.20,.47,.70,1)),('aluminum',(.85,.70,.28,1)),('flagged_strain',(.85,.17,.10,1))]:
    m=bpy.data.materials.new(name); m.diffuse_color=color; obj.data.materials.append(m)
obj['scope']='Generic non-eroding contact pilot; NOT Boeing 767 geometry or physical impact validation'
obj['source_npz']=str(src); obj['material_color_red']='Equivalent plastic strain exceeds declared diagnostic flag 0.02, not measured rupture'
obj.shape_key_add(name='Basis')
for i in range(1,len(times)):
    key=obj.shape_key_add(name=f'State_{i:03d}_{times[i]:.6f}ms')
    key.data.foreach_set('co',pts[i].reshape(-1))
    for frame,val in [(1,0),(i+1,1),(i+2,0)]:
        key.value=val; key.keyframe_insert(data_path='value',frame=frame)
    key.value=0
# Keyed states are constant (no invented in-between deformations).
action=obj.data.shape_keys.animation_data.action
for layer in action.layers:
    for strip in layer.strips:
        for slot in action.slots:
            bag=strip.channelbag(slot)
            if bag:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points: k.interpolation='CONSTANT'
camdata=bpy.data.cameras.new('Camera'); camera=bpy.data.objects.new('Camera',camdata); scene.collection.objects.link(camera)
camera.location=(5.5,-5.0,4.3); target=Vector((0,.55,.25)); camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camdata.type='ORTHO'; camdata.ortho_scale=8.0; scene.camera=camera
scene.frame_start=1; scene.frame_end=len(times); scene.render.fps=6
audits=[]; start=time.perf_counter()
for i,t in enumerate(times):
    scene.frame_set(i+1)
    for j,poly in enumerate(mesh.polygons): poly.material_index=2 if strains[i,j]>.02 else (1 if parts[j]==3 else 0)
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); evaluated_mesh=evaluated.to_mesh()
    co=np.empty(len(mesh.vertices)*3,dtype='float32'); evaluated_mesh.vertices.foreach_get('co',co); evaluated.to_mesh_clear()
    err=float(np.max(np.abs(co.reshape(-1,3)-pts[i]))); assert err<1e-5,err
    audits.append({'frame':i+1,'time_ms':float(t),'max_position_error_m':err,'max_box_epsp':float(strains[i,parts==3].max())})
    scene.render.filepath=str(out/f'raw_{i:03d}.png'); bpy.ops.render.render(write_still=True)
scene.frame_set(1)
for j,poly in enumerate(mesh.polygons): poly.material_index=1 if parts[j]==3 else 0
# State-dependent color is rendered in PNGs. Saved .blend geometry animates; colors are neutral.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'wtc1_3d_v4/output/IMPACT_I01_CONTACT_DIAGNOSTIC_FINAL.blend'))
(out/'render_audit.json').write_text(json.dumps({'blender':bpy.app.version_string,'render_seconds':time.perf_counter()-start,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'coordinate_transform':'mm x,y,z -> m x,z,y; display reflection only, faces two-sided','states':audits,'interpolation':'CONSTANT','physics_engine':False,'scope':'Numerical diagnostic only; rupture disabled; initial 50-to-25 mm impulse convergence fails'},indent=2),encoding='utf-8')
