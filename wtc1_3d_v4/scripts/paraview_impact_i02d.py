"""VTK transfer of exactly saved nodal states, with independent binary readback."""
import json,hashlib
from pathlib import Path
import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter,vtkXMLUnstructuredGridReader
from vtkmodules.util.numpy_support import numpy_to_vtk,vtk_to_numpy
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_3d_v4/output/impact_i02d';OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'wtc1_simulation_v8/output/impact_i02d_lap_joint/LAP_SEPARATE_H025_R5/computed_frames.npz';data=np.load(source)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[];pvd=['<?xml version="1.0"?>','<VTKFile type="Collection" version="0.1" byte_order="LittleEndian"><Collection>']
for k,t in enumerate(data['times_ms']):
    mesh=vtkUnstructuredGrid();points=vtkPoints();points.SetData(numpy_to_vtk(data['points_mm'][k].copy(),deep=True));mesh.SetPoints(points)
    for q in data['quads']:mesh.InsertNextCell(9,4,q.tolist())
    for b in data['bricks']:mesh.InsertNextCell(12,8,b.tolist())
    arrays={'Part':np.r_[data['parts'],np.full(len(data['bricks']),3)],'Active':np.r_[np.ones(len(data['quads'])),data['active'][k]]}
    for name,a in arrays.items():
        arr=numpy_to_vtk(a,deep=True);arr.SetName(name);mesh.GetCellData().AddArray(arr)
    path=OUT/f'state_{k:03d}.vtu';writer=vtkXMLUnstructuredGridWriter();writer.SetFileName(str(path));writer.SetInputData(mesh);writer.SetDataModeToBinary();assert writer.Write()==1
    back=vtkXMLUnstructuredGridReader();back.SetFileName(str(path));back.Update();r=back.GetOutput()
    checks={'coordinates_exact':bool(np.array_equal(vtk_to_numpy(r.GetPoints().GetData()),data['points_mm'][k])),
        'connectivity_exact':bool(np.array_equal(vtk_to_numpy(mesh.GetCells().GetConnectivityArray()),vtk_to_numpy(r.GetCells().GetConnectivityArray()))),
        'arrays_exact':all(np.array_equal(vtk_to_numpy(r.GetCellData().GetArray(n)),a) for n,a in arrays.items())}
    records.append({'state':k,'time_ms':float(t),'sha256':sha(path),'checks':checks});pvd.append(f'<DataSet timestep="{t:.12g}" group="" part="0" file="{path.name}"/>')
pvd.append('</Collection></VTKFile>');(OUT/'I02D_lap_ms.pvd').write_text('\n'.join(pvd))
(OUT/'paraview_audit.json').write_text(json.dumps({'status':'PASS' if all(all(r['checks'].values()) for r in records) else 'FAIL','states':records,'source_sha256':sha(source),'units':{'length':'mm','time':'ms'},'scope':'Exact nodal-history states. Threshold Active >=0.5 to hide deleted cohesive elements. No interpolation through failure.'},indent=2)+'\n')
(OUT/'README.md').write_text('# I02D — recouvrement\n\nOuvrir I02D_lap_ms.pvd ; filtre Threshold sur Active >= 0.5 pour masquer les éléments cohésifs supprimés. Couleur Part : 1/2 tôles, 3 liaison numérique distribuée. Coordonnées mm, temps ms, aucune amplification ni interpolation de rupture. Géométrie et propriétés hypothétiques ; chargement imposé aux prises, pas un Boeing ni une simulation d’impact complète.\n',encoding='utf-8')
print(json.dumps({'status':'PASS' if all(all(r['checks'].values()) for r in records) else 'FAIL','states':len(records)}))
