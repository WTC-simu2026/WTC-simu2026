"""New static surface-topology audit of A77 failure nodes, no native replay."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from prepare_aircraft_a66_current_area_r1 import sections
from pathlib import Path
import json,collections,tarfile,hashlib

PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a78_preparation'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a78_contact_geometry_audit'


def main():
    assert not PREP.exists() and not PRIVATE.exists();PREP.mkdir();PRIVATE.mkdir()
    rows=[]
    for case in read(ROOT/'wtc1_simulation_v8/data/aircraft_a77_predeclaration.json')['cases']:
        path=ROOT/case['inputs'][0]['path'];assert sha(path)==case['inputs'][0]['sha256'];d=sections(path)
        params=d['/INTER/TYPE7/2'];group=int(params[1][:10]);surface=int(params[1][10:20])
        secondary={int(v) for l in d[f'/GRNOD/NODE/{group}'][1:] for v in l.split()}
        main_parts={int(v) for l in d[f'/SURF/PART/{surface}'][1:] for v in l.split()}
        coords={int(l[:10]):tuple(map(float,l[10:].split())) for l in d['/NODE']}
        parent={};incidence=collections.defaultdict(list);facets=[]
        def find(n):
            parent.setdefault(n,n)
            while parent[n]!=n:parent[n]=parent[parent[n]];n=parent[n]
            return n
        def union(a,b):
            a=find(a);b=find(b)
            if a!=b:parent[max(a,b)]=min(a,b)
        for part in sorted(main_parts):
            for family,size in [('SHELL',4),('SH3N',3),('TRIA',3)]:
                for line in d.get(f'/{family}/{part}',[]):
                    fields=list(map(int,line.split()));ID=fields[0];nodes=fields[1:1+size]
                    assert len(nodes)==size and all(n in coords for n in nodes)
                    for n in nodes:find(n);incidence[n].append({'part':part,'element':ID,'nodes':nodes,'family':family})
                    for n in nodes[1:]:union(nodes[0],n)
                    facets.append({'part':part,'element':ID,'nodes':nodes,'family':family})
        components=collections.defaultdict(list)
        for n in parent:components[find(n)].append(n)
        coordinate_sets=collections.defaultdict(list)
        for n in parent:coordinate_sets[coords[n]].append(n)
        multiple=[v for v in coordinate_sets.values() if len(v)>1]
        cross_components=[v for v in multiple if len({find(n) for n in v})>1]
        failures=read(ROOT/'wtc1_simulation_v8/output/aircraft_a77'/case['case']/'initialization_message_audit.json')
        printed=[e['printed_node'] for e in failures['events'] if e['kind']=='ERROR']
        assert len(printed)==916;failed=set(printed)
        assert failed<=secondary and failed<=set(parent)
        coordinate_lookup={n:group for group in multiple for n in group}
        details=[{'printed_node_number':n,'source_label_exists_and_on_self_surface':True,
            'coordinate_mm':coords[n],'source_surface_component_min_label':find(n),
            'main_element_incidence':incidence[n],'same_written_coordinate_main_labels':coordinate_lookup.get(n,[n]),
            'same_coordinate_distinct_surface_components':sorted({find(v) for v in coordinate_lookup.get(n,[n])}),
            'native_actual_pair_segment_NOT_identified_from_number_only':True} for n in sorted(failed)]
        out=PREP/(case['case']+'_surface_nodes.json')
        dump(out,{'nodes':details,'source_surface_components':dict(components),'source_main_facets':facets,
            'source_topology_only_NOT_mechanical_constraint_rank':True})
        row={'case':case['case'],'source':rel(path),'source_sha256':sha(path),'main_parts':len(main_parts),
            'main_facets':len(facets),'main_nodes':len(parent),'secondary_nodes':len(secondary),
            'surface_components_by_shared_ID':len(components),'same_written_coordinate_groups':len(multiple),
            'same_written_coordinate_groups_across_surface_components':len(cross_components),
            'error_records':len(printed),'unique_printed_error_node_numbers':len(failed),
            'all_printed_failure_numbers_match_source_secondary_and_main_labels':True,
            'failed_numbers_with_coincident_labels_in_other_components':sum(len(r['same_coordinate_distinct_surface_components'])>1 for r in details),
            'geometry_file':rel(out),'native_segment_pair_mapping_or_coordinate_memory_validation':False,
            'no_structural_disconnection_inferred':True}
        rows.append(row)
    compare_keys=[k for k in rows[0] if k not in ['case','source','source_sha256','geometry_file']]
    assert all(rows[0][k]==rows[1][k] for k in compare_keys)
    archive=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'
    assert sha(archive)=='d64b773e899c174f5d59aadc4d2b73a101a083581e611d67215aaa50037cf9f8'
    sources=[]
    with tarfile.open(archive) as t:
        paths=['starter/source/general_controls/inputoutput/hm_read_ioflag.F',
            'hm_cfg_files/config/CFG/radioss2023/CARDS/ioflag.cfg']
        for path in paths:
            m=next(m for m in t if m.name.endswith('/'+path));b=t.extractfile(m).read();p=PRIVATE/Path(path).name
            p.write_bytes(b);sources.append({'source_path':path,'private_copy':rel(p),'sha256':hashlib.sha256(b).hexdigest()})
    dump(PREP/'surface_topology_review.json',{'created_utc':now(),'pass_static_only':True,'models':rows,
        'original_paired_static_self_surface_results_equal':True,'native_pair_labels_not_available':True,
        'new_native':0,'source_Engine_or_Starter_modified_or_compiled':False,
        'print_option_sources':sources,'related_pinned_source_NOT_assumed_identical_to_Windows_binary':True,
        'primary_print_document':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/ioflag_starter_r.htm'})
    print(json.dumps({'static_models':[{k:v for k,v in r.items() if k not in ['source','source_sha256','geometry_file']} for r in rows],
        'new_native':0}),flush=True)


if __name__=='__main__':main()
