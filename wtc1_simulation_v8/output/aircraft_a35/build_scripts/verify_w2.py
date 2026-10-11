import pathlib,json,hashlib,sys
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);base=json.loads((out/'source_git_verification.json').read_text());changes=[]
for r in base['files']:
 b=(root/'source'/r['path']).read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 if h!=r['archive_git_blob_sha1']:changes.append(r['path'])
assert changes==['EXTLIB_VERSION.json'],changes
tree=json.loads((out/'extlib_v67_tree.json').read_text());rows=[]
for r in tree['tree']:
 if r['type']!='blob':continue
 b=(root/'dependency'/r['path']).read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();n=b.replace(b'\r\n',b'\n');nh=hashlib.sha1(b'blob '+str(len(n)).encode()+b'\0'+n).hexdigest();assert r['sha'] in [h,nh],r['path'];rows.append({'path':r['path'],'git_blob_sha1':r['sha'],'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
assert json.loads((root/'source/EXTLIB_VERSION.json').read_text())['version']=='67'
assert b'H3D_NF_FORMAT' in (root/'source/extlib/h3d/includes/h3dpublic_defs.h').read_bytes()
(out/'source_w2_verification.json').write_text(json.dumps({'pass':True,'tracked_physics_source_unchanged':True,'tracked_changes':changes,'dependency_files':rows,'dependency_pin':tree['sha'],'revision':67},indent=2))
