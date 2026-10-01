"""Reproducible V11D, CPU-only, immutable prior results and sources."""
import argparse
import csv
import json
import platform
import sys
import time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import v11d_panel_model as physics
from run_v11c_floor_panel import sha,read,write_json,write_csv,digest

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/"wtc1_simulation_v8/data/v11d_slab_contact_predeclaration.json"


def calculate(cfg,cfg_c,base,transfer,seats,subdivisions=2,step_factor=1.,keep=True):
    summaries=[]; history=[]; fibers=[]; physical_forces=[]; node_rows=[]; releases=[]; endpoints={}
    paths=[]
    for case in cfg["cold_cases"]:
        common={**case,"subdivisions":subdivisions,"horizontal_mode":"roller"}
        paths.append((case["id"],"COLD_LOAD",lambda p,common=common:{**common,"gravity_factor":p},cfg["cold_load_factor_end"],cfg["cold_step"]*step_factor))
    for case in cfg["prescribed_paths"]:
        initial={"subdivisions":subdivisions,"gravity_factor":cfg["preload_factor"],"horizontal_mode":case["horizontal_mode"]}
        preload=physics.evaluate_panel(cfg,cfg_c,base,transfer,seats,initial)
        mid=cfg_c["panel"]["panels"]//2
        initial_middle=float(preload["u"][2*mid+1])
        def make(p,case=case,initial=initial,mid=mid,initial_middle=initial_middle):
            spec={**initial,"steel_c":20+p*(case["steel_end_c"]-20),"slab_top_c":20+p*(case["slab_top_end_c"]-20),
                "slab_bottom_c":20+p*(case["slab_bottom_end_c"]-20),"support_c":20+p*(case["support_end_c"]-20)}
            if "middle_top_lowering_m" in case:
                spec["prescribed_top_vertical"]={mid:initial_middle-p*case["middle_top_lowering_m"]}
            return spec
        paths.append((case["id"],"PRESCRIBED_AFTER_COLD_PRELOAD",make,1.,cfg["prescribed_parameter_step"]*step_factor))
    for name,kind,make,end,step in paths:
        summary,rows,last,release=physics.trace_path(name,cfg,cfg_c,base,transfer,seats,make,end,step)
        summaries.append({"path_kind":kind,**summary}); endpoints[name]=last
        if release: releases.append(release)
        if not keep: continue
        history.extend(rows)
        fibers.extend({"path_id":name,**r} for r in last["fiber_rows"])
        # Do not export bending quadrature conjugates as axial force_N.
        for item in last["terms"]:
            if item["kind"]=="slab_bending": continue
            physical_forces.append({"path_id":name,"id":item["id"],"kind":item["kind"],"force_N":item["force_N"],
                "extension_or_gap_m":item["generalized_strain"],"DCR":item["DCR"],"strain_energy_J":item["strain_energy_J"],
                "state":item["state"],"station":item.get("station")})
        model=last["model"]
        for j,x in enumerate(model["slab_x_m"]):
            node_rows.append({"path_id":name,"slab_node":j,"x_m":float(x),"u_axial_m":float(last["u"][model["ux"][j]]),
                "w_vertical_m":float(last["u"][model["w"][j]]),"theta_rad":float(last["u"][model["theta"][j]])})
    return {"path_summaries":summaries,"path_history":history,"slab_fiber_stresses":fibers,
        "physical_component_forces":physical_forces,"slab_displacements":node_rows,"release_diagnostics":releases},endpoints


def coupon(cfg,cfg_c):
    rows=[]
    kc=cfg["vertical_connection"]["contact_stiffness_per_equivalent_knuckle_N_m"]
    kt=cfg["vertical_connection"]["tension_stiffness_per_equivalent_knuckle_N_m"]
    for temp in (20.,450.,600.):
        capacity=float(np.interp(temp,cfg_c["bond"]["concrete_temperature_c"],cfg_c["bond"]["vertical_pullout_per_knuckle_kip_reference_only"])*physics.KIP)
        critical_gap=capacity/kt
        broken=False
        for step,fraction in enumerate((-1.,0.,.5,1.,1.1,0.,-1.)):
            gap=fraction*critical_gap
            if broken: tie=0.
            else: tie=kt*max(gap,0.)
            contact=kc*min(gap,0.)
            rows.append({"concrete_temperature_c":temp,"step":step,"gap_m":gap,"contact_force_N":contact,
                "tie_force_N":tie,"pullout_capacity_N":capacity,"tie_broken":broken,
                "state":"CAPACITY_POINT_BEFORE_REMOVAL" if fraction==1 else "PRESCRIBED_GAP_COUPON",
                "stored_contact_energy_J":.5*kc*min(gap,0.)**2,"stored_tie_energy_J":.5*tie*tie/kt,
                "global_energy_credit_J":0.})
            if fraction==1:
                broken=True
                rows.append({**rows[-1],"tie_force_N":0.,"tie_broken":True,"state":"SAME_GAP_AFTER_TENSION_TIE_REMOVAL",
                    "stored_tie_energy_J":0.})
    return rows


def audit(cfg,data,replay,mesh_data,half_data,extra,coupon_rows):
    tests=list(extra)
    def check(name,ok,evidence):tests.append({"test":name,"pass":bool(ok),"evidence":evidence})
    states=list(data["path_history"])
    states += [r["post_state"] for r in data["release_diagnostics"] if r.get("post_state")]
    maxima={key:max(r[key] for r in states) for key in ("equilibrium_residual","energy_identity_residual","recovered_energy_identity_residual")}
    check("declared_12_paths",len(data["path_summaries"])==12,len(data["path_summaries"]))
    check("deterministic_replay_exact",digest(data)==digest(replay),digest(data))
    for name,value in maxima.items():check("all_path_"+name,value<1e-8,value)
    balance=max(abs(r["total_seat_vertical_reaction_N"]+r["actuator_vertical_reaction_N"]-r["total_gravity_load_N"])/max(1.,r["total_gravity_load_N"]) for r in states)
    check("seats_plus_actuator_balance_gravity_once",balance<1e-8,balance)
    check("all_contact_forces_compressive",all(r["force_N"]<=0 for r in data["physical_component_forces"] if r["kind"]=="contact"),"No adhesion in contact branch")
    check("all_vertical_ties_tensile",all(r["force_N"]>=0 for r in data["physical_component_forces"] if r["kind"]=="vertical_tie"),"No compressive tie force")
    check("no_bending_quadrature_values_exported_as_axial_force",not any(r["kind"]=="slab_bending" for r in data["physical_component_forces"]),"Recovered physical moment and stress in separate file")
    check("no_state_past_first_limit_promoted",all(r["max_DCR"]<1+1e-6 for r in states if r["state"]=="WITHIN_UNCRACKED_CHECKED_DOMAIN"),len(states))
    check("zero_global_resistance_energy",all(r["global_energy_credit_J"]==0 for r in states+coupon_rows),"No V11B coupling")
    check("all_coupons_broken_tie_zero_and_recontact_retained",all(r["tie_force_N"]==0 for r in coupon_rows if r["tie_broken"]) and all(r["contact_force_N"]<0 for r in coupon_rows if r["step"]==6),len(coupon_rows))
    comparisons=[]
    reference={r["path_id"]:r for r in data["path_summaries"]}
    for subdivisions,other in mesh_data.items():
        for row in other["path_summaries"]:
            ref=reference[row["path_id"]]
            comparisons.append({"path_id":row["path_id"],"subdivisions":subdivisions,
                "same_terminal":row["state"]==ref["state"],"same_limit_kind":row["governing_kind"]==ref["governing_kind"],
                "parameter":row["parameter"],"relative_parameter_difference":abs(row["parameter"]-ref["parameter"])/max(1e-7,ref["parameter"]),
                "max_slab_nodal_down_m":row["max_slab_nodal_down_m"],
                "relative_nodal_deflection_difference":abs(row["max_slab_nodal_down_m"]-ref["max_slab_nodal_down_m"])/max(1e-8,abs(ref["max_slab_nodal_down_m"]))})
    finest=[r for r in comparisons if r["subdivisions"]==4]
    check("slab_only_mesh_2_to_4_same_termination_and_limit_kind",all(r["same_terminal"] and r["same_limit_kind"] for r in finest),finest)
    check("slab_only_mesh_2_to_4_event_parameter_within_2percent",max(r["relative_parameter_difference"] for r in finest)<cfg["acceptance"]["slab_mesh_first_event_relative_tolerance"],max(r["relative_parameter_difference"] for r in finest))
    check("slab_only_mesh_2_to_4_nodal_deflection_within_2percent",max(r["relative_nodal_deflection_difference"] for r in finest)<cfg["acceptance"]["slab_mesh_nodal_deflection_relative_tolerance"],max(r["relative_nodal_deflection_difference"] for r in finest))
    half_changes=[{"path_id":r["path_id"],"delta_parameter":abs(r["parameter"]-reference[r["path_id"]]["parameter"]),
        "same_end":r["state"]==reference[r["path_id"]]["state"],"same_kind":r["governing_kind"]==reference[r["path_id"]]["governing_kind"]} for r in half_data["path_summaries"]]
    check("half_path_step_same_first_event",all(r["same_end"] and r["same_kind"] and r["delta_parameter"]<=cfg["acceptance"]["half_step_first_event_tolerance"] for r in half_changes),half_changes)
    return {"status":"PASS" if all(t["pass"] for t in tests) else "FAIL","test_count":len(tests),
        "tests_passed":sum(t["pass"] for t in tests),"tests":tests,"path_residual_maxima":maxima,
        "mesh_comparison":comparisons,"half_step_comparison":half_changes}


def figure(path,data,endpoints):
    im=Image.new("RGB",(1600,1100),"#f2f5f8"); draw=ImageDraw.Draw(im)
    def font(size,bold=False):return ImageFont.truetype("C:/Windows/Fonts/segoeui"+("b" if bold else "")+".ttf",size)
    def text(x,y,s,size=22,color="#203447",bold=False):draw.text((x,y),s,font=font(size,bold),fill=color)
    text(50,27,"WTC 1 / V11D - dalle en flexion et contact vertical",34,bold=True)
    text(50,78,"Panneau local : fissuration, ouverture et arrachement sont des événements distincts.",23)
    draw.rounded_rectangle((35,126,1565,438),radius=15,fill="white")
    text(60,141,"Trois états possibles de la liaison verticale",26,bold=True)
    for j,(name,caption,gap,color) in enumerate([
        ("Contact comprimé","Le treillis porte la dalle.",0,"#3f877b"),
        ("Ouverture retenue","L'attache travaille en traction.",35,"#c5813f"),
        ("Attache arrachée","Le contact pourra revenir.",35,"#b45753")]):
        x=80+j*505
        text(x,191,name,24,color,bold=True)
        draw.line((x+20,305,x+380,305),fill="#497d9f",width=7)
        draw.line((x+20,288-gap,x+380,288-gap),fill="#b58e55",width=15)
        for xx in (x+90,x+190,x+290):
            if j!=2: draw.line((xx,288-gap,xx,303),fill=color,width=4)
            else:
                draw.line((xx,260,xx,271),fill=color,width=4);draw.line((xx,289,xx,301),fill=color,width=4)
        text(x,338,caption,22)
        text(x,375,"Schéma de principe, non à l'échelle",17)
    draw.rounded_rectangle((35,458,835,882),radius=15,fill="white")
    text(60,477,"À froid : borne 125 %, sans seuil franchi",25,bold=True)
    names=["COLD_E0_FT10","COLD_E05_FT10"]
    colors=["#bd8351","#3688b0"]
    labels=["Décalage nul, ft 1 MPa","Décalage t/2, ft 1 MPa"]
    selected=[r for r in data["path_history"] if r["path_id"] in names]
    xmax=max(r["max_slab_nodal_down_m"]*1000 for r in selected)*1.08
    ax,ay,aw,ah=117,783,650,218
    for i in range(6):
        x=ax+aw*i/5; y=ay-ah*i/5
        draw.line((x,ay-ah,x,ay),fill="#dce4eb");draw.line((ax,y,ax+aw,y),fill="#dce4eb")
        text(x-14,ay+7,f"{xmax*i/5:.0f}",17);text(ax-47,y-11,f"{125*i/5:.0f}",17)
    text(60,536,"Charge / référence (%)",18);text(306,825,"Flèche nodale de dalle (mm)",20)
    for j,name in enumerate(names):
        text(61+j*256,515,labels[j],16,colors[j])
        pts=[r for r in selected if r["path_id"]==name]
        draw.line([(ax+aw*r["max_slab_nodal_down_m"]*1000/xmax,ay-ah*r["gravity_factor"]/1.25) for r in pts],fill=colors[j],width=4)
    draw.rounded_rectangle((855,458,1565,882),radius=15,fill="white")
    text(880,477,"Chauffage et déplacement imposés",25,bold=True)
    labels2={"HEAT_UNIFORM_ROLLER":"Chauffage uniforme / appui libre","HEAT_UNIFORM_RESTRAINED":"Chauffage uniforme / appui retenu",
        "HEAT_FROM_BELOW":"Chauffage de dalle par dessous","LOCAL_TRUSS_LOWERING_COLD":"Abaissement local imposé au treillis"}
    kinds={"slab_first_cracking":"Première fissuration du prédicteur","top_chord":"Premier écran de membrure supérieure",
        "vertical_tie":"Seuil d'arrachement d'attache","horizontal_tie":"Seuil de glissement d'attache","seat_h":"Seuil de traction d'appui"}
    for j,row in enumerate(r for r in data["path_summaries"] if r["path_kind"]!="COLD_LOAD"):
        y=528+j*80;text(880,y,labels2[row["path_id"]],21,bold=True)
        label=kinds.get(row["governing_kind"],row["governing_kind"]) if row["state"].startswith("FIRST") else "Fin sans franchir les critères vérifiés"
        text(880,y+30,label,20,"#a5623c")
    draw.rounded_rectangle((35,907,1565,1070),radius=15,fill="#203447")
    text(60,927,"Une première fissure n'est pas une rupture de plancher.",25,"white",True)
    text(60,972,"Pas encore de béton fissuré, d'armatures résistantes, de postflambement ou de dynamique de rupture.",22,"white")
    text(60,1014,"Températures prescrites et valeurs d'attaches hypothétiques/documentées séparées. Aucun verdict global.",21,"white")
    im.save(path)


def report(data,audit,seconds):
    count=Counter(r["governing_kind"] for r in data["path_summaries"] if r["state"].startswith("FIRST"))
    table="\n".join(f"| {r['path_id']} | {r['parameter']:.6f} | {r['steel_c']:.1f} | {r['slab_top_c']:.1f}/{r['slab_bottom_c']:.1f} | {r['max_slab_nodal_down_m']*1000:.2f} | "+(r['governing_kind'] if r['state'].startswith('FIRST') else 'Fin sans seuil vérifié')+" |" for r in data["path_summaries"])
    return f"""# WTC 1 - V11D : flexion de dalle, contact et arrachement

## Résultat utilisable

Le panneau possède maintenant des déplacements et rotations de dalle indépendants du treillis. Le poids passe par des contacts comprimés ou des attaches tendues, et non par un lien vertical parfait. Une attache retirée ne supprime pas le contact comprimé. La dalle est un prédicteur élastique **non fissuré** : une première fissure calculée termine son domaine de validité, sans être déclarée rupture du plancher.

Douze chemins et un contrôle d'attache isolée sont calculés. Premiers seuils : {dict(count)}. Les autres chemins atteignent simplement leur borne de paramètre. Ni ces comptes ni leurs températures ne donnent des probabilités ou un verdict historique. Aucune sortie V11D n'est transférée à la tour globale ou à Blender.

## 1. Faits directement transcrits ou vérifiés

Les dimensions de référence V11A/V11C sont préservées : paire symétrique, portée713in, largeur80in, épaisseur rectangulaire équivalente4,35in ; charge80psf incluant déjà le poids propre. Le treillis comporte toujours16panneaux Warren supposés et17stations de liaison. Une subdivision de la dalle n'ajoute ni treillis ni attache.

## 2. Résultats d'un modèle officiel réutilisés

Le tableau d'arrachement de [NIST NCSTAR1-6C, tableau5-7 p67](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-6c.pdf), vérifié en V11C, fournit15/12/10/7kip par attache pour les températures moyennes de béton20-300/450/600/750°C. Il est maintenant activé en traction verticale. Ce sont des estimations NIST, pas des essais incendie de toutes les pièces construites. L'interpolation reste une hypothèse. Les capacités de glissement et de siège sont celles déjà utilisées, avec leurs mêmes limites.

## 3. Informations d'archives

Aucune nouvelle inspection de l'archive ou des PDF. Les copies, sources et anciennes versions sont conservées. La disposition réelle des attaches, le ferraillage, le bac et les décalages exacts dalle/cordons ne sont pas établis par V11D.

## 4. Hypothèses et mécanique du prototype

### Dalle et excentricité

La dalle est une bande de poutre Euler-Bernoulli et une ligne axiale bilatérale jusqu'au premier seuil de fissuration/écrasement. Contrairement à V11C, sa traction axiale n'est donc pas supprimée avant que le critère combiné ne soit atteint. Il ne s'agit pas d'une résistance après fissuration. Aucun apport d'armature n'est inventé. E, fc et leurs réductions sont hérités des hypothèses V11A ; ft20=0,5/1/2MPa et sa réduction sont de nouvelles hypothèses déclarées, pas une formule réglementaire ou une mesure WTC.

Le glissement vaut us+e·theta−uacier. L'excentricité e=0 ou t/2 est explicite et la force de liaison transmet son moment e·N. La valeur t/2 suppose une attache sous une dalle rectangulaire équivalente ; le détail réel de bac et de cordon reste inconnu. Les déplacements sont petits, sans chaînette, raideur géométrique, torsion ou postflambement.

### Contact et attache

Le jeu g=wdalle−wtreillis est positif en ouverture. Contact : N=kc·min(g,0), sans adhérence ni traction. Attache : N=kt·max(g,0), limitée par l'arrachement. kc=1000MN/m et kt=10/100/1000MN/m par attache équivalente sont des paramètres non mesurés. Le contact autorise une petite interpénétration de régularisation, mesurée dans les sorties ; elle n'est pas une pénétration physique du béton.

La densité32attaches équivalentes et les poids tributaires sont conservés. Le retrait au premier seuil d'une liaison, s'il intervient avant fissuration/flambement, supprime traction verticale et glissement horizontal de la station, mais garde le contact. Un rééquilibrage éventuel n'est qu'un diagnostic statique ; énergie stockée retirée et dissipation dynamique sont distinctes. Le contrôle d'attache isolée démontre la logique numérique de retrait/recontact, pas la validation expérimentale d'une loi de rupture.

### Charge, température et contraintes

Toute la gravité est appliquée **une seule fois à la dalle**, avec forces et moments nodaux cohérents de charge répartie. Le cas d'abaissement local utilise un déplacement imposé au milieu du treillis après précharge0,25 : sa réaction est incluse dans l'équilibre. Ce n'est ni un dommage d'avion calculé ni un mouvement spontané.

La température moyenne des deux faces de dalle fixe E, résistances et expansion axiale. La différence des faces donne une courbure libre kappa0=−alpha(Tsup−Tinf)/t. Il s'agit d'un gradient prescrit simplifié : pas de section multicouche, de feu, de transfert thermique, de fluage ou de temps réel.

Les contraintes de fibres sont N/A ± M·t/(2I), avec recherche aux extrémités et à l'extremum intérieur de moment de chaque élément. La solution particulière quartique de charge uniforme est ajoutée pour récupérer le moment local ; on ne confond pas la courbure de l'interpolation seule avec le moment physique sous charge répartie. Les flèches exportées sont des maxima **nodaux**, pas une recherche exacte du maximum intérieur entre nœuds.

### Énergie et limites

Deux points de Gauss intègrent exactement la raideur de flexion cubique. Leurs conjugués ne sont pas des forces axiales en newtons : ils ne figurent pas dans le tableau d'efforts physiques. La récupération sous charge répartie ajoute une énergie q²L⁵/(1440EI) et un travail double, séparément consignés. L'identité d'état inclut déformations propres et travail d'appui imposé. Ce n'est pas un bilan de chaleur ou une simulation de fracture dynamique.

Les critères restent séparés : fissuration initiale ou compression de dalle, écrans nominaux de barres, traction des sièges, glissement ou arrachement d'attache. La compression horizontale et l'interactionV-H des sièges restent non vérifiées. Aucune résistance au flambement latéral n'est déduite automatiquement du contact vertical.

## 5. Résultats dérivés

| Chemin | Paramètre final | Acier°C | Dalle sup/inf°C | Flèche nodale mm | Premier critère atteint ou fin |
|---|---:|---:|---:|---:|---|
{table}

Pour les chemins froids, le paramètre est le facteur de charge ; pour les autres il est la fraction de la sollicitation prescrite. Ce n'est jamais un temps. Chaque courbe s'arrête au premier critère et n'est pas prolongée pour atteindre un arrachement après fissuration. Nombre de diagnostics de retrait de panneau :{len(data['release_diagnostics'])}. Les seuils de fissuration ne préjugent pas de la résistance résiduelle d'une dalle armée réelle.

Différence importante avec V11C : son modèle axial comprimé ne vérifiait pas la fissuration combinant traction et flexion. L'arrêt plus tôt du chemin uniformément chauffé dans V11D traduit ce nouveau domaine de calcul ; ce n'est pas une preuve que le plancher réel tombe à la première fissure, ni une correction rétroactive de la V11C. Les parcours thermiques emploient ici une précharge0,25 et ne doivent pas être confondus avec la précharge0,5 de V11C.

### Contrôles

{audit['tests_passed']}/{audit['test_count']} contrôles passent : poutres à solutions analytiques, courbure libre/bloquée, contact/traction/recontact, moments récupérés, excentricité, unités, charge et réactions, identité énergétique, répétition déterministe, division du pas de parcours par2 et subdivision de dalle1/2/4 à treillis/attaches fixes. Les comparaisons finales de maillage utilisent2→4 ; elles ne constituent pas une validation des géométries réelles.

Résidus maximaux des parcours :{audit['path_residual_maxima']}. Temps CPU{seconds:.2f}s avec répétitions/raffinements, Python{platform.python_version()}, NumPy{np.__version__}. Aucun GPU, logiciel nouveau ou Blender. Les contrôles valident l'exécution du prototype, pas toute la chaîne causale historique.

## 6. Limites, contradictions et suite

La dalle équivalente, son excentricité, ses propriétés et les capacités officielles d'attaches ne forment pas encore une calibration matérielle cohérente du plancher construit. Les premiers seuils ne doivent pas être interprétés comme des ruptures complètes. Les valeurs d'attaches peuvent rester inutilisées si la fissuration intervient auparavant : il serait incorrect de sauter cette limite pour afficher un arrachement.

La V11E devra traiter la réponse de dalle après fissuration avec des hypothèses d'armatures déclarées et des vérifications de section/cycle, avant d'utiliser cette résistance dans le panneau ; géométrie non linéaire, postflambement, liaisons avec colonnes/allèges et calcul de l'impact/incendie restent à développer. V11A/V11B/V11C et le film V10Z demeurent inchangés. Aucun effondrement ou non-effondrement n'est imposé.
"""


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output-dir");args=parser.parse_args()
    cfg=read(CONFIG);out=(ROOT/(args.output_dir or cfg["output_directory"])).resolve()
    if out!=(ROOT/cfg["output_directory"]).resolve() and not out.is_relative_to((ROOT/cfg["scratch_directory"]).resolve()):raise ValueError("Outside V11D paths")
    if out.exists():raise FileExistsError("Preserve previous attempt; choose new output")
    cfg_c=read(ROOT/cfg["base_configuration"]);base=read(ROOT/cfg_c["base_configuration"])
    transfer=read(ROOT/cfg_c["transfer"]);seats=read(ROOT/cfg_c["seats"])["floor_truss_seats"]
    inputs=list(dict.fromkeys([cfg["base_configuration"],cfg_c["base_configuration"],cfg_c["transfer"],cfg_c["seats"],
        *cfg["source_files"],*cfg["protected_files"],"wtc1_simulation_v8/scripts/run_v11c_floor_panel.py","wtc1_simulation_v8/scripts/v11a_component_model.py"]))
    manifest=[{"path":p,"sha256_before":sha(ROOT/p)} for p in inputs]
    out.mkdir(parents=True);start=time.perf_counter();utc=datetime.now(timezone.utc).isoformat()
    data,endpoints=calculate(cfg,cfg_c,base,transfer,seats)
    print("Primary12paths computed",flush=True)
    replay,_=calculate(cfg,cfg_c,base,transfer,seats)
    half,_=calculate(cfg,cfg_c,base,transfer,seats,step_factor=.5,keep=False)
    meshes={}
    for sub in (1,4):
        meshes[sub],_=calculate(cfg,cfg_c,base,transfer,seats,subdivisions=sub,keep=False)
        print(f"Slab mesh{sub} checked",flush=True)
    from test_v11d_independent import run as independent
    from test_v11d_panel_review import run as panel_review
    coupons=coupon(cfg,cfg_c)
    checks=audit(cfg,data,replay,meshes,half,independent()+panel_review(cfg,cfg_c,base,transfer,seats),coupons)
    elapsed=time.perf_counter()-start
    write_json(out/"numerical_audit.json",checks)
    if checks["status"]!="PASS":
        print(json.dumps([r for r in checks["tests"] if not r["pass"]],indent=2));raise RuntimeError("Numerical gate failed; draft preserved")
    for key,rows in data.items():
        if key=="release_diagnostics":write_json(out/(key+".json"),rows)
        else:write_csv(out/(key+".csv"),rows)
    write_csv(out/"slab_mesh_comparison.csv",checks["mesh_comparison"]);write_csv(out/"isolated_pullout_coupon.csv",coupons)
    reference=physics.build_panel(cfg,cfg_c,base,transfer,seats,{})
    inventory={k:v for k,v in reference.items() if k not in ("nodes","force","ux","w","theta","slab_x_m")}
    for key in ("nodes","force","ux","w","theta","slab_x_m"):inventory[key]=reference[key].tolist()
    write_json(out/"panel_inventory.json",inventory)
    figure(out/"synthese_v11d_dalle_contact.png",data,endpoints)
    with (out/"rapport_v11d_dalle_contact.md").open("x",encoding="utf-8") as stream:stream.write(report(data,checks,elapsed))
    for item in manifest:
        item["sha256_after"]=sha(ROOT/item["path"]);item["unchanged"]=item["sha256_after"]==item["sha256_before"]
    if not all(r["unchanged"] for r in manifest):raise RuntimeError("Protected input changed")
    code=[CONFIG,*[ROOT/"wtc1_simulation_v8/scripts"/name for name in ("v11d_panel_model.py","run_v11d_slab_contact.py","test_v11d_independent.py","test_v11d_panel_review.py")]]
    write_json(out/"source_manifest.json",{"iteration":"V11D","input_and_protected_files":manifest,
        "code_config_files":[{"path":str(p.relative_to(ROOT)).replace("\\","/"),"sha256":sha(p)} for p in code],
        "source_basis":"Existing V11C checked Table5-7, no new source PDF/archive read; no new as-built promotion"})
    results={"iteration":"V11D","status":"PASS_UNCRACKED_SLAB_CONTACT_PREDICTOR_NOT_GLOBAL_VALIDATION",
        "path_count":len(data["path_summaries"]),"path_point_count":len(data["path_history"]),
        "first_event_counts":dict(Counter(r["governing_kind"] for r in data["path_summaries"] if r["state"].startswith("FIRST"))),
        "no_checked_limit_crossed_at_parameter_end":sum(r["state"].startswith("PARAMETER_END") for r in data["path_summaries"]),
        "release_diagnostic_count":len(data["release_diagnostics"]),"tests_passed":checks["tests_passed"],"test_count":checks["test_count"],
        "path_residual_maxima":checks["path_residual_maxima"],"numerical_digest_sha256":digest(data),
        "path_summaries":data["path_summaries"],"execution":{"start_utc":utc,"end_utc":datetime.now(timezone.utc).isoformat(),
            "seconds_including_replay_and_refinement":elapsed,"python":platform.python_version(),"numpy":np.__version__},
        "slab_flexure_and_vertical_contact_enabled":True,"pullout_tie_enabled":True,"first_cracking_is_not_floor_failure":True,
        "postcracking_reinforcement_or_postbuckling_solved":False,"fracture_dynamics_solved":False,
        "impact_independently_computed":False,"fire_solved":False,"global_coupled":False,"blender_changed":False,
        "historical_collapse_verdict":None,"source_and_previous_inputs_unchanged":True}
    write_json(out/"results_v11d.json",results)
    write_json(out/"offline_manifest.json",{"iteration":"V11D","self_excluded":True,"files":[{"path":p.name,"sha256":sha(p),"bytes":p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file()]})
    print(json.dumps({k:v for k,v in results.items() if k!="path_summaries"},indent=2))


if __name__=="__main__":main()
