"""Small read-only ASCII DXF inventory/LINE preview; not a general CAD importer."""
from pathlib import Path
from collections import Counter,defaultdict
import json,math
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'wtc1_simulation_v8/input/aircraft_a01/767-200.dxf'
OUT=ROOT/'tmp/aircraft_a01_sources';OUT.mkdir(exist_ok=True)
s=SRC.read_text(encoding='cp1252').splitlines();pairs=[(int(s[i]),s[i+1].strip()) for i in range(0,len(s)-1,2)]
items=[];current=[];section=None
for k,v in pairs:
    if k==0:
        if current:items.append(current)
        current=[(k,v)]
    else:current.append((k,v))
if current:items.append(current)
entities=[];section=None
for item in items:
    d=defaultdict(list)
    for k,v in item:d[k].append(v)
    if d[0]==['SECTION']:section=d[2][0]
    elif d[0]==['ENDSEC']:section=None
    elif section=='ENTITIES':entities.append(d)
lines=[];texts=[];polylines=[];poly=None
for d in entities:
    kind=d[0][0]
    if kind=='POLYLINE':
        poly={'points':[],'closed':bool(int(d.get(70,['0'])[0])&1),'bulge_nonzero':False};polylines.append(poly)
    if kind=='VERTEX' and poly is not None:
        poly['points'].append([float(d[k][0]) for k in [10,20]])
        poly['bulge_nonzero']|=float(d.get(42,['0'])[0])!=0
    if kind=='SEQEND':poly=None
    if kind=='LINE':
        a=[float(d[k][0]) for k in [10,20]];b=[float(d[k][0]) for k in [11,21]]
        lines.append({'a':a,'b':b,'layer':d[8][0]})
    if kind=='TEXT':texts.append({'text':d[1][0],'x':d[10][0],'y':d[20][0]})
result={'entity_types':dict(Counter(d[0][0] for d in entities)),
    'layers':dict(Counter(d[8][0] for d in entities if 8 in d)), 'texts':texts,'lines':lines,'polylines':polylines,
    'scope':'ENTITIES LINE and POLYLINE vertices only; arcs and bulges not evaluated'}
(OUT/'dxf_inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
xs=[c for r in lines for c in [r['a'][0],r['b'][0]]];ys=[c for r in lines for c in [r['a'][1],r['b'][1]]]
lo=min(xs),min(ys);hi=max(xs),max(ys);scale=min(1450/(hi[0]-lo[0]),1100/(hi[1]-lo[1]))
im=Image.new('RGB',(1500,1150),'white');draw=ImageDraw.Draw(im)
for row in lines:
    p=[(25+(q[0]-lo[0])*scale,1125-(q[1]-lo[1])*scale) for q in [row['a'],row['b']]]
    draw.line(p,fill='#213f66',width=1)
for row in polylines:
    p=[(25+(q[0]-lo[0])*scale,1125-(q[1]-lo[1])*scale) for q in row['points']]
    if row['closed']:p.append(p[0])
    if len(p)>1:draw.line(p,fill='#b33d31' if row['bulge_nonzero'] else '#213f66',width=1)
im.save(OUT/'dxf_lines.png')
print(json.dumps({k:v for k,v in result.items() if k not in ['lines','polylines']},indent=2))
print('Largest polylines:',sorted([(i,len(p['points']),min(q[0] for q in p['points']),max(q[0] for q in p['points']),min(q[1] for q in p['points']),max(q[1] for q in p['points'])) for i,p in enumerate(polylines)],key=lambda v:len(polylines[v[0]]['points']),reverse=True)[:12])
