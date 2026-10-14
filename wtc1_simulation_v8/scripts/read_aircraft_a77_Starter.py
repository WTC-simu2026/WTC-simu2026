"""Own cached-listing reader; exact pair labels and dynamic contact equivalence remain unqualified."""
from build_aircraft_a54_graph import read,dump,now,rel
from pathlib import Path
import re

def field(block,label):
    lines=[l for l in block.splitlines() if l.strip().startswith(label)]
    if len(lines)!=1:return None
    m=re.search(r'([+\-]?\d+(?:\.\d*)?(?:[EDed][+\-]?\d+)?)\s*$',lines[0])
    return float(m[1].replace('D','E').replace('d','e')) if m else None

def read_starter(d,case,execution,baseline,save=True):
    name=case['name'];listing=d/(name+'_0000.out')
    text=listing.read_text(encoding='utf8',errors='replace') if listing.exists() else ''
    log=(d/'starter.log').read_text(encoding='utf8',errors='replace')
    errors=re.findall(r'(\d+)\s+ERROR\(S\)',log);warnings=re.findall(r'(\d+)\s+WARNING\(S\)',log)
    mass=re.search(r'TOTAL MASS AND MASS CENTER.*?\n\s*([\d.E+\-]+)\s+([\d.E+\-]+)\s+([\d.E+\-]+)\s+([\d.E+\-]+)',text,re.S)
    added=re.search(r'TOTAL ADDED MASS\s*=\s*([\d.E+\-]+)',text)
    observed_mass=float(mass[1]) if mass else None
    observed_added=float(added[1]) if added else None
    observed_center=[float(v) for v in mass.groups()[1:]] if mass else None
    headings=list(re.finditer(r'^\s*INTERFACE NUMBER\s*:\s*(\d+)\s+([^\n]*)$',text,re.M))
    contacts={}
    for i,h in enumerate(headings):
        if not h[2].startswith('A75_DECLARED_TYPE7_'):continue
        block=text[h.end():headings[i+1].start() if i+1<len(headings) else len(text)]
        contacts[int(h[1])]={'native_title':h[2].strip(),'TYPE7_printed':'TYPE==7' in block,
            'Istf':field(block,'STIFFNESS FORMULATION.'),'Stfac':field(block,'STIFFNESS FACTOR.'),
            'Fric':field(block,'FRICTION FACTOR'),'Igap':field(block,'VARIABLE GAP FLAG'),
            'Gapmin_mm':field(block,'MINIMUM GAP '),'Irem_i2':field(block,'DE-ACTIVATION FLAG IF CONFLICT'),
            'Inacti':field(block,'DE-ACTIVATION OF INITIAL PENETRATIONS'),
            'Irem_gap':field(block,'NODES IN CASE'),
            'initial_penetration_factor':field(block,'MAXIMUM INITIAL PENETRATION FACTOR'),
            'possible_impact_numbers_printed':[int(v) for v in re.findall(r'POSSIBLE IMPACT NUMBER:\s*(\d+)',block)],
            'exact_filtered_pair_labels_not_available_from_this_listing_reader':True}
    impacts=re.findall(r'INTERFACE NUMBER\.[^\n]*?(\d+)\s*\n\s*INTERFACE TYPE\.[^\n]*?(\d+)\s*\n\s*POSSIBLE IMPACT NUMBER:\s*(\d+)',text)
    possible={int(ID):int(count) for ID,typ,count in impacts if int(typ)==7}
    for ID,r in contacts.items():r['possible_impact_numbers_printed']=[possible[ID]] if ID in possible else []
    expected_ids=set(case['contact_interface_IDs']);observed_ids=set(contacts)
    readback_pass=observed_ids==expected_ids
    for ID,r in contacts.items():
        gap=.5 if ID==2 else 5.
        readback_pass=readback_pass and all([r['TYPE7_printed'],r['Istf']==4,r['Stfac']==1,r['Fric']==0,
            r['Igap']==1000,r['Gapmin_mm']==gap,r['Irem_i2']==3,r['Inacti']==1000,
            r['Irem_gap']==(case.get('expected_self_Irem_gap',2) if ID==2 else 1)])
    checks={'normal_and_code0':execution['exit_code']==0 and not execution['timed_out'] and 'NORMAL TERMINATION' in log,
        'errors_zero':bool(errors) and int(errors[-1])==0,
        'warnings_strict_zero':bool(warnings) and int(warnings[-1])==0,
        'mass_same_declared_relative':observed_mass is not None and abs(observed_mass-baseline['mass_g'])<=1e-6*baseline['mass_g'],
        'ADMAS_exact':observed_added==baseline['prescribed_ADMAS_g'],
        'five_TYPE7_registered_and_declared_gaps_filter_flags_read':bool(readback_pass),
        'all_references_valid_no_Starter_error':bool(errors) and int(errors[-1])==0,
        'initial_filter_configuration_read':observed_ids==expected_ids and all(r['Inacti'] is not None for r in contacts.values()),
        'native_initial_contact_inventory_printed':observed_ids==expected_ids and all(r['possible_impact_numbers_printed'] for r in contacts.values()),
        'fresh_initial_restart_exists':(d/(name+'_0000_0001.rst')).exists()}
    result={'created_utc':now(),'pass':bool(all(checks.values())),'checks':checks,
        'failed_checks':[k for k,v in checks.items() if not v],'warnings':int(warnings[-1]) if warnings else None,
        'errors':int(errors[-1]) if errors else None,'mass_g':observed_mass,'center_mm':observed_center,
        'prescribed_ADMAS_g':observed_added,'native_contact_readback':contacts,'listing':rel(listing),
        'full_dynamic_pair_filtering_or_equivalence_qualified':False,'whole_credit_s':0}
    if save:dump(d/'Starter_gate_review.json',result)
    return result
