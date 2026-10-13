import pathlib,json,hashlib,sys
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);pre=pathlib.Path(sys.argv[3]);old=pathlib.Path(sys.argv[4]);rows=[]
for tree,sub in [(json.loads((pre/'legacy_candidate_git_tree.json').read_text())['data'],'source'),(json.loads((old/'extlib_v67_tree.json').read_text()),'dependency')]:
 assert not tree.get('truncated')
 for e in tree['tree']:
  if e['type']!='blob':continue
  p=root/sub/e['path'];b=p.read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();n=b.replace(b'\r\n',b'\n');nh=hashlib.sha1(b'blob '+str(len(n)).encode()+b'\0'+n).hexdigest();assert e['sha'] in [h,nh],e['path'];rows.append({'kind':sub,'path':e['path'],'git_blob_sha1':e['sha'],'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
(out/'source_and_dependency_verification.json').write_text(json.dumps({'pass':True,'files':rows,'no_physics_source_patch':True},indent=2))
