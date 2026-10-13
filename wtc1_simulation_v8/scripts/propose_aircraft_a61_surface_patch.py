"""Prepare an exact unapplied AGPL source difference outside public MIT outputs."""
from prepare_aircraft_a61_surface_iteration import ROOT,OUT,CFG,guard,read,dump,sha,now,rel
import tarfile,hashlib,difflib,json

TARGET='engine/source/elements/solid/solide8z/s8zke3.F'
PROPOSAL=ROOT/'wtc1_simulation_v8/openradioss_runtime/a61_surface_iteration_proposal'

HELPER='''C=======================================================================
C     WTC A61 candidate: symmetric ELASTIC iteration matrix only.
C     Native SUSER43/SIGEPS117 residual and history remain untouched.
C     Reference Gauss areas: TYPE43, LAW117, Ismstr=1, four points.
C     Damage/frame derivatives are omitted, NOT an exact Jacobian.
      SUBROUTINE WTC_A61_S43_K(ELBUF_STR,NEL,IXS,X,IPM,BUFMAT,
     .              IDDL,IADK,JDIK,K_DIAG,K_LT,ETAG)
      USE ELBUFDEF_MOD
      USE ELEMENT_MOD, ONLY : NIXS
#include "implicit_f.inc"
#include "mvsiz_p.inc"
#include "param_c.inc"
#include "com04_c.inc"
      TYPE(ELBUF_STRUCT_), TARGET :: ELBUF_STR
      TYPE(G_BUFEL_), POINTER :: GB
      TYPE(L_BUFEL_), POINTER :: LB
      INTEGER NEL,IXS(NIXS,*),IPM(NPROPMI,*),IDDL(*),IADK(*)
      INTEGER JDIK(*),ETAG(*),NN(MVSIZ,8)
      INTEGER I,J,A,B,P,NA,NB,IA,IB,MAT,IAD
      my_real X(*),BUFMAT(*),K_DIAG(*),K_LT(*)
      my_real BLOCK(3,3,MVSIZ),DG(3,3,MVSIZ),OFF(MVSIZ)
      my_real MID(3,4),R(3),S(3),N(3),LEN,EN,ET,H(4,4)
      my_real PG,P1,P2,P3,W,SGN,AREA,GPON(MVSIZ,4)
C     Fail closed on unsupported layouts; do not invent a thickness.
      IF (NEL<=0.OR.NEL>MVSIZ) STOP 61
      GB => ELBUF_STR%GBUF
      IF (.NOT.ASSOCIATED(ELBUF_STR%BUFLY)) STOP 61
      IF (SIZE(ELBUF_STR%BUFLY)/=1) STOP 61
      IF (.NOT.ASSOCIATED(ELBUF_STR%BUFLY(1)%LBUF)) STOP 61
      IF (SIZE(ELBUF_STR%BUFLY(1)%LBUF,1)/=4) STOP 61
      IF (SIZE(ELBUF_STR%BUFLY(1)%LBUF,2)/=1) STOP 61
      IF (SIZE(ELBUF_STR%BUFLY(1)%LBUF,3)/=1) STOP 61
      IF (.NOT.ASSOCIATED(GB%OFF)) STOP 61
      IF (SIZE(GB%OFF)<NEL) STOP 61
      MAT=IXS(1,1)
      IF (IPM(2,MAT)/=117.OR.IPM(9,MAT)<2) STOP 61
      IAD=IPM(7,MAT)
      EN=BUFMAT(IAD)
      ET=BUFMAT(IAD+1)
      IF (EN<=ZERO.OR.ET<=ZERO) STOP 61
      PG=ONE/SQRT(THREE)
      P1=(ONE+PG)*(ONE-PG)*FOURTH
      P2=(ONE+PG)*(ONE+PG)*FOURTH
      P3=(ONE-PG)*(ONE-PG)*FOURTH
      H(:,1)=(/P2,P1,P3,P1/)
      H(:,2)=(/P1,P2,P1,P3/)
      H(:,3)=(/P3,P1,P2,P1/)
      H(:,4)=(/P1,P3,P1,P2/)
      DO A=1,8
        DO I=1,NEL
          NN(I,A)=IXS(A+1,I)
        ENDDO
      ENDDO
      OFF(1:NEL)=MIN(ONE,MAX(ZERO,GB%OFF(1:NEL)))
      IF (NEIG>0) CALL S8EOFF(1,NEL,IXS,ETAG,OFF)
      DO P=1,4
        LB => ELBUF_STR%BUFLY(1)%LBUF(P,1,1)
        IF (.NOT.ASSOCIATED(LB%VOL)) STOP 61
        IF (.NOT.ASSOCIATED(LB%OFF)) STOP 61
        IF (SIZE(LB%VOL)<NEL.OR.SIZE(LB%OFF)<NEL) STOP 61
        DO I=1,NEL
          GPON(I,P)=ZERO
          IF (OFF(I)<=ZERO) CYCLE
          IF (LB%OFF(I)/=ZERO.AND.LB%OFF(I)/=ONE) STOP 61
          IF (LB%VOL(I)<=ZERO) STOP 61
          GPON(I,P)=LB%VOL(I)*LB%OFF(I)
        ENDDO
      ENDDO
      DG=ZERO
      DO I=1,NEL
        IF (OFF(I)<=ZERO) CYCLE
        DO A=1,4
          NA=NN(I,A)
          NB=NN(I,A+4)
          IF (NA<=0.OR.NB<=0) STOP 61
          DO J=1,3
            MID(J,A)=HALF*(X(3*(NA-1)+J)+X(3*(NB-1)+J))
          ENDDO
        ENDDO
        R=MID(:,2)+MID(:,3)-MID(:,1)-MID(:,4)
        S=MID(:,3)+MID(:,4)-MID(:,1)-MID(:,2)
        N(1)=R(2)*S(3)-R(3)*S(2)
        N(2)=R(3)*S(1)-R(1)*S(3)
        N(3)=R(1)*S(2)-R(2)*S(1)
        LEN=SQRT(SUM(N*N))
        IF (LEN<=ZERO) STOP 61
        N=N/LEN
        DO J=1,3
          DO P=1,3
            DG(J,P,I)=(EN-ET)*N(J)*N(P)
          ENDDO
          DG(J,J,I)=DG(J,J,I)+ET
        ENDDO
      ENDDO
      DO A=1,8
        IA=MOD(A-1,4)+1
        DO B=A,8
          IB=MOD(B-1,4)+1
          SGN=ONE
          IF ((A<=4).NEQV.(B<=4)) SGN=-ONE
          BLOCK=ZERO
          DO I=1,NEL
            W=ZERO
            DO P=1,4
              W=W+H(IA,P)*H(IB,P)*GPON(I,P)
            ENDDO
            BLOCK(:,:,I)=SGN*W*DG(:,:,I)
          ENDDO
          IF (A==B) THEN
            CALL ASSEM_KII(NN(1,A),NEL,IDDL,IADK,K_DIAG,
     .                     K_LT,BLOCK,3,OFF)
          ELSE
            CALL ASSEM_KIJ(NN(1,A),NN(1,B),NEL,IDDL,IADK,
     .                     JDIK,K_DIAG,K_LT,BLOCK,3,OFF)
          ENDIF
        ENDDO
      ENDDO
      RETURN
      END
'''

def main():
    c=guard();assert read(OUT/'symmetric_surface_iteration_review_R1.json')['pass']
    assert not PROPOSAL.exists();PROPOSAL.mkdir()
    archive=ROOT/c['software_source']['archive'];assert sha(archive)==c['software_source']['sha256']
    source_rows=[]
    selected=[TARGET,'engine/source/elements/solid/sconnect/suser43.F','engine/source/elements/solid/sconnect/scoor43.F','engine/source/elements/solid/sconnect/sdef43.F','engine/source/elements/solid/sconnect/sfint43.F','engine/source/elements/solid/sconnect/sdet43.F','engine/source/implicit/imp_glob_k.F','engine/source/elements/elbuf/copy_elbuf.F','engine/source/elements/elbuf/copy_elbuf_1.F','common_source/modules/mat_elem/elbufdef_mod.F90']
    with tarfile.open(archive) as t:
        names=t.getnames()
        for target in selected:
            name=next(n for n in names if n.endswith('/'+target));raw=t.extractfile(name).read();text=raw.decode('utf8');lines=text.splitlines()
            anchors=[]
            for i,line in enumerate(lines):
                for key in ['SUBROUTINE ASSEM_KIJ','SUBROUTINE ASSEM_KII','CALL S8ZKE3','CALL SIGEPS117','UPARAM =>','IPM(7,IMAT)','IXS(1','HH(1,1)','AREAP(I,1)','VOL(1:NEL)=AREAP','SIZE','COPY','%VAR','%VOL','P1X(I)=(X1','N(1)']:
                    if key in line:anchors.append({'line':i+1,'keyword':key})
            source_rows.append({'path':target,'sha256':hashlib.sha256(raw).hexdigest(),'line_count':len(lines),'anchors':anchors})
            if target==TARGET:original=text;original_bytes=raw
    anchor='      GBUF => ELBUF_STR%GBUF\n';assert original.count(anchor)==1
    insertion='''C     Experimental area stiffness, scoped to the declared cohesive card.
      IF (IGTYP==43.AND.MTN==117.AND.ISMSTR==1) THEN
        CALL WTC_A61_S43_K(ELBUF_STR,NEL,IXS(1,NFT+1),X,IPM,
     .                    BUFMAT,IDDL,IADK,JDIK,K_DIAG,K_LT,ETAG)
        RETURN
      ENDIF
'''
    proposed=original.replace(anchor,anchor+insertion)+HELPER
    overlong=[{'line':i+1,'length':len(l)} for i,l in enumerate((insertion+HELPER).splitlines()) if len(l)>72 and not l.startswith('C')]
    assert not overlong,overlong
    source_path=PROPOSAL/'s8zke3.proposed.F';source_path.write_text(proposed,encoding='utf8',newline='\n')
    patch=PROPOSAL/'type43_surface_elastic_iteration.patch'
    patch.write_text(''.join(difflib.unified_diff(original.splitlines(True),proposed.splitlines(True),fromfile='a/'+TARGET,tofile='b/'+TARGET)),encoding='utf8',newline='\n')
    dump(OUT/'surface_patch_source_contract_review.json',{'created_utc':now(),'source_pin':c['software_source']['pin'],'archive_sha256':sha(archive),'sources':source_rows,
      'native_mapping':{'material_id':'IXS(1,1), homogeneous block as SRCOORK','nodes':'IXS(2:9,element)','parameter_start':'IPM(7,material)','EN_ET':'BUFMAT(start:start+1)','reference_area':'BUFLY(1)%LBUF(GP,1,1)%VOL set by SUSER43 at TIME=0 for Ismstr1','Gauss_shape':'SDEF43 columns: dominant node1,2,3,4','normal':'cross of SCOOR43 midface R and S; isotropic tangential stiffness needs only normal'},
      'actual_surface_assembler':'ASSEM_KII/ASSEM_KIJ, not ASSEMC routines; same triangular storage limitation confirmed at pinned ASSEM_KIJ lines1042 onward',
      'history_copy_sources_inspected_but_full_Newton_restore_order_not_qualified':True,
      'native_state_rollback_and_moving_geometry_qualified':False,'raw_AGPL_sources_not_published':True})
    review={'created_utc':now(),'target':TARGET,'source_sha256':hashlib.sha256(original_bytes).hexdigest(),'proposed_source_path':rel(source_path),'proposed_sha256':sha(source_path),'patch_path':rel(patch),'patch_sha256':sha(patch),
      'only_new_engine_file':TARGET,'new_routine_appended_in_existing_file':True,'no_build_system_change':True,'conditional':'IGTYP43 and MTN117 and Ismstr1 only',
      'fixed_format_new_code_columns_within_72':True,'matrix':'integral B^T[ET I+(EN-ET) n n^T]B dA over four reference-area Gauss points; active GP flags retained',
      'is_exact_Jacobian':False,'native_forces_and_damage_history_source_unchanged':True,'new_source_patch_applied':False,'compiled':False,'native_mechanical_pass_claimed':False,'requires_distinct_explicit_human_approval':True,
      'future_candidate_name':'a62_type43_surface_iteration_candidate','future_Engine_number':6,'future_build_cap_s':3600,'future_CPU':6,'GPU':False,'installation':False,
      'future_control_plan':['First elastic normal/shear/mixed implicit loaded witnesses with nodal reactions and fields, all fail on USER BREAK/empty histories.',
        'Then damaged cyclic/mixed witnesses with material state/rollback observation, equivalent native traction/work and unchanged physical gates; stop qualification if state staging fails.',
        'New binary regressions for explicit cohesive branch and TYPE7 implicit contact; bounded whole CHECK only after local gate, no long impact yet.'],
      'native_Engine_maximum_runs':12,'each_native_cap_s':180,'physical_budgets_or_criteria_changed':False,'old_Engines_and_failures_preserved':True,'whole_insertion_qualified':False,'objective1_complete':False}
    dump(OUT/'surface_patch_proposal_review.json',review)
    proposal=OUT/'proposition_correctif_surface_implicite.md'
    proposal.write_text('''# Proposition A61 — rigidité surfacique d’itération, sixième moteur isolé

Statut : préparé, non appliqué et non compilé. Cette modification n’est couverte par aucun accord moteur antérieur.

## Problème concret et modification

Le témoin TYPE43/LAW117 à hauteur nulle appelle correctement les forces surfaciques natives, puis échoue à T=0 dans la rigidité volumique S8ZKE3. Les nouveaux témoins explicites A60 qualifient la branche mixte déclarée, mais sa dérivée exacte est généralement non symétrique et l’assemblage natif ASSEM_KII/ASSEM_KIJ stocke un triangle. Insérer cette dérivée directement ou changer seulement le drapeau MUMPS serait incorrect.

Une seule nouvelle différence porte sur engine/source/elements/solid/solide8z/s8zke3.F : avant SRCOORK et les dérivées volumiques, TYPE43 + LAW117 + Ismstr1 appelle une nouvelle routine ajoutée au même fichier. Elle forme une matrice surfacique symétrique d’itération avec EN/ET natifs, les quatre aires de référence déjà conservées par SUSER43, les fonctions SDEF43 et la normale du plan moyen courant. Les points supprimés n’ajoutent plus de matrice. Les blocs suivent ASSEM_KII/KIJ ; les autres branches conservent leur code.

Cette matrice élastique est une approximation d’itération, pas la tangente cohérente d’adoucissement ou de géométrie. Le résidu de force, la loi, les états de dommage et l’énergie restent calculés par SUSER43/SIGEPS117. Aucune épaisseur fictive, modification de masse/matériau, terme RKE ou assouplissement d’un seuil physique. Les trois corrections déjà autorisées restent présentes dans le nouveau moteur ; les cinq anciens moteurs restent conservés.

## Préparation vérifiée et limites

44contrôles propres passent : aire uniforme/nonuniforme, reconstruction triangulaire, équilibre et translations nulles, rang12, spectre non négatif, changement de repère courant, exclusion des points supprimés, géométries invalides rejetées ; neuf résolutions à résidu mixte complet convergent au même équilibre avec états validés gelés. Une égalité bit à bit échouée reste archivée ; R1 utilise la tolérance matricielle1e-12 déjà déclarée, sans changement de seuil. Aucune compilation Fortran ni convergence native n’est revendiquée. Sources, lignes, empreintes, différence exacte et script de production sont sauvegardés. Le code source/différence AGPL reste hors des archives publiques MIT.

L’ordre natif de restauration des états Newton et l’objectivité des grandes rotations ne sont pas qualifiés. Le candidat n’altère pas les routines d’état existantes : les futurs témoins doivent vérifier leur comportement, et un échec bloque l’intégration. Les branches Ismstr autres que1 ne sont pas prises en charge par cette proposition. Un arrêt fermé code61 est prévu pour un agencement/une aire/un matériau non admissible ; il ne peut constituer un essai mécanique réussi.

## Exécution soumise à accord distinct

Appliquer exactement cette différence dans un sixième moteur isolé AIRCRAFT-A62, sources figées et trois anciens correctifs conservés. Estimation compilation5–15minutes, plafond absolu1heure, six CPU au maximum, sans GPU ni installation. Puis au maximum12 nouveaux contrôles Engine à un CPU et180s chacun : d’abord élastique implicite chargé, puis dommage/cycles/états, enfin régressions du nouveau binaire. Estimation des contrôles5–20minutes. Aucun impact de plusieurs heures lancé par cet accord.

Les critères initiaux et anciens échecs restent visibles. La meilleure fenêtre entière reste0,0200001220703125s ; la vidéo des dix premières secondes physiques n’existe pas encore. Après les contrôles natifs, l’intégration avion/façade restera conditionnée aux autres critères entiers déjà ouverts.
''',encoding='utf8')
    dump(OUT/'proposal_readability_review.json',{'created_utc':now(),'proposal':rel(proposal),'sha256':sha(proposal),'UTF8':True,'replacement_character_absent':'\ufffd' not in proposal.read_text(encoding='utf8'),'patch_and_proposed_source_outside_public_MIT_output':True,'not_applied_or_compiled':True})
    print(json.dumps({'surface_patch_prepared':True,'source_sha256':review['source_sha256'],'proposed_sha256':review['proposed_sha256'],'patch_sha256':review['patch_sha256'],'compiled':False}),flush=True)

if __name__=='__main__':main()
