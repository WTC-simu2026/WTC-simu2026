"""New current-model contact contract inventory, read-only; no native runs or deck substitution."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from prepare_aircraft_a66_current_area_r1 import sections
from pathlib import Path
import collections,json,hashlib

PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a74_preparation'


def main():
    assert not PREP.exists();PREP.mkdir()
    sources=[ROOT/'wtc1_simulation_v8/output/aircraft_a49/WHOLE_EQUIVALENT_RIGID_CHAINS_CHECK/A49_EQUIVALENT_RIGID_CHAINS_0000.rad',
        ROOT/'wtc1_simulation_v8/output/aircraft_a52/WHOLE_PAIRED_TYPE2_BINDING_TRACE_R1/A52_TYPE2_FACET_PAIRS_R1_0000.rad']
    expected=[read(ROOT/'wtc1_simulation_v8/data/aircraft_a52_predeclaration.json')['source_files']['input']['sha256'],
        next(r['sha256'] for r in read(ROOT/'wtc1_simulation_v8/output/aircraft_a52/artifact_manifest.json')['files'] if r['path']==rel(sources[1]))]
    models=[]
    sizes={'SHELL':4,'SH3N':3,'TRIA':3,'BRICK':8,'TETRA4':4,'TETRA10':10,'BEAM':2,'SPRING':2,'TRUSS':2}
    for path,expected_sha in zip(sources,expected):
        assert sha(path)==expected_sha
        d=sections(path);roles=collections.defaultdict(set);element_counts=collections.Counter()
        for key,values in d.items():
            family=key.split('/')[1]
            if family not in sizes:continue
            for line in values:
                fields=line.split();assert len(fields)>=1+sizes[family],key
                nodes=list(map(int,fields[1:1+sizes[family]]));element_counts[family]+=1
                for node in nodes:
                    if node>0:roles[node].add(family)
        rows=[]
        for key,values in d.items():
            if not key.startswith('/INTER/TYPE25/'):continue
            assert len(values)==8
            ints=[int(values[1][i:i+10]) for i in range(0,100,10)]
            first,second,istf,ithe,igap,irem,unused,idel,iedge,ipstif=ints
            group=int(values[2][:10]);th=[float(values[7][i:i+20]) for i in range(0,80,20)]
            assert first==0 and second>0 and group>0 and igap==5 and istf==4 and ithe==ipstif==0
            group_key=f'/GRNOD/NODE/{group}';surface_key=f'/SURF/PART/{second}'
            assert group_key in d and surface_key in d
            nodes=[int(v) for line in d[group_key][1:] for v in line.split()]
            parts=[int(v) for line in d[surface_key][1:] for v in line.split()]
            assert len(nodes)==len(set(nodes))
            classes=collections.Counter();gap_classes=collections.Counter();unclassified=[]
            nodal_rows=[]
            for node in nodes:
                families=roles[node];classes['+'.join(sorted(families)) or 'no_element']+=1
                secondary_gap=th[0]*th[1]/2 if families & {'SHELL','SH3N','TRIA','BEAM','TRUSS','SPRING'} else 0.
                if not families or not families<=set(sizes):unclassified.append(node)
                gap=secondary_gap+th[2]*th[3]/2
                gap_classes[str(gap)]+=1
                nodal_rows.append({'node':node,'families':sorted(families),'provisional_gap_if_main_shell_mm':gap})
            payload=json.dumps(nodal_rows,separators=(',',':'),sort_keys=True).encode('utf8')
            fname=PREP/(path.stem+'_contact_'+key.split('/')[-1]+'_node_roles.json')
            dump(fname,{'nodes':nodal_rows,'classification_is_static_not_native_gap_readback':True})
            rows.append({'interface_ID':int(key.split('/')[-1]),'title':values[0],'TYPE25_raw_cards':values,
                'surf_ID1':first,'surf_ID2_main_candidate':second,'secondary_group_ID':group,
                'secondary_group_title':d[group_key][0],'secondary_nodes':len(nodes),'secondary_labels_sha256':hashlib.sha256(payload).hexdigest(),
                'main_surface_title':d[surface_key][0],'main_part_IDs':parts,'main_parts':len(parts),
                'Istf':istf,'Ithe':ithe,'Igap':igap,'Irem_i2':irem,'Idel':idel,'Iedge':iedge,'Ipstif':ipstif,
                'Thickness_s_Scale_s_Thickness_m_Scale_m':th,'node_element_family_counts':dict(classes),
                'provisional_gap_if_main_shell_counts':dict(gap_classes),'unclassified_nodes':unclassified,
                'per_node_role_file':rel(fname),'native_gap_equivalence_NOT_qualified':True})
        assert len(rows)==5
        models.append({'input':rel(path),'sha256':sha(path),'element_counts':dict(element_counts),'contacts':rows})
    assert [r['TYPE25_raw_cards'] for r in models[0]['contacts']]==[r['TYPE25_raw_cards'] for r in models[1]['contacts']]
    assert [r['secondary_labels_sha256'] for r in models[0]['contacts']]==[r['secondary_labels_sha256'] for r in models[1]['contacts']]
    dump(PREP/'current_contact_inventory.json',{'created_utc':now(),'models':models,'original_paired_TYPE25_and_roles_equal':True,
        'new_native':0,'new_Starter':0,'new_compilation':False,'source_engine_modified':False,
        'documents':[{'url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm','review_date':'2026-10-14'},
            {'url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm','review_date':'2026-10-14'}],
        'contact_algorithm_equivalence_assumed':False,'all_old_failed_gates_preserved':True})
    print(json.dumps({'contacts':[{'ID':r['interface_ID'],'nodes':r['secondary_nodes'],'gap_classes':r['provisional_gap_if_main_shell_counts'],
        'roles':r['node_element_family_counts']} for r in models[0]['contacts']],'new_native':0}),flush=True)


if __name__=='__main__':main()
