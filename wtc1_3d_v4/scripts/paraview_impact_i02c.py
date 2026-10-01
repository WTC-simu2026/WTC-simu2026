"""Convert verified raw animation files for interactive ParaView inspection."""
import json,hashlib
from pathlib import Path
import numpy as np
from vtkmodules.vtkIOLegacy import vtkUnstructuredGridReader
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter,vtkXMLUnstructuredGridReader
from vtkmodules.util.numpy_support import vtk_to_numpy
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_3d_v4/output/impact_i02c';audit=json.loads((OUT/'animation_cross_audit.json').read_text());assert audit['status']=='PASS'
records=[];pvd=['<?xml version="1.0"?>','<VTKFile type="Collection" version="0.1" byte_order="LittleEndian"><Collection>']
for state in audit['states']:
    index=state['state'];source=OUT/'vtk_raw'/f'state_{index:03d}.vtk';assert hashlib.sha256(source.read_bytes()).hexdigest()==state['vtk_sha256']
    reader=vtkUnstructuredGridReader();reader.SetFileName(str(source));reader.ReadAllScalarsOn();reader.ReadAllVectorsOn();reader.Update();mesh=reader.GetOutput()
    path=OUT/f'state_{index:03d}.vtu';writer=vtkXMLUnstructuredGridWriter();writer.SetFileName(str(path));writer.SetInputData(mesh);writer.SetDataModeToBinary();assert writer.Write()==1
    back=vtkXMLUnstructuredGridReader();back.SetFileName(str(path));back.Update();r=back.GetOutput()
    checks={'coordinates_exact':bool(np.array_equal(vtk_to_numpy(mesh.GetPoints().GetData()),vtk_to_numpy(r.GetPoints().GetData()))),'connectivity_exact':bool(np.array_equal(vtk_to_numpy(mesh.GetCells().GetConnectivityArray()),vtk_to_numpy(r.GetCells().GetConnectivityArray()))),'cell_types_exact':bool(np.array_equal(vtk_to_numpy(mesh.GetCellTypesArray()),vtk_to_numpy(r.GetCellTypesArray())))}
    for location in ('PointData','CellData'):
        original=getattr(mesh,'Get'+location)();copied=getattr(r,'Get'+location)()
        equal=[]
        for j in range(original.GetNumberOfArrays()):
            aa=vtk_to_numpy(original.GetArray(j));bb=vtk_to_numpy(copied.GetArray(original.GetArrayName(j)))
            equal.append(np.array_equal(aa,bb))
        checks[location+'_arrays_exact']=all(equal)
    records.append({'state':index,'checks':checks,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    pvd.append(f'<DataSet timestep="{state["time_ms"]:.9g}" group="" part="0" file="{path.name}"/>')
pvd.append('</Collection></VTKFile>');(OUT/'I02C_coupled_joint_ms.pvd').write_text('\n'.join(pvd),encoding='utf-8')
result={'status':'PASS' if all(all(r['checks'].values()) for r in records) else 'FAIL','states':records,'units':{'length':'mm','time':'ms'},'source_cross_audit_sha256':hashlib.sha256((OUT/'animation_cross_audit.json').read_bytes()).hexdigest()}
(OUT/'paraview_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(OUT/'README.md').write_text('# I02C — joint couplé\n\nOuvrir I02C_coupled_joint_ms.pvd. Coordonnées mm, temps ms. Aucun facteur d’amplification. États du cas DYN_BASE_H025_R2 à 2,5 J, deux bandes coplanaires et liaison tangentielle unilatérale. Ce n’est ni un avion ni un recouvrement riveté réel. Ne pas interpoler la rupture entre les états.\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'states':len(records)}))
