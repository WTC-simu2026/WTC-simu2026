"""Restricted glTF 1.0 binary geometry reader. No shaders or remote code executed."""
import json,struct,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; cfg=json.loads((ROOT/'wtc1_simulation_v8/data/impact_i02_geom.json').read_text())
src=ROOT/cfg['source_directory']/'models/b762.glb'; out=ROOT/cfg['output_directory']; out.mkdir(parents=True,exist_ok=True)
b=src.read_bytes(); magic,version,total,jn,fmt=struct.unpack_from('<5I',b)
assert magic==0x46546c67 and version==1 and total==len(b) and fmt==0
d=json.loads(b[20:20+jn]); buf=b[20+jn:]; assert len(buf)==d['buffers']['binary_glTF']['byteLength']
assert not d['animations'] and not d['skins']
metadata_mismatches={}
def access(key):
    a=d['accessors'][key]; v=d['bufferViews'][a['bufferView']]; assert v['buffer']=='binary_glTF'
    typ={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    dims={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]; size=np.dtype(typ).itemsize
    stride=a.get('byteStride',0) or dims*size; offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    assert offset+(a['count']-1)*stride+dims*size<=v.get('byteOffset',0)+v['byteLength']
    ar=np.ndarray((a['count'],dims),dtype=typ,buffer=buf,offset=offset,strides=(stride,size)).copy()
    assert np.all(np.isfinite(ar))
    for label,value in [('min',ar.min(axis=0)),('max',ar.max(axis=0))]:
        if label in a and not np.allclose(value,a[label],rtol=1e-5,atol=1e-5):
            metadata_mismatches[key+'_'+label]={'declared':a[label],'actual':value.tolist(),'type':a['type'],'disposition':'Source unchanged; use validated actual buffer values, not incorrect metadata'}
    return ar
points=[]; tris=[]; groups=[]; records=[]; visited=set(); offset=0
def walk(key,parent):
    global offset
    assert key not in visited; visited.add(key); n=d['nodes'][key]
    assert not any(t in n for t in ['translation','rotation','scale']) # This particular file is matrix-only.
    local=np.asarray(n.get('matrix',np.eye(4).flatten(order='F').tolist())).reshape(4,4,order='F'); mat=parent@local
    assert np.allclose(mat[3],[0,0,0,1])
    for meshkey in n.get('meshes',[]):
        for primitive in d['meshes'][meshkey]['primitives']:
            assert primitive.get('mode',4)==4
            p=access(primitive['attributes']['POSITION']).astype(float); idx=access(primitive['indices']).reshape(-1)
            assert len(idx)%3==0 and idx.min()>=0 and idx.max()<len(p)
            transformed=(np.c_[p,np.ones(len(p))]@mat.T)[:,:3]
            # glTF x/right,y/up,z/aft -> analysis x/aft,y/span,z/up, a proper rotation.
            normalized=transformed[:,[2,0,1]]
            k=len(records); tri=idx.reshape(-1,3).astype(np.int64)
            records.append({'id':k,'node':key,'mesh':meshkey,'material':primitive.get('material'),'vertices':len(p),'triangles':len(tri),'min':normalized.min(axis=0).tolist(),'max':normalized.max(axis=0).tolist()})
            points.append(normalized); tris.append(tri+offset); groups.append(np.full(len(tri),k)); offset+=len(p)
    for child in n.get('children',[]): walk(child,mat)
for key in d['scenes'][d['scene']]['nodes']: walk(key,np.eye(4))
pts=np.concatenate(points); triangles=np.concatenate(tris); group=np.concatenate(groups)
assert len(visited)==len(d['nodes'])
np.savez_compressed(out/'source_geometry.npz',points_m=pts,triangles=triangles,primitive_ids=group)
audit={'source_sha256':hashlib.sha256(b).hexdigest(),'source_format':'glTF binary 1.0','raw_units':'glTF metres','analysis_axes':'x aft, y span, z up (cyclic permutation from glTF)','min_m':pts.min(axis=0).tolist(),'max_m':pts.max(axis=0).tolist(),'dimensions_m':np.ptp(pts,axis=0).tolist(),'vertices':len(pts),'triangles':len(triangles),'primitives':records,'node_count':len(visited),'no_animations':True,'no_skins':True,'mechanical_credit':cfg['mechanical_credit'],'all_buffer_bounds_checked':True,'accessor_metadata_mismatches':metadata_mismatches,'scope':'Geometry only; materials are graphics identifiers, not mechanical material cards'}
(out/'geometry_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k not in ['primitives','accessor_metadata_mismatches']},indent=2)); print('metadata_mismatches',len(metadata_mismatches))
