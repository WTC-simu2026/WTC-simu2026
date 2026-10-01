"""Independent native Blender reopen and glTF2 round-trip comparison by source primitive."""
import bpy,numpy as np,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; base=ROOT/'wtc1_3d_v4/output/impact_i02_geom'; out=base/'final'
data=np.load(base/'source_geometry.npz'); pts=data['points_m']; faces=data['triangles']; ids=data['primitive_ids']; selection=np.load(out/'retained_triangle_indices.npz')['source_triangle_indices']; faces=faces[selection]; ids=ids[selection]
def canonical(arr):
    # Compare geometric triangles independent of winding/index order, quantization
    # used only for sorting; differences measured on original floating coordinates.
    result=[]
    for tri in arr:
        order=np.lexsort(tuple(np.round(tri[:,j],5) for j in [2,1,0])); result.append(tri[order].reshape(-1))
    arr=np.asarray(result); order=np.lexsort(tuple(np.round(arr[:,j],5) for j in reversed(range(9))))
    return arr[order]
expected={int(k):canonical(pts[faces[ids==k]]) for k in np.unique(ids)}
reports={}
for mode in ['blend','glb']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if mode=='blend': bpy.ops.wm.open_mainfile(filepath=str(out/'B762_GEOMETRY_ONLY.blend'),use_scripts=False)
    else: bpy.ops.import_scene.gltf(filepath=str(out/'B762_GEOMETRY_ONLY.glb'))
    errors=[]; actual_count=0; seen=set()
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH': continue
        k=int(obj['source_primitive']); seen.add(k); mesh=obj.data; mesh.calc_loop_triangles()
        actual=np.asarray([[list(obj.matrix_world@mesh.vertices[i].co) for i in tri.vertices] for tri in mesh.loop_triangles])
        want=expected[k]; got=canonical(actual); assert want.shape==got.shape,(mode,k,want.shape,got.shape)
        error=float(np.max(np.abs(want-got))); assert error<1e-5,(mode,k,error)
        assert obj.rigid_body is None and not obj.modifiers and not obj.constraints
        errors.append(error); actual_count+=len(actual)
    assert seen==set(expected)
    reports[mode]={'primitive_count':len(seen),'triangles':actual_count,'max_triangle_vertex_error_m':max(errors),'no_rigid_bodies_modifiers_or_constraints':True}
(out/'roundtrip_audit.json').write_text(json.dumps(reports,indent=2),encoding='utf-8'); print(json.dumps(reports,indent=2))
