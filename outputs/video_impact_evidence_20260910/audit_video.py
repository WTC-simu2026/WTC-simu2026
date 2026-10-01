"""Read-only evidence intake and contact sheets. No inferred/reconstructed pixels."""
import hashlib, json, subprocess, sys, time, struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def save(name,data):
    (ROOT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
def boxes(data,start=0,end=None):
    end=len(data) if end is None else end
    while start+8<=end:
        n,typ=struct.unpack_from('>I4s',data,start); header=8
        if n==1: n=struct.unpack_from('>Q',data,start+8)[0]; header=16
        if n==0: n=end-start
        if n<header or start+n>end: raise ValueError('Invalid MP4 box')
        yield typ,data[start+header:start+n]
        start+=n
def mp4_tables(p):
    # Preserve encoded timing tables independently of the decoder's fps report.
    result=[]
    def walk(data,path=''):
        for typ,b in boxes(data):
            tag=typ.decode('ascii',errors='replace'); loc=path+'/'+tag
            if typ in (b'moov',b'trak',b'mdia',b'minf',b'stbl',b'edts'): walk(b,loc)
            elif typ in (b'stts',b'ctts'):
                n=struct.unpack_from('>I',b,4)[0]
                fmt='>Ii' if typ==b'ctts' and b[0]==1 else '>II'
                entries=[list(struct.unpack_from(fmt,b,8+8*i)) for i in range(n)]
                result.append({'path':loc,'version':b[0],'entries':entries,'sample_count':sum(x[0] for x in entries)})
            elif typ==b'mdhd':
                offset=20 if b[0]==1 else 12
                scale=struct.unpack_from('>I',b,offset)[0]
                duration=struct.unpack_from('>Q' if b[0]==1 else '>I',b,offset+4)[0]
                result.append({'path':loc,'timescale':scale,'duration_ticks':duration})
            elif typ==b'elst': result.append({'path':loc,'raw_hex':b.hex()})
    walk(Path(p).read_bytes()); return result
def prepare():
    if (ROOT/'intake.json').exists(): raise RuntimeError('Preserve existing intake')
    data={'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'sources':{}}
    for key,p in CFG['sources'].items():
        data['sources'][key]={'path':p,'bytes':Path(p).stat().st_size,'sha256_before':digest(p)}
        if p.endswith('.mp4'):
            r=subprocess.run([CFG['ffmpeg'],'-hide_banner','-i',p],capture_output=True,text=True)
            (ROOT/(key+'_metadata.txt')).write_text(r.stderr,encoding='utf-8')
            data['sources'][key]['mp4_tables']=mp4_tables(p)
    save('intake.json',data)
    r=subprocess.run([CFG['ffmpeg'],'-version'],capture_output=True,text=True)
    (ROOT/'decoder_metadata_version.txt').write_text(r.stdout,encoding='utf-8')
    r=subprocess.run(['C:/Program Files/PowerShell/7/pwsh.exe','-NoProfile','-File',str(ROOT.parents[1]/'harness/tools/Test-WtcHarness.ps1')],capture_output=True,text=True,encoding='utf-8')
    (ROOT/'harness_before.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
    if r.returncode: raise RuntimeError('Harness precheck failed')
    print('Intake and harness saved')
def sheet(folder):
    files=sorted((ROOT/folder).glob('*.png'))
    if not files: raise RuntimeError('No frames')
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
    for offset in range(0,len(files),24):
        subset=files[offset:offset+24]; out=Image.new('RGB',(4*350,((len(subset)+3)//4)*290),(24,28,34)); d=ImageDraw.Draw(out)
        for j,p in enumerate(subset):
            im=Image.open(p).convert('RGB'); im.thumbnail((344,255))
            x=(j%4)*350; y=(j//4)*290
            out.paste(im,(x+(350-im.width)//2,y))
            d.text((x+5,y+258),p.stem,fill='white',font=font)
        out.save(ROOT/(folder+f'_sheet_{offset//24+1:02d}.jpg'),quality=95)
    print('Sheets:',len(files))
def verify():
    intake=json.loads((ROOT/'intake.json').read_text(encoding='utf-8'))
    checks={k:digest(v['path'])==v['sha256_before'] for k,v in intake['sources'].items()}
    save('integrity_after.json',{'checks':checks,'all_originals_unchanged':all(checks.values())})
    assert all(checks.values()); print(checks)
if __name__=='__main__':
    if sys.argv[1]=='prepare': prepare()
    elif sys.argv[1]=='sheet': sheet(sys.argv[2])
    elif sys.argv[1]=='verify': verify()
