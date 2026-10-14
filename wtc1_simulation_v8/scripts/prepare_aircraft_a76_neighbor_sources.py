"""Supplement pinned source audit with pair-local removal and error612 call site."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import tarfile,hashlib,json


def main():
    prep=ROOT/'wtc1_simulation_v8/output/aircraft_a76_preparation'
    private=ROOT/'wtc1_simulation_v8/openradioss_runtime/a76_initial_contact_source_audit'
    manifest=prep/'source_manifest.json';archive=ROOT/read(manifest)['archive']
    assert sha(archive)==read(manifest)['archive_sha256']
    names=['starter/source/interfaces/inter3d1/get_list_remnode.F90',
        'starter/source/interfaces/inter3d1/inint3.F','starter/source/interfaces/inter3d1/i7pwr3.F',
        'starter/source/general_controls/default_values/definter.F']
    rows=[]
    with tarfile.open(archive) as t:
        members={m.name.split('/',1)[1]:m for m in t if '/' in m.name and m.isfile()}
        for name in names:
            assert name in members,name;b=t.extractfile(members[name]).read();p=private/Path(name).name
            assert not p.exists();p.write_bytes(b)
            rows.append({'source_path':name,'private_copy':rel(p),'sha256':hashlib.sha256(b).hexdigest()})
    dump(prep/'source_manifest_supplement.json',{'created_utc':now(),'prior_source_manifest':rel(manifest),
        'prior_source_manifest_sha256':sha(manifest),'files':rows,'new_native':0,
        'source_applied_or_compiled':False,'Windows_binary_source_equivalence_NOT_assumed':True})
    print(json.dumps({'source_supplement':len(rows),'new_native':0}),flush=True)


if __name__=='__main__':main()
