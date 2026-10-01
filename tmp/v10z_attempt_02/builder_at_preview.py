"""Bake the V10Z driver into ordinary Blender keyframes and labelled media.

No handler is needed when opening the saved derivative.  The intact master
scene is retained separately.  The animated scene uses V10Y uniform levels.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'wtc1_simulation_v8/data/v10z_blender_exploratory_visualization.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def record(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path), 'size_bytes': path.stat().st_size}


def require(value, text):
    if not value:
        raise RuntimeError(text)


def material(name, color, emission=False):
    m = bpy.data.materials.new('V10Z_' + name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    if emission:
        nodes.clear()
        e = nodes.new('ShaderNodeEmission')
        e.inputs['Color'].default_value = (*color, 1)
        out = nodes.new('ShaderNodeOutputMaterial')
        m.node_tree.links.new(e.outputs[0], out.inputs['Surface'])
    else:
        n = nodes.get('Principled BSDF')
        n.inputs['Base Color'].default_value = (*color, 1)
        n.inputs['Roughness'].default_value = .48
        n.inputs['Metallic'].default_value = .24
    return m


def link(scene, name, data=None, parent=None):
    obj = bpy.data.objects.new('V10Z_' + name, data)
    scene.collection.objects.link(obj)
    obj.parent = parent
    obj['iteration'] = 'V10Z'
    obj['visualization_only'] = True
    obj['physical_validation'] = False
    return obj


def boxes(scene, name, parts, mat, parent=None):
    vertices, faces = [], []
    for center, dims in parts:
        x, y, z = center
        a, b, c = [v/2 for v in dims]
        start = len(vertices)
        vertices.extend([(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
                         (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)])
        faces.extend(tuple(start+i for i in face) for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    mesh = bpy.data.meshes.new('V10Z_' + name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    return link(scene, name, mesh, parent)


def text(scene, name, body, xy, size, mat, camera, align='LEFT'):
    data = bpy.data.curves.new('V10Z_' + name, 'FONT')
    data.body = body
    data.size = size
    data.align_x = align
    data.align_y = 'TOP_BASELINE'
    data.space_line = 1.28
    data.materials.append(mat)
    obj = link(scene, name, data, camera)
    obj.location = (xy[0], xy[1], -2.6)
    return obj


def panel(scene, name, xy, dims, mat, camera):
    return boxes(scene, name, [((xy[0], xy[1], -3.0), (dims[0], dims[1], .01))], mat, camera)


def action_curves(owner):
    if not owner.animation_data or not owner.animation_data.action:
        return []
    a = owner.animation_data.action
    if hasattr(a, 'fcurves'):
        return list(a.fcurves)
    return [c for layer in a.layers for strip in layer.strips for bag in strip.channelbags for c in bag.fcurves]


def set_interpolation(owner):
    for curve in action_curves(owner):
        interpolation = 'CONSTANT' if 'hide_' in curve.data_path else 'LINEAR'
        for point in curve.keyframe_points:
            point.interpolation = interpolation


def visible_only_at(obj, frame):
    for f, hidden in [(0, True), (frame-1, True), (frame, False), (frame+1, True)]:
        obj.hide_render = obj.hide_viewport = hidden
        obj.keyframe_insert(data_path='hide_render', frame=f)
        obj.keyframe_insert(data_path='hide_viewport', frame=f)
    set_interpolation(obj)


def hide_from(obj, frame):
    for f, hidden in [(0, False), (frame-1, False), (frame, True)]:
        obj.hide_render = obj.hide_viewport = hidden
        obj.keyframe_insert(data_path='hide_render', frame=f)
        obj.keyframe_insert(data_path='hide_viewport', frame=f)
    set_interpolation(obj)


def tower_segment(scene, name, bottom, top, width, mat, parent, floor):
    height = top-bottom
    center = (top+bottom)/2
    # Coarse facade sampling is a drawing convention, not a member topology.
    parts = [((0,0,bottom+.14),(width,width,.28))]
    for u in range(17):
        position = -width/2 + width*u/16
        for side in [-1, 1]:
            parts.append(((position,side*width/2,center),(.60,.55,height)))
            parts.append(((side*width/2,position,center),(.55,.60,height)))
    parts.append(((0,0,top-.43),(width,width,.78)))
    obj = boxes(scene, name, parts, mat, parent)
    obj['floor'] = floor
    obj['coarse_facade_drawing_not_member_topology'] = True
    return obj


def build(config, driver, scratch):
    v = config['visual_contract']
    scene = bpy.data.scenes.new(v['scene_name'])
    if bpy.context.window:
        bpy.context.window.scene = scene
    scene.render.engine = v['render_engine']
    scene.render.resolution_x, scene.render.resolution_y = v['resolution_px']
    scene.render.resolution_percentage = v['resolution_percentage']
    scene.render.fps = v['fps']
    scene.frame_start, scene.frame_end = v['frame_start'], v['frame_end']
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.world = bpy.data.worlds.new('V10Z_WORLD')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.018,.027,.045,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .50
    scene['iteration'] = 'V10Z'
    scene['visualization_only'] = True
    scene['physical_validation'] = False
    scene['driver_sha256'] = digest(ROOT / config['outputs']['selected_driver'])
    scene['permanent_banner'] = v['permanent_banner']
    scene['uniform_level_height_m'] = driver['geometry']['story_height_m']
    scene['initial_drop_duration_excluded'] = True
    camera_data = bpy.data.cameras.new('V10Z_CAMERA')
    camera_data.type, camera_data.ortho_scale = 'ORTHO', 1150
    camera_data.clip_end = 3000
    camera = link(scene, 'CAMERA', camera_data)
    camera.location = (520, -850, 360)
    camera.rotation_euler = (Vector((0,0,201)) - camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera = camera
    width, height = 1150, 646.875
    root = link(scene, 'TOWER_ROOT')
    root.location = camera.rotation_euler.to_matrix() @ Vector((-width*.246,0,0))
    upper = link(scene, 'UPPER_BLOCK', parent=root)
    front = link(scene, 'FRONT_REFERENCE', parent=root)
    mats = {
        'background': material('UI_BACKGROUND', (.013,.023,.042), True),
        'panel': material('UI_PANEL', (.026,.044,.071), True),
        'white': material('UI_WHITE', (.87,.93,1), True),
        'muted': material('UI_MUTED', (.48,.61,.76), True),
        'cyan': material('UI_CYAN', (.13,.77,.9), True),
        'orange': material('UI_ORANGE', (1,.40,.075), True),
        'dark': material('UI_DARK', (.010,.018,.03), True),
        'cold': material('FACADE', (.36,.47,.58)),
        'upper': material('UPPER_FACADE', (.15,.60,.72)),
        'ground': material('GROUND', (.065,.087,.115)),
    }
    params = load(ROOT / 'wtc1_3d_v4/data/wtc1_parameters.json')
    tower_width = params['established_facts']['tower_width_m']
    h = driver['geometry']['story_height_m']
    initial_floor = driver['summary']['initiation_floor']
    split_z = driver['geometry']['upper_block_original_bottom_m']
    floor_mats = {}
    lower_objects = {}
    for floor in range(1,111):
        m = mats['upper'] if floor >= initial_floor else mats['cold']
        if 93 <= floor <= 99:
            m = material(f'HEAT_LEVEL_{floor}', (.20,.36,.5))
            floor_mats[floor] = m
        bottom, top = (floor-1)*h, floor*h
        if floor == initial_floor:
            lower_objects[floor] = tower_segment(scene, f'LOWER_LEVEL_{floor:03}', bottom, split_z, tower_width, m, root, floor)
            tower_segment(scene, f'UPPER_LEVEL_{floor:03}', split_z, top, tower_width, m, upper, floor)
        elif floor < initial_floor:
            lower_objects[floor] = tower_segment(scene, f'LOWER_LEVEL_{floor:03}', bottom, top, tower_width, m, root, floor)
        else:
            tower_segment(scene, f'UPPER_LEVEL_{floor:03}', bottom, top, tower_width, m, upper, floor)
    # The ground is a datum. No debris settlement or compaction is drawn.
    boxes(scene, 'GROUND', [((0,0,-.7),(160,160,1.4))], mats['ground'], root)
    boxes(scene, 'FRONT_RING', [((0,-tower_width/2-1,0),(tower_width+4,1.5,1.5)),
                                ((0,tower_width/2+1,0),(tower_width+4,1.5,1.5)),
                                ((-tower_width/2-1,0,0),(1.5,tower_width+4,1.5)),
                                ((tower_width/2+1,0,0),(1.5,tower_width+4,1.5))], mats['orange'], front)
    # Bake every video frame, including the deliberately labelled initialization jump.
    for row in driver['frames']:
        f = row['frame']
        upper.location.z = -row['upper_block_drop_m']
        upper.keyframe_insert(data_path='location', frame=f)
        front.location.z = row['upper_block_bottom_z_m']
        front.keyframe_insert(data_path='location', frame=f)
        for floor, mat in floor_mats.items():
            q = min(1, max(0, (row['selected_truss_temperature_c_by_floor'][str(floor)]-20)/800))
            color = (.18+.77*q, .36-.18*q, .50-.43*q, 1)
            mat.diffuse_color = color
            mat.keyframe_insert(data_path='diffuse_color', frame=f)
            socket = mat.node_tree.nodes['Principled BSDF'].inputs['Base Color']
            socket.default_value = color
            socket.keyframe_insert(data_path='default_value', frame=f)
    set_interpolation(upper)
    set_interpolation(front)
    for mat in floor_mats.values():
        set_interpolation(mat)
        set_interpolation(mat.node_tree)
    hide_from(lower_objects[initial_floor], v['collapse_start_frame'])
    for i, event in enumerate(driver['events'][1:], 1):
        floor = initial_floor-i
        frame = math.ceil(v['collapse_start_frame'] + event['relative_time_s']*v['fps'] - 1e-9)
        hide_from(lower_objects[floor], frame)
    # Sun lighting for the model; the camera-attached annotations use emission.
    sun_data = bpy.data.lights.new('V10Z_SUN', 'SUN')
    sun_data.energy, sun_data.angle = 2.0, math.radians(10)
    sun = link(scene, 'SUN', sun_data)
    sun.rotation_euler = (math.radians(24),math.radians(-20),math.radians(-30))
    panel(scene, 'TOP_PANEL', (0,height*.417), (width,height*.17), mats['background'], camera)
    panel(scene, 'RIGHT_PANEL', (width*.225,-height*.015), (width*.505,height*.64), mats['panel'], camera)
    panel(scene, 'BOTTOM_PANEL', (0,-height*.452), (width,height*.096), mats['orange'], camera)
    text(scene, 'TITLE', 'WTC 1  /  Impact, chaleur et progression', (-width*.467,height*.441), height*.044, mats['white'], camera)
    text(scene, 'SUBTITLE', 'Calcul V10Y  •  Exemple GRID-0119  •  Géométrie schématique à 110 niveaux', (-width*.466,height*.378), height*.026, mats['muted'], camera)
    text(scene, 'CASE', 'SCÉNARIO EXPLORATOIRE GRID-0119', (-width*.008,height*.268), height*.028, mats['cyan'], camera)
    text(scene, 'BANNER', 'MODÈLE EXPLORATOIRE NON VALIDÉ\nBLENDER VISUALISE LE CALCUL', (0,-height*.433), height*.024, mats['dark'], camera, 'CENTER')
    text(scene, 'MODEL_NOTE', 'Niveaux uniformes : 3,6576 m\nCouleurs : enveloppes thermiques\nBloc bleu : partie supérieure', (-width*.455,-height*.335), height*.023, mats['muted'], camera)
    text(scene, 'ASSUMPTIONS', 'Hypothèses : 3 200 t / niveau ; réserve 1,8\nRésistance 1,2 GJ ; chute initiale 1,83 m\nDommages et températures : entrées dépendantes\nLes niveaux masqués restent dans la masse calculée.', (-width*.008,-height*.220), height*.022, mats['muted'], camera)
    text(scene, 'ENERGY', 'Impact + échauffement localisé + gravité', (-width*.008,-height*.345), height*.023, mats['cyan'], camera)
    for row in driver['frames']:
        phase = row['phase']
        minute, second = divmod(int(row['time_after_impact_s']), 60)
        lines = [f'Après impact     {minute:02d} min {second:02d} s']
        if phase in ['IMPACT_DAMAGE_INPUT', 'THERMAL_FAST_FORWARD']:
            lines.extend(['DOMMAGES FOURNIS EN ENTRÉE' if phase == 'IMPACT_DAMAGE_INPUT' else 'ÉCHAUFFEMENT ACCÉLÉRÉ',
                          f'Étage contrôlant                 {row["controlling_floor"]}',
                          f'Demande / capacité          {row["controlling_dcr"]:.4f}',
                          'Seuil d’initiation                       1',
                          'Feux : plages de températures'])
        elif phase == 'CAPACITY_INITIATION_BEFORE_ASSUMED_DROP':
            lines.extend(['INITIATION DU MODÈLE', f'Étage                                     {initial_floor}',
                          f'Demande / capacité          {row["controlling_dcr"]:.4f}',
                          'Référence : 101 min 54 s', 'Modèle : 5 min 04 s en avance'])
        else:
            lines.extend([f'Propagation                      + {row["model_time_s"]:.2f} s',
                          f'Vitesse                                  {row["velocity_m_s"]:.1f} m/s',
                          f'Masse mobile                       {row["moving_mass_kg"]/1e6:.1f} Mkg',
                          f'Descente du bloc                 {row["upper_block_drop_m"]:.1f} m',
                          'Temps initial de chute exclu'])
            if phase == 'FINAL_MODEL_EVENT_NOT_SETTLED_DEBRIS':
                lines[-1] = 'FIN DU CALCUL : vitesse non nulle'
        obj = text(scene, f'FRAME_TEXT_{row["frame"]:03}', '\n'.join(lines), (-width*.008,height*.201), height*.032, mats['white'], camera)
        visible_only_at(obj, row['frame'])
    driver_text = bpy.data.texts.new('V10Z_DRIVER.json')
    driver_text.write(json.dumps(driver, ensure_ascii=False, indent=2))
    readme = bpy.data.texts.new('LIRE_V10Z.txt')
    readme.write('Scène V10Z : animation enregistrée image par image, sans script à exécuter.\n'
                 + v['permanent_banner'] + '\n' + v['geometry_mapping'] + '\n' + v['initial_drop_warning'] + '\n'
                 + 'La scène WTC1_MASTER est une référence géométrique séparée. Aucun état déformé du modèle EF n’est transmis.\n')
    for area in bpy.context.screen.areas if bpy.context.screen else []:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
    scene.frame_set(1)
    scene.render.filepath = str(ROOT / config['outputs']['video'])
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(scratch / 'preview.blend'), check_existing=False)
    for i, (frame, label) in enumerate(zip(v['still_frames'], v['still_labels']), 1):
        scene.frame_set(frame)
        scene.render.filepath = str(scratch / f'{i:02d}_{label}.png')
        bpy.ops.render.render(write_still=True, scene=scene.name)
    write(scratch / 'preview_manifest.json', {'iteration':'V10Z','blender_version':bpy.app.version_string,
                                             'preview_blend':record(scratch/'preview.blend'),
                                             'animation_audit':audit_animation(scene,driver,config)})


def audit_animation(scene, driver, config):
    upper = bpy.data.objects['V10Z_UPPER_BLOCK']
    objects = [o for o in scene.objects if o.get('iteration') == 'V10Z']
    dynamic_texts = [o for o in objects if o.name.startswith('V10Z_FRAME_TEXT_')]
    position_error, visibility_errors = 0.0, []
    for row in driver['frames']:
        scene.frame_set(row['frame'])
        position_error = max(position_error, abs(upper.location.z + row['upper_block_drop_m']))
        visible = [o.name for o in dynamic_texts if not o.hide_render]
        if visible != [f'V10Z_FRAME_TEXT_{row["frame"]:03}']:
            visibility_errors.append({'frame':row['frame'],'visible':visible})
    physics_count = sum(bool(o.rigid_body) + len(o.particle_systems) + sum(m.type == 'FLUID' for m in o.modifiers) for o in objects)
    require(scene.rigidbody_world is None and physics_count == 0, 'Unexpected Blender physics')
    require(position_error < 1e-4 and not visibility_errors, 'Animation-driver fidelity failure')
    curve_count = sum(len(c.keyframe_points) for o in objects for c in action_curves(o))
    require(curve_count >= config['acceptance']['keyframe_count_minimum'], 'Missing keyframes')
    return {'checked_frame_count':len(driver['frames']),'maximum_position_error_m':position_error,
            'dynamic_caption_visibility_errors':visibility_errors,'physics_object_count':physics_count,
            'keyframe_count':curve_count,'unique_displayed_floor_count':len({o['floor'] for o in objects if 'floor' in o}),
            'blender_used_as_physical_validation':False,'fractional_frame_interpolation_visual_only':True}


def render(config, driver, scratch):
    v, out = config['visual_contract'], config['outputs']
    scene = bpy.data.scenes[v['scene_name']]
    if bpy.context.window:
        bpy.context.window.scene = scene
    require(scene['driver_sha256'] == digest(ROOT/out['selected_driver']), 'Saved driver hash differs')
    preview_manifest = load(scratch/'preview_manifest.json')
    require(digest(scratch/'preview.blend') == preview_manifest['preview_blend']['sha256'], 'Preview blend changed')
    animation_audit = audit_animation(scene, driver, config)
    video_path, blend_path = ROOT/out['video'], ROOT/out['derivative_blend']
    require(not video_path.exists() and not blend_path.exists(), 'Refusing to overwrite a final derivative')
    video_path.parent.mkdir(parents=True, exist_ok=True)
    scene.frame_set(1)
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = v['video_container']
    scene.render.ffmpeg.codec = v['video_codec']
    scene.render.ffmpeg.constant_rate_factor = v['video_quality']
    scene.render.ffmpeg.audio_codec = 'NONE'
    scene.render.filepath = str(video_path)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    started = time.perf_counter()
    bpy.ops.render.render(animation=True, scene=scene.name)
    require(video_path.is_file() and video_path.stat().st_size > 10000, 'Missing video')
    movie = bpy.data.movieclips.load(str(video_path))
    movie_record = {**record(video_path), 'frame_duration':int(movie.frame_duration),
                    'dimensions_px':list(movie.size), 'fps':float(movie.fps), 'decoded':movie.frame_duration>0}
    require(movie_record['frame_duration'] == v['frame_end'], 'Incomplete video frame count')
    require(movie_record['dimensions_px'] == v['resolution_px'], 'Wrong decoded video dimensions')
    bpy.data.movieclips.remove(movie)
    images = []
    for i, (frame,label) in enumerate(zip(v['still_frames'],v['still_labels']),1):
        name = f'{i:02d}_{label}.png'
        target = ROOT/out['render_directory']/name
        require(not target.exists(), 'Refusing to overwrite final still')
        shutil.copyfile(scratch/name,target)
        images.append({'frame':frame,**record(target)})
    master = ROOT/config['protected_files'][0]['path']
    master_unchanged = digest(master) == config['protected_files'][0]['expected_sha256']
    require(master_unchanged, 'Master hash changed')
    manifest = {'iteration':'V10Z','status':'PASS_BAKED_EXPLORATORY_VISUALIZATION',
                'blender_version':bpy.app.version_string,'configuration':record(CONFIG),
                'builder':record(Path(__file__)),'driver':record(ROOT/out['selected_driver']),
                'derivative':record(blend_path),'master':record(master),'master_unchanged':master_unchanged,
                'video':movie_record,'stills':images,'animation_audit':animation_audit,
                'video_render_elapsed_s':time.perf_counter()-started,
                'blender_physics_execution':False,'finite_element_solver_execution':False,
                'rendering_engine':scene.render.engine,'gpu_physical_solver_execution':False,
                'render_gpu_usage':'Eevee uses available graphics hardware; no GPU physics solver',
                'scientific_validation_claim_count':0}
    write(ROOT/out['blender_internal_manifest'],manifest)
    print(json.dumps(manifest,ensure_ascii=False))


def main():
    config = load(CONFIG)
    driver = load(ROOT/config['outputs']['selected_driver'])
    require(driver['configuration']['sha256'] == digest(CONFIG), 'Configuration changed after driver preparation')
    require(bpy.app.version_string.startswith(config['software_files'][0]['expected_version_prefix']), 'Blender version mismatch')
    stage = sys.argv[sys.argv.index('--')+1]
    scratch = ROOT/config['scratch_directory']
    scratch.mkdir(parents=True,exist_ok=True)
    if stage == 'preview':
        require(not (scratch/'preview.blend').exists(), 'Preview already exists')
        require(Path(bpy.data.filepath).resolve() == (ROOT/config['protected_files'][0]['path']).resolve(), 'Wrong master opened')
        build(config,driver,scratch)
    elif stage == 'render':
        render(config,driver,scratch)
    else:
        raise ValueError(stage)


if __name__ == '__main__':
    main()
