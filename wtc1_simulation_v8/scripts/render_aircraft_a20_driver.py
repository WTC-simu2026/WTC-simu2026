"""Run the native-state renderer with reproducible external-tool metadata."""
from run_aircraft_a20_whole import *
from run_aircraft_a17 import execute as external_execute

def main():
    whole_guard();assert (D/'review.json').exists() and not (OUT/'video').exists()
    exe=Path('C:/Program Files/Blender Foundation/Blender 5.2/blender.exe');script=ROOT/'wtc1_3d_v4/scripts/render_aircraft_a20.py'
    assert external_execute(exe,['--background','--factory-startup','--threads','2','--python',str(script)],OUT,'blender_render.log',600,env())
    assert (OUT/'video/render_manifest.json').exists()

if __name__=='__main__':main()
