"""Render native positions and native erosion, with no Blender dynamics."""
import hashlib,json,time
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a20';SOURCE=OUT/'r0/CORE3D_TIED_20'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def main():
    start=time.perf_counter();cfg=read(OUT/'media_declaration.json');dst=OUT/'video';assert not dst.exists();dst.mkdir();(dst/'whole').mkdir();(dst/'nose').mkdir()
    if hasattr(bpy.context.preferences.filepaths,'save_preview_images'):bpy.context.preferences.filepaths.save_preview_images=False
    z=np.load(SOURCE/'verified_states_SI.npz');m=read(SOURCE/'mesh.json');times=z['time_s'];P=z['positions_m'];assert len(P)>1 and times[-1]<.021
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.fps=30;scene.frame_end=len(times)*9;scene.render.image_settings.file_format='PNG';scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD';scene.world.color=(.035,.055,.075);scene.view_settings.view_transform='Standard'
    mats=[]
    for name,color in [('Fuselage',(.13,.68,.56,1)),('Wing',(.14,.47,.68,1)),('Engine',(.7,.76,.8,1)),('Skin',(.37,.78,.69,1)),('Core',(.98,.65,.17,1)),('Facade',(.7,.41,.2,1))]:
        a=bpy.data.materials.new(name);a.diffuse_color=color;mats.append(a)
    camera_rows=[]
    for name,pos,target,scale in [('whole',(53,-62,37),(17,0,0),64),('nose',(6,-10,6),(-1,0,0),11)]:
        data=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,data);scene.collection.objects.link(cam);cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale;camera_rows.append((name,cam))
    frames=[];objects=[];maxerr=0.;counts=[]
    def obj(name,faces,colors,positions,wire=False):
        nonlocal maxerr
        ids=np.unique(np.concatenate([np.array(f,int)-1 for f in faces]));remap={int(n+1):j for j,n in enumerate(ids)}
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(positions[ids].tolist(),[],[[remap[n] for n in f] for f in faces]);mesh.update();ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob)
        for material in mats:mesh.materials.append(material)
        mesh.polygons.foreach_set('material_index',colors);a=np.empty(len(ids)*3,np.float32);mesh.vertices.foreach_get('co',a);err=float(abs(a.reshape(-1,3)-positions[ids]).max(initial=0));maxerr=max(maxerr,err);assert err<1e-5
        if wire:mod=ob.modifiers.new('DisplayEdges_8mm','WIREFRAME');mod.thickness=.008;mod.use_replace=True
        ob['native_coordinate_error_m']=err;ob['physics_engine_used']=False;return ob
    hexfaces=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
    for i,tm in enumerate(times):
        f=m['original_triangle_node_ids'].copy();colors=[2 if p in range(22,28) else 1 if p in range(3,13) else 0 for p in m['aircraft_triangle_part_ids']]
        for row,alive in zip(m['radome_skin_quads'],z['skin_alive'][i]):
            if alive:f.append(row['nodes']);colors.append(3)
        boundary={}
        for row,alive in zip(m['radome_core_bricks'],z['core_alive'][i]):
            if alive:
                for side in hexfaces:
                    face=[row[j+1] for j in side];key=tuple(sorted(face))
                    if key in boundary:boundary[key]=None
                    else:boundary[key]=face
        cf=[face for face in boundary.values() if face is not None];f+=cf;colors+=[4]*len(cf)
        group=[obj(f'AIRCRAFT_STATE_{i:03d}',f,colors,P[i]),obj(f'FACADE_STATE_{i:03d}',m['facade_quads_node_ids'],[5]*len(m['facade_quads_node_ids']),P[i],True)]
        first=i*9+1;last=(i+1)*9
        for ob in group:
            for frame,hidden in [(first-1,True),(first,False),(last,False),(last+1,True)]:
                ob.hide_render=hidden;ob.hide_viewport=hidden;ob.keyframe_insert(data_path='hide_render',frame=frame);ob.keyframe_insert(data_path='hide_viewport',frame=frame)
            ob['physical_time_s']=float(tm);ob['source_sha256']=sha(SOURCE/'verified_states_SI.npz');objects.append(ob)
        counts.append({'state':i,'time_s':float(tm),'alive_skin_quads':int(z['skin_alive'][i].sum()),'alive_core_bricks':int(z['core_alive'][i].sum()),'core_exposed_faces':len(cf),'aircraft_display_polygons':len(f)})
    for ob in objects:
        action=ob.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for slot in action.slots:
                    bag=strip.channelbag(slot)
                    if bag:
                        for curve in bag.fcurves:
                            for k in curve.keyframe_points:k.interpolation='CONSTANT'
    for i,tm in enumerate(times):
        scene.frame_set(i*9+1);visible=[o for o in objects if not o.hide_render];assert len(visible)==2 and all(abs(o['physical_time_s']-tm)<1e-8 for o in visible)
        for name,cam in camera_rows:
            scene.camera=cam;p=dst/name/f'state_{i:03d}.png';scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);frames.append({'view':name,'state':i,'time_s':float(tm),'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)})
        print({'rendered_state':i,'native_ms':float(tm*1000),'alive_skins':counts[i]['alive_skin_quads'],'alive_core':counts[i]['alive_core_bricks']},flush=True)
    scene.camera=camera_rows[0][1];scene.frame_set(1);scene['physical_duration_s']=float(times[-1]);scene['display_duration_s']=len(times)*.3;scene['goal_complete']=False;scene['physics_engine_used']=False;scene['native_erosion_used']=True;scene['source_solver_model_physical_qualification']=False
    blend=dst/'A20_native_core_skin_erosion.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    dump(dst/'render_manifest.json',{'created_utc':cfg['declared_utc'],'renderer':bpy.app.version_string,'render_seconds':time.perf_counter()-start,'unique_native_states':len(times),'physical_duration_s':float(times[-1]),'target_physical_duration_s':10,'objective1_complete':False,
        'native_coordinate_max_abs_error_m':maxerr,'displacement_scale':1,'native_erosion_used':True,'eroded_elements_not_rendered':True,'separate_core_and_skin_geometry':True,'state_geometry_counts':counts,
        'physics_engine_used':False,'NIST_damage_fitting':False,'geometry_interpolation':'constant saved native poses','no_motion_extrapolation':True,'rendered_images':frames,'blend':str(blend.relative_to(ROOT)).replace('\\','/'),'blend_sha256':sha(blend),'source_states_sha256':sha(SOURCE/'verified_states_SI.npz')})

if __name__=='__main__':main()
