"""Native labels for existing beam channels, same-material observation only."""
import os,shutil
from run_aircraft_a04 import OUT,RUNTIME,read,dump,sha,rel,now,ff,execute
if __name__=='__main__':
    src=OUT/'r1/ELASTIC_HIGHY_N5';n=read(src/'generation.json')['name'];d=OUT/'history_label_probe';assert not d.exists();d.mkdir()
    pins={rel(p):sha(p) for p in src.rglob('*') if p.is_file()}
    for p in src.glob(n+'_0001_*.rst'):shutil.copy2(p,d/p.name)
    end=read(src/'audit.json')['actual_main_end_time_ms'];lines=['/TH/TITLE','/PRINT/-1/100',f'/RUN/{n}/2',ff(end+1e-6),'/TFILE/4',ff(1e30),'/VERS/2026']
    (d/(n+'_0002.rad')).write_text('\n'.join(lines)+'\n')
    env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='2',KMP_STACKSIZE='400m')
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0002.rad'],d,'probe.log',60,env)
    assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T02'],d,'converter.log',60,env)
    changed=[p for p,h in pins.items() if sha(OUT.parents[2]/p)!=h]
    dump(d/'provenance.json',{'created_utc':now(),'source_files_unchanged':not changed,'changed':changed,'labels_only':True,'physical_window_extension_credited':False,'material_properties_unchanged':True})
    assert not changed
    print({'labels_saved':True})
