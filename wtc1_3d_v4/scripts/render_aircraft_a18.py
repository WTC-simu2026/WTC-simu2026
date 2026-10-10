"""Render exact fresh A18 native geometry in Blender; no dynamics extrapolation."""
import hashlib,json,sys,time
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a18';CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a18_predeclaration.json'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def main():
    # Factory session only: suppress optional thumbnail writes outside workspace.
    if hasattr(bpy.context.preferences.filepaths,'save_preview_images'):
        bpy.context.preferences.filepaths.save_preview_images=False
    start=time.perf_counter();cfg=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];source=ROOT/cfg['video']['source'];dst=OUT/'video';assert not dst.exists();dst.mkdir();(dst/'whole').mkdir();(dst/'nose').mkdir()
    z=np.load(source/'verified_states_SI.npz');dm=np.load(source/'native_radome_damage.npz');m=read(source/'mesh.json');times=z['time_s'];X=z['initial_positions_m'];P=X[None]+z['displacement_m'];assert 1 < len(P) < 200;assert times[-1]<.021
    idx=[int(np.argmin(abs(dm['time_s']-t))) for t in times];assert max(abs(dm['time_s'][idx]-times))<1e-7;D=np.max(dm['skin_core_skin_damage'][idx][:,[0,2]],axis=1);di={int(e):i for i,e in enumerate(dm['element_ids'])};mapping=[di.get(int(e),-1) for e in m['aircraft_triangle_ids']]
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.fps=30;scene.frame_start=1;scene.frame_end=len(P)*9
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD';scene.world.color=(.035,.055,.075);scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard'
    mats=[]
    for name,color in [('Fuselage',(.13,.68,.56,1)),('Wing',(.14,.47,.68,1)),('Engine',(.7,.76,.8,1)),('SkinPartial',(.96,.63,.17,1)),('SkinPointFailed',(.9,.16,.14,1)),('Facade',(.7,.41,.2,1))]:
        mat=bpy.data.materials.new(name);mat.diffuse_color=color;mats.append(mat)
    meshrows=[]
    for name,faces0 in [('AIRCRAFT',m['original_triangle_node_ids']),('FACADE',m['facade_quads_node_ids'])]:
        faces0=np.asarray(faces0,int)-1;nodes=np.unique(faces0);remap={int(n):i for i,n in enumerate(nodes)};faces=[[remap[int(n)] for n in f] for f in faces0];mesh=bpy.data.meshes.new(name);mesh.from_pydata(P[0,nodes].tolist(),[],faces);mesh.update();obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
        for mat in mats:mesh.materials.append(mat)
        base=obj.shape_key_add(name='Basis')
        for i,tm in enumerate(times):
            key=obj.shape_key_add(name=f'NATIVE_{i:03d}_{tm*1000:.6f}ms');key.data.foreach_set('co',P[i,nodes].astype(np.float32).ravel());first=i*9+1;last=(i+1)*9
            for f,v in [(first-1,0),(first,1),(last,1),(last+1,0)]:key.value=v;key.keyframe_insert(data_path='value',frame=f)
            key.value=0
        action=obj.data.shape_keys.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for slot in action.slots:
                    bag=strip.channelbag(slot)
                    if bag:
                        for curve in bag.fcurves:
                            for k in curve.keyframe_points:k.interpolation='CONSTANT'
        if name=='FACADE':
            mesh.polygons.foreach_set('material_index',[5]*len(faces));mod=obj.modifiers.new('DisplayEdges_8mm','WIREFRAME');mod.thickness=.008;mod.use_replace=True
        meshrows.append((obj,nodes));obj['coordinate_source']='native solver metres, displacements x1';obj['source_sha256']=sha(source/'verified_states_SI.npz')
    air=meshrows[0][0];parts=m['aircraft_triangle_part_ids'];base=np.array([2 if p in range(22,28) else 1 if p in range(3,13) else 0 for p in parts]);assert len(base)==len(air.data.polygons)
    cameras=[]
    for name,position,target,scale in [('whole',(53,-62,37),(17,0,0),64),('nose',(6,-10,6),(0,0,0),11)]:
        data=bpy.data.cameras.new(name);obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=position;obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale;cameras.append((name,obj))
    maxerr=0.;rendered=[]
    for i,tm in enumerate(times):
        scene.frame_set(i*9+1);colors=base.copy()
        for j,k in enumerate(mapping):
            if k>=0:colors[j]=4 if D[i,k]>=.999999 else 3 if D[i,k]>.01 else 0
        air.data.polygons.foreach_set('material_index',colors.tolist());air.data.update()
        for obj,nodes in meshrows:
            dg=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dg)
            # The facade wire modifier is display-only; audit source shape-key data.
            key=obj.data.shape_keys.key_blocks[f'NATIVE_{i:03d}_{tm*1000:.6f}ms'];q=np.empty(len(nodes)*3,np.float32);key.data.foreach_get('co',q);err=float(np.max(abs(q.reshape(-1,3)-P[i,nodes])));maxerr=max(maxerr,err);assert err<1e-5
        for name,cam in cameras:
            scene.camera=cam;file=dst/name/f'state_{i:03d}.png';scene.render.filepath=str(file);bpy.ops.render.render(write_still=True);rendered.append({'view':name,'state':i,'time_s':float(tm),'path':str(file.relative_to(ROOT)).replace('\\','/'),'sha256':sha(file)})
        print({'native_state_rendered':i,'time_ms':float(tm*1000)},flush=True)
    scene.camera=cameras[0][1];scene['physical_duration_s']=float(times[-1]);scene['display_duration_s']=len(P)*.3;scene['target_physical_duration_s']=10;scene['goal_complete']=False;scene['physics_engine_used']=False;scene['damage_material_colors']='native state colors at final pose; rerun this script to update colors with timeline';scene['facade_display_edges_m']=.008
    blend=dst/'A18_exact_native_poses.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    dump(dst/'render_manifest.json',{'created_utc':read(CFG)['declared_utc'],'renderer':bpy.app.version_string,'render_seconds':time.perf_counter()-start,'unique_native_states':len(P),'physical_duration_s':float(times[-1]),'target_physical_duration_s':10,'objective1_complete':False,'geometry_interpolation':'constant exact saved state holds','native_coordinate_max_abs_error_m':maxerr,'displacement_scale':1,'physics_engine_used':False,'NIST_damage_fitting':False,'no_kinematic_extrapolation':True,'rendered_images':rendered,'blend':str(blend.relative_to(ROOT)).replace('\\','/'),'blend_sha256':sha(blend),'source_states_sha256':sha(source/'verified_states_SI.npz'),'source_damage_sha256':sha(source/'native_radome_damage.npz')})

if __name__=='__main__':main()
