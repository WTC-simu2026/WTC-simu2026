"""Read cached pinned Starter contact sources for the NEW A75 initialization failure."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import tarfile,json,hashlib

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a76_preparation'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a76_initial_contact_source_audit'


def main():
    assert not OUT.exists() and not PRIVATE.exists();OUT.mkdir();PRIVATE.mkdir()
    archive=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'
    assert sha(archive)=='d64b773e899c174f5d59aadc4d2b73a101a083581e611d67215aaa50037cf9f8'
    names=['starter/source/interfaces/int07/hm_read_inter_type07.F',
        'starter/source/interfaces/inter3d1/i7err3.F','starter/source/interfaces/inter3d1/i7cor3.F',
        'starter/source/interfaces/inter3d1/i7remnode.F','starter/source/interfaces/inter3d1/i7cmp3.F',
        'starter/source/general_controls/default_values/hm_read_definter_type07.F']
    rows=[]
    with tarfile.open(archive) as t:
        members={m.name.split('/',1)[1]:m for m in t if '/' in m.name and m.isfile()}
        for name in names:
            b=t.extractfile(members[name]).read();p=PRIVATE/Path(name).name;p.write_bytes(b)
            rows.append({'source_path':name,'private_copy':rel(p),'sha256':hashlib.sha256(b).hexdigest()})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a',
        'archive':rel(archive),'archive_sha256':sha(archive),'files':rows,
        'Windows_Starter_binary_sha256':read(ROOT/'wtc1_simulation_v8/data/aircraft_a75_predeclaration.json')['Starter_sha256'],
        'source_binary_equivalence_NOT_assumed':True,'source_analysis_secondary_to_actual_A75_messages':True,
        'historical_archive_inspected':False,'source_applied_or_compiled':False,'new_native':0})
    print(json.dumps({'A76_cached_sources':len(rows),'new_native':0,'source_not_applied_or_compiled':True}),flush=True)


if __name__=='__main__':main()
