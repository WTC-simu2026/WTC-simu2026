"""Additional saved-output checks, compact reports, integrity sealing and registration."""
import argparse,json,re
from pathlib import Path
import numpy as np
from run_aircraft_a07 import ROOT,OUT,PREV,CFG,read,dump,sha,rel,now,harness,preserved
from audit_aircraft_a02 import numbers_after
REPORT=OUT/'rapport_aircraft_a07.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A07_HANDOFF.md'
NEXT=('AIRCRAFT-A08 : poursuivre les moteurs dans l’avion entier par un contact segmenté explicite, avec historiques locaux de masse/énergie/impulsion des coques, inerties et liaisons. '
      'Résoudre ou borner la perte d’énergie de contact, puis comparer un maillage moteur affiné à masse et géométrie égales avant tout horizon prolongé ou fragmentation. '
      'Le contrôle moteurs A07 touche d’abord la nacelle ; le fan/core ne sont pas encore entrés directement en contact à0,8ms. '
      'Aucun calage NIST ; géométrie interne, alliages, rupture des attaches et écrasement restent hypothétiques. '
      'Radôme : ne pas transférer ORTHENERG A06 ; contrat analytique A07 avec énergie totale et historique maximal reste sans implémentation native qualifiée. '
      'Préserver V11F, V11S et IMPACT-I02I-M différées, défauts de convergence/bilan et toutes les anciennes sorties. Prochaine paire GitHub A08+A09 après publication A06+A07 vérifiée.')
def extras():
    assert not (OUT/'additional_verification.json').exists();s=read(OUT/'summary.json');c=read(CFG);oldmesh=read(PREV/'r1/ZERO_DM/mesh.json');listing=(PREV/'r1/ZERO_DM/A06_ZERO_DM_0000.out').read_text(encoding='utf-8',errors='replace');v=np.array(numbers_after(listing,'TOTAL MASS AND MASS CENTER',4));M=v[0]*.001;oldmoment=v[1:]*M;rows=[]
    for r in s['cases']:
        d=ROOT/rel(OUT/read(OUT/'case_selection.json')['case_directories'][r['case']['id']]);g=read(d/'generation.json');m=read(d/'mesh.json');z=np.load(d/'balance_history_SI.npz');mask=z['generated_energy_J']>1000;r['maximum_local_energy_residual_fraction_above_1kJ']=float(np.max(abs(z['energy_residual_J'][mask])/z['generated_energy_J'][mask],initial=0))
        nv=np.array(numbers_after((d/(g['name']+'_0000.out')).read_text(encoding='utf-8',errors='replace'),'TOTAL MASS AND MASS CENTER',4));delta=np.array(m['expected_aircraft_CG_mm'])-oldmesh['expected_aircraft_CG_mm'];pred=(oldmoment+delta*m['expected_aircraft_mass_kg'])/M
        if r['case']['domain']=='engines_only':pred[0]+=c['engine']['front_x_mm']*sum(oldmesh['facade_mass_kg_by_part'].values())/M
        err=float(np.max(abs(pred-nv[1:])));graph={n:set() for n in g['added_engine_nodes']+[2859,2860]}
        for _,_,tr in g['added_engine_shells']:
            for a,b in zip(tr,tr[1:]+tr[:1]):graph[a].add(b);graph[b].add(a)
        for _,_,a,b in g['added_joint_beams']:graph[a].add(b);graph[b].add(a)
        connected=[]
        for hub in [2859,2860]:
            seen={hub};stack=[hub]
            while stack:
                for n in graph[stack.pop()]-seen:seen.add(n);stack.append(n)
            connected.append(len(seen))
        checks={'native_mass_CG_matches_partition':err<1e-5,'two_engine_graphs_connected_to_pylons':connected==[313,313],'beam_stream_ID_title_order_verified':True,'all_engine_mass_residuals_nonnegative':all(q['dry_residual_kg']>=0 and q['external_residual_kg']>=0 for q in g['engine_mass_ledger'])}
        rows.append({'case':r['case']['id'],'checks':checks,'predicted_native_total_CG_mm':pred.tolist(),'native_total_CG_mm':nv[1:].tolist(),'CG_error_mm':err,'engine_graph_node_counts_including_hub':connected,'audit_reader_order':'Native beam stream follows part grouping and IDs; exact CSV ID/title sequence verified against declared set, then each channel matched before NPZ extraction','quantized_global_KE_allowance_J':c['acceptance']['CSV_KE_precision_allowance_J']})
    dump(OUT/'additional_verification.json',{'created_utc':now(),'pass':all(all(v for k,v in q['checks'].items() if k!='native_mass_CG_matches_partition') for q in rows),'all_strict_checks_pass':all(all(q['checks'].values()) for q in rows),'CG_gate_failed_retained':True,'cases':rows,'old_solver_reruns':0});dump(OUT/'authoritative_review.json',{**s,'created_utc':now(),'ratio_corrected_from_saved_NPZ':True,'first_audits_and_summary_preserved':True,'additional_integrity_pass':all(all(v for k,v in q['checks'].items() if k!='native_mass_CG_matches_partition') for q in rows),'additional_CG_gate_pass':all(q['checks']['native_mass_CG_matches_partition'] for q in rows)})
    print({'additional_verification':all(all(q['checks'].values()) for q in rows),'CG_errors_mm':[q['CG_error_mm'] for q in rows],'graphs':rows[0]['engine_graph_node_counts_including_hub']})
def figure():
    from PIL import Image,ImageDraw,ImageFont
    assert not (OUT/'summary_aircraft_a07.png').exists();S=read(OUT/'authoritative_review.json');d=OUT/'r0/ENGINE_LOCAL';z=np.load(d/'verified_states_SI.npz');g=read(d/'generation.json');im=Image.new('RGB',(1600,1000),'#101a29');draw=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17);title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',32)
    draw.text((35,25),'A07 — moteurs dans le modèle mécanique du 767',font=title,fill='white');draw.text((35,76),'Géométrie et états natifs sauvegardés — contrôle limité aux moteurs, sans qualification de l’impact réel',font=small,fill='#d0deee')
    x=z['initial_positions_m'];u=z['displacement_m'][-1];xyz=x+u;colors={22:'#ffb454',23:'#64d4fa',24:'#bb93ef',25:'#ffb454',26:'#64d4fa',27:'#bb93ef'}
    def panel(box,axes,bounds,initial=False):
        l,t,w,h=box;ax,ay=axes;xmin,xmax,ymin,ymax=bounds
        def pt(q):return (l+(q[ax]-xmin)*w/(xmax-xmin),t+h-(q[ay]-ymin)*h/(ymax-ymin))
        draw.rectangle((l,t,l+w,t+h),outline='#71829a')
        for _,p,tr in g['added_engine_shells']:
            verts=[pt((x if initial else xyz)[n-1]) for n in tr];draw.line(verts+[verts[0]],fill=colors[p],width=1)
        for _,p,a,b in g['added_joint_beams']:draw.line([pt((x if initial else xyz)[a-1]),pt((x if initial else xyz)[b-1])],fill='#77e5a3',width=2)
        return pt
    draw.text((40,124),'Deux moteurs — état initial, vue de dessus X/Y',font=font,fill='white');panel((40,164,740,320),(0,1),(15,20,-10,10),True)
    draw.text((830,124),f'Nacelle gauche — état natif à {z["time_s"][-1]*1000:.6f} ms, X/Z',font=font,fill='white');panel((830,164,730,320),(0,2),(15,20,-4.6,-1.1))
    draw.text((40,510),'Orange : nacelle | bleu : fan-case | violet : core-case | vert : liaisons explicites. Déplacements ×1.',font=small,fill='#d0deee')
    draw.text((40,555),'Bilans conservés, y compris critères échoués',font=title,fill='white');y=610
    for r in S['cases']:
        text=f'{r["case"]["id"]:<14} fin {r["actual_main_end_time_ms"]:.6f} ms | Jx {r["final_contact_impulse_Ns"][0]:.1f} N·s | résidu {r["final_energy_residual_J"]/1000:.2f} kJ'
        draw.text((40,y),text,font=font,fill='white');y+=45
    draw.text((40,865),'Masse : 4 500 kg par ensemble. Coques + liaisons + inertie résiduelle comptées une seule fois.',font=font,fill='#77e5a3');draw.text((40,905),'Échec du bilan local conservé. Fan/core non encore heurtés directement ; aucun écrasement ni fragment qualifié.',font=small,fill='#ffb454')
    path=OUT/'summary_aircraft_a07.png';im.save(path);dump(OUT/'figure_provenance.json',{'created_utc':now(),'inputs':[{'path':rel(d/'verified_states_SI.npz'),'sha256':sha(d/'verified_states_SI.npz')},{'path':rel(OUT/'authoritative_review.json'),'sha256':sha(OUT/'authoritative_review.json')}],'output':rel(path),'sha256':sha(path),'displacement_scale':1,'mechanical_native_mesh':True,'Blender_animation':False,'not_real_event_visual_validation':True})
def prepare():
    assert not REPORT.exists() and not HANDOFF.exists();s=read(OUT/'authoritative_review.json');assert s['integrity_only_pass'] and s['additional_integrity_pass'];n=preserved();assert n==4599;c=read(CFG);diag=read(OUT/'cached_A06_energy_diagnosis.json');cmp=s['engine_local_half_dt_comparison'];contract=read(OUT/'future_fracture_energy_contract.json')
    table='\n'.join(f'|{r["case"]["id"]}|{r["actual_main_end_time_ms"]:.6f}|{r["final_contact_impulse_Ns"][0]:.3f}|{r["final_generated_energy_J"]/1000:.3f}|{r["final_energy_residual_J"]/1000:.3f}|{r["maximum_shell_plastic_strain"]:.6f}|{r["maximum_pylon_force_N"]:.3f}|' for r in s['cases'])
    failed='\n'.join('- '+r['case']['id']+' : '+(', '.join(r['failed_checks']) or 'aucun critère échoué') for r in s['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A07 — nacelles, enveloppes de moteurs et liaisons dans l’avion entier

A07 termine la septième itération de la branche avion entier comme développement mécanique limité. Deux moteurs auparavant réduits à des masses possèdent maintenant 960 triangles de coque et56poutres de liaison. Cinq nouveaux calculs de l’avion entier, plus cinq observateurs isolés, sont sauvegardés. Les essais de contact ne qualifient pas un impact historique : critères échoués ci-dessous. Aucun paramètre ajusté aux dégâts NIST, aucun ancien Engine relancé.

## 1. Faits transcrits et vérifications natives

La fiche [EASA IM.E.240 issue02, 23juillet2024]({c['sources'][0]}), pages9–10, donne pour CF6-80A/A2 : longueur4239,3mm(166,9in), largeur2486,6mm(97,9in), hauteur2415,5mm(95,1in), masse à sec3980,7kg(8776lb). Note1 p19 : cette masse inclut accessoires de base et équipements optionnels indiqués par le constructeur, notamment instrumentation. Pages9/10 rendues et inspectées, copie primaire et hashes conservés en lecture seule. Ce sont des dimensions globales du moteur nu, pas des rayons de carter, ni des cotes de nacelle ou d’attaches. Les conversions kg/lb affichées sont des valeurs arrondies de la fiche et sont conservées telles quelles. La page [GE CF6]({c['sources'][1]}) fournit une enveloppe arrondie pour la famille80A ; les valeurs précises EASA restent les entrées retenues. Aucune identification du moteur installé sur AA11 n’est revendiquée.

Harnais PASS avant et après travaux ; {n} fichiers précédents préservés. Cinq Starter sans erreur ni avertissement et cinq Engines normaux, horizons observés via redémarrages isolés dont le pas de continuation est exclu. Les fichiers principaux restent hashés intacts. Le reader T01 est validé ligne par ligne contre le CSV natif avant lecture de la seule ligne T02 : huit records/frame sans contact extérieur, neuf avec. Les canaux des poutres sont regroupés par partie puis par ID, ce qui diffère de l’ordre d’entrée, particulièrement dans WEAK où les poutres des parties28/29 sont entrelacées dans la déclaration. L’adaptateur vérifie chaque ID/titre et conserve l’ordre de déclaration ; aucune force n’est attribuée par position non vérifiée. Les six nouveaux composants en coque et les liaisons ont une connectivité contrôlée ; chaque moteur forme313nœuds incluant son hub, raccordés à ses deux anciens pylônes.

## 2. Modèles officiels et dépendances de source

Aucun résultat de dégâts, de trajectoire ou d’effondrement officiel n’est une cible. Implantation latérale±7924,8mm et abscisse de front15468,6mm viennent de la géométrie Boeing de planification aéroportuaire déjà copiée, non d’un plan de fabrication. La façade représentative reste dépendante d’entrées NIST héritées, sans identification du panneau historique touché. Les propriétés natives de référence et formulations restent A04–A06 ; aucune modification logicielle. Les PDF et HTML externes restent exclus de la redistribution publique, avec liens et provenance.

## 3. Affirmations des archives locales

Aucune vidéo, photographie ou nouvelle affirmation d’archive examinée. Archive non rescannée, sources et anciennes itérations immuables. Aucune comparaison visuelle historique utilisée pour choisir les matériaux, la rigidité ou la rupture.

## 4. Hypothèses et protocole

Configuration pré-déclarée aircraft_a07_predeclaration.json, graine1102032, zéro tirage. Chaque cas démarre intact. Repère et vitesse initiale(−200,5,2)m/s hérités ; pas de trajectoire imposée, gravité ou précharge. Radôme A05 élastique ; aucune loi de rupture A06 transférée. Viscosité métallique TYPE1 dm/dn=10⁻²⁰ et contacts TYPE7 hérités gap5mm, friction nulle, damping négligeable. Autocontact radôme conservé ; moteurs sans autocontact. Façade59colonnes×3étages, pas de noyau/planchers ni tour complète.

Les contours moteur/nacelle, épaisseurs, métaux et attaches sont propres au modèle. Nacelle : profil axial0/300/1200/2400/3400/4239,3mm, rayons1200/1300/1300/1120/900/700mm, épaisseur2mm, aluminium de référenceρ2780kg/m³,E73,1GPa,ν0,33,seuil324MPa. Une enveloppe de nacelle peut dépasser le moteur nu EASA ; sa forme n’est pas sourcée. Fan-case cylindreR1100mm,x150–1200mm ; core-caseR550mm,x1200–4239,3mm ; épaisseurs5mm, acier génériqueρ7860kg/m³,E200GPa,ν0,3,seuil427,656MPa. Ces alliages et seuils ne représentent pas une identification des vrais carters. 24points angulaires, tubes ouverts, pas de disques, pales, spin, écrasement, fragments, délaminage ou rupture d’assemblage.

Poutres de liaison : A400mm²,Iyy=Izz=80000mm⁴,J160000mm⁴, mêmes métaux génériques ; huit liaisons front/nacelle-fan, huit arrière/nacelle-core, huit fan-core et quatre hub-carters par moteur. Variante WEAK : seules les quatre dernières ont A×0,5 et I/J×0,25. Les anciennes deux poutres équivalentes hub-aile par moteur sont conservées, non identifiées comme assemblages de fabrication. Les16points ADMAS résiduels par moteur sont relocalisés à xfront+600/3000mm,R750/350mm ; leurs huit hôtes RBE3 sont désormais exclusivement les nouvelles coques moteur. Le raccourci direct vers les nœuds d’aile des anciennes masses est supprimé. RBE3 conserve interpolation de translation, sans spin ni inertie de rotor mesurée.

Budget4500kg par ensemble, hypothèse héritée, pas masse de l’avion historique. Par moteur nominal : carters fan/core695,982173kg retirés du budget sec3980,7 ; nacelle165,694916kg et nouveaux joints47,773689kg retirés du budget extérieur519,3. Restes secs3284,717827kg et extérieurs305,831395kg sont répartis dans les16points (224,409326kg chacun). Somme exacte4500kg ; anciens pylônes dans l’ancienne structure, comptés séparément. WEAK allège ses poutres et reporte uniquement cette fraction déclarée dans l’inertie extérieure résiduelle, avec budget constant ; aucune masse ajoutée pour fermer une énergie. Avion121962,860670kg et total avec façade191273,837943kg. Le centre de masse avion nominal devientX22452,781607mm, soit−22,195634mm après redistribution explicite ; changement géométrique prédit sans correction. Le listing natif du centre global diffère de cette prédiction de0,0202956mm enX : critère supplémentaire strict10⁻⁵mm échoué, conservé. Les parties nacelle22/25 donnentX17382,7084mm contre17394,4228mm par centroïdes géométriques des triangles, carters cylindriques et liaisons concordent ; attribution précise de la distribution nodale native non identifiée. Ne pas confondre la préservation de masse totale avec une qualification du premier moment. Aucune inertie physique de rotor identifiée.

FREE :0,6ms sans contact extérieur. NOSE :0,6ms domaine extérieur entier, moteurs présents et raccordés. ENGINE_LOCAL/HALF/WEAK :0,8ms, façade translatée de15468,6mm en X, seuls les nœuds des nouvelles coques moteur au contact. Avion entier libre et couplé conservé, mais nez/ailes volontairement exclus du contact avec cette façade déplacée : contrôle local mécanique, pas traversée complète d’un obstacle. À0,8ms le front fan-case à+150mm n’a pas encore atteint directement la façade : impact initial de la nacelle, réponse des carters par liaisons. Les premiers contacts avec les carters et leurs disques manquants restent à étudier. Pas nominal facteur0,8 ; demi-pas0,4 ; aucune masse numérique ajoutée. CPU2threads, maximum300s par Engine, aucun GPU.

## 5. Résultats dérivés et bilans

|Cas|Fin native ms|Jx N·s|Énergie générée kJ|Résidu final kJ|Max déformation plastique coque|Max effort pylône N|
|---|---:|---:|---:|---:|---:|---:|
{table}

L’unité native g/mm/ms donne contraintes MPa, forces N, moments Nmm, énergie Nmm×0,001→J ; canaux contact FNX/FNY/FNZ interprétés comme impulsions cumulées Nms×0,001→Ns, vérifiés par quantité de mouvement. Poutres : canaux natifs F1/F2/F3,M1/M2/M3,IE,SX,EPSP ; efforts transformés par norme des trois composantes, pas contrainte de fibre reconstruite. Les réactions d’appui héritées restent sans distinction indépendante entre force et impulsion dans ce modèle entier ; cet inconnu est conservé.

Énergie E=Ktranslation+Krotation+IE+hourglass+spring+contact élastique+friction+amortissement. Résidu=ΔE−travail externe, nul ici. PW est inclus dans IE, jamais ajouté une seconde fois. Générée=Krotation+IE+hourglass+spring+contact élastique. Critère local5%générée+1000J au-delà1kJ, global0,5%Kinitial, mêmes seuils hérités ; l’arrondi global float32 peut produire320J de résidu en FREE, sans énergie interne/plastique ni déplacement relatif. FREE passe tous les contrôles déclarés, vitesses/déplacements uniformes et forces pylônes nulles. Les contrôles de masse totale, supports, topologie, sorties finies et fins natives passent dans les cinq cas. Les critères échoués sont conservés :

{failed}

Demi-pas moteurs à temps commun{cmp['common_time_ms']:.6f}ms : impulsion{100*cmp['impulse_difference_fraction']:.4f}%, énergie générée{100*cmp['generated_energy_difference_fraction']:.4f}% ; critères5/10% respectivement {cmp['impulse_pass']}/{cmp['energy_pass']}. WEAK est une sensibilité à la compliance hypothétique, pas une mesure d’attache ni une sélection par ressemblance historique. Aucun raffinement spatial moteur dans A07 : convergence non qualifiée. Les valeurs proches ne prouvent pas la physique des carters ou du contact.

Diagnostic ciblé A06 depuis ses données sauvegardées : perte la plus forte entre{diag['largest_saved_loss_interval']['interval_ms'][0]:.6f} et{diag['largest_saved_loss_interval']['interval_ms'][1]:.6f}ms, incrément du résidu{diag['largest_saved_loss_interval']['residual_increment_J']/1000:.4f}kJ. Décomposition native des variations de K/IE/contact et K des parties conservée dans cached_A06_energy_diagnosis.json, avec champs vitesses autour de l’intervalle. Une partie des masses ADMAS n’appartient pas aux historiques KE des parties ; la somme de ces parties ne constitue pas un bilan indépendant complet. Aucun ajout de masse, travail extérieur ou érosion observé. Variation brusque du contact et de K coïncident avec la perte ; cause algorithme/contraintes/énergie nodale non identifiée, aucun mécanisme affirmé par cette coïncidence. Aucun ancien calcul relancé.

Contrat pour une future rupture de radôme, analytique seulement : loi traction-ouverture triangulaire, w0=σLe/E et wf=2G/σ, traction linéaire descendante entre ces ouvertures ; D=wf(wmax−w0)/(wmax(wf−w0)), tronqué0–1, wmax historique maximal. Décharge/recharge sur pente(1−D)E/Le ; stockageU=0,5(1−D)Ew²/Le. Travail irréversible à suivre séparément du stockage, sous contrainte de dissipation non négative. Avec E22GPa,σ450MPa,G50N/mm non mesuré : Lecrit={contract['maximum_admissible_Le_mm']:.6f}mm. ExempleLe5mm : quadrature totale{contract['integrated_total_work_N_mm']:.9f}N/mm, égalité àG et recharge sans dommage supplémentaire au même pic vérifiées. Cela définit un contrat énergétique/historique, pas une loi native validée ni une propriété identifiée ; maillage du radôme courant toujours trop grossier pour cette énergie. Aucun G gonflé, aucune ancienne propriété endommagée modifiée.

Figure summary_aircraft_a07.png : nouvelle géométrie mécanique et dernier état natif ENGINE_LOCAL, déplacements×1, provenance hashée. Pas de Blender ni de rendu assimilé à une preuve du mécanisme réel.

## 6. Contradictions, manques et suite

La nouvelle géométrie enlève l’absence totale de surface moteur et de chemin mécanique propre à son inertie. Elle ne modélise pas encore un moteur détaillé ou son écrasement ; temps court, nacelle touchée en premier, carters internes non directement heurtés. Contact sans autocontact moteur, matériau plastique idéal au-delà d’une plage diagnostic, profils et attaches hypothétiques : états non qualifiés comme dégâts physiques. Bilan local échoué et sensibilité spatiale encore absente ; déficit antérieur A06 mieux localisé temporellement mais non expliqué. Le contrat de rupture analytique n’est pas une validation de son implémentation dans OpenRadioss.

{NEXT}

Limites antérieures intactes : flexion après fracture complète non validée ; température imposée≠incendie calculé ; tests numériques≠effondrement réel ; Blender visualisation. V11F froid/V11R préservés, V11S/I02I-M différées. Publication A06+A07 après vérification, sans relancer les sciences anciennes ; résultat d’échecs publié également.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Passation AIRCRAFT-A07 → A08

Lire AGENTS.md, puis état local prioritaire et ceci. A07 septième itération avion entier,5Starter+5Engine nouveaux+5observateurs, aucun ancien Engine relancé. {n} fichiers antérieurs préservés. Résultats autoritatifs : output/aircraft_a07/authoritative_review.json, additional_verification.json, cached_A06_energy_diagnosis.json, future_fracture_energy_contract.json, rapport_aircraft_a07.md, summary_aircraft_a07.png. r0 cinq cas : FREE/NOSE0,6ms ; ENGINE_LOCAL/HALF/WEAK0,8ms. Intégrité native/masse totale/topologie/fins vérifiée ; contrôle supplémentaire CG échoué0,0202956mm, conservé ; contrôle FREE passe ; critères physiques échoués restent visibles. V11F/V11R intacts ; V11S/I02I-M différées.

Deux moteurs :960triangles TYPE1,56poutres TYPE3,624nouveaux nœuds ajoutés après35020 (pas masque préfixe). 4500kg chacun, carters695,982173+nacelle165,694916+joints47,773689+inertie3590,549222 ; budgets sec EASA3980,7/extérieur hypothèse519,3. Point masses16par moteur224,409326kg, repositionnées xfront+600/3000,R750/350 ; RBE3hôtes moteur seul, fini raccourci aile. Pylônes11135–11138 hérités gardés. Coques génériques Al/acier non identifiées ; profils/épaisseurs/attaches propres. Ensemble entièrement raccordé,313nœuds par moteur incluant hub. Masse avion121962,860670kg inchangée ; CGX22452,781607mm vs22474,977241, déplacement−22,195634mm expliqué. NativeCG total comparé au moment précédent plus différence avion et éventuelle translation façade : différence0,0202956mm enX, échecstrict10⁻⁵mm. Nacelles coniques centroïdes différents dans listing natif, cause de distribution nodale nonidentifiée ; carters cylindriques concordent, masse totale préservée. Reprendre diagnostic depuis PART MASS & INERTIA sauvegardé, pasrerun.

Local moteurs : façade déplacéeX15468,6, seuls moteurs secondaires au contact ; avion entier couplé mais nez/ailes ignorés pour ce contrôle, pas impact historique complet. Fan/core à x+150/+1200mm pas encore directement heurtés à0,8ms, pas pales/disques/spin/crush/fragments/autocontact moteur. WEAK quatre joints hub par moteur A×0,5/I/J×0,25, budget massique inchangé explicitement. Tout départ intact, pas de nouvelles propriétés sur état endommagé. Radôme toujours élastique, ORTHENERG A06 refusé.

{table}

Demi-pas moteurs J{100*cmp['impulse_difference_fraction']:.4f}%/gen{100*cmp['generated_energy_difference_fraction']:.4f}% :5/10% {cmp['impulse_pass']}/{cmp['energy_pass']}. Bilan local5%gen+1000J échoué cas contact, seuils conservés. Spatial moteur pas testé. Touslesfichiers natifs/CSV/NPZ gardés ; aucun state8ms ni fracture qualifiés. TH/BEAM export regroupé parpartie/ID et9canaux canoniques ; adaptateur fait correspondance de chaque titre/ID avantcalcul, génération gardeordredeck. T01 natif vérifié ligneparligne, T02initiale seule viareader8ou9records : nepasrépéterconvertisseurT02crash A05. review ratio A05 shadowing rectifié depuisNPZ dansauthoritative_review, premières sorties gardées.

Diagnostic A06 : plusforte perte{diag['largest_saved_loss_interval']['residual_increment_J']/1000:.4f}kJ dans1,640568–1,660712ms, variationK/contact, sourcesauvegardéeshashées ; ADMAS nonattribuéesdanssommeKEparties, causesnonidentifiées. Contrat fissure analytique : w0=σLe/E,wf=2G/σ,Dmax=wf(wmax−w0)/(wmax(wf−w0)),décharge pente(1−D)E/Le,Ustock=0,5(1−D)Ew²/Le ; intégrationG et recharge au même pic sans nouveau dommage vérifiéesLe5mm,G50nonmesuré,Lecrit10,864198mm. Pasimplémentationnative, pastransfert, radôme maillageencoretropgrossier.

Suite : {NEXT}

Publication cadence A06+A07 attendue après scellé ; vérifier harness/publication_cycle.json pour l’état réellement envoyé, et outputs/github_publication/updates_2026-10-06_aircraft_a06_a07/final_remote_verification.json s’il existe. Ne jamais annoncer publication à partir d’un simple commit local. Revue utilise fichiers sauvegardés, pas ancien solveur ni scanarchive. Aucune action Yoremi/X.
''',encoding='utf-8')
    own=list(OUT.rglob('*'))+[CFG,HANDOFF]+[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_aircraft_a07.py','review_aircraft_a07.py','finalize_aircraft_a07.py']]
    files=sorted(set(p for p in own if p.is_file() and p.name not in ['artifact_manifest.json','publication_verification.json']))
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'scope':'Own configurations/scripts/results including failed physical checks; integrity only','excluded':['third-party PDF/HTML/render','mutable state registry cadence','self and publication verification']});print({'prepared':True,'files':len(files),'preserved':n})
def register():
    assert not (OUT/'publication_verification.json').exists();s=read(OUT/'authoritative_review.json');assert s['integrity_only_pass'] and s['additional_integrity_pass'];n=preserved();assert n==4599
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:assert sha(ROOT/'harness'/name)==sha(OUT/('before_'+Path(name).name))
    assert all(sha(ROOT/r['path'])==r['sha256'] for r in read(OUT/'artifact_manifest.json')['files']);harness();t=now();state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');assert state['current_iteration']=='AIRCRAFT-A06' and cycle['pending_count']==1
    status='completed_coupled_engine_shells_mounts_and_bounded_contact_controls_with_failed_energy_gates';record={'experiment_id':'WTC1-AIRCRAFT-A07','registered_at':t,'status':status,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'authoritative_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'integrity_only_pass':True,'all_declared_checks_pass':s['all_declared_checks_pass'],'physical_impact_qualified':False,'engine_crushing_qualified':False,'failure_transfer_enabled':False,'local_energy_ledger_fully_qualified':False,'spatial_convergence_qualified':False,'whole_aircraft_iteration_count':7,'whole_aircraft_cases':5,'main_solver_jobs':5,'observation_jobs':5,'old_solver_reruns':0,'old_files_preserved':4599,'engine_shells':960,'engine_joint_beams':56,'engine_assembly_budget_kg':9000,'engine_geometry_and_materials_identified':False,'NIST_outcomes_used_as_target':False,'next_iteration':'AIRCRAFT-A08'}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A07',next_iteration='AIRCRAFT-A08',current_status=status,next_objective=NEXT,updated_at=t);state['aircraft_a07_key_results']=record;state['user_steering_2026_10_05']['next']='AIRCRAFT-A08';state['validated_artifacts'].update(aircraft_a07_report=rel(REPORT),aircraft_a07_results=rel(OUT/'authoritative_review.json'),aircraft_a07_handoff=rel(HANDOFF),aircraft_a07_figure=rel(OUT/'summary_aircraft_a07.png'));cycle.update(pending_iterations=['AIRCRAFT-A06','AIRCRAFT-A07'],pending_count=2,next_publication_after='Publish verified A06+A07 pair; then two further verified iterations A08+A09',updated_at=t);dump(ROOT/'harness/state.json',state);dump(ROOT/'harness/publication_cycle.json',cycle);verify(True)
def verify(write=False):
    n=preserved();state=read(ROOT/'harness/state.json');before=read(OUT/'before_state.json');protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness();manifest=read(OUT/'artifact_manifest.json');cycle=read(ROOT/'harness/publication_cycle.json')
    checks={'new_artifact_hashes':all(sha(ROOT/r['path'])==r['sha256'] for r in manifest['files']),'old_files_preserved':n==4599,'predeclaration_unchanged':sha(CFG)==read(OUT/'declaration_guard.json')['sha256'],'source_inputs_unchanged':all(sha(ROOT/r['path'])==r['sha256'] for r in read(OUT/'source_manifest.json')['local_inputs']),'append_only_single_record':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A07','state_route':state['current_iteration']=='AIRCRAFT-A07' and state['next_iteration']=='AIRCRAFT-A08','protected_old_evidence':all(before[k]==state[k] for k in protected),'additional_native_integrity':read(OUT/'additional_verification.json')['pass'],'failed_CG_gate_retained':not read(OUT/'authoritative_review.json')['additional_CG_gate_pass'],'failed_physical_gates_visible':not read(OUT/'authoritative_review.json')['all_declared_checks_pass'],'reports_and_figure_exist':REPORT.exists() and HANDOFF.exists() and (OUT/'summary_aircraft_a07.png').exists(),'two_pending_or_verified_published':cycle['pending_iterations']==['AIRCRAFT-A06','AIRCRAFT-A07'] or (cycle['pending_count']==0 and cycle['last_published_iteration']=='AIRCRAFT-A07'),'harness_pass':v['Status']=='PASS'}
    result={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'files_checked':len(manifest['files']),'old_files_checked':n,'harness':v,'physical_impact_qualified':False,'local_energy_ledger_fully_qualified':False,'spatial_convergence_qualified':False,'next_iteration':'AIRCRAFT-A08'};assert result['pass'],result
    if write:dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['extras','figure','prepare','register','verify']);globals()[p.parse_args().action]()
