"""Locate paired inertia bias in native kinetic channels without correcting any energy."""
from run_aircraft_a23 import *

def main(revision):
    rows=[];duration=1 if revision=='w0' else 10
    for a in 'XYZ':
        rd=OUT/revision/f'REFERENCE_ROTATION_{a}';cd=OUT/revision/f'CONNECTED_ROTATION_{a}'
        if not (cd/'review.json').exists():continue
        rg=read(rd/'generation.json');cg=read(cd/'generation.json')
        r=histories(rd/(rg['name']+'T01.csv'));h=histories(cd/(cg['name']+'T01.csv'));T=h['time'];mask=(T>=r['time'][0])&(T<=r['time'][-1]);tm=T[mask]
        q=np.asarray(cg['nodes_mm'])[np.asarray(cg['clip_node_ids'])-1];m=np.asarray(cg['clip_known_nodal_masses_g'])
        X,V,angle,w=rotation(q,tm/duration,a);V/=duration;expected=.5*np.sum(m[None,:,None]*V**2,axis=(1,2))*.001
        ix=int(np.argmax(expected));channels={}
        for k,v in h.items():
            if k in ['KINETIC ENERGY','ROTATION ENERGY'] or k.strip().endswith('KE'):
                if k in r:delta=v[mask]*.001-np.interp(tm,r['time'],r[k])*.001
                else:delta=v[mask]*.001
                channels[k]={'delta_at_peak_J':float(delta[ix]),'maximum_abs_delta_J':float(abs(delta).max())}
        clip=next(v[mask]*.001 for k,v in h.items() if k.startswith('FINITE_METAL_CLIP') and k.strip().endswith('KE'))
        ke=(h['KINETIC ENERGY'][mask]+h['ROTATION ENERGY'][mask])*.001-np.interp(tm,r['time'],r['KINETIC ENERGY']+r['ROTATION ENERGY'])*.001
        wphys=w/duration;observable=wphys>float(wphys.max())*.2
        inferred=2*ke[observable]/wphys[observable]**2/.001
        nativeClip=2*clip[observable]/wphys[observable]**2/.001
        known=inertia(q,m)['XYZ'.index(a),'XYZ'.index(a)]
        rows.append({'axis':a,'duration_ms':duration,'peak_time_ms':float(tm[ix]),'expected_peak_J':float(expected[ix]),
            'native_clip_part_peak_J':float(clip[ix]),'global_added_peak_J':float(ke[ix]),'channels':channels,
            'independent_clip_lumped_I_g_mm2':float(known),'native_added_global_I_median_g_mm2':float(np.median(inferred)),
            'native_clip_part_I_median_g_mm2':float(np.median(nativeClip)),
            'mass_condensation_hypothesis_not_proven':True,'physical_strength_not_qualified':True})
    dest=OUT/f'inertia_channels_{revision}.json';assert not dest.exists();dump(dest,{'created_utc':now(),'rows':rows,'cached_solver_only':True,
      'no_native_energy_reconstruction_or_compensation':True,'hypothesis':'TYPE2 main mass distribution can conserve total mass while changing the diagonal lumped tensor. Compare source theory and finer main surface before insertion.'})
    print({'channels':revision,'axes':len(rows)},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('revision',choices=['w0','w1']);main(p.parse_args().revision)
