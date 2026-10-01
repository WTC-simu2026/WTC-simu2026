"""Blender's installed FFmpeg-backed sequencer used only as a video decoder.
No scene simulation, interpolation, retiming, stabilization or enhancement.
Indices zero-based in the source presentation sequence; PNGs decoded to sRGB.
"""
import bpy, json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
cfg=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
args=sys.argv[sys.argv.index('--')+1:]
mode=args[0]
t0=time.perf_counter(); records=[]
for key in ['Evidence1','Evidence2']:
    if mode!='overview' and key!=args[1]: continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene; ed=s.sequence_editor_create()
    strip=ed.strips.new_movie(key,cfg['sources'][key],channel=1,frame_start=1)
    s.render.resolution_x,s.render.resolution_y=cfg['dimensions'][key]
    s.render.resolution_percentage=100
    s.render.fps=30; s.render.fps_base=1.001 if key=='Evidence1' else 1
    s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGB'
    s.render.use_sequencer=True
    s.view_settings.view_transform='Standard'
    s.view_settings.look='None'; s.view_settings.exposure=0; s.view_settings.gamma=1
    s.sequencer_colorspace_settings.name='sRGB'
    fps=cfg['fps'][key]
    indices=[round(t*fps) for t in cfg['overview_seconds'][key]] if mode=='overview' else list(range(int(args[2]),int(args[3])+1))
    out=ROOT/(mode if mode=='overview' else f'{key}_{indices[0]}_{indices[-1]}'); out.mkdir(exist_ok=True)
    for i in indices:
        name=f'{key}_f{i:05d}_t{i/fps:08.3f}.png'; p=out/name
        if p.exists(): continue
        s.frame_set(i+1); s.render.filepath=str(p)
        bpy.ops.render.render(write_still=True)
        records.append({'key':key,'source_index':i,'time_seconds_index_over_fps':i/fps,'file':str(p.relative_to(ROOT)),'strip_frame_duration':strip.frame_duration})
(ROOT/(mode+'_'+('_'.join(args[1:]) or 'all')+'_decode.json')).write_text(json.dumps({'blender':bpy.app.version_string,'seconds':time.perf_counter()-t0,'frames':records},indent=2),encoding='utf-8')
