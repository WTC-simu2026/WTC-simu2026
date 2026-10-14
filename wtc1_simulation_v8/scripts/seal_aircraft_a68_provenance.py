"""Preserve both prior manifests and seal the registrar/provenance files before registering A68."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import json

def main():
    out=ROOT/'wtc1_simulation_v8/output/aircraft_a68';p=out/'artifact_manifest_r1.json';m=read(p)
    for r in m['files']:assert sha(ROOT/r['path'])==r['sha256']
    paths={ROOT/r['path'] for r in m['files']}|{p,out/'artifact_manifest.json',Path(__file__),ROOT/'wtc1_simulation_v8/scripts/register_aircraft_a68.py'}
    dump(out/'artifact_manifest_r2.json',{'created_utc':now(),'previous_manifest':rel(p),'previous_manifest_sha256':sha(p),'previous_manifests_preserved':True,
        'own_data_scripts_outputs_only_AGPL_excluded':True,'files':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':sha(x)} for x in sorted(paths)]})
    print(json.dumps({'A68_provenance_sealed':True,'files':len(paths)}),flush=True)

if __name__=='__main__':main()
