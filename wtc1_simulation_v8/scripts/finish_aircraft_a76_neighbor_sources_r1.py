"""Preserve partial R0 source lookup; finish only its missing correctly located helper."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import tarfile,hashlib,json


def main():
    prep=ROOT/'wtc1_simulation_v8/output/aircraft_a76_preparation'
    private=ROOT/'wtc1_simulation_v8/openradioss_runtime/a76_initial_contact_source_audit'
    prior=prep/'source_manifest.json';archive=ROOT/read(prior)['archive']
    assert sha(archive)==read(prior)['archive_sha256']
    names=['starter/source/interfaces/inter3d1/get_list_remnode.F90',
        'starter/source/interfaces/inter3d1/inint3.F','starter/source/interfaces/inter3d1/i7pwr3.F',
        'starter/source/interfaces/interf1/definter.F']
    dump(prep/'source_supplement_R0_failure.json',{'created_utc':now(),'pass':False,
        'script':'wtc1_simulation_v8/scripts/prepare_aircraft_a76_neighbor_sources.py',
        'error':'Guessed definter path absent; guard failed after three private source copies, no native run.',
        'partial_source_copies_retained':names[:3],'no_Engine_or_Starter_or_source_modification':True,
        'repair':'Use actual tar index path starter/source/interfaces/interf1/definter.F in separate R1 finisher.'})
    rows=[]
    with tarfile.open(archive) as t:
        members={m.name.split('/',1)[1]:m for m in t if '/' in m.name and m.isfile()}
        assert all(name in members for name in names)
        for index,name in enumerate(names):
            b=t.extractfile(members[name]).read();p=private/Path(name).name
            if index<3:assert p.read_bytes()==b
            else:assert not p.exists();p.write_bytes(b)
            rows.append({'source_path':name,'private_copy':rel(p),'sha256':hashlib.sha256(b).hexdigest(),
                'existing_R0_copy_reused':index<3})
    dump(prep/'source_manifest_supplement_r1.json',{'created_utc':now(),'prior_source_manifest':rel(prior),
        'prior_source_manifest_sha256':sha(prior),'files':rows,'new_native':0,
        'source_applied_or_compiled':False,'Windows_binary_source_equivalence_NOT_assumed':True,
        'R0_lookup_failure_preserved':True})
    print(json.dumps({'source_supplement_R1':4,'new_native':0}),flush=True)


if __name__=='__main__':main()
