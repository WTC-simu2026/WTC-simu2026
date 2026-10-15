"""Read-only A80 topology audit of saved A79 initial-penetration pairs.

Only new files beside this script are written. The current A79 deck takes
precedence over A20 mesh metadata. Presence/connectivity is not constitutive,
constraint-rank, compression or contact-reentry validation, and never provides
automatic permission to exclude a pair from contact.
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
MESH = ROOT / 'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20/mesh.json'
DECK = ROOT / 'wtc1_simulation_v8/output/aircraft_a78_preparation/SELF_PAIR_PRINT/A79_SELF_PAIR_PRINT_0000.rad'
EVENTS = ROOT / 'wtc1_simulation_v8/output/aircraft_a79/pair_listing_events.json'
NATIVE_REVIEW = ROOT / 'wtc1_simulation_v8/output/aircraft_a79/pair_listing_review.json'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=True, indent=2, allow_nan=False)
        f.write('\n')


def blocks(path):
    result, key = {}, None
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('/'):
            key = line
            if key in result:
                raise ValueError('Repeated keyword: ' + key)
            result[key] = []
        elif key and line.strip() and not line.startswith('#'):
            result[key].append(line)
    return result


def decimal_quantum(token):
    mantissa, *exponent = token.lower().replace('d', 'e').split('e')
    places = len(mantissa.split('.')[1]) if '.' in mantissa else 0
    return 10. ** ((int(exponent[0]) if exponent else 0) - places)


def main():
    targets = [OUT / 'pair_cohesive_topology_review.json', OUT / 'pair_cohesive_topology_events.json',
        OUT / 'current_joint_presence_review.json']
    assert not any(p.exists() for p in targets), 'Keep every earlier result.'
    before = {rel(p): sha(p) for p in [MESH, DECK, EVENTS, NATIVE_REVIEW]}
    mesh, events, native_review, deck = load(MESH), load(EVENTS), load(NATIVE_REVIEW), blocks(DECK)
    native_input_binding = any(i['path'] == rel(DECK) and i['sha256'] == sha(DECK) for i in native_review['inputs'])
    source_nodes = {int(l[:10]): list(map(float, l[10:].split())) for l in deck['/NODE']}
    source_node_tokens = {int(l[:10]): l[10:].split() for l in deck['/NODE']}
    source_groups = {int(k.rsplit('/', 1)[1]): [int(v) for l in rows[1:] for v in l.split()]
        for k, rows in deck.items() if k.startswith('/GRNOD/NODE/')}
    source_shells = {}
    node_to_skin_parts = collections.defaultdict(set)
    for key, rows in deck.items():
        if key.startswith('/SHELL/'):
            part = int(key.rsplit('/', 1)[1])
            for line in rows:
                numbers = list(map(int, line.split()))
                source_shells[numbers[0]] = {'part': part, 'nodes': numbers[1:5]}
    source_bricks = {}
    for line in deck.get('/BRICK/117', []):
        v = list(map(int, line.split()))
        source_bricks[v[0]] = v[1:9]
    source_rbe2 = {}
    for key, rows in deck.items():
        if key.startswith('/RBE2/'):
            ID, line = int(key.rsplit('/', 1)[1]), rows[1]
            gid = int(line[30:40])
            source_rbe2[ID] = {'id': ID, 'host': int(line[:10]), 'DOF_field': line[10:20],
                'skew': int(line[20:30]), 'group': gid, 'flag': int(line[40:50]),
                'dependent_nodes': source_groups.get(gid, [])}
    facets = {f['original_element_id']: f for f in mesh['radome_facets']}
    part_metadata = {}
    for f in facets.values():
        for side, partkey, layer in [('lo', 'lower_part_id', 0), ('hi', 'upper_part_id', 1)]:
            part_metadata[f[partkey]] = {'facet': f['original_element_id'], 'side': side, 'layer_nodes': f['layers'][layer]}
    skin_scope_mismatches, ordered_to_parts = [], collections.defaultdict(list)
    for q in mesh['radome_skin_quads']:
        actual = source_shells.get(q['id'])
        exact = actual == {'part': q['part'], 'nodes': q['nodes']}
        if not exact:
            skin_scope_mismatches.append({'element': q['id'], 'A20': q, 'current': actual})
        if actual and actual['part'] in part_metadata:
            ordered_to_parts[tuple(actual['nodes'])].append({'part': actual['part'], 'element': q['id'],
                **part_metadata[actual['part']], 'A20_connectivity_current_exact': exact})
            for n in actual['nodes']:
                node_to_skin_parts[n].add(actual['part'])
    original_vertices = collections.defaultdict(set)
    seam_by_pair_side = collections.defaultdict(list)
    brick_metadata = {row[0]: row[1:] for row in mesh['cohesive_connectivity']}
    mesh_rbe2 = {r['id']: r for r in mesh['new_RBE2']}
    host_by_dep = collections.defaultdict(list)
    for host, dep, distance in mesh['cohesive_offset_map']:
        host_by_dep[dep].append({'host': host, 'A20_offset_distance_mm': distance})
    current_dep_rbe2 = collections.defaultdict(list)
    for r in source_rbe2.values():
        for dep in r['dependent_nodes']:
            current_dep_rbe2[dep].append(r)
    mesh_dep_rbe2 = collections.defaultdict(list)
    for r in mesh_rbe2.values():
        for dep in r['dependent_nodes']:
            mesh_dep_rbe2[dep].append(r)
    rbe2_mismatches = []
    for ID, reference in mesh_rbe2.items():
        current = source_rbe2.get(ID)
        required_DOF = '111000' if reference['role'] == 'cohesive_corner' else '111111'
        ok = current is not None and current['host'] == reference['host'] and sorted(current['dependent_nodes']) == sorted(reference['dependent_nodes'])
        ok = ok and ''.join(current['DOF_field'].split()) == required_DOF and current['skew'] == 0 and current['flag'] == 0
        if not ok:
            rbe2_mismatches.append({'A20': reference, 'current': current})
    seam_records = {}
    coordinate_mismatches = []
    required_nodes = set()
    for seam in mesh['cohesive_seams']:
        ID = seam['element_id']; fids = seam['facet_ids']; side = 'lo' if seam['skin_offset_bounds_mm'][0] < 0 else 'hi'
        for f in fids:
            original_vertices[f].update(seam['original_edge'])
        seam_by_pair_side[(tuple(sorted(fids)), side)].append(ID)
        conn = brick_metadata.get(ID, [])
        actual = source_bricks.get(ID)
        half_records, all_rbe_ids = [], set()
        for index, fid in enumerate(fids):
            layer = facets[fid]['layers'][0 if side == 'lo' else 1]
            expected_hosts, mapping_errors = [], []
            for dep in conn[index * 4:index * 4 + 4]:
                required_nodes.add(dep)
                hosts, current_rbes, expected_rbes = host_by_dep.get(dep, []), current_dep_rbe2.get(dep, []), mesh_dep_rbe2.get(dep, [])
                if len(hosts) != 1 or len(current_rbes) != 1 or len(expected_rbes) != 1:
                    mapping_errors.append({'dependent_node': dep, 'host_mapping_count': len(hosts), 'current_RBE2_count': len(current_rbes), 'A20_RBE2_count': len(expected_rbes)})
                    continue
                host, r, mr = hosts[0]['host'], current_rbes[0], expected_rbes[0]
                required_nodes.add(host); expected_hosts.append(host); all_rbe_ids.add(r['id'])
                if host not in layer[:3] or r['host'] != host or mr['host'] != host or r['id'] != mr['id'] or mr['role'] != 'cohesive_corner' or ''.join(r['DOF_field'].split()) != '111000':
                    mapping_errors.append({'dependent_node': dep, 'host': host, 'current_RBE2': r['id'], 'A20_RBE2': mr['id'], 'reason': 'host_facet_side_or_RBE2_mismatch'})
            half_records.append({'facet': fid, 'side': side, 'cohesive_dependent_nodes': conn[index * 4:index * 4 + 4],
                'skin_corner_hosts': expected_hosts, 'mapping_errors': mapping_errors,
                'four_corner_dependencies_and_correct_facet_skin_hosts_present': len(expected_hosts) == 4 and not mapping_errors})
        checks = {'current_BRICK117_exists_with_exact_eight_nodes': actual == conn and len(conn) == 8,
            'both_halves_have_exact_current_RBE2_host_paths': len(half_records) == 2 and all(h['four_corner_dependencies_and_correct_facet_skin_hosts_present'] for h in half_records),
            'current_material117_property43_part117_exist': all(k in deck for k in ['/MAT/LAW117/117', '/PROP/TYPE43/117', '/PART/117']),
            'current_part117_references_material_and_property117': bool(deck.get('/PART/117')) and list(map(int, deck['/PART/117'][1].split()))[:2] == [117, 117]}
        seam_records[ID] = {'element': ID, 'facets': fids, 'original_edge': seam['original_edge'], 'side': side,
            'checks': checks, 'presence_connectivity_pass_only': all(checks.values()), 'halves': half_records,
            'RBE2_ids': sorted(all_rbe_ids), 'no_force_strength_compression_or_failure_qualification': True}
    for n in sorted(required_nodes):
        if n not in source_nodes or n < 1 or n > len(mesh['nodes_mm']):
            coordinate_mismatches.append({'node': n, 'reason': 'absent_from_current_or_A20'})
            continue
        current, metadata = source_nodes[n], mesh['nodes_mm'][n - 1]
        delta = [abs(a - b) for a, b in zip(current, metadata)]
        bounds = [.51 * decimal_quantum(t) + 16 * math.ulp(max(abs(a), abs(b), 1.)) for a, b, t in zip(current, metadata, source_node_tokens[n])]
        if any(d > q for d, q in zip(delta, bounds)):
            coordinate_mismatches.append({'node': n, 'A20_current_absolute_delta_mm': delta, 'current_decimal_resolution_bounds_mm': bounds})
    seam_vertex_reconstruction = {str(fid): sorted(nodes) for fid, nodes in original_vertices.items()}
    vertex_graph = collections.defaultdict(lambda: collections.defaultdict(list))
    for ID, s in seam_records.items():
        if not s['presence_connectivity_pass_only']:
            continue
        a, b = s['facets']
        for vertex in s['original_edge']:
            vertex_graph[(vertex, s['side'])][a].append((b, ID))
            vertex_graph[(vertex, s['side'])][b].append((a, ID))

    def path_at_vertex(a, b, vertex, side):
        graph = vertex_graph[(vertex, side)]
        queue = collections.deque([(a, [], [a])]); seen = {a}
        while queue:
            node, seam_path, facet_path = queue.popleft()
            if node == b:
                return {'shared_original_vertex': vertex, 'facets': facet_path, 'seam_elements': seam_path,
                    'all_current_BRICK_and_RBE2_presence_paths_verified_only': True}
            for other, ID in sorted(graph[node]):
                if other not in seen:
                    seen.add(other); queue.append((other, seam_path + [ID], facet_path + [other]))
        return None

    results = []
    for event in events['error612_events'] + events['warning1164_details']:
        ns, *nodes = event['tuple']
        sec_parts = sorted(node_to_skin_parts.get(ns, set()))
        segment = ordered_to_parts.get(tuple(nodes), [])
        result = {'kind': event['kind'], 'tuple_line': event['tuple_line'], 'tuple': event['tuple'],
            'secondary_current_parts': sec_parts, 'main_current_ordered_matches': segment,
            'A79_native_pair_mapping_pass': event['mapping_pass'], 'classification': 'unexplained',
            'topology_presence_certificate_only': False, 'eligible_for_contact_exclusion': False,
            'no_constitutive_force_compression_or_dynamic_qualification': True}
        if len(sec_parts) != 1 or len(segment) != 1 or sec_parts[0] not in part_metadata:
            result['classification'] = 'ambiguous_current_part_mapping'
            results.append(result); continue
        sec, mainpart = part_metadata[sec_parts[0]], segment[0]
        a, b = sec['facet'], mainpart['facet']; sa, sb = sec['side'], mainpart['side']
        common = sorted(original_vertices[a] & original_vertices[b])
        result.update({'secondary_original_facet': a, 'main_original_facet': b, 'secondary_skin': sa, 'main_skin': sb,
            'common_original_vertices': common, 'both_original_triangles_have_three_reconstructed_vertices': len(original_vertices[a]) == len(original_vertices[b]) == 3})
        baseline = event['mapping_pass'] and mainpart['A20_connectivity_current_exact'] and result['both_original_triangles_have_three_reconstructed_vertices']
        if sa != sb:
            result['classification'] = 'opposite_skins'
        elif a == b:
            result['classification'] = 'same_original_facet'
        elif len(common) == 2:
            IDs = seam_by_pair_side.get((tuple(sorted((a, b))), sa), [])
            result['direct_cohesive_seam_candidates'] = IDs
            if len(IDs) == 1 and set(seam_records[IDs[0]]['original_edge']) == set(common):
                result['classification'] = 'same_skin_direct_cohesive_edge'
                result['current_joint_presence'] = seam_records[IDs[0]]['presence_connectivity_pass_only']
                result['joint_RBE2_ids'] = seam_records[IDs[0]]['RBE2_ids']
                result['topology_presence_certificate_only'] = baseline and result['current_joint_presence']
            else:
                result['classification'] = 'shared_edge_but_missing_or_ambiguous_same_skin_joint'
        elif len(common) == 1:
            result['classification'] = 'same_skin_vertex_only'
            path = path_at_vertex(a, b, common[0], sa)
            result['current_cohesive_path_around_vertex'] = path
            result['topology_presence_certificate_only'] = baseline and path is not None
        results.append(result)
    class_counts = collections.Counter(r['classification'] for r in results)
    kind_counts = collections.defaultdict(collections.Counter)
    side_counts = collections.defaultdict(collections.Counter)
    path_lengths = collections.Counter()
    direct_joints = set()
    for r in results:
        kind_counts[r['kind']][r['classification']] += 1
        side_counts[r.get('secondary_skin', 'unknown')][r['classification']] += 1
        if r['classification'] == 'same_skin_direct_cohesive_edge':
            direct_joints.update(r.get('direct_cohesive_seam_candidates', []))
        elif r['classification'] == 'same_skin_vertex_only' and r.get('current_cohesive_path_around_vertex'):
            path_lengths[len(r['current_cohesive_path_around_vertex']['seam_elements'])] += 1
    checks = {'A79_native_review_pass_and_current_deck_hash_bound': native_review['pass_observation'] and native_input_binding,
        'exact1296_A20_skin_quad_connectivities_remain_current': len(mesh['radome_skin_quads']) == 1296 and not skin_scope_mismatches,
        'all216_original_triangles_reconstructed_from_cohesive_edges': len(facets) == len(original_vertices) == 216 and all(len(v) == 3 for v in original_vertices.values()),
        'all624_current_cohesive_bricks_and_corner_RBE2_paths_present': len(seam_records) == 624 and all(s['presence_connectivity_pass_only'] for s in seam_records.values()),
        'all1320_A20_RBE2_hosts_groups_DOF_present_current_exact': len(mesh_rbe2) == len(source_rbe2) == 1320 and not rbe2_mismatches,
        'required_joint_and_host_coordinates_preserved_at_input_resolution': not coordinate_mismatches,
        'all4430_native_pairs_classified_by_certified_current_topology': len(results) == 4430 and all(r['topology_presence_certificate_only'] for r in results),
        'all916_errors_are_direct_same_skin_cohesive_edge_neighbors': sum(r['kind'] == 'ERROR612' and r['classification'] == 'same_skin_direct_cohesive_edge' for r in results) == 916,
        'no_older_input_modified': all(sha(ROOT / p) == h for p, h in before.items())}
    domain = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checks': checks,
        'current_deck_authoritative_over_A20_metadata': True, 'original_triangle_vertices_reconstructed': seam_vertex_reconstruction,
        'current_cohesive_seams': list(seam_records.values()), 'RBE2_mismatches': rbe2_mismatches,
        'skin_connectivity_mismatches': skin_scope_mismatches, 'required_coordinate_mismatches': coordinate_mismatches,
        'required_joint_or_host_nodes_checked': len(required_nodes),
        'no_mechanical_compression_strength_constraint_rank_or_contact_reentry_validation': True}
    summary = {'created_utc': domain['created_utc'], 'iteration': 'AIRCRAFT-A80_PREPARATION', 'pass_topology_presence_only': all(checks.values()),
        'checks': checks, 'pairs': len(results), 'classification_counts': dict(class_counts),
        'counts_by_native_event_kind': {k: dict(v) for k, v in kind_counts.items()}, 'counts_by_skin': {k: dict(v) for k, v in side_counts.items()},
        'vertex_only_shortest_verified_cohesive_path_length_counts': dict(path_lengths), 'unique_direct_cohesive_joints_in_observed_pairs': len(direct_joints),
        'uncertified_pairs': [{'tuple_line': r['tuple_line'], 'classification': r['classification']} for r in results if not r['topology_presence_certificate_only']],
        'physical_Starter_pass': False, 'contact_exclusion_qualified': False, 'contact_exclusion_authorized': False,
        'cohesive_constitutive_compression_strength_or_failure_qualified': False, 'contact_reentry_after_separation_qualified': False,
        'why_no_automatic_exclusion': 'Direct cohesive adjacency or a path around an original vertex establishes only present topology. Cohesive neighbors can open or compress; their later fragment collision must remain represented and tested.',
        'new_native': 0, 'source_engine_model_or_sealed_A79_mutation': False,
        'inputs': [{'path': p, 'sha256': h} for p, h in before.items()],
        'reader': {'path': rel(Path(__file__)), 'sha256': sha(Path(__file__))},
        'events_file': rel(targets[1]), 'presence_file': rel(targets[2])}
    save(targets[1], {'created_utc': domain['created_utc'], 'pairs': results, 'no_automatic_contact_exclusion': True})
    save(targets[2], domain)
    save(targets[0], summary)
    print(json.dumps(summary, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
