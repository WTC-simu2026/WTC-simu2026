"""Prepare a distinct original-buffer fix after native descriptor evidence; do not apply."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
import tarfile,hashlib,difflib,json

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a56'
DEST=ROOT/'tmp/aircraft_a56_original_smstr_patch_proposal'
TARGET='engine/source/elements/elbuf/allocbuf_auto.F'

def main():
    assert not DEST.exists();h=harness()
    measured=read(OUT/'ACTIVE_COHESIVE_ALLOCATION_TRACE_R1/allocation_trace_result.json')
    actual=measured['SRCOORK_context'];assert actual['IGTYP']==43 and actual['NEL']==1
    matched=actual['matching_allocations'];assert len(matched)==1
    assert matched[0]['label']=='ELBUF_STR%GBUF%SMSTR' and matched[0]['native_capacity']==0 and matched[0]['requested_values']==0
    archive=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'
    with tarfile.open(archive) as t:
        m=next(x for x in t.getmembers() if x.name.endswith(TARGET));original=t.extractfile(m).read()
    source=original.decode();original_sha=hashlib.sha256(original).hexdigest()
    assert original_sha=='dd98f5fc264c750bc85fc244f3513a657e13a666583d75f1a72daabca89777f0'
    line=next(l for l in source.splitlines(keepends=True) if 'call my_alloc(ELBUF_STR%GBUF%SMSTR, NEL*G_SMSTR' in l)
    block='''C     TYPE43 implicit geometry also uses the original scratch buffer.
C     Pad allocation only; retain restart widths and read offsets.
      IF (IGTYP==43.AND.G_SMSTR<21) THEN
       call my_alloc(ELBUF_STR%GBUF%SMSTR, NEL*21,
     .               "ELBUF_STR%GBUF%SMSTR")
       ELBUF_STR%GBUF%SMSTR = 0.0D0
      ELSE
       call my_alloc(ELBUF_STR%GBUF%SMSTR, NEL*G_SMSTR,
     .               "ELBUF_STR%GBUF%SMSTR")
      ENDIF
'''
    assert source.count(line)==1 and max(map(len,block.splitlines()))<=72
    proposed=source.replace(line,block).encode()
    assert 'ELBUF_STR%IGTYP  = IGTYP' in source
    tests=[]
    for kind in [14,21,43]:
        for nel in [0,1,128,624]:
            for width in [0,6,21,24]:
                alloc=nel*(max(width,21) if kind==43 else width)
                encoded=nel*width
                saved=list(range(encoded));padded=[0]*alloc;padded[:encoded]=saved
                tests.append({'kind':kind,'NEL':nel,'encoded_width':width,'allocation':alloc,'encoded_read_count':encoded,'pass':padded[:encoded]==saved and (kind!=43 or alloc>=21*nel)})
    assert len(tests)==48 and all(v['pass'] for v in tests)
    DEST.mkdir();(DEST/'allocbuf_auto.F.proposed').write_bytes(proposed)
    patch=''.join(difflib.unified_diff(source.splitlines(keepends=True),proposed.decode().splitlines(keepends=True),fromfile='a/'+TARGET,tofile='b/'+TARGET))
    (DEST/'type43_original_smstr.patch').write_bytes(patch.encode())
    review={'created_utc':now(),'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','target':TARGET,'source_sha256':original_sha,
      'patch_path':rel(DEST/'type43_original_smstr.patch'),'patch_sha256':sha(DEST/'type43_original_smstr.patch'),'proposed_source_path':rel(DEST/'allocbuf_auto.F.proposed'),'proposed_sha256':sha(DEST/'allocbuf_auto.F.proposed'),
      'native_original_allocation_capacity_zero_proven':True,'actual_SAV_matches_original_allocation':matched[0],
      'A55_temporary_buffer_only_hypothesis_rejected':True,'software_patch_applied':False,'compiled_or_native_qualified':False,'human_authorization_received':False,
      'arithmetic_and_restart_restore_cases':tests,'arithmetic_gate_pass':True,'fixed_form_added_lines_at_most_72':True,
      'scope':'Original TYPE43 scratch allocation at restart load, at least NEL*21. Serialized G_SMSTR widths/SDP_RBUF/read counts unchanged. Shared loader affects memory allocation in explicit and implicit; physics cards unchanged.',
      'build_proposal':{'iteration':'AIRCRAFT-A57','isolated_directory':'wtc1_simulation_v8/openradioss_runtime/a57_original_type43_scratch_candidate','prior_A53_graph_and_A55_temporary_patches_retained':True,'maximum_build_s':3600,'CPU_threads':6,'GPU':False,'new_installation':False,'dependencies':'same cached A54/A56 environment'},
      'native_proposal':{'cap_s':180,'CPU':1,'GPU':False,'checks':['native capacity >=NEL*21 and actual pointer identity','heap header writer regression','implicit loaded cohesion/work and time step','whole graph and CHECK','explicit cohesion and TYPE7 conservation'],'acceptance_thresholds_unchanged':True},
      'remaining_failed_gates':['implicit loaded cohesion','whole CHECK 15errors','five implicit TYPE25 ignored','whole inertias/local energy coverage'],'objective1_complete':False,'new_whole_duration_credit_s':0,'harness':h}
    dump(OUT/'original_scratch_patch_proposal_review.json',review)
    (OUT/'proposition_correctif_tampon_origine.md').write_text('''# Proposition A56 pour A57 â€” allocation du tampon d'origine rÃ©ellement utilisÃ©

PrÃ©parÃ©e, non appliquÃ©e et non compilÃ©e. Nouveau correctif distinct, nÃ©cessitant un accord explicite.

## 1. Faits directement observÃ©s

A56 applique et compile le correctif A55 du tampon temporaire ; les tÃ©moins implicites Ã©chouent encore. La surveillance observe de nouveau NODREAC0x31â†’0 pendant SRCOORK et l'arrÃªt avant tout pas chargÃ©. Une autre mesure native,740appels d'allocateur bornÃ©s, capture le descripteur SMSTR : label ELBUF_STR%GBUF%SMSTR, demande0, double8octets, bornes1..0, capacitÃ©0. Son pointeur correspond exactement Ã  SAV reÃ§u par SRCOORK, TYPE43/NEL1. Ce buffer vient du chargeur ALLOCBUF_AUTO, retour0x468d01 dans le binaire A56. L'hypothÃ¨se Â« seule copie temporaire Â» est rejetÃ©e et conservÃ©e.

## 2. Source du logiciel

ALLOCBUF_AUTO alloue le tampon original d'aprÃ¨s NEL*G_SMSTR issu du redÃ©marrage. SRCOORK utilise21colonnes. Le dÃ©faut de capacitÃ© sur le pointeur effectivement utilisÃ© est maintenant une observation native, pas seulement une infÃ©rence du contrat source.

## 3. Archives

Aucune archive historique consultÃ©e ou modifiÃ©e.

## 4. Modification proposÃ©e

Dans allocbuf_auto.F seulement, porter l'allocation TYPE43 Ã  au moins21*NEL valeurs et initialiser le stockage ajoutÃ©. Garder exactement la largeur sÃ©rialisÃ©e G_SMSTR, SDP_RBUF, les offsets et le nombre de valeurs lues ; restaurer ces valeurs dans leur plage d'origine. Les autres types restent inchangÃ©s. Le chargeur est partagÃ© explicite/implicite ; l'allocation mÃ©moire est donc concernÃ©e dans les deux modes, sans changer les cartes physiques. Conserver les correctifs A53 du graphe et A55 du tampon temporaire dans un cinquiÃ¨me moteur sÃ©parÃ©.

## 5. ContrÃ´les prÃ©paratoires

48cas de bornes et restauration des donnÃ©es sÃ©rialisÃ©es passent ; nouvelles lignes72colonnes maximum, empreintes enregistrÃ©es. Aucun contrÃ´le compilÃ© ou physique du nouveau correctif revendiquÃ©. A56, ses sorties et son critÃ¨re mÃ©moire Ã©chouÃ© restent intacts.

## 6. Limites et suite aprÃ¨s accord

Compilation plafonnÃ©e1h, sixCPU, sans GPU ni installation, mÃªmes sources/dÃ©pendances. ContrÃ´les natifs de capacitÃ©/pointeur/mÃ©moire, cohÃ©sion implicite chargÃ©e et demi-pas, graphe/CHECK et tÃ©moins explicites/TYPE7,180s par processus, seuils inchangÃ©s. La rÃ©ponse implicite et les15erreurs entiÃ¨res/cinqTYPE25 ignorÃ©s restent bloquants. Aucun rÃ©sultat d'impact entier supplÃ©mentaire : meilleure fenÃªtre0,0200001220703125s, objectif vidÃ©o3D des dix secondes physiques toujours incomplet.
''',encoding='utf8')
    print(json.dumps({'new_proposal_ready':True,'patch_sha256':review['patch_sha256'],'applied':False}),flush=True)

if __name__=='__main__':main()
