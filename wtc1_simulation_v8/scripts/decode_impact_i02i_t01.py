"""Own bounded reader for the four declared two-node version3040 T01 files.

Derived from local raw-file inspection. Rejects different schemas and corrupt
records; not an upstream converter replacement or a general T01 decoder.
"""
from __future__ import annotations
import struct
from pathlib import Path
import numpy as np

def records(data):
    pos=0;out=[]
    while pos<len(data):
        if pos+8>len(data):raise ValueError('Truncated record marker')
        n=struct.unpack_from('>i',data,pos)[0]
        if n<0 or pos+n+8>len(data):raise ValueError('Invalid record length')
        if struct.unpack_from('>i',data,pos+n+4)[0]!=n:raise ValueError('Different trailing marker')
        out.append((pos,data[pos+4:pos+4+n]));pos+=n+8
    if pos!=len(data):raise ValueError('Bytes unconsumed')
    return out

def ints(b):
    if len(b)%4:raise ValueError('Non-integer payload')
    return list(struct.unpack('>'+str(len(b)//4)+'i',b))

def decode(data,schema,title):
    rec=records(data)
    if len(rec)<20 or [len(b) for _,b in rec[:16]]!=schema['header_payload_bytes']:raise ValueError('Unsupported header layout')
    b=[r[1] for r in rec[:16]]
    if ints(b[0][:4])!=[schema['version']]:raise ValueError('Unsupported version')
    if b[0][4:].decode('ascii').rstrip()!=title:raise ValueError('Wrong run title')
    if ints(b[2])!=schema['counts_signature'] or ints(b[3])!=schema['global_codes']:raise ValueError('Wrong counts/global codes')
    if ints(b[9][:20])!=schema['spring_group_signature'] or b[9][20:].decode('ascii').rstrip()!='SEAM_HISTORY':raise ValueError('Wrong spring group')
    if ints(b[10][:4])!=[1] or b[10][4:].decode('ascii').rstrip()!='ONE_SPRING':raise ValueError('Wrong element')
    if ints(b[11])!=schema['spring_codes']:raise ValueError('Wrong spring variable codes')
    if ints(b[12][:20])!=schema['node_group_signature'] or b[12][20:].decode('ascii').rstrip()!='NODES':raise ValueError('Wrong node group')
    if [ints(b[j][:4])[0] for j in [13,14]]!=schema['node_ids'] or ints(b[15])!=schema['node_codes']:raise ValueError('Wrong node fields')
    if rec[16][0]!=schema['header_end_byte'] or (len(rec)-16)%4:raise ValueError('Unsupported tail layout')
    rows=[]
    for j in range(16,len(rec),4):
        payloads=[r[1] for r in rec[j:j+4]]
        if [len(v) for v in payloads]!=schema['row_payload_bytes']:raise ValueError('Wrong time row length')
        # Independent scalar struct decoding, promoted to double without
        # adding information to the originally stored 32-bit values.
        rows.append([value for raw in payloads for value in struct.unpack('>'+str(len(raw)//4)+'f',raw)])
    a=np.asarray(rows,dtype=np.float64)
    if a.shape[1]!=41 or not np.isfinite(a).all() or not np.all(np.diff(a[:,0])>0):raise ValueError('Invalid numeric history')
    meta={'version':schema['version'],'endian':'big','bytes':len(data),'records':len(rec),'rows':len(a),'columns':41,
        'header_records':16,'first_row_byte':rec[16][0],'title':title,
        'spring_codes':ints(b[11]),'node_codes':ints(b[15]),'exact_EOF_consumed':True,
        'date_build_header':b[1].decode('ascii').rstrip(),'scope':'Declared two-node layout only, exact upstream code provenance unknown'}
    return a,meta

def decode_file(path,schema,title):return decode(Path(path).read_bytes(),schema,title)

def strided_check(data,schema):
    """Separate fixed-stride NumPy reader checks value packing after framing."""
    start=schema['header_end_byte'];stride=sum(n+8 for n in schema['row_payload_bytes'])
    if (len(data)-start)%stride:raise ValueError('Incomplete stride')
    n=(len(data)-start)//stride;blocks=[];offset=start
    for size in schema['row_payload_bytes']:
        blocks.append(np.ndarray((n,size//4),dtype='>f4',buffer=data,offset=offset+4,strides=(stride,4)).astype(np.float64))
        offset+=size+8
    return np.column_stack(blocks)
