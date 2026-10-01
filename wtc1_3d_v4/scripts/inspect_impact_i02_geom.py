"""Read-only examination of imported mesh datablocks; launch Blender with --disable-autoexec."""
import bpy,json,numpy as np,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
cfg=json.loads((ROOT/'wtc1_simulation_v8/data/impact_i02_geom.json').read_text())
src=ROOT/cfg['source_directory']/'source/b762/767-200.blend'; out=ROOT/cfg['output_directory']; out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(src),link=False) as (available,loaded):
    source_names=list(available.objects); loaded.objects=list(source_names)
items=[]
for obj in loaded.objects:
    if obj is None: continue
    if obj.type!='MESH' or not len(obj.data.vertices): continue
    # No scene evaluation, drivers, constraints or modifiers executed here.
    points=np.asarray([list(obj.matrix_world@v.co) for v in obj.data.vertices])
    items.append({'name':obj.name,'vertices':len(points),'polygons':len(obj.data.polygons),'min':points.min(axis=0).tolist(),'max':points.max(axis=0).tolist(),'dimensions':np.ptp(points,axis=0).tolist(),'matrix_world':[list(r) for r in obj.matrix_world],'materials':[m.name if m else None for m in obj.data.materials],'modifiers':[m.type for m in obj.modifiers],'constraints':[c.type for c in obj.constraints],'parent':obj.parent.name if obj.parent else None})
report={'source_objects':source_names,'meshes':items,'blender':bpy.app.version_string,'global_min':np.min([i['min'] for i in items],axis=0).tolist(),'global_max':np.max([i['max'] for i in items],axis=0).tolist(),'embedded_text_blocks':[t.name for t in bpy.data.texts],'method':'Raw mesh data and object transforms only, not source scene evaluated; automatic scripts disabled'}
(out/'source_geometry_inventory.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'mesh_count':len(items),'global_min':report['global_min'],'global_max':report['global_max'],'scope':'Unfiltered source datablocks, not assembled aircraft dimensions'},indent=2))
