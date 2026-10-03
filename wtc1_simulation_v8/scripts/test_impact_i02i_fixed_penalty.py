"""Independent dimensional/partition checks and bounded primary-source snapshots."""
import json, math, sys, urllib.request
from datetime import datetime,timezone
from pathlib import Path
from run_impact_i02i_fixed_penalty import ROOT,CFG,OUTPUT,generate,dump,sha

cfg=json.loads(CFG.read_text()); folder=OUTPUT/'reference_decks'; folder.mkdir(exist_ok=False)
checks={}; rows=[]; widths=cfg['geometry']['width_mm']-cfg['geometry']['initial_total_crack_length_mm']; th=cfg['geometry']['thickness_mm']; traction=cfg['seam']['peak_normal_traction_mpa']; Kn=cfg['seam']['normal_penalty_N_per_mm3']
for case in [c for c in cfg['cases'] if c['mode']=='fracture' and c['interpretation']=='engineering' and c['id'].startswith(('ENG_L254_','ENG_L127_R','ENG_L0635_'))]:
    p=folder/case['id']; p.mkdir(); m=generate(cfg,case,p); springs=m['seam_pairs']
    areas=sum(s['area_mm2'] for s in springs); energy=sum(.5*s['peak_force_N']*s['deltaf_mm']*.001 for s in springs)
    checks[case['id']+'_reference_area_partition']=math.isclose(areas,widths*th,rel_tol=1e-12)
    checks[case['id']+'_triangular_energy_units']=math.isclose(energy,30*widths*th*.001,rel_tol=1e-12)
    checks[case['id']+'_mesh_independent_peak_gap']=all(math.isclose(s['delta0_mm'],traction/Kn,rel_tol=1e-12) for s in springs)
    rows.append({'case':case['id'],'initial_ligament_area_mm2':areas,'complete_monotone_normal_triangle_work_J':energy,'delta0_mm':springs[0]['delta0_mm'],'deltaf_mm':springs[0]['deltaf_mm'],'solver_executed':False})
checks['three_spatial_meshes']=len(rows)==3
dump(OUTPUT/'reference_checks.json',{'pass':all(checks.values()),'checks':checks,'rows':rows,'scope':'Independent reference-area and monotone pure-normal triangle integral; not actual irreversible dissipation under hysteresis or mixed-mode loading.'})
sources=[]; sf=OUTPUT/'source_snapshots'; sf.mkdir(exist_ok=False)
oldmanifest=ROOT/'wtc1_simulation_v8/output/impact_i02i_material/source_manifest.json'
sources.append({'id':'REUSED_I02I_A_SOURCE_MANIFEST','path':str(oldmanifest.relative_to(ROOT).as_posix()),'sha256':sha(oldmanifest),'reuse':'Existing bounded NASA and constitutive documents, no redownload or archive scan.'})
for item in cfg['sources']:
    if item['id'] not in ['ALTAIR_SENSOR_DIST','ALTAIR_STOP_SENSOR','ALTAIR_SPRING_HISTORY','ALTAIR_TYPE8']: continue
    row=dict(item,accessed_utc=datetime.now(timezone.utc).isoformat()); p=sf/(item['id']+'.html')
    try:
        with urllib.request.urlopen(urllib.request.Request(item['url'],headers={'User-Agent':'WTC1 bounded research harness'}),timeout=15) as response: data=response.read(1000001)
        assert len(data)<=1000000
        p.write_bytes(data); row.update(path=str(p.relative_to(ROOT).as_posix()),bytes=len(data),sha256=sha(p),status='saved_primary_page')
    except Exception as e: row.update(status='fetch_failed_primary_web_tool_read_used',error=str(e))
    sources.append(row)
dump(OUTPUT/'source_manifest.json',{'sources':sources,'bounded_access':True,'archives_scanned':False,'date':datetime.now(timezone.utc).isoformat()})
print(json.dumps({'reference_checks':sum(checks.values()),'total':len(checks),'pass':all(checks.values()),'primary_snapshots':sum(s.get('status')=='saved_primary_page' for s in sources)}))
