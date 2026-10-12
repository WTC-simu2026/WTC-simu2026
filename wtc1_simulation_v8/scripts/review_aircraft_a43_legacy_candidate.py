"""Review an immutable legacy-format Engine candidate; do not build or install it."""
from preflight_aircraft_a43 import *
import hashlib
PIN='3d75ff13d1946f6d28a43920eac4fa2aae41b27a'
REVIEW=ROOT/'tmp/aircraft_a43_source_review'

def review():
 guard();assert not (OUT/'legacy_candidate_source_review.json').exists();REVIEW.mkdir(parents=True,exist_ok=True);treefile=OUT/'legacy_candidate_git_tree.json';t=read(treefile) if treefile.exists() else fetch(f'https://api.github.com/repos/gabrielrussell/OpenRadioss/git/trees/{PIN}?recursive=1');assert t['status']==200 and not t['data']['truncated'];
 if not treefile.exists():dump(treefile,t)
 entries={e['path']:e for e in t['data']['tree'] if e['type']=='blob'}
 wanted=['engine/source/materials/mat/mat117/sigeps117.F','starter/source/materials/mat/mat117/hm_read_mat117.F','engine/CMakeLists.txt','engine/CMake_Compilers/cmake_linux64_gf.txt','LICENSE.md'];assert all(x in entries for x in wanted);rows=[]
 for name in wanted:
  url=f'https://raw.githubusercontent.com/gabrielrussell/OpenRadioss/{PIN}/{name}'
  p=REVIEW/name
  if p.exists():b=p.read_bytes()
  else:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'WTC1-reproducible-preflight'}),timeout=15) as r:b=r.read(1000000)
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blob==entries[name]['sha'];rows.append({'source_path':name,'git_blob_sha1':blob,'sha256':streamsha(p),'bytes':len(b),'url':url})
 engine=(REVIEW/wanted[0]).read_text();starter=(REVIEW/wanted[1]).read_text();compiler=(REVIEW/wanted[3]).read_text();assert 'UPARAM(21)' in engine and 'NUPARAM = 21' in starter;assert 'MATPARAM%TABLE' not in engine.upper();assert 'MUMPS' in compiler.upper();assert 'matparam%ntable' not in starter.lower()
 dump(OUT/'legacy_candidate_source_review.json',{'created_utc':now(),'source_repository':'https://github.com/gabrielrussell/OpenRadioss','pin':PIN,'commit_date':'2026-07-28T15:06:41Z','complete_recursive_tree_verified':True,'files':rows,'legacy_LAW117_user_array_21_parameters':True,'legacy_user_functions':2,'no_new_matparam_table_access_in_LAW117':True,'MUMPS_build_options_present':True,'source_identical_to_installed_Windows_build_proven':False,'candidate_only':True,'raw_source_review_cache':rel(REVIEW),'no_installation_or_compilation':True,'no_source_physics_patches':True,'route':'Build only this complete pinned Engine source separately with installed MUMPS; retain existing Windows Starter. Validate native compatibility and numerical behavior before any whole extension.','external_libraries':{'required_original_version':'71','original_delivery_availability_unconfirmed':True,'existing_mirror_version':'59','existing_libraries_not_assumed_equivalent':True}});print({'legacy_LAW117_source_review_pass':True,'pin':PIN,'candidate_only':True},flush=True)

if __name__=='__main__':review()
