"""Preserve the failed insertion gate; inspect native initial mass moments only."""
from run_aircraft_a20_whole import *

def main():
    whole_guard()
    o = D/'initial_diagnostic'
    assert not o.exists()
    o.mkdir()
    declaration = {'created_utc':now(), 'scope':'Initial native mass/coordinate output only; no impact progression authorized by this diagnostic.',
        'original_CG_gate_preserved':True, 'end_ms':1e-6, 'maximum_requested_travel_mm':.0002,
        'whole_engine_still_blocked':True, 'source_restart_sha256':streamsha(D/(N+'_0000_0001.rst')),
        'analysis':'Compare native initial node mass moments against cached intact A19; isolate the geometry/discretization contribution before any change.'}
    dump(o/'declaration.json',declaration)
    shutil.copy2(D/(N+'_0000_0001.rst'),o/(N+'_0000_0001.rst'))
    lines=[]
    for b in blocks((D/(N+'_0001.rad')).read_text().splitlines()):
        if b[0].startswith('/RUN/'):b[1]=ff(1e-6)
        lines+=b
    (o/(N+'_0001.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    assert execute(RUNTIME/'engine_win64.exe',['-i',N+'_0001.rad'],o,'engine.log',120,env())
    oldn=read(SOURCE/'generation.json')['name']
    files=sorted(p for p in o.glob(N+'A*') if re.fullmatch(re.escape(N)+r'A\d{3}',p.name))
    q=fast(files[0]);old=fast(SOURCE/(oldn+'A001'))
    assert q['time_ms']==old['time_ms']==0
    def moments(z):
        return {'mass_g':float(z['node_mass_g'].sum()),'CG_mm':(z['node_mass_g']@z['x']/z['node_mass_g'].sum()).tolist()}
    qm,om=moments(q),moments(old)
    ix={int(n):j for j,n in enumerate(old['nid'])}
    oldm=read(SOURCE/'mesh.json');newm=read(D/'mesh.json')
    oldrad=set(oldm['radome_node_ids']);newrad={n for f in newm['radome_facets'] for layer in f['layers'] for n in layer}
    rows=[]
    for label,selector_old,selector_new in [('radome',oldrad,newrad),('other',set(old['nid'])-oldrad,set(q['nid'])-newrad)]:
        mask0=np.array([n in selector_old for n in old['nid']]);mask1=np.array([n in selector_new for n in q['nid']])
        rows.append({'scope':label,'old_mass_g':float(old['node_mass_g'][mask0].sum()),'new_mass_g':float(q['node_mass_g'][mask1].sum()),
            'old_moment_g_mm':(old['node_mass_g'][mask0]@old['x'][mask0]).tolist(), 'new_moment_g_mm':(q['node_mass_g'][mask1]@q['x'][mask1]).tolist()})
    changes=[]
    for j,n in enumerate(q['nid']):
        if int(n) in ix:
            z=ix[int(n)];dm=q['node_mass_g'][j]-old['node_mass_g'][z];dc=q['x'][j]-old['x'][z]
            if abs(dm)>1e-5 or np.max(abs(dc))>.00001:
                changes.append({'id':int(n),'old_mass_g':float(old['node_mass_g'][z]),'new_mass_g':float(q['node_mass_g'][j]),'delta_coordinates_mm':dc.tolist(),'old_radome':int(n) in oldrad,'new_radome':int(n) in newrad})
    dump(o/'mass_moments.json',{'created_utc':now(),'old':om,'new':qm,'scopes':rows,'existing_node_changes':changes,'all_nodes_mass_retained':True,'original_gate_not_overwritten':True})
    print({'old':om,'new':qm,'scope_moments':rows,'changes':len(changes)},flush=True)

if __name__=='__main__':main()
