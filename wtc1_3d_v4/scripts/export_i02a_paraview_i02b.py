"""ParaView/VTK transfer of cached I02A results; no solver rerun or old writes.

Run with the installed pvpython. Millimetres and milliseconds are explicit.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints,vtkIdList
from vtkmodules.vtkCommonDataModel import vtkPolyData,vtkCellArray
from vtkmodules.vtkIOXML import vtkXMLPolyDataWriter,vtkXMLPolyDataReader
from vtkmodules.util.numpy_support import numpy_to_vtk,vtk_to_numpy

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'wtc1_simulation_v8/output/impact_i02a_structured_wing/CONTACT_M050_R1/computed_frames.npz'
OUT=ROOT/'wtc1_3d_v4/output/impact_i02b/paraview_i02a'
OUT.mkdir(parents=True,exist_ok=True)
d=np.load(SOURCE); quads=d['quads'];parts=d['parts']; records=[]
for i,t in enumerate(d['times_ms']):
    mesh=vtkPolyData(); points=vtkPoints(); points.SetData(numpy_to_vtk(d['points_mm'][i],deep=True));mesh.SetPoints(points)
    polys=vtkCellArray()
    for q in quads:
        ids=vtkIdList()
        for n in q:ids.InsertNextId(int(n))
        polys.InsertNextCell(ids)
    mesh.SetPolys(polys)
    for name,array in [('solver_part_id',parts),('plastic_strain_equivalent',d['epsp'][i])]:
        a=numpy_to_vtk(array,deep=True);a.SetName(name);mesh.GetCellData().AddArray(a)
    path=OUT/f'state_{i:03d}.vtp';writer=vtkXMLPolyDataWriter();writer.SetFileName(str(path));writer.SetInputData(mesh);writer.SetDataModeToBinary()
    assert writer.Write()==1
    reader=vtkXMLPolyDataReader();reader.SetFileName(str(path));reader.Update();r=reader.GetOutput()
    error=float(np.max(abs(vtk_to_numpy(r.GetPoints().GetData())-d['points_mm'][i])))
    cells=np.array([list(r.GetCell(j).GetPointIds().GetId(k) for k in range(4)) for j in range(len(quads))])
    checks={'points_exact':error==0.,'connectivity_exact':bool(np.array_equal(cells,quads)),
            'parts_exact':bool(np.array_equal(vtk_to_numpy(r.GetCellData().GetArray('solver_part_id')),parts)),
            'strain_exact':bool(np.array_equal(vtk_to_numpy(r.GetCellData().GetArray('plastic_strain_equivalent')),d['epsp'][i]))}
    records.append({'state':i,'time_ms':float(t),'max_coordinate_error_mm':error,'checks':checks,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
pvd=['<?xml version="1.0"?>','<VTKFile type="Collection" version="0.1" byte_order="LittleEndian"><Collection>']
for row in records:pvd.append(f'<DataSet timestep="{row["time_ms"]:.9g}" group="" part="0" file="state_{row["state"]:03d}.vtp"/>')
pvd.append('</Collection></VTKFile>');(OUT/'I02A_solver_states_ms.pvd').write_text('\n'.join(pvd),encoding='utf-8')
audit={'status':'PASS' if all(all(r['checks'].values()) for r in records) else 'FAIL','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
       'length_units':'mm','time_units':'ms','states':records,'scope':'I02A non-eroding wing section; late strains outside constitutive validity. I02B connector not integrated yet.'}
(OUT/'transfer_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
(OUT/'README.md').write_text('# I02A dans ParaView\n\nOuvrir I02A_solver_states_ms.pvd. Longueurs en mm, temps en ms. Couleur par solver_part_id ou plastic_strain_equivalent.\n\n25 états mécaniques sauvegardés I02A ; rupture désactivée, grandes déformations tardives non qualifiées. Le connecteur I02B ne fait pas encore partie de cette aile. Ne pas activer une interpolation temporelle.\n',encoding='utf-8')
print(json.dumps({'status':audit['status'],'states':len(records),'pvd':str(OUT/'I02A_solver_states_ms.pvd')}))
