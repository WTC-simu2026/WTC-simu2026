"""Read TH3040 records in Python; no native converter or solver launch.

Scope: the pinned HIST1 metadata layout with 40-character entity titles, as
independently checked against the saved A67 native CSV before A81 use.
"""
import struct
import numpy as np
from recover_aircraft_a05_history import records


def integers(b):
    assert len(b)%4==0
    return list(struct.unpack('>'+str(len(b)//4)+'i',b))


def decode(path):
    rr=records(path); code=integers(rr[0][:4])[0];assert code==3040,code
    counts=integers(rr[2]);assert len(counts)==6
    npart,nmat,ngeo,nsub,ngroup,nglobal=counts
    global_ids=integers(rr[3]);assert len(global_ids)==nglobal
    offset=4;parts=[];subsets=[];groups=[]
    for k in range(npart):
        b=rr[offset];offset+=1;assert len(b)==60
        ident=integers(b[:4])[0];title=b[4:44].decode('ascii').rstrip()
        material,subset,prop,nvars=integers(b[44:])
        variables=integers(rr[offset]) if nvars else []
        if nvars:offset+=1
        assert len(variables)==nvars
        parts.append({'id':ident,'title':title,'material':material,'subset':subset,'property':prop,'variables':variables})
    for k in range(nmat+ngeo):
        assert len(rr[offset])==44;offset+=1
    for k in range(nsub):
        b=rr[offset];offset+=1;assert len(b)==60
        ident,parent,nchild,nparts,nvars=integers(b[:20]);title=b[20:].decode('ascii').rstrip()
        children=integers(rr[offset]) if nchild else []
        if nchild:offset+=1
        part_ids=integers(rr[offset]) if nparts else []
        if nparts:offset+=1
        variables=integers(rr[offset]) if nvars else []
        if nvars:offset+=1
        assert len(children)==nchild and len(part_ids)==nparts and len(variables)==nvars
        subsets.append({'id':ident,'title':title,'parent':parent,'parts':part_ids,'variables':variables})
    for k in range(ngroup):
        b=rr[offset];offset+=1;assert len(b)==60
        ident,kind,extra,nentities,nvars=integers(b[:20]);title=b[20:].decode('ascii').rstrip();entities=[]
        for j in range(nentities):
            b=rr[offset];offset+=1;assert len(b)==44
            entities.append({'id':integers(b[:4])[0],'title':b[4:].decode('ascii').rstrip()})
        variables=integers(rr[offset]) if nvars else []
        if nvars:offset+=1
        assert len(variables)==nvars
        groups.append({'id':ident,'title':title,'kind':kind,'extra':extra,'entities':entities,'variables':variables})
    schema=[('time',1),('global',nglobal)]
    if sum(len(p['variables']) for p in parts):schema.append(('parts',sum(len(p['variables']) for p in parts)))
    for k,s in enumerate(subsets):
        if s['variables']:schema.append(('subset_'+str(k),len(s['variables'])))
    for k,g in enumerate(groups):
        if g['variables']:schema.append(('group_'+str(k),len(g['entities'])*len(g['variables'])))
    nr=len(schema);assert (len(rr)-offset)%nr==0,(len(rr),offset,nr)
    nrows=(len(rr)-offset)//nr;assert nrows>0
    result={}
    for j,(name,size) in enumerate(schema):
        payloads=rr[offset+j::nr];assert len(payloads)==nrows and all(len(p)==size*4 for p in payloads)
        result[name]=np.frombuffer(b''.join(payloads),dtype='>f4').astype(float).reshape(nrows,size)
    flat=np.concatenate([result[k] for k,n in schema],axis=1)
    assert np.all(np.isfinite(flat)) and np.all(np.diff(result['time'][:,0])>0)
    return {'code':code,'header_records':offset,'records_per_frame':nr,'rows':nrows,
        'global_ids':global_ids,'parts':parts,'subsets':subsets,'groups':groups,
        'frame_schema':schema},result,flat
