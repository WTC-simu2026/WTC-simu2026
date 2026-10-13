"""Prepare a reviewable AGPL source patch and independent storage-oracle controls; do not apply or compile it."""
from probe_aircraft_a53 import *
from pathlib import Path
import difflib,random

HELPERS='''
C     Proposed storage selection only; original AGPL-3.0-or-later license.
      SUBROUTINE TYPE2_KIN_ADD(ROW,NODE,FIRST,NNMAX,NKMAX,BOUND,
     .                        NROW,ICOK,ICOKM)
      INTEGER ROW,NODE,FIRST,NNMAX,NKMAX,BOUND,NROW(*)
      INTEGER ICOK(NNMAX,*),ICOKM(NKMAX,*),COL
      IF (FIRST==1) THEN
        IF (ROW<=BOUND) THEN
          CALL REORDER_A(NROW(ROW),ICOKM(1,ROW),NODE)
        ELSE
          CALL REORDER_A(NROW(ROW),ICOK(1,ROW),NODE)
        ENDIF
      ELSE
        IF (ROW<=BOUND) THEN
          CALL REORDER_A(NROW(ROW),ICOK(1,ROW),NODE)
        ELSE
          COL=ROW-BOUND
          CALL REORDER_A(NROW(ROW),ICOKM(1,COL),NODE)
        ENDIF
      ENDIF
      END

      INTEGER FUNCTION TYPE2_KIN_COL(ROW,POS,FIRST,NNMAX,NKMAX,
     .                               BOUND,ICOK,ICOKM)
      INTEGER ROW,POS,FIRST,NNMAX,NKMAX,BOUND
      INTEGER ICOK(NNMAX,*),ICOKM(NKMAX,*)
      IF (FIRST==1) THEN
        IF (ROW<=BOUND) THEN
          TYPE2_KIN_COL=ICOKM(POS,ROW)
        ELSE
          TYPE2_KIN_COL=ICOK(POS,ROW)
        ENDIF
      ELSE
        IF (ROW<=BOUND) THEN
          TYPE2_KIN_COL=ICOK(POS,ROW)
        ELSE
          TYPE2_KIN_COL=ICOKM(POS,ROW-BOUND)
        ENDIF
      ENDIF
      END

      LOGICAL FUNCTION TYPE2_KIN_HAS(ROW,NODE,FIRST,NNMAX,NKMAX,
     .                              BOUND,NROW,ICOK,ICOKM)
      INTEGER ROW,NODE,FIRST,NNMAX,NKMAX,BOUND,NROW(*)
      INTEGER ICOK(NNMAX,*),ICOKM(NKMAX,*)
      LOGICAL INTAB
      EXTERNAL INTAB
      IF (FIRST==1) THEN
        IF (ROW<=BOUND) THEN
          TYPE2_KIN_HAS=INTAB(NROW(ROW),ICOKM(1,ROW),NODE)
        ELSE
          TYPE2_KIN_HAS=INTAB(NROW(ROW),ICOK(1,ROW),NODE)
        ENDIF
      ELSE
        IF (ROW<=BOUND) THEN
          TYPE2_KIN_HAS=INTAB(NROW(ROW),ICOK(1,ROW),NODE)
        ELSE
          TYPE2_KIN_HAS=INTAB(NROW(ROW),ICOKM(1,ROW-BOUND),NODE)
        ENDIF
      ENDIF
      END
'''

def patch_block(text,name,first,nrow):
 start=text.index('      SUBROUTINE '+name+'(');end=text.index('      SUBROUTINE ',start+25);full=text[start:end]
 a=full.index('C------interface 2') if first else full.index('      DO J=1,NINT2');z=full.index('C------Rbe2',a) if first else full.index('C-----RBE2',a);block=full[a:z];audit=[]
 pattern=rf'^(\s*)(IF\s*\([^\n]*?\)\s*)?CALL REORDER_A\({nrow}\((\w+)\),ICOK\(1,\3\),(\w+)\)\s*$'
 def add(m):
  row,node=m.group(3),m.group(4);conditional=m.group(2);audit.append({'kind':'add','row':row,'neighbor':node})
  lines=[]
  if conditional:lines.append('      '+conditional.strip()+' THEN')
  lines+=['      CALL TYPE2_KIN_ADD('+row+','+node+','+str(first)+',','     . NNMAX,NKMAX,INK,'+nrow+',ICOK,ICOKM)']
  if conditional:lines.append('      ENDIF')
  return '\n'.join(lines)
 block,adds=re.subn(pattern,add,block,flags=re.M);assert adds==5,(name,adds)
 readpat=r'NJ=ICOK\((\w+),(\w+)\)'
 def get(m):
  pos,row=m.group(1),m.group(2);audit.append({'kind':'get','row':row,'position':pos});return 'NJ=TYPE2_KIN_COL('+row+','+pos+','+str(first)+',\n     . NNMAX,NKMAX,INK,ICOK,ICOKM)'
 block,gets=re.subn(readpat,get,block);assert gets==1,(name,gets)
 haspat=rf'INTAB\({nrow}\((\w+)\),ICOK\(1,\1\),(\w+)\)'
 def has(m):
  row,node=m.group(1),m.group(2);audit.append({'kind':'has','row':row,'neighbor':node});return 'TYPE2_KIN_HAS('+row+','+node+','+str(first)+',NNMAX,NKMAX,\n     . INK,'+nrow+',ICOK,ICOKM)'
 block,hases=re.subn(haspat,has,block);assert hases==1,(name,hases)
 fixed=full[:a]+block+full[z:];marker='      EXTERNAL INTAB';assert marker in fixed;fixed=fixed.replace(marker,marker+'\n      INTEGER TYPE2_KIN_COL\n      LOGICAL TYPE2_KIN_HAS\n      EXTERNAL TYPE2_KIN_COL,TYPE2_KIN_HAS',1)
 return text[:start]+fixed+text[end:],audit

def oracle_controls(watch):
 # Graph semantics are an independent dict-of-sets oracle, not numerical damage targets.
 rng=random.Random(1102078);cases=[]
 for first in [0,1]:
  for ordinary,mains in [(3,2),(0,3),(4,0),(8,5)]:
   total=ordinary+mains;bound=mains if first else ordinary;nnmax,nkmax=24,119
   # Sizing stage deliberately retains padded ordinary rows with global indices.
   obase=mains*nkmax if first else 0;mbase=0 if first else ordinary*nnmax
   storage=[0]*(mains*nkmax+total*nnmax if first else ordinary*nnmax+mains*nkmax);counts=[0]*(total+1);semantic={row:set() for row in range(1,total+1)}
   def offset(row):
    main=row<=bound if first else row>bound
    col=row if first or not main else row-bound
    return (mbase if main else obase)+(col-1)*(nkmax if main else nnmax)
   for _ in range(120):
    row=rng.randrange(1,total+1);node=rng.randrange(1,16);base=offset(row);values=storage[base:base+counts[row]]
    if node not in values:storage[base+counts[row]]=node;counts[row]+=1
    semantic[row].add(node)
   checks=[]
   for row in semantic:
    start=offset(row);actual=storage[start:start+counts[row]];checks.append(set(actual)==semantic[row] and len(actual)==len(semantic[row]));assert all(checks)
   cases.append({'main_first':bool(first),'ordinary_rows':ordinary,'main_rows':mains,'edges':sum(len(v) for v in semantic.values()),'dict_set_oracle_pass':all(checks)})
 n=watch['watch']['initial_count'];old=watch['watch']['correct_initial_columns'];written=next(e for e in watch['write_events'] if e['watched_wrong_column_written'])['wrong_stride_next_value_now'];assert written in old
 old_count=n+1;correct_count=len(set(old+[written]));assert old_count==4 and correct_count==3
 return {'created_utc':now(),'seed':1102078,'synthetic_graphs_not_probabilities':True,'cases':cases,'all_oracle_cases_pass':all(r['dict_set_oracle_pass'] for r in cases),'native_duplicate_edge_reproduction':{'initial_count':n,'initial_correct_columns':old,'already_present_neighbor':written,'observed_old_count_after_write':old_count,'semantic_expected_count':correct_count,'current_wrong_stride_route_fails_semantics':True},'scope':'Independent sparse graph set invariants and native observed duplicate; proposed Fortran has not been compiled or executed.'}

def main():
 guard();proposal=OUT/'proposition_correctif_graphe_moteur.md';assert not proposal.exists();r=read(OUT/'WHOLE_REFERENCE_GRAPH_WRITE_WATCH/write_watch_result.json');assert r['Engine_exit_code']==0 and r['watch']['dimensions']['NNMAX']==24 and r['watch']['dimensions']['NKMAX']==119;bad=[e for e in r['write_events'] if e['watched_wrong_column_written']];assert len(bad)==1 and not any(e['watched_correct_column_written'] for e in r['write_events']);assert bad[0]['wrong_stride_next_value_now'] in r['watch']['correct_initial_columns']
 folder=ROOT/'tmp/aircraft_a53_graph_patch_proposal';assert not folder.exists();folder.mkdir();path='engine/source/implicit/ind_glob_k.F'
 with tarfile.open(CAND/'source.tar.gz','r:gz') as tar:
  m=next(x for x in tar if x.name.endswith('/'+path));original=tar.extractfile(m).read();s=original.decode()
 fixed,a=patch_block(s,'DIM_KINE_T',1,'NROWI');fixed,b=patch_block(fixed,'IND_KINE_K',0,'NROWK');fixed+='\n'+HELPERS
 # Only the two Type2 blocks and their helper declarations change; preserve other original routines.
 for line in HELPERS.splitlines():assert not line or line.startswith('C') or len(line)<=72,(len(line),line)
 (folder/'ind_glob_k.F.proposed').write_text(fixed,encoding='utf8');patch=''.join(difflib.unified_diff(s.splitlines(keepends=True),fixed.splitlines(keepends=True),fromfile='a/'+path,tofile='b/'+path));(folder/'type2_graph_routing.patch').write_text(patch,encoding='utf8')
 controls=oracle_controls(r);dump(OUT/'graph_storage_oracle_review.json',controls)
 metadata={'created_utc':now(),'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','source_path':path,'original_sha256':hashlib.sha256(original).hexdigest(),'proposed_source_path':rel(folder/'ind_glob_k.F.proposed'),'proposed_sha256':streamsha(folder/'ind_glob_k.F.proposed'),'patch_path':rel(folder/'type2_graph_routing.patch'),'patch_sha256':streamsha(folder/'type2_graph_routing.patch'),'source_license':'AGPL-3.0-or-later','raw_proposed_third_party_source_not_in_public_manifest':True,'modified_functions':['DIM_KINE_T TYPE2 block','IND_KINE_K TYPE2 block'],'replacement_audit':{'DIM_KINE_T':a,'IND_KINE_K':b},'helpers':'Route add/get/membership to ordinary vs main row storage, retaining padded global ordinary indices in the sizing phase and row-INK main indices in building phase.','software_source_or_binary_changed':False,'patch_applied':False,'compiled_or_native_qualified':False,'requires_explicit_user_software_authorization':True};dump(OUT/'engine_patch_proposal_review.json',metadata)
 proposal.write_text('''# Proposition A53 : correction du rangement du graphe, moteur isolé

La mesure sur le moteur actuel non modifié montre un défaut précis. Pour le nœud48151, ligne9891dans la région principale, NNMAX24etNKMAX119donnent deux adresses différentes. Le moteur écrit le voisin48154dans le tableau calculé avec le mauvais pas24, puis augmente le compteur de la bonne ligne de3à4. Le voisin figurait déjà dans ses trois colonnes correctes. La quatrième colonne correcte reste0pendant que le compteur monte ensuite jusqu’à14. Cela explique des lignes contaminées ; la cause de toutes les autres erreurs n’est pas déclarée prouvée.

Le correctif proposé concerne un seul fichier, ind_glob_k.F, dans la source figée du28juillet. Il sélectionne le tableau et le pas corrects pour les opérations TYPE2de dimensionnement et de construction : ajout de colonne, lecture de voisin, test d’appartenance. La phase de dimensionnement conserve ses indices globaux avec padding, conformément à l’allocation existante ; la phase de construction utilise row-INKpour les principales. Les matériaux, géométrie, masses, liaisons physiques, charges, pas de temps et critères restent inchangés. Aucun bloc n’est ignoré pour éviter un arrêt.

Huit contrôles de graphes indépendants passent une référence dictionnaire/ensembles, y compris domaines sans région principale ou ordinaire. Le cas observé reproduit l’ajout erroné d’un voisin déjà présent. Ces contrôles ne sont pas une compilation ou qualification du moteur proposé.

Le fichier proposé et le patch exact sont dans tmp/aircraft_a53_graph_patch_proposal/, sous la licenceAGPLdu moteur. Les empreintes et la liste des changements sont enregistrées dans engine_patch_proposal_review.json. Aucun fichier du logiciel actuel n’a été modifié, aucun nouveau binaire compilé.

## Exécution proposée après accord explicite

Créer un troisième moteur séparé depuis le même code3d75ff13d1946f6d28a43920eac4fa2aae41b27a, avec uniquement ce correctif. Utiliser les compilateurs et bibliothèques déjà installés, les dépendances en cache, aucune nouvelle installation, aucun GPU. Compilation limitée à une heure, sixCPUmaximum. Conserver source/patch/empreintes, paramètres de compilation, journaux, version et nouveau binaire ; ne remplacer aucun ancien moteur.

Puis vérifier la syntaxe compilée, les cas indépendants de masse/lois cohésives/contact et la destination native des écritures de graphe. Comparer les CHECKentiers original et candidat, sans toucher les entrées physiques. Chaque contrôle natif reste borné180s. Les critères échoués restent explicites : cela n’autorise pas un impact implicite avec TYPE25ignorés. Le moteur ne sera intégré à l’impact qu’après bilans et contrôles nécessaires ; les dix secondes3D restent l’objectif, pas la simple compilation.

## Autorisation requise

AGENTS.md impose : « Les écritures externes, publications, envois ou modifications de logiciels exigent une demande explicite de Jeremy. » L’accord A43 concernait le moteur non modifié du28juillet. Cette proposition modifie son code de rangement du graphe ; elle nécessite donc un accord supplémentaire. La publicationA52+A53est déjà autorisée et peut continuer indépendamment.
''',encoding='utf8');print({'software_patch_proposal_ready':True,'actual_patch_applied':False,'oracle_graphs_pass':8,'explicit_new_software_authorization_required':True},flush=True)

if __name__=='__main__':main()
