"""Read saved A79 detailed Starter listing; no solver or model mutation.

Printed labels, coordinates and ordered connectivity are checked directly in the
saved Windows listing. Related Fortran explains the output order, without any
claim that the pinned source built that binary. All output writes are exclusive.
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'wtc1_simulation_v8/output/aircraft_a79'
LISTING = OUT / 'SELF_PAIR_PRINT/A79_SELF_PAIR_PRINT_0000.out'
INPUT = ROOT / 'wtc1_simulation_v8/output/aircraft_a78_preparation/SELF_PAIR_PRINT/A79_SELF_PAIR_PRINT_0000.rad'
TOPOLOGY = ROOT / 'wtc1_simulation_v8/output/aircraft_a78_preparation/WHOLE_ORIGINAL_NEIGHBOR_CHECK_surface_nodes.json'
A77_EVENTS = ROOT / 'wtc1_simulation_v8/output/aircraft_a77/WHOLE_ORIGINAL_NEIGHBOR_CHECK/initialization_message_audit.json'
FLOAT = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?'
FIVE = re.compile(r'^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$')
COORD = re.compile(r'^\s*(\d+)\s+(' + FLOAT + r')\s+(' + FLOAT + r')\s+(' + FLOAT + r')\s*$')
PENE = re.compile(r'INITIAL PENETRATION\s*=\s*(' + FLOAT + r').*SECONDARY NODE\s+(\d+)')
SURFACE = re.compile(r'^\s*SURFACE:\s*(\d+),.*?,\s*(\d+)\s+SEGMENTS:')
GROUP = re.compile(r'^\s*NODE GROUP:\s*(\d+),.*?,\s*(\d+)\s+NODES:')


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def relative(p):
    return p.relative_to(ROOT).as_posix()


def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def save_new(p, value):
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=True, indent=2, allow_nan=False)
        f.write('\n')


def number(s):
    return float(s.replace('D', 'E').replace('d', 'e'))


def quantum(s):
    """Least printed decimal place; this is textual precision, not physics."""
    v = s.lower().replace('d', 'e').split('e')
    exponent = int(v[1]) if len(v) > 1 else 0
    fraction = len(v[0].split('.')[1]) if '.' in v[0] else 0
    return 10.0 ** (exponent - fraction)


def sections(path):
    d, key = {}, None
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('/'):
            key = line
            if key in d:
                raise ValueError('Duplicate section: ' + key)
            d[key] = []
        elif key and line.strip() and not line.startswith('#'):
            d[key].append(line)
    return d


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(a, s):
    return tuple(x * s for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    return math.sqrt(dot(a, a))


def dist(a, b):
    return norm(sub(a, b))


def segment_closest(p, a, b):
    ab = sub(b, a)
    den = dot(ab, ab)
    t = max(0., min(1., dot(sub(p, a), ab) / den)) if den else 0.
    return add(a, scale(ab, t))


def triangle_distance(p, a, b, c):
    """Plane projection inside triangle, otherwise nearest bounded edge."""
    ab, ac = sub(b, a), sub(c, a)
    n = cross(ab, ac)
    n2 = dot(n, n)
    candidates = [segment_closest(p, a, b), segment_closest(p, b, c), segment_closest(p, c, a)]
    if n2 > 0:
        q = sub(p, scale(n, dot(sub(p, a), n) / n2))
        aq = sub(q, a)
        d00, d01, d11 = dot(ab, ab), dot(ab, ac), dot(ac, ac)
        d20, d21 = dot(aq, ab), dot(aq, ac)
        den = d00 * d11 - d01 * d01
        if den > 0:
            u, v = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
            if u >= 0 and v >= 0 and u + v <= 1:
                candidates.append(q)
    return min(dist(p, q) for q in candidates)


def ordered_match(a, b):
    """Never match a quadrilateral merely by its unordered set of nodes."""
    a, b = tuple(a), tuple(b)
    if a == b:
        return 'exact'
    if len(a) != len(b):
        return None
    for k in range(1, len(b)):
        if a == b[k:] + b[:k]:
            return 'cyclic_rotation'
    r = tuple(reversed(b))
    for k in range(len(b)):
        if a == r[k:] + r[:k]:
            return 'reversed_orientation'
    return None


def parse_native(lines):
    coords, shells, surfaces, groups = {}, {}, {}, {}
    duplicates, malformed = [], []
    mode, current, remaining = None, None, 0
    for index, line in enumerate(lines, 1):
        s = line.strip()
        if s == 'NODAL POINT COORDINATES':
            mode = 'coordinate'
            continue
        if s == 'SHELL ELEMENTS':
            mode = 'shell4'
            continue
        if s == 'TRIANGULAR SHELL ELEMENTS':
            mode = 'shell3'
            continue
        m = SURFACE.match(line)
        if m:
            current, remaining = map(int, m.groups())
            if current in surfaces:
                duplicates.append({'kind': 'surface_header', 'label': current, 'line': index})
            surfaces[current] = {'header_line': index, 'declared_count': remaining, 'rows': []}
            mode = 'surface'
            continue
        m = GROUP.match(line)
        if m:
            current, remaining = map(int, m.groups())
            if current in groups:
                duplicates.append({'kind': 'group_header', 'label': current, 'line': index})
            groups[current] = {'header_line': index, 'declared_count': remaining, 'rows': []}
            mode = 'group'
            continue
        if not s or set(s) <= {'-', '~'}:
            continue
        if mode == 'coordinate':
            if s.startswith('NODE') and 'X-ORD' in s:
                continue
            m = COORD.match(line)
            if m:
                n = int(m[1])
                if n in coords:
                    duplicates.append({'kind': 'coordinate', 'label': n, 'line': index})
                coords[n] = {'line': index, 'xyz': [number(t) for t in m.groups()[1:]], 'tokens': list(m.groups()[1:])}
                continue
            mode = None
        elif mode in ('shell4', 'shell3'):
            if s.startswith('ELEMENT') and 'NODE1' in s:
                continue
            f = s.split()
            size = 4 if mode == 'shell4' else 3
            if len(f) == size + 6 and all(re.fullmatch(r'\d+', x) for x in f[:size + 4]):
                try:
                    number(f[-2]); number(f[-1])
                except ValueError:
                    malformed.append({'kind': mode, 'line': index})
                    mode = None
                    continue
                n = int(f[0])
                if n in shells:
                    duplicates.append({'kind': 'shell', 'label': n, 'line': index})
                shells[n] = {'line': index, 'element_label': n, 'internal_index': int(f[1]), 'material': int(f[2]),
                    'property': int(f[3]), 'nodes': list(map(int, f[4:4 + size])), 'family': 'SHELL' if size == 4 else 'SH3N'}
                continue
            mode = None
        elif mode == 'surface':
            if s.startswith('NODE 1'):
                continue
            f = s.split()
            if remaining and len(f) == 6 and all(re.fullmatch(r'\d+', x) for x in f):
                v = list(map(int, f))
                surfaces[current]['rows'].append({'line': index, 'nodes': v[:4], 'ELTYP': v[4], 'element_label': v[5]})
                remaining -= 1
                if not remaining:
                    mode = None
                continue
            if remaining:
                malformed.append({'kind': 'surface_short_or_unexpected', 'label': current, 'line': index, 'remaining': remaining})
            mode = None
        elif mode == 'group':
            f = s.split()
            if remaining and all(re.fullmatch(r'\d+', x) for x in f) and len(f) <= remaining:
                groups[current]['rows'].append({'line': index, 'nodes': list(map(int, f))})
                remaining -= len(f)
                if not remaining:
                    mode = None
                continue
            if remaining:
                malformed.append({'kind': 'group_short_or_unexpected', 'label': current, 'line': index, 'remaining': remaining})
            mode = None
    return coords, shells, surfaces, groups, duplicates, malformed


def read_events(lines):
    events, warnings, missing = [], [], []
    for i, line in enumerate(lines):
        if re.fullmatch(r'\s*ERROR ID\s*:\s*612\s*', line):
            # Search backward only to the immediately preceding penetration line.
            p = next((j for j in range(i - 1, max(-1, i - 7), -1) if PENE.search(lines[j])), None)
            t = p - 1 if p is not None else None
            m = FIVE.match(lines[t]) if t is not None else None
            body = '\n'.join(lines[i:i + 8])
            interface = re.search(r'-- INTERFACE ID:\s*(\d+)', body)
            node = re.search(r'SECONDARY NODE\s+(\d+)\s+IS ON THE MAIN SURFACE', body)
            inacti = re.search(r'INACTI\s*=\s*(\d+)', body)
            if p is None or m is None or interface is None or node is None or inacti is None:
                missing.append({'kind': 'error_association_incomplete', 'error_line': i + 1})
                continue
            pen = PENE.search(lines[p])
            events.append({'kind': 'ERROR612', 'error_line': i + 1, 'tuple_line': t + 1, 'penetration_line': p + 1,
                'interface': int(interface[1]), 'tuple': list(map(int, m.groups())),
                'penetration_mm_printed': number(pen[1]), 'penetration_secondary_label': int(pen[2]),
                'message_secondary_label': int(node[1]), 'native_inacti': int(inacti[1])})
        if re.fullmatch(r'\s*WARNING ID\s*:\s*1164\s*', line):
            block = lines[i:i + 9]
            body = '\n'.join(block)
            interface = re.search(r'-- INTERFACE ID:\s*(\d+)', body)
            declared = re.search(r'CONCERNING\s+(\d+) NODE\(S\)', body)
            h = next((j for j in range(i + 1, min(len(lines), i + 10)) if 'SECONDARY_NODE' in lines[j] and 'INITIAL PENETRATION' in lines[j]), None)
            if interface is None or declared is None or h is None:
                missing.append({'kind': 'warning1164_header_incomplete', 'warning_line': i + 1})
                continue
            count = int(declared[1])
            for j in range(h + 1, h + 1 + count):
                f = lines[j].split()
                if len(f) != 6 or not all(re.fullmatch(r'\d+', x) for x in f[:5]):
                    missing.append({'kind': 'warning1164_row_incomplete', 'line': j + 1})
                    continue
                warnings.append({'kind': 'WARNING1164_detail', 'warning_line': i + 1, 'tuple_line': j + 1,
                    'interface': int(interface[1]), 'tuple': list(map(int, f[:5])), 'penetration_mm_printed': number(f[-1])})
    return events, warnings, missing


def main():
    targets = [OUT / 'pair_listing_review.json', OUT / 'pair_listing_events.json', OUT / 'pair_listing_native_domain_review.json']
    assert all(not p.exists() for p in targets), 'Never replace an existing analysis.'
    lines = LISTING.read_text(encoding='utf-8', errors='replace').splitlines()
    native_coords, native_shells, native_surfaces, native_groups, duplicates, malformed = parse_native(lines)
    errors, warning_pairs, association_missing = read_events(lines)
    source = sections(INPUT)
    source_coords = {int(l[:10]): list(map(number, l[10:].split())) for l in source['/NODE']}
    group = {int(x) for l in source['/GRNOD/NODE/1004'][1:] for x in l.split()}
    main_parts = {int(x) for l in source['/SURF/PART/1005'][1:] for x in l.split()}
    topology = load(TOPOLOGY)
    source_facets = topology['source_main_facets']
    facet_by_element = {f['element']: f for f in source_facets}
    component = {int(n): int(c) for c, nodes in topology['source_surface_components'].items() for n in nodes}
    incidence = collections.defaultdict(list)
    facets_by_order = collections.defaultdict(list)
    for f in source_facets:
        facets_by_order[tuple(f['nodes'])].append(f)
        for n in f['nodes']:
            incidence[n].append(f)
    ties = []
    part_to_ties = collections.defaultdict(list)
    for key, rows in source.items():
        if key.startswith('/INTER/TYPE2/'):
            tie = int(key.rsplit('/', 1)[1]); g, s = int(rows[1][:10]), int(rows[1][10:20])
            parts = {int(v) for line in source.get(f'/SURF/PART/{s}', [])[1:] for v in line.split()}
            sec = {int(v) for line in source.get(f'/GRNOD/NODE/{g}', [])[1:] for v in line.split()}
            record = {'TYPE2': tie, 'source_secondary_group': g, 'source_main_surface': s, 'source_main_parts': sorted(parts),
                'source_secondary_nodes': sorted(sec), 'native_surface_definition_printed': s in native_surfaces,
                'native_secondary_group_definition_printed': g in native_groups,
                'presence_only_NOT_binding_rank_force_or_dynamic_qualification': True}
            ties.append(record)
            for part in parts:
                part_to_ties[part].append(tie)
    # Use printed decimal resolution plus floating arithmetic slack, never a
    # physical tolerance chosen to make a damaged model pass.
    coord_bad, all_coord_deltas, node_bounds = [], [], {}
    for n, row in native_coords.items():
        if n not in source_coords:
            coord_bad.append({'node': n, 'reason': 'native_label_not_in_input'})
            continue
        bounds, delta = [], []
        for a, b, t in zip(row['xyz'], source_coords[n], row['tokens']):
            bounds.append(.51 * quantum(t) + 16 * math.ulp(max(abs(a), abs(b), 1.)))
            delta.append(abs(a - b))
        node_bounds[n] = norm(bounds)
        all_coord_deltas.extend(delta)
        if any(d > q for d, q in zip(delta, bounds)):
            coord_bad.append({'node': n, 'native_line': row['line'], 'absolute_delta_mm': delta, 'text_resolution_bounds_mm': bounds})
    native_surface = native_surfaces.get(1005, {})
    surface_rows = native_surface.get('rows', [])
    native_surface_map = collections.defaultdict(list)
    native_surface_source_mismatches = []
    for row in surface_rows:
        native_surface_map[tuple(row['nodes'])].append(row)
        src = facet_by_element.get(row['element_label'])
        if not src or ordered_match(row['nodes'], src['nodes']) != 'exact':
            native_surface_source_mismatches.append(row)
    native_shell_source_mismatches = []
    for f in source_facets:
        n = native_shells.get(f['element'])
        if not n or n['nodes'] != f['nodes']:
            native_shell_source_mismatches.append({'source_facet': f, 'native_shell': n})
    native_group_nodes = [n for row in native_groups.get(1004, {}).get('rows', []) for n in row['nodes']]

    def annotate(e):
        ns, *main = e['tuple']
        exact_f = facets_by_order.get(tuple(main), [])
        candidates = [(f, 'exact') for f in exact_f]
        if not candidates:
            # Usually unused; retain an explicit order classification.
            candidates = [(f, m) for f in source_facets if (m := ordered_match(main, f['nodes']))]
        native_segment = native_surface_map.get(tuple(main), [])
        base_checks = {'all_five_labels_have_native_coordinates': all(n in native_coords for n in e['tuple']),
            'secondary_in_source_group1004': ns in group, 'secondary_in_native_group1004': ns in native_group_nodes,
            'one_source_facet_with_preserved_order': len(candidates) == 1,
            'one_exact_native_self_surface_segment': len(native_segment) == 1,
            'source_and_native_segment_element_agree': len(candidates) == len(native_segment) == 1 and candidates[0][0]['element'] == native_segment[0]['element_label']}
        if e['kind'] == 'ERROR612':
            base_checks['tuple_PENE_message_secondary_agree'] = ns == e['penetration_secondary_label'] == e['message_secondary_label']
            base_checks['native_interface2_and_inacti0'] = e['interface'] == 2 and e['native_inacti'] == 0
        else:
            base_checks['native_interface2'] = e['interface'] == 2
        e['checks'] = base_checks
        e['mapping_pass'] = all(base_checks.values())
        e['source_facet_matches'] = [{'part': f['part'], 'element': f['element'], 'family': f['family'], 'order_match': m} for f, m in candidates]
        e['native_surface_segment_matches'] = native_segment
        e['native_coordinate_lines'] = {str(n): native_coords[n]['line'] for n in e['tuple'] if n in native_coords}
        e['native_shell_matches'] = [native_shells[f['element']] for f, _ in candidates if f['element'] in native_shells]
        e['secondary_source_own_parts'] = sorted({f['part'] for f in incidence.get(ns, [])})
        e['secondary_main_TYPE2_incidence_presence_only'] = sorted({t for part in e['secondary_source_own_parts'] for t in part_to_ties[part]})
        e['segment_main_TYPE2_incidence_presence_only'] = sorted({t for f, _ in candidates for t in part_to_ties[f['part']]})
        e['secondary_surface_component'] = component.get(ns)
        e['segment_surface_components'] = sorted({component[n] for n in main if n in component})
        e['secondary_and_segment_shared_ID_component'] = component.get(ns) in e['segment_surface_components']
        if not base_checks['all_five_labels_have_native_coordinates']:
            return
        p = native_coords[ns]['xyz']; xyz = [native_coords[n]['xyz'] for n in main]
        n0, n1 = cross(sub(xyz[1], xyz[0]), sub(xyz[2], xyz[0])), cross(sub(xyz[2], xyz[0]), sub(xyz[3], xyz[0]))
        area0, area1 = norm(n0) / 2, norm(n1) / 2
        edge_scale = max(dist(a, b) for a in xyz for b in xyz)
        resolution = max(node_bounds.get(n, 0.) for n in e['tuple'])
        area_roundoff = max(32 * math.ulp(max(edge_scale * edge_scale, 1.)), 4 * edge_scale * resolution)
        planarity = abs(dot(sub(xyz[3], xyz[0]), n0)) / norm(n0) if norm(n0) else None
        eq = [n for n, q in zip(main, xyz) if p == q and n != ns]
        near = [n for n, q in zip(main, xyz) if dist(p, q) <= node_bounds[ns] + node_bounds[n] and n != ns]
        e['geometry_from_native_printed_coordinates'] = {'unique_segment_node_labels': len(set(main)),
            'triangle_012_area_mm2': area0, 'triangle_023_area_mm2': area1, 'triangulated_area_mm2': area0 + area1,
            'area_roundoff_bound_mm2': area_roundoff, 'both_triangles_resolved_nondegenerate': area0 > area_roundoff and area1 > area_roundoff,
            'triangle_normals_dot': dot(n0, n1), 'planarity_departure_mm': planarity,
            'max_coordinate_text_resolution_bound_mm': resolution,
            'nearest_vertex_distance_mm': min(dist(p, q) for q in xyz),
            'exact_coordinate_coincident_distinct_label_vertices': eq,
            'within_combined_text_resolution_distinct_label_vertices': near,
            'point_to_triangulated_quad_distance_mm': min(triangle_distance(p, xyz[0], xyz[1], xyz[2]), triangle_distance(p, xyz[0], xyz[2], xyz[3])),
            'distance_construction': 'minimum over ordered triangles012 and023; not a reconstruction of the native bilinear projection algorithm',
            'no_native_coordinate_buffer_or_force_measurement_inferred': True}

    for e in errors + warning_pairs:
        annotate(e)
    counts = collections.Counter()
    for e in errors + warning_pairs:
        prefix = 'ERROR612' if e['kind'] == 'ERROR612' else 'WARNING1164'
        g = e.get('geometry_from_native_printed_coordinates', {})
        counts[prefix + '_mapping_pass'] += e['mapping_pass']
        counts[prefix + '_nondegenerate_quad'] += g.get('both_triangles_resolved_nondegenerate', False)
        counts[prefix + '_exact_distinct_label_vertex_coincidence'] += bool(g.get('exact_coordinate_coincident_distinct_label_vertices'))
        counts[prefix + '_within_text_resolution_distinct_vertex_coincidence'] += bool(g.get('within_combined_text_resolution_distinct_label_vertices'))
        counts[prefix + '_shared_surface_ID_component'] += e['secondary_and_segment_shared_ID_component']
    # Full output inventories and counts remain physical failures.
    warning_ids = [int(m[1]) for line in lines if (m := re.fullmatch(r'\s*WARNING ID\s*:\s*(\d+)\s*', line))]
    error_ids = [int(m[1]) for line in lines if (m := re.fullmatch(r'\s*ERROR ID\s*:\s*(\d+)\s*', line))]
    summary_error = [int(m[1]) for line in lines if (m := re.fullmatch(r'\s*(\d+) ERROR\(S\)\s*', line))]
    summary_warning = [int(m[1]) for line in lines if (m := re.fullmatch(r'\s*(\d+) WARNING\(S\)\s*', line))]
    warning343 = [i for i, l in enumerate(lines) if re.fullmatch(r'\s*WARNING ID\s*:\s*343\s*', l)]
    previous_errors = [e['printed_node'] for e in load(A77_EVENTS)['events'] if e['kind'] == 'ERROR']
    same_error_sequence = [e['tuple'][0] for e in errors] == previous_errors
    p343 = []
    for i in warning343:
        body = '\n'.join(lines[i:i + 10]); m = re.search(r'THERE ARE\s+(\d+) INITIAL PENETRATIONS', body); n = re.search(r'CONCERNING\s+(\d+) NODES', body)
        if m and n:
            p343.append({'warning_line': i + 1, 'penetrations': int(m[1]), 'nodes': int(n[1])})
    all_pairs = errors + warning_pairs
    all_tuple_counter = collections.Counter(tuple(e['tuple']) for e in all_pairs)
    native_domain_checks = {'native_coordinate_count_matches_source': len(native_coords) == len(source_coords) == 48171,
        'all_native_coordinates_compatible_with_input_at_printed_resolution': not coord_bad and set(native_coords) == set(source_coords),
        'native_main1296_segments_equal_A78_ordered_facets': len(surface_rows) == len(source_facets) == 1296 and not native_surface_source_mismatches,
        'native_shells_match_all_A78_main_elements_in_order': not native_shell_source_mismatches,
        'native_secondary_group1004_exact': len(native_group_nodes) == len(set(native_group_nodes)) == 3024 and set(native_group_nodes) == group,
        'all_main_parts_are_declared': {f['part'] for f in source_facets} == main_parts,
        'no_duplicate_native_coordinate_element_group_or_surface_headers': not duplicates,
        'no_malformed_native_table_rows': not malformed}
    observation_checks = {**native_domain_checks, 'all916_error612_fully_associated': len(errors) == len(error_ids) == 916 and set(error_ids) == {612} and not association_missing,
        'all3514_warning1164_rows_parsed': len(warning_pairs) == 3514,
        'all4430_pairs_resolve_native_coordinates_ordered_surface_and_source': len(all_pairs) == 4430 and all(e['mapping_pass'] for e in all_pairs),
        'warning343_count_closes_error_plus_detail_rows': len(p343) == 1 and p343[0]['penetrations'] == len(all_pairs),
        'warning343_unique_secondary_count_closes': len(p343) == 1 and p343[0]['nodes'] == len({e['tuple'][0] for e in all_pairs}),
        'error_secondary_sequence_identical_to_saved_A77': same_error_sequence,
        'physical_failure_counts_preserved': summary_error == [916] and summary_warning == [2] and collections.Counter(warning_ids) == {1164: 1, 343: 1}}
    details = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'iteration': 'AIRCRAFT-A79',
        'listing': relative(LISTING), 'listing_sha256': sha(LISTING), 'one_based_lines': True,
        'pair_order': ['secondary_node', 'main_node1', 'main_node2', 'main_node3', 'main_node4'],
        'error612_events': errors, 'warning1164_details': warning_pairs, 'association_missing': association_missing,
        'geometry_from_printed_coordinates_NOT_native_buffer_access': True,
        'source_binary_identity_NOT_assumed': True, 'TYPE2_incidence_presence_only': True}
    domain = {'checks': native_domain_checks, 'native_nodes': len(native_coords), 'native_shell_elements': len(native_shells),
        'native_self_surface_header': {k: v for k, v in native_surface.items() if k != 'rows'},
        'native_secondary_group_header': {k: v for k, v in native_groups.get(1004, {}).items() if k != 'rows'},
        'coordinate_mismatches': coord_bad, 'max_absolute_native_input_coordinate_difference_mm': max(all_coord_deltas, default=None),
        'native_surface_source_mismatches': native_surface_source_mismatches, 'native_shell_source_mismatches': native_shell_source_mismatches,
        'duplicates': duplicates, 'malformed_tables': malformed, 'TYPE2_source_presence': ties,
        'TYPE2_stiffness_binding_rotations_failure_and_dynamic_contact_reentry_NOT_qualified': True}
    distributions = {}
    for kind, records in [('ERROR612', errors), ('WARNING1164', warning_pairs)]:
        geo = [e['geometry_from_native_printed_coordinates'] for e in records if 'geometry_from_native_printed_coordinates' in e]
        distributions[kind] = {'records': len(records), 'unique_secondary_labels': len({e['tuple'][0] for e in records}),
            'min_max_point_to_triangulated_quad_distance_mm': [min((g['point_to_triangulated_quad_distance_mm'] for g in geo), default=None), max((g['point_to_triangulated_quad_distance_mm'] for g in geo), default=None)],
            'min_max_triangulated_area_mm2': [min((g['triangulated_area_mm2'] for g in geo), default=None), max((g['triangulated_area_mm2'] for g in geo), default=None)],
            'max_planarity_departure_mm': max((g['planarity_departure_mm'] for g in geo if g['planarity_departure_mm'] is not None), default=None),
            'max_text_resolution_bound_mm': max((g['max_coordinate_text_resolution_bound_mm'] for g in geo), default=None)}
    review = {'created_utc': details['created_utc'], 'iteration': 'AIRCRAFT-A79', 'checks': observation_checks,
        'pass_observation': all(observation_checks.values()), 'physical_Starter_pass': False, 'physical_impact_pass': False,
        'new_Starter_in_this_reader': 0, 'new_Engine': 0, 'software_or_input_modified': False,
        'native_warning_ids': dict(collections.Counter(warning_ids)), 'native_error_ids': dict(collections.Counter(error_ids)),
        'native_error_count': summary_error, 'native_warning_count': summary_warning,
        'added_warning1164_is_detailed_output_for_existing_positive_penetrations': True,
        'warning1164_emitted_at_IPRI5_in_related_pinned_source_only_NOT_source_binary_identity': True,
        'error_events': len(errors), 'warning1164_detail_rows': len(warning_pairs), 'total_initial_penetrations': len(all_pairs),
        'error612_count': len(errors), 'pair_count_1164': len(warning_pairs),
        'counts': {'error612_count': len(errors), 'pair_count_1164': len(warning_pairs), 'total_initial_penetrations': len(all_pairs)},
        'all_error612_pair_labels_and_native_geometry_verified': len(errors) == 916 and all(e['mapping_pass'] for e in errors) and all(native_domain_checks.values()),
        'same_error_node_sequence_as_A77': same_error_sequence,
        'zero_area_error_facets': sum(e.get('geometry_from_native_printed_coordinates', {}).get('triangulated_area_mm2') == 0 for e in errors),
        'error_secondary_coincident_with_distinct_main_vertex': counts['ERROR612_exact_distinct_label_vertex_coincidence'],
        'deviation_from_expected_one_warning': {'expected': 1, 'observed': summary_warning, 'additional_warning': 1164,
            'cause': 'detailed initial-penetration output requested by IPRI5; native count remains two and physical gate remains failed'},
        'unique_all_secondary_labels': len({e['tuple'][0] for e in all_pairs}), 'warning343': p343,
        'unique_pair_tuples': len(all_tuple_counter), 'duplicate_pair_tuple_events': sum(c - 1 for c in all_tuple_counter.values()),
        'classification_counts': dict(counts), 'geometry_distributions': distributions,
        'unmapped_pair_events': [e['tuple_line'] for e in all_pairs if not e['mapping_pass']],
        'source_TYPE2_count_presence_only': len(ties),
        'source_TYPE2_with_native_group_and_surface_definition_printed': sum(t['native_surface_definition_printed'] and t['native_secondary_group_definition_printed'] for t in ties),
        'inferences_not_made': ['source_binary_identity', 'mechanical_disconnection', 'constraint_rank', 'zero_mass_or_zero_stiffness',
            'contact_force_or_work', 'contact_reentry_after_cohesive_separation', 'ten_second_impact_qualification'],
        'reader': {'path': relative(Path(__file__)), 'sha256': sha(Path(__file__))},
        'inputs': [{'path': relative(p), 'sha256': sha(p)} for p in [LISTING, INPUT, TOPOLOGY, A77_EVENTS]],
        'details_file': relative(targets[1]), 'native_domain_file': relative(targets[2]), 'whole_dynamic_credit_s': 0}
    save_new(targets[1], details)
    save_new(targets[2], domain)
    save_new(targets[0], review)
    print(json.dumps({k: review[k] for k in ['pass_observation', 'physical_Starter_pass', 'error_events', 'warning1164_detail_rows',
        'total_initial_penetrations', 'classification_counts', 'geometry_distributions', 'unmapped_pair_events']}, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
