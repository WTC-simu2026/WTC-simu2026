"""Seal AIRCRAFT-A01 delivery, preserve predecessors and route by human steering."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,csv,hashlib,json,shutil,struct,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a01'
BUILD=OUT/'verification_r2'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a01_predeclaration.json'
REPORT=OUT/'rapport_aircraft_a01.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A01_HANDOFF.md'
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def harness():
    r=subprocess.run(['C:/Program Files/PowerShell/7/pwsh.exe','-NoProfile','-Command','& ./harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json -Depth 6'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert r.returncode==0,r.stdout+r.stderr
    v=json.loads(r.stdout);assert v['Status']=='PASS';return v
def preservation():
    pins=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in pins if sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad;return len(pins)
def initialize():
    assert not OUT.exists();v=harness();assert v['CurrentIteration']=='IMPACT-I02I-L';OUT.mkdir()
    dump(OUT/'harness_before.json',v)
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    old=ROOT/'wtc1_simulation_v8/output/impact_i02i_deletion_ledger'
    files={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(old/name)['files']}
    # Pin the predecessor verification as well; old registry/state administration is intentionally snapshotted separately.
    for p in [old/'artifact_manifest.json',old/'publication_verification.json',ROOT/'wtc1_simulation_v8/data/impact_i02_geom.json',ROOT/'wtc1_simulation_v8/data/impact_i02a_structured_wing.json']:
        files[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(files.values())})
    manifest=read(ROOT/'wtc1_simulation_v8/input/aircraft_a01/source_manifest.json');p=ROOT/'wtc1_simulation_v8/input/aircraft_a01/767-200.dxf'
    manifest['configuration_material_reference']={'path':'wtc1_simulation_v8/data/impact_i02a_structured_wing.json','sha256':sha(ROOT/'wtc1_simulation_v8/data/impact_i02a_structured_wing.json'),'use':'static alloy constants only; no wing dynamics or NIST impact target'}
    manifest['CAD_notice']={'url':'https://www.boeing.com/commercial/airports/3-view','accuracy_statement_in_inches':6,'accuracy_statement_m':0.1524,'not_structural_schedule':True}
    dump(OUT/'source_manifest.json',manifest)
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'configuration':rel(CFG),'sha256':sha(CFG),'prior_registry_entries':v['RegistryEntries'],
        'criteria_declared_before_build':True,'outcome_fit_prohibited':True,'no_existing_damaged_state_modified':True})
    print(json.dumps({'initialized':True,'old_files_pinned':preservation(),'harness':v},indent=2))

def independent_mass_audit():
    # Read the exported spatial artifact independently of the builder and assemble its moments.
    rows=list(csv.DictReader((BUILD/'mass_quadrature_SI.csv').open(encoding='utf-8')))
    m=np.array([float(r['mass_kg']) for r in rows]);x=np.array([[float(r[k]) for k in ['x_m','y_m','z_m']] for r in rows])
    s=read(BUILD/'summary.json')['nominal'];total=sum(float(r['mass_kg']) for r in rows)
    cg=np.array([sum(float(r['mass_kg'])*float(r[k]) for r in rows)/total for k in ['x_m','y_m','z_m']]);d=x-cg
    inertia=np.array([[sum(m[n]*((float(d[n]@d[n])) if i==j else 0)-m[n]*d[n,i]*d[n,j] for n in range(len(m))) for j in range(3)] for i in range(3)])
    checks={'mass_matches_export':abs(total-s['total_kg'])/s['total_kg']<1e-10,'CG_matches_export':float(np.linalg.norm(cg-np.array(s['CG_m'])))<1e-9,
        'inertia_matches_export':float(np.linalg.norm(inertia-np.array(s['inertia_CG_kg_m2'])))/float(np.linalg.norm(inertia))<1e-10,
        'all_particle_masses_nonnegative':bool(np.all(m>=0))}
    result={'created_utc':now(),'pass':all(checks.values()),'checks':checks,'rows':len(rows),'mass_kg':total,'CG_m':cg.tolist(),'inertia_kg_m2':inertia.tolist(),'scope':'Saved CSV mass moments, no impact validation'}
    assert result['pass'];dump(OUT/'mass_export_audit.json',result);return result

def geometry_export_audit():
    mesh=read(BUILD/'airframe_mesh_SI.json');c=read(CFG);points=np.array(mesh['nodes_m']);p=BUILD/'B767_airframe_A01.glb';data=p.read_bytes()
    magic,version,size=struct.unpack_from('<III',data,0);nj,kind=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+nj]);nb,bkind=struct.unpack_from('<II',data,20+nj)
    blob=data[28+nj:28+nj+nb];a=doc['accessors'][0];v=doc['bufferViews'][a['bufferView']]
    coords=np.frombuffer(blob[v['byteOffset']:v['byteOffset']+v['byteLength']],dtype='<f4').reshape(-1,3)
    err=float(np.max(np.abs(coords[:len(points)]-points)));indices_ok=True
    for primitive in doc['meshes'][0]['primitives']:
        aa=doc['accessors'][primitive['indices']];vv=doc['bufferViews'][aa['bufferView']]
        ids=np.frombuffer(blob[vv['byteOffset']:vv['byteOffset']+vv['byteLength']],dtype='<u4')
        indices_ok &= len(ids)==aa['count'] and len(ids)%3==0 and int(ids.max())<len(coords)
    checks={'GLB_header':magic==0x46546c67 and version==2 and size==len(data) and kind==0x4e4f534a and bkind==0x004e4942,
        'positions_preserved_5micrometre':err<5e-6,'all_triangle_indices_valid':bool(indices_ok),
        'length_and_span_match_primary_dimensions':abs(float(points[:,0].max()-points[:,0].min())-c['envelope']['length']['value_m'])<1e-9 and abs(float(points[:,1].max()-points[:,1].min())-c['envelope']['span']['value_m'])<1e-9,
        'visual_only_explicit':doc['nodes'][0]['extras']['visualization_only'] and not doc['extras']['physical_impact_qualified'],
        'OEW_conversion_uses_original_units':read(BUILD/'summary.json')['nominal']['OEW_kg']==c['mass_hypotheses']['OEW_reference']['original_lb']*c['envelope']['lb_to_kg']}
    r={'created_utc':now(),'pass':all(checks.values()),'checks':checks,'maximum_GLBF32_position_error_m':err,'scope':'Export preservation and external dimensions only'}
    assert r['pass'];dump(OUT/'geometry_export_audit.json',r);return r

def prepare():
    assert not REPORT.exists();s=read(BUILD/'summary.json');assert s['all_declared_checks_pass'];count=preservation();a=independent_mass_audit();g=geometry_export_audit();c=read(CFG);n=s['nominal']
    tables='\n'.join(f"| {r['case']} | {r['total_kg']/1000:.3f} | {r['CG_m'][0]:.4f} | {r['unresolved_OEW_mass_kg']/1000:.3f} | {r['inertia_CG_kg_m2'][1][1]/1e6:.4f} |" for r in s['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A01 - Boeing complet : geometrie, topologie intacte et masses

Le 5 octobre 2026, Jeremy demande de construire l'avion complet et des conditions realistes sans forcer un resultat NIST. Le registre comptait119 entrees,22 dans la branche impact; les12 dernieres I02I-A a L etaient surtout des diagnostics locaux. AIRCRAFT-A01 quitte cette succession de microtests. I02I-M est **differee**, son plan conserve. A01 ne remplace ni ne requalifie les anciennes lois echouees.

Livrable concret : un fuselage complet, deux ailes avec caisson central, longerons, nervures et raidisseurs, empennages horizontal/vertical, deux moteurs equivalents et leurs attaches; maillage SI {n['nodes']}noeuds,{n['shells']}triangles,{n['beams']}poutres. La configuration, le maillage JSON, l'OBJ/GLB,l'apercu et la quadrature spatiale des masses sont sauvegardes dans verification_r2. Les cylindres de moteur dans OBJ/GLB sont visuels : seuls masse/inertie et pylones equivalents existent mecaniquement. Aucun moteur structurel lance en A01 : il reste a transferer ces masses au solveur sans perdre l'inertie, puis verifier le vol libre. Le maillage n'est pas declare pret a lancer un impact.

## 1. Faits directement transcrits

Les plans primaires [Boeing CAD](https://www.boeing.com/commercial/airports/3-view) et [D6-58328 RevK](https://www.boeing.com/content/dam/boeing/v2/airports/acaps/767_REV_K.pdf),PDF28/section2-8, donnent longueur159ft2in, envergure156ft1in, largeur16ft6in et hauteur de fuselage17ft9in. Conversion exacte :48,514m;47,5742m;5,0292m;5,4102m. Un dessin de planification n'est pas un plan de fabrication. Boeing annonce une precision indicative+/-6in=0,1524m pour les vues CAD; cela ne borne pas nos inconnues internes.

Dans le DXF, les extensions de cote x92,7878 et2002,7878 different de1910unites. La cote159ft2in confirme une unite en pouces. Origine du plan declaree x92,7878,y-637,838561; x vers l'arriere,y transversal,z vers le haut. Les contours d'aile selectionnes sont traces dans le JSON, pas interpretes comme positions de longerons. Les raccords, l'arrondi du bout et les stations retenues sont des approximations annoncees. Les anciennes geometries FR24 restent intactes et ne fournissent aucune raideur a A01.

PDF21/2-1 : OEW comprend structure,moteurs,equipements,amenagements,agents inutilisables et certains elements necessaires aux operations; il exclut carburant utilisable et charge utile. PDF23/2-3, les configurations types767-200ER ont OEW181130..181610lb; nous choisissons181130lb x0,45359237={n['OEW_kg']:.9f}kg. Ce n'est pas la pesee de N334AA. Les capacites de carburant utilisable publiees varient63216..91379L selon configuration. Aucun de ces maximums ne donne le carburant effectivement present a l'impact.

La page primaire [GE CF6](https://www.geaerospace.com/commercial/aircraft-engines/cf6) cite le CF6-80A sur767 et une longueur167in=4,2418m. Elle ne donne pas ici la masse ni la deformation interne; ces informations restent ouvertes. Un moteur equivalent de4500kg n'est pas un CF6-80A2 detaille valide.

## 2. Resultats de modeles officiels

**Aucun resultat NIST ne sert d'entree ni de cible dans ce nouveau constructeur.** La vitesse443mph, la masse totale, les dommages de facade et le remplacement NIST des moteurs par un PW4000 ne sont pas imposes. Les anciens sous-modeles bases sur des hypotheses/topologies NIST restent etiquetes comme tels, sans etre effaces. Le NIST pourra constituer une comparaison externe apres gel des conditions et calcul des sorties; aucun parametre ne devra etre reajuste pour supprimer un ecart observe. Modifier un parametre apres comparaison demandera une justification independante de l'ecart et une nouvelle iteration visible.

## 3. Affirmations des archives locales

Aucune nouvelle assertion issue de videos ou d'archives locales n'est examinee. Pas de rescan d'archive. {count} fichiers anterieurs sont epingles et verifies inchanges, y compris V11F froid,V11R et les diagnostics I02I. Les sources Boeing existantes sont lues sans modification; le DXF nouvellement acquis et son ZIP sont conserves avec hashes,copyright et exclusion de redistribution. Les extractions ciblees sont locales. La publication utilise une reconstruction parametrique propre et des liens, sans incorporer le CAD Boeing.

## 4. Hypotheses, proprietes, unites et histoire

Systeme SI :m,kg,s,N,J,Pa; inertieskgm2. Proprietes generiques statiques deja referencees :aluminium2024 rho2780kg/m3,E73,1GPa,nu0,33; aluminium7075 rho2810kg/m3,E71,7GPa,nu0,33. Attribuer ces alliages aux peaux et elements internes est une hypothese, pas une nomenclature Boeing. Lois **lineaires elastiques intactes seulement**; aucune limite de rupture,d'ecrasement ou de fissuration n'est calibree. La plasticite/fracture anterieure n'est pas transferee arbitrairement a cet avion.

Peaux fuselage2,54mm,aile3,175mm,empennage2mm; ames3,175mm; deux longerons a25%/65% de corde; cadres tous les~0,6m et24raidisseurs de fuselage. Ce sont des choix de premier assemblage. SectionsA,I,J des poutres explicites dansJSON; J=2I est une equivalence circulaire hypothetique, pas une section reelle certifiee. Pylones/attaches=equivalents elastiques sans rupture. La peau du fuselage continue aux intersections d'aile, sans decoupes portes/fenetres; elle peut surestimer certaines rigidites. Les moteurs sont des masses/inerties de cylindres equivalents; leur structure interne ne porte aucune resistance d'impact qualifiee. Aucun materiau deja endommage n'est modifie; neuf et sans energie de dommage.

Toutes les masses de structure sont rho x volume :coques rho*t*A,poutres rho*A*L. Quadrature3points sur triangles exacte jusqu'au degre2,2points sur poutres,8points sur boites et16points sur cylindres pour les moments du modele. Les poutres sont comptabilisees en lignes, sans inertie transversale de section : simplification explicite. CG=sum(m*r)/M; I=sum[m*((r-CG)^2*Id-(r-CG)tensor(r-CG))]. L'audit relit leCSV independamment du constructeur.

Masse vide=structure explicite+2moteurs+**reserve de masse vide non resolue**, puis masse totale=vide+carburant+charge utile. La reserve n'est pas ajoutee au vide une deuxieme fois. Elle inclut la structure manquante autant que les equipements,amenagements et elements d'exploitation. Sa distribution dans une boite fuselage est une hypothese; elle n'a **aucun credit de raideur cache**. Ajuster cette reserve conserve une enveloppe de masse publiee et expose l'incompletude; les epaisseurs ne sont pas ajustees pour atteindre cette enveloppe ou un degat. Si la structure depasse le budget, le cas est rejete.

Carburant nominal30000kg,densite800kg/m3 :scenario arrondi propre, pas reconstruction AA11; sensibilites20000/40000kg. Distribution symetrique proportionnelle au volume geometrique du caisson entre25%/65% de corde,jusqu'a75% de la demi-envergure,caisson central inclus. Pas de sloshing ni pression. La capacite geometrique hypothetique={n['geometric_tank_capacity_kg']:.1f}kg et le remplissage nominal={n['tank_uniform_fill_fraction']:.5f}; la capacite Boeing depend de la configuration et n'est pas ajustee pour coïncider. Charge utile nominal10000kg,boite cabine,variations5000/15000kg. Epaisseurs peaux x0,7/x1,3; distribution de la reserve translatee de-3/+3m. Pas de probabilites attribuees a ces9scenarios.

## 5. Resultats derives et controle energetique

Nominal :structure explicite{n['structure_mass_kg']/1000:.3f}t,moteurs9t,reserve vide{n['unresolved_OEW_mass_kg']/1000:.3f}t ({100*n['unresolved_OEW_fraction']:.1f}% du vide),carburant30t,charge10t,total{n['total_kg']/1000:.3f}t. CG=({n['CG_m'][0]:.5f},{n['CG_m'][1]:.3e},{n['CG_m'][2]:.5f})m. Ces valeurs caracterisent nos distributions, pas le centre de gravite mesure de l'avion historique.

| Scenario | Masse totale (t) | CG x (m) | Vide non resolu (t) | Iyy (millions kg m2) |
|---|---:|---:|---:|---:|
{tables}

Les{n['quadrature_particles']}points de masse reproduisent le bilan a erreur relative{n['mass_relative_error']:.3e}. {s['checks_passed']}/{s['checks_total']}criteres declares passent, plus4/4controles de relecture des masses et6/6controles d'export geometrique/conversion. Connexite,absence d'aires nulles exportees,symetrie de masse,inertie positive et capacite conditionnelle controlees. L'erreur maximale des positions float32GLB={g['maximum_GLBF32_position_error_m']:.3e}m. Maillage double :variation de masse structure{100*s['coarse_fine_structure_mass_relative_difference']:.4f}%,norme d'inertie{100*s['coarse_fine_inertia_relative_norm_difference']:.4f}%,seuils2% declares avant calcul. Ces tests verifient cette construction numerique, pas les proprietes reelles de l'avion.

Premiere execution r0 conservee au niveau racine :57/66criteres,neuf echecs de symetrie de masse. Le decoupage identique des quadrilateres gauchis sur les deux ailes ne refletait pas la diagonale physique et introduisait unCG transversal~1,3e-7m. Correction r1 :diagonales en miroir. Aucun seuil,propriete,masse cible ou resultat externe modifie; ancien script preserve dans development_r0. Ces neuf echecs r0 restent visibles. r2 conserve egalement r1 et corrige une erreur arithmetique de3e-6kg dans la conversion decimale predeclaree d'OEW : calcul direct181130lb x0,45359237. Le champ original errone reste dans la configuration immuable et la difference est affichee dans chaque bilan. Ce n'est pas un changement de masse physique pour ajuster une sortie. L'apercu r2 utilise la meme echelle sur les deux axes du plan et exporte des cylindres moteur visuels.

Dans cet etat neuf non sollicite,Uelastique=0 et energie de dommage=0 par definition. Aucune reaction ou collision calculee. A titre inertiel seulement, une translation uniforme a200m/s donnerait KE=0,5*M*v²={n['energy_if_uniform_translation_200_m_s_J']/1e9:.6f}GJ, vitesse ronde hypothetique **non attribuee a AA11**. Aucun bilan d'absorption/ejection/incendie n'est encore produit. Reactions,travail interne et repartition energetique d'impact devront venir des sorties mecaniques futures, jamais d'une animation imposee.

## 6. Contradictions et donnees manquantes

La fraction importante de vide non resolu montre exactement pourquoi ce premier Boeing n'est pas encore un modele de resistance d'impact complet. Le plan de chargement,le CG,l'etat de carburant et la configuration specifique ne sont pas etablis. Les epaisseurs,sections,pylones,fixations,moteur interne et lois a grande deformation restent incomplets. Le maillage ferme visuellement n'est pas une preuve de fidelite mecanique. La masse de coque et les inerties convergent pour les hypotheses actuelles; elles ne permettent pas d'identifier les inconnues.

A02 :transfert de masses/inerties au solveur,orientation locale des poutres et controle de l'avion intact en vol libre court; recherches primaires ciblees sur les inconnues qui dominent les charges/rigidites. Ensuite un impact de l'avion entier sur facade representative, avec plage de vitesse/attitude declaree avant observation des degats. Des mailles plastiques non physiques,une energie non conservee ou une fracture non calibree resteront des echecs affiches. Ne pas repousser indefiniment l'assemblage complet pour finir tous les microtests :I02I-M reste disponible si un blocage concret de la loi exige son execution.

Preserver les echecs E/F/G/I/J,L,convention NASA et Gf30hypothetique; aucune propagation physique qualifiee. V11F froid conserve,V11R versV11S differee. Localisation en flexion apres fracture complete non validee; temperature imposee n'est pas un incendie calcule. Aucun effondrement historique valide. Blender/OBJ/apercu restent des visualisations de la configuration, sans animation d'impact forcee.

## Reproduction et passation

Configuration et garde declarees avant construction; graine1102026,aucun tirage. Construction{ s['runtime_seconds']:.3f}s,zéro moteur; lecture seule des anciens calculs. Ne pas relancer inutilement :complete_aircraft_a01.py verify verifie les sorties sauvegardees. Dans un dossier neuf, utiliserles scripts avec les sources ciblees referencées; ne jamais ecraser A01.

AIRCRAFT-A02 est la prochaine route; passation WTC1_AIRCRAFT_A01_HANDOFF.md. Publication cadence2iterations :L+A01 apres verification. Aucune publication X n'est autorisee dans ce travail.
''',encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# Passation compacte - AIRCRAFT-A01 vers A02

Lire AGENTS.md puis harness/state.json(prioritaire) et cette passation. Jeremy a recentre le5octobre2026 sur le Boeing complet et des conditions sans forcer NIST; I02I-M differee, son plan ancien intact. Registre120 apres A01; avant119 dont22 impact et12 microdiagnostics I02I-A..L.

A01 :configuration aircraft_a01_predeclaration.json; sorties aircraft_a01,rapport et B767_assemblage_A01.png. Fuselage,deux ailes/caisson central,longerons,nervures,raidisseurs,empennages,deux moteurs/pylones equivalents; {n['nodes']}noeuds,{n['shells']}coques,{n['beams']}poutres. Intact elastique hypothetique,aucune dynamique complete ni loi d'ecrasement/fracture qualifiee. Pas encore un deck solveur. SourcesprimairesBoeingCAD+ACAPp21/23/28+GE; sourceslocaleslectureseule/excluespub.

Nominal :M={n['total_kg']:.6f}kg,structure={n['structure_mass_kg']:.6f}kg,vide nonresolu={n['unresolved_OEW_mass_kg']:.6f}kg,moteurs9000kg,fuel30000kg,charge10000kg. Reserve vide inclut structure manquante autant qu'equipements; pas de raideur cachee. CG={n['CG_m']}; massesCSV/inertieexacte pourgeometrieapprochee.9scenarios,checks{s['checks_passed']}/{s['checks_total']},export4/4,raffinementstructure{100*s['coarse_fine_structure_mass_relative_difference']:.4f}%,inertie{100*s['coarse_fine_inertia_relative_norm_difference']:.4f}%. Ce n'est pas une pesee/CG historique. Aucun ancien solveur relance,{count}anciens fichiersepingles. Verifier via complete_aircraft_a01.py verify.

A02 concret :exporter masses coherentes et inerties sans les remplacer par un unique projectile rigide; orienter poutres; vol libre intact court et bilan masse/energie/moment. Preciserd'abordles inconnuesdominantes sursourcesprimaires. Puis avionentier/facade representative avec conditionsvitesse/attitude declarees et gammeplausible, pas de cibledegatsNIST. Limitesjointsmoteurs/structures manquantes etfracnoncalibree restentvisibles. Ne pas replonger automatiquement dans M.

NISTcomparaisonsepareeapresgel,aucun ajustementpourrejoindreunresultat. GarderV11F/V11R/V11S,tous échecsI02I etplanM. Grande deformation/fracturephysique/feu/effondrement nonvalides; Blender visualisation. PublicationL+A01dueapresaudit,cadenceactuelle a lire; aucunpostX ni actionYoremi.
''',encoding='utf-8',newline='\n')
    dump(OUT/'release_audit.json',{'created_utc':now(),'pass':True,'old_files_preserved':count,'mass_export_audit':a,'geometry_export_audit':g,'harness':harness(),'scope':s['scope']})
    scripts=[ROOT/'wtc1_simulation_v8/scripts'/name for name in ['intake_aircraft_a01.py','read_aircraft_a01_dxf.py','build_aircraft_a01.py','complete_aircraft_a01.py']]
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,HANDOFF]+scripts
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(paths))],
        'excluded_mutable':['artifact_manifest.json self','publication_verification.json','administration harness/state.json, registry and cadence'],
        'source_documents_public_redistribution':False})
    print(json.dumps({'prepared':True,'old_files_preserved':count,'mass_export_checks':a['checks']},indent=2))

def register():
    assert REPORT.exists() and HANDOFF.exists();assert not (OUT/'publication_verification.json').exists();count=preservation();s=read(BUILD/'summary.json');assert s['all_declared_checks_pass']
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        assert sha(ROOT/'harness'/name)==sha(OUT/('before_'+Path(name).name)),('Concurrent administration',name)
    state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');assert state['current_iteration']=='IMPACT-I02I-L' and cycle['pending_iterations']==['IMPACT-I02I-L']
    when=now();status='completed_whole_aircraft_parametric_intact_assembly_and_conditional_mass_ledger'
    record={'experiment_id':'WTC1-AIRCRAFT-A01','registered_at':when,'status':status,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(BUILD/'summary.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
        'source_manifest':rel(OUT/'source_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),
        'checks_passed':s['checks_passed'],'checks_total':s['checks_total'],'cases':s['cases_count'],'mass_export_checks':4,'geometry_export_checks':6,
        'old_files_preserved':count,'runtime_seconds':s['runtime_seconds'],'solver_jobs':0,'NIST_results_used_as_target':False,
        'aircraft_impact_qualified':False,'whole_aircraft_mass_mapping_to_solver_validated':False,'whole_aircraft_deformation_qualified':False,
        'user_reoriented_from':'IMPACT-I02I-M','next_iteration':'AIRCRAFT-A02'}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A01',current_status=status,next_iteration='AIRCRAFT-A02',next_objective=read(CFG)['next_objective'],updated_at=when)
    state['aircraft_a01_key_results']=record
    state['user_steering_2026_10_05']={'instruction':'Build complete aircraft, conditions rather than outcome-fitting; NIST discrepancy must not be forced away',
        'deferred_iteration':'IMPACT-I02I-M','preserved_plan':'wtc1_simulation_v8/data/impact_i02i_m_plan_from_l.json','next':'AIRCRAFT-A02',
        'outcome_calibration_allowed':False,'microtests_only_when_concrete_model_blocker':True}
    state['validated_artifacts'].update(aircraft_a01_report=rel(REPORT),aircraft_a01_results=rel(BUILD/'summary.json'),aircraft_a01_handoff=rel(HANDOFF),
        aircraft_a01_mesh=rel(BUILD/'airframe_mesh_SI.json'),aircraft_a01_mass_csv=rel(BUILD/'mass_quadrature_SI.csv'),aircraft_a01_preview=rel(BUILD/'B767_assemblage_A01.png'))
    cycle.update(pending_iterations=['IMPACT-I02I-L','AIRCRAFT-A01'],pending_count=2,next_publication_after='L+AIRCRAFT-A01 after A01 verified; user reoriented Boeing whole assembly',updated_at=when)
    dump(ROOT/'harness/publication_cycle.json',cycle);dump(ROOT/'harness/state.json',state);verify(write=True)

def verify(write=False):
    old=read(OUT/'before_state.json');state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');cfg=read(CFG);s=read(BUILD/'summary.json');v=harness()
    m=read(OUT/'artifact_manifest.json');bad=[r['path'] for r in m['files'] if sha(ROOT/r['path'])!=r['sha256']];count=preservation()
    reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();suffix=reg[len(prefix):].decode('utf-8').splitlines()
    protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy','open_limitations']
    checks={'new_artifact_hashes':not bad,'predecessors_unchanged':True,'predeclared_configuration':sha(CFG)==read(OUT/'declaration_guard.json')['sha256'],
        'registry_prefix_unchanged':reg.startswith(prefix),'one_new_record':len(suffix)==1 and json.loads(suffix[0])['experiment_id']=='WTC1-AIRCRAFT-A01',
        'state_route_A01_to_A02':state['current_iteration']=='AIRCRAFT-A01' and state['next_iteration']=='AIRCRAFT-A02',
        'prior_science_limits_preserved':all(old[k]==state[k] for k in protected),'M_plan_preserved_and_deferred':state['user_steering_2026_10_05']['deferred_iteration']=='IMPACT-I02I-M',
        'cadence_two_pending_or_verified_publication':cycle['pending_iterations']==['IMPACT-I02I-L','AIRCRAFT-A01'] or (cycle['pending_iterations']==[] and cycle['last_published_iteration']=='AIRCRAFT-A01'),
        'new_mass_and_mesh_checks_pass':s['all_declared_checks_pass'] and read(OUT/'mass_export_audit.json')['pass'] and read(OUT/'geometry_export_audit.json')['pass'],
        'NIST_outcomes_not_used':not s['NIST_results_used_as_target'] and not cfg['outcome_calibration']['allowed'],
        'physical_limits_explicit':not s['aircraft_impact_qualified'] and not s['whole_aircraft_mass_mapping_to_solver_validated'] and not s['whole_aircraft_deformation_qualified'],
        'zero_old_solver_reruns':s['solver_jobs']==0 and not s['old_solver_rerun'],'harness_pass':v['Status']=='PASS'}
    sources=read(OUT/'source_manifest.json');checks['source_hashes']=all(sha(ROOT/r['path'])==r['sha256'] for r in sources['sources']+sources['extracted_files'])
    result={'created_utc':now(),'pass':all(checks.values()),'checks':checks,'manifest_files_checked':len(m['files']),'old_files_checked':count,
        'harness':v,'registry_entries':v['RegistryEntries'],'configuration_declared_before_build':True,
        'scientific_checks':f"{s['checks_passed']}/{s['checks_total']}",'mass_export_checks':'4/4','geometry_export_checks':'6/6','physical_impact_qualified':False,
        'next_iteration':'AIRCRAFT-A02','github_pending_iterations':cycle['pending_count']}
    assert result['pass'],result
    if write:dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['initialize','prepare','register','verify']);args=ap.parse_args();globals()[args.action]()
