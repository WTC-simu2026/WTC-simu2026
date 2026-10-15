"""Save the reviewed proposal addendum without overwriting its first preparation."""
from pathlib import Path
import json,hashlib

HERE=Path(__file__).resolve().parent
OUT=HERE/'witness_preparation'
ROOT=HERE.parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,x):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(x if isinstance(x,str) else json.dumps(x,indent=2,ensure_ascii=True)+'\n')

def main():
    c=json.loads((OUT/'configuration_A81_proposed.json').read_text())
    a=json.loads((ROOT/'wtc1_simulation_v8/data/aircraft_a67_controls.json').read_text())
    c['status']='prepared_no_native_requires_separate_human_authorization'
    c['inherits_A67_acceptance_formulae']=a['acceptance']
    c['physical_gates_separate_from_observation']['same_energy_and_momentum_formulae']=True
    c['physical_gates_separate_from_observation']['no_constant_1e_minus5_J_threshold_inferred_from_elastic_report']=True
    c['mode_I_eligibility_gate']={
      'reason_XY_not_prescribed':'Preserve genuinely free unknown translations as in the known implicitA67 witness; all-prescribed unknown-space case is not qualified.',
      'maximum_absolute_XY_displacement_mm':a['extra_analytical_displacement_tolerance_mm'],
      'maximum_four_nodal_Z_jump_spread_mm':a['extra_analytical_displacement_tolerance_mm'],
      'maximum_current_Gauss_area_relative_change':1e-6,
      'maximum_shear_stress_MPa':a['acceptance']['junction_state_absolute']+a['acceptance']['junction_state_relative']*450,
      'if_any_gate_fails':'Do not compare with pure-modeI closed-form failure0.22222mm; record observation and preserve failed qualification. No correction/rerun within the lot.'}
    c['material_default_limit']={
      'Imass1_Idel4_Irupt1_Ismstr4':'Explicit card fields equal currentA79 andA67 numerically.',
      'short_card_CritType1_EvoShape1_ISYM0':'Related pinned reader/cfg defaults; WindowsStarter source identity not assumed. Native outputs must establish the constitutive branch, using active parameter print if available plus initiation/failure/USR9/USR12/stress histories. If unobservable mark branch unqualified.',
      'source_reader':'starter/source/materials/mat/mat117/hm_read_mat117.F:141-159,211-240,315-336',
      'source_model':'engine/source/materials/mat/mat117/sigeps117.F:175-189,362-381,455-467',
      'cfg_defaults':'hm_cfg_files/config/CFG/radioss2612/MAT/mat117.cfg:77-84'}
    c['contact_feature_decision']={
      'WAITING_until_full_nominal_gap_exit_retained':False,
      'counterexample':'For current pure-modeI linear branch rupture0.222222mm<0.3mm<0.5mm. A failed seam can reclose without a full envelope exit; geometric-only waiting would never arm. Must observe compression and deletion before designing any feature.',
      'no_implicit_gap_change_or_global_deactivation':True,
      'uncertified_initial_pair':'Retain ordinary ARMED contact treatment and reject the preparation if overlap persists; never WAITING based only on coincidence.'}
    c['native_result_interpretation']={
      'observation_success':'A clean bounded launch and complete actual histories with qualified variables and target state; independent of whether cohesion persists after failure.',
      'physical_result':'Measure intact compression versus analytic linear branch and residual compression after element deletion, with force/energy balance and unchanged material parameters.',
      'contact_result':'No general contact exists. No contact response, recontact adequacy or whole-impact qualification can be inferred.',
      'null_USR':'Missing or unpopulated zero user-history fields are an observation failure, not zero damage.',
      'deleted_fields':'Do not mistake disappearing/reset fields after OFF0 for healing.'}
    final=OUT/'configuration_A81_final.json';save(final,c)
    save(OUT/'proposition_A81_compression_rupture_refermeture.md', '''# Proposition A81 — observer la compression et la refermeture du joint

## Décision A80
L'attente d'un contact jusqu'à sa première sortie complète du gap nominal n'est pas retenue comme correctif. Avec la carte cohésive actuelle, la formule de mode I linéaire donne un début de dommage à 450/4400 ≈ 0,10227 mm et une rupture à 2×50/450 ≈ 0,22222 mm. Une ouverture de 0,3 mm peut ainsi rompre le joint sans sortir d'un gap de 0,5 mm. Sa refermeture pourrait alors manquer de réaction. Il faut mesurer ce point avant un développement logiciel transversal.

Ces nombres sont des résultats dérivés sous une branche constitutive donnée, non une observation du binaire ni une propriété mesurée d'un assemblage d'avion. Les défauts de la carte courte doivent être confrontés aux sorties natives. A67 qualifiait un domaine élastique limité; dommage, suppression et retour après rupture restent ouverts.

## Un seul témoin proposé
Le témoin reprend la géométrie native connue A67 FREE_Ismstr4 : deux faces carrées superposées de 10×10 mm, huit nœuds distincts et un élément TYPE43. Les lignes numériques LAW117/TYPE43 sont identiques à A79 : EN4400, ET800, TN450, TT100, GI/GII50; Imass1, Idel4, Irupt1, Ismstr4 et épaisseur vraie0. Aucun lien avec la géométrie nœud–facette A79 n'est introduit dans ce coupon.

La face inférieure est fixée. Le déplacement normal Z de la face supérieure suit une compression−0,05 mm, un retour0, une ouverture+0,3 mm, puis une refermeture−0,05 mm. Des paliers et des transitions quintiques échantillonnées sont tabulés dans les entrées. Le trajet finit à0,65 ms. X/Y restent libres afin de conserver des inconnues dynamiques comme dans la trame implicite déjà vérifiée; la validité du mode I exige donc déplacements transverses et cisaillements négligeables, quatre sauts normaux uniformes et aire constante.

La vitesse initialeY de la trame A67 est supprimée. Aucun contact général n'est défini afin d'isoler la cohésion. Les huit masses instrumentales de1g sont conservées dans ce coupon indépendant; aucune masse de la scène entière n'est compensée. Les unités restent g/mm/ms, forceN et énergieN·mm convertie enJ par0,001. Graine1102092, zéro tirage.

## Enregistrement et critères
Moteur A73 et Starter Windows inchangés, vérifiés par empreinte. Newmark et les tolérances sont conservés. Le pas plafond est0,000125 ms, comme A67; le minimum est fixé à la même valeur : toute réduction nécessaire arrête le témoin et sera un échec conservé. Les historiques et champs sont demandés tous les demi-pas, environ5200 pas jusqu'à la cible, et le RUN va jusqu'à0,6500625 ms pour sauvegarder la frontière réelle.

Sont demandés : mouvements et réactions des huit nœuds, accélérationZ, énergies de la pièce et globales, étatOFF, contraintes et variables de matériau (saut, maximum historique, dommage, traction, seuils). La disponibilité et le peuplement réels des sortiesUSR restent à vérifier; leurs zéros ou absences ne seront jamais assimilés à un dommage nul. Les sorties de champ doublent les historiques. Une sortie manquante, une référence non qualifiée, une erreur ou un avertissement non classé empêche de déclarer l'observation complète.

Les critères de mesure sont séparés des critères physiques : réactions de la base fixe pour l'effort cohésif, inertie du déplacement imposé identifiée avec les accélérations, bilan action/réaction/impulsion et travail extérieur/énergie. Les formules de seuils A67 restent inchangées dans la configuration. L'aire et les quatre sauts seront contrôlés avant d'utiliser la formule puremodeI. La réaction en compression après rupture sera mesurée, non supposée. Une fin normale ne qualifie pas le comportement physique. L'absence de contact dans le coupon ne valide aucun contact futur.

## Autorisation distincte demandée, aucun lancement effectué
Maximum deux processus natifs : un Starter, puis un seul Engine si la préparation passe. Un CPU, plafond180s chacun, estimation totale1–5minutes. Sans correctif, compilation, GPU, installation ni prolongement d'impact entier. Tout lancement, même échoué ou expiré, consomme sa place; aucun remplacement automatique. Si le Starter échoue, l'Engine conditionnel reste inutilisé. Les budgets et échecs A75/A77/A79 sont conservés.

Les cartes exactes, la configuration finale et les vérifications statiques sont présentes. Aucun calcul A81 n'est autorisé par cette préparation. Les dix secondes physiques et la vidéo3D de l'impact entier restent incomplètes.

Références primaires : [LAW117](https://help.altair.com/2024/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm), [TYPE43](https://2025.help.altair.com/2025/hwsolvers/rad/topics/solvers/rad/prop_type43_connect_starter_r.htm), [sorties BRICK](https://2024.help.altair.com/2024/hwsolvers/rad/topics/solvers/rad/anim_brick_restype_engine_r.htm). Les sources épinglées éclairent les branches logicielles sans établir l'identité du Starter Windows.
''')
    v=json.loads((HERE/'pair_lifecycle_specification_v2.json').read_text())
    v['status']='design_path_not_retained_pending_cohesive_gate'
    v['state_policy']['eligibility']='Only certified cohesive-neighbour initial pairs could be WAITING. Uncertified pairs remain ARMED with ordinary contact and cause preparation failure if overlapping.'
    v['state_policy']['retained_for_implementation']=False
    v['state_policy']['stop_reason']='A0.3mmopening may fail currentLAW117 before0.5mmgapexit. Pure geometric waiting cannot guarantee recontact after rupture and partial opening; do not implement it as proposed.'
    v['optional_unchanged_engine_witness']=c
    v['correction_to_previous_research_labels']='The constitutive law is LAW117 with propertyTYPE43; references toLAW43 in earlier research JSONs were imprecise and are superseded.'
    v['source_state_points']=[
      {'path':'common_source/modules/interfaces/intbufdef_mod.F90','lines':[1042,1231,1543],'role':'buffer type, initialpenetration sizing andCAND_P storage'},
      {'path':'starter/source/interfaces/intbuf/intbuf_ini_starter.F','lines':[765,1951],'role':'exampleTYPE7 buffer sizing andallocation; full branch not patched'},
      {'path':'common_source/interf/copy_intbuf_tab.F','lines':[106,110,713,715],'role':'state copies require new-field propagation'},
      {'path':'common_source/interf/intbuf_ini.F','lines':[402,1550,1553],'role':'restart size table, allocation andREAD_DB'},
      {'path':'engine/source/output/restart/write_intbuf.F','lines':[397,1107,1108],'role':'restart size table andWRITE_DB'},
      {'path':'engine/source/interfaces/int07/i7ke3.F','lines':[400,514,573],'role':'implicit activepair preparation before force andmatrix'},
      {'path':'engine/source/interfaces/int07/i7dstk3.F','lines':[352,393,396],'role':'implicit distancepair selection andCAND_P reset'},
      {'path':'engine/source/interfaces/intsort/i7sto.F','lines':[95,97,145,195],'role':'paircandidate sorting andinitialization'},
      {'path':'engine/source/interfaces/int07/i7for3.F','lines':[722,731,741,751],'role':'force-side initialgapcorrection'},
      {'path':'engine/source/implicit/imp_int_k.F','lines':[146,216,305],'role':'existingTYPE7 matrixcalls; exactnewstatecommit hook unresolved'}]
    v['future_development_cost']='At least Starter input/state, shared allocation/copies/read/write format, sorting, implicit force/matrix, rollback/acceptedcommit and restart. Not a small engine-only repair; no diff ready or build estimate claimed.'
    save(HERE/'pair_lifecycle_specification_v3.json',v)
    manifest=[{'path':str(p.relative_to(HERE)).replace('\\','/'),'sha256':sha(p)} for p in sorted(OUT.glob('*')) if p.is_file()]
    save(OUT/'final_preparation_manifest.json',{'files':manifest,'native_started':0,'source_modification':False,'compiled':False,'prepared_static_only':True})
    print(json.dumps({'A81_prepared':True,'native_started':0,'configuration':final.name,'WAITING_full_gap_exit_retained':False}))

if __name__=='__main__':main()
