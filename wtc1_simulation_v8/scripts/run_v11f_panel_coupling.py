"""Reproducible cold coupling experiment; existing output folders refused."""
import argparse
import csv
import hashlib
import json
import os
import platform
import sys
import time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,__version__ as pillow_version
import v11f_panel_model as physics
import test_v11f_panel

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/"wtc1_simulation_v8/data/v11f_panel_coupling_predeclaration.json"


def read(path):return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def write_json(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
def write_csv(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)


def load_inputs(cfg):
    paths={"d":cfg["panel_configuration"],"e":cfg["section_configuration"]}
    inputs={k:read(ROOT/p) for k,p in paths.items()}
    paths["c"]=inputs["d"]["base_configuration"];inputs["c"]=read(ROOT/paths["c"])
    paths.update({"a":inputs["c"]["base_configuration"],"transfer":inputs["c"]["transfer"],"seats":inputs["c"]["seats"]})
    for k in ("a","transfer","seats"):inputs[k]=read(ROOT/paths[k])
    inputs["seats"]=inputs["seats"]["floor_truss_seats"]
    return inputs,paths


def calculate(cfg,inputs,sub=None,step=1.):
    results=[]
    for case in cfg["cases"]:
        data,_,_=physics.trace(cfg,inputs,case,sub,step);results.append(data)
    return results


def compare(cfg,reference,other,label,half=False):
    rows=[];accept=cfg["acceptance"]
    for a,b in zip(reference,other,strict=True):
        sa,sb=a["summary"],b["summary"];assert sa["id"]==sb["id"]
        fields={"max_slab_down_m":"displacement","actuator_reaction_N":"actuator_force","concrete_dissipated_J":"concrete_dissipation"}
        errors={v:0. for v in fields.values()};counts=0
        for phase in sorted(set(r["phase"] for r in a["history"])&set(r["phase"] for r in b["history"])):
            ar=[r for r in a["history"] if r["phase"]==phase];br=[r for r in b["history"] if r["phase"]==phase]
            bx=[r["phase_progress"] for r in br]
            for key,outkey in fields.items():
                floor=1e-6 if key=="max_slab_down_m" else 1.
                scale=max(floor,max(abs(r[key]) for r in ar))
                by=[r[key] for r in br]
                for r in ar:
                    if bx[0]-1e-12<=r["phase_progress"]<=bx[-1]+1e-12:
                        errors[outkey]=max(errors[outkey],abs(r[key]-float(np.interp(r["phase_progress"],bx,by)))/scale)
                        counts+=1
        same=sa["terminal"]==sb["terminal"] and sa["phase"]==sb["phase"] and sa["governing_kind"]==sb["governing_kind"]
        enddiff=abs(sa["phase_progress"]-sb["phase_progress"])/max(1e-6,sa["phase_progress"]) if sa["phase"]==sb["phase"] else 1.
        dtol=accept["half_step_response_relative"] if half else accept["mesh_common_displacement_relative"]
        ftol=accept["half_step_response_relative"] if half else accept["mesh_common_actuator_force_relative"]
        etol=accept["half_step_response_relative"] if half else accept["mesh_common_concrete_dissipation_relative"]
        ptol=accept["half_step_response_relative"] if half else accept["mesh_last_control_relative"]
        passes={"same_terminal_and_governing_kind":same,"end_parameter":enddiff<=ptol,"displacement":errors["displacement"]<=dtol,
                "actuator_force":errors["actuator_force"]<=ftol,"concrete_dissipation":errors["concrete_dissipation"]<=etol}
        rows.append({"case_id":sa["id"],"comparison":label,"reference_has_cracking":max(r["cracked_sections"] for r in a["history"])>0,
                     "response_gate_pass":all(passes.values()),"gates":passes,"common_values_compared":counts,
                     "end_parameter_relative_difference":enddiff,**{key+"_relative_difference":value for key,value in errors.items()},
                     "other_terminal":sb["terminal"],"other_governing_kind":sb["governing_kind"],"other_actuator_offset_m":sb["actuator_offset_m"],
                     "other_cracked_sections":sb["cracked_sections"],"other_concrete_dissipated_J":sb["concrete_dissipated_J"]})
    return rows


def audit(cfg,inputs,data,replay,meshes,half):
    tests,coupons=test_v11f_panel.run(cfg,inputs)
    def check(name,ok,evidence):tests.append({"test":name,"pass":bool(ok),"evidence":evidence})
    allruns=[data,replay,*meshes.values(),half]
    histories=[r for run in allruns for d in run for r in d["history"]]
    check("declared_14_unique_paths",len(data)==14 and len({d["summary"]["id"] for d in data})==14,len(data))
    check("deterministic_replay_exact",digest(data)==digest(replay),digest(data))
    maxima={k:max(r[k] for r in histories) for k in ("equilibrium_residual","exact_energy_residual","external_energy_residual")}
    for key,tol in (("equilibrium_residual",cfg["solver"]["relative_equilibrium_tolerance"]),
                    ("exact_energy_residual",cfg["acceptance"]["exact_material_plus_spring_energy_relative"]),
                    ("external_energy_residual",cfg["acceptance"]["whole_path_external_energy_relative"])):
        check("all_runs_"+key,maxima[key]<=tol,{"max":maxima[key],"tolerance":tol})
    force_error=max(abs(r["seat_reaction_N"]+r["actuator_reaction_N"]-r["gravity_load_N"])/max(1.,r["gravity_load_N"],abs(r["actuator_reaction_N"])) for r in histories)
    check("gravity_plus_actuator_vertical_balance",force_error<1e-8,force_error)
    check("all_runs_nominal_domain_not_overrun",max(r["max_DCR"] for r in histories)<1+1e-5,max(r["max_DCR"] for r in histories))
    check("all_runs_zero_global_energy_credit",all(r["global_energy_credit_J"]==0 for r in histories),"Local panel energy not sent to V11B or Blender")
    check("postcracked_panel_states_computed",any(r["cracked_sections"]>0 for r in histories),"A crack does not end the panel calculation")
    for key in ("concrete_dissipated_J","steel_dissipated_J","max_damage"):
        delta=min(b[key]-a[key] for run in allruns for d in run for a,b in zip(d["history"][:-1],d["history"][1:],strict=True))
        check("irreversible_"+key,delta>=-1e-8,delta)
    check("all_rejections_marked_uncommitted",all(not r["state_committed"] for run in allruns for d in run for r in d["rejected_trials"]),sum(len(d["rejected_trials"]) for run in allruns for d in run))
    physical=[r for run in allruns for d in run for r in d["terms"]]
    check("contact_and_tie_force_signs",all(r["force_N"]<=1e-8 for r in physical if r["kind"]=="contact") and all(r["force_N"]>=-1e-8 for r in physical if r["kind"]=="vertical_tie"),"No adhesion in contact or compression in tensile tie")
    check("no_old_bending_quadrature_exported_as_force",not any(r["kind"] in ("slab_axial","slab_bending") for r in physical),"Section N in N, M in Nm exported separately")
    local_recovery=[]
    for d in data:
        last=d["summary"]
        for key,outkey in (("stored_J_per_m","slab_stored_J"),("dissipated_J_per_m","dissipated_J")):
            actual=sum(p[key]*p["weight_m"] for p in d["sections"])
            local_recovery.append(abs(actual-last[outkey])/max(1.,abs(last[outkey])))
    check("section_J_per_m_integrates_to_panel_J",max(local_recovery)<1e-10,max(local_recovery))
    comparisons=[]
    for n,run in meshes.items():comparisons+=compare(cfg,data,run,f"SUBDIVISIONS_4_TO_{n}")
    halfrows=compare(cfg,data,half,"HALF_LOADING_STEP",True)
    # Spatial convergence is a distinct gate, not hidden inside the implementation count.
    fine=[r for r in comparisons if r["comparison"]=="SUBDIVISIONS_4_TO_8"]
    gate={"status":"PASS" if all(r["response_gate_pass"] for r in fine) else "POSTCRACKED_MESH_DEPENDENCE_NOT_CONVERGED",
          "passing_cases":sum(r["response_gate_pass"] for r in fine),"case_count":len(fine),
          "failing_cases":[r["case_id"] for r in fine if not r["response_gate_pass"]],
          "half_step_status":"PASS" if all(r["response_gate_pass"] for r in halfrows) else "STEP_DEPENDENCE_NOT_CONVERGED",
          "half_step_failing_cases":[r["case_id"] for r in halfrows if not r["response_gate_pass"]],
          "caveat":"Passing force/deflection gates alone is insufficient: local concrete dissipation is also compared. A single-band Gf check does not fix the number of distributed cracks."}
    return {"status":"PASS" if all(r["pass"] for r in tests) else "FAIL","test_count":len(tests),"tests_passed":sum(r["pass"] for r in tests),
            "tests":tests,"all_runs_residual_maxima":maxima,"vertical_balance_relative_error":force_error,
            "mesh_comparison":comparisons,"half_step_comparison":halfrows,"discretization_gate":gate},coupons


def figure(path,data,meshes,au):
    im=Image.new("RGB",(1600,1120),"#f1f5f8");draw=ImageDraw.Draw(im)
    def text(x,y,s,n=21,color="#273e50",bold=False):
        font=ImageFont.truetype("C:/Windows/Fonts/segoeui"+("b" if bold else "")+".ttf",n);draw.text((x,y),s,font=font,fill=color)
    text(45,25,"WTC 1 / V11F — dalle fissurable intégrée au panneau",33,bold=True)
    text(45,79,"Essais mécaniques à froid : treillis + dalle + contact + attaches. Aucun impact calculé ici.",23)
    draw.rounded_rectangle((35,128,1565,286),radius=16,fill="white")
    text(60,145,"Le calcul tient ensemble les efforts et l’énergie des composants.",26,bold=True)
    text(60,192,"Ferraillage et lois du béton hypothétiques ; géométrie équivalente et petits déplacements.")
    text(60,232,"Les déplacements ci-dessous sont imposés par un dispositif d’essai, pas causés par un avion.")
    def chart(x,y,w,h,title,xmax,ymax,xlabel,ylabel):
        draw.rounded_rectangle((x-43,y-96,x+w+33,y+h+85),radius=14,fill="white")
        text(x-18,y-82,title,25,bold=True);text(x-18,y-43,ylabel,17)
        def xy(a,b):return x+w*a/xmax,y+h-h*b/ymax
        for j in range(5):
            xx,yy=xy(xmax*j/4,ymax*j/4)
            draw.line((xx,y,xx,y+h),fill="#dce4eb");draw.line((x,yy,x+w,yy),fill="#dce4eb")
            text(xx-12,y+h+8,f"{xmax*j/4:.0f}",16);text(x-41,yy-10,f"{ymax*j/4:g}",16)
        text(x+98,y+h+47,xlabel,19);return xy
    ix={d["summary"]["id"]:d for d in data}
    names=["TRUSS_LOWER_PLAIN","TRUSS_LOWER_R01","TRUSS_LOWER_R02","TRUSS_LOWER_R04"]
    maximum=max(-r["actuator_reaction_N"]/1000 for name in names for r in ix[name]["history"] if r["phase"].startswith("actuator"))
    maximum=math_ceil_to(maximum,25.)
    xy=chart(94,421,630,305,"Abaissement local du treillis",80,maximum,"Abaissement imposé (mm)","Effort du dispositif vers le bas (kN)")
    colors=["#8e9aa0","#9970b1","#287db0","#c3893b"]
    for name,color in zip(names,colors,strict=True):
        h=[r for r in ix[name]["history"] if r["phase"].startswith("actuator")]
        if len(h)>1:draw.line([xy(-r["actuator_offset_m"]*1000,-r["actuator_reaction_N"]/1000) for r in h],fill=color,width=4)
    for j,(label,color) in enumerate(zip(("Sans armature","0,1 %","0,2 %","0,4 %"),colors,strict=True)):text(78+173*j,823,label,18,color,True)
    xy2=chart(895,421,602,305,"Fissuration : effet du découpage",18.1102,1.,"Position sur la portée (m)","Endommagement maximal de la section (0 à 1)")
    for run,color in ((meshes[2],"#999d9e"),(data,"#287db0"),(meshes[8],"#c3893b")):
        d=next(d for d in run if d["summary"]["id"]=="TRUSS_LOWER_R02")
        draw.line([xy2(r["x_m"],r["max_damage"]) for r in d["sections"]],fill=color,width=3)
    text(866,823,"Gris : 2 subdivisions   Bleu : 4   Ocre : 8",19)
    text(866,850,"Profils à l’état terminal propre à chaque maillage.",16)
    draw.rounded_rectangle((35,881,1565,1086),radius=16,fill="white")
    text(60,899,f"{au['tests_passed']}/{au['test_count']} contrôles de calcul réussis",26,bold=True)
    gate=au["discretization_gate"]
    label="Raffinement : tous les cas passent les critères choisis." if gate["status"]=="PASS" else f"Raffinement : {len(gate['failing_cases'])} cas restent sensibles au maillage."
    text(60,945,label,25,"#9a613a",True)
    text(60,989,"Première fissure, seuil de membrure et effondrement du plancher sont des événements différents.",21)
    text(60,1031,"Les énergies restent locales au panneau ; aucun transfert vers l’animation ou la propagation globale.",20)
    im.save(path)


def math_ceil_to(value,step):return float(np.ceil(value/step)*step)


def report(path,cfg,data,au,runtime,number_digest):
    gate=au["discretization_gate"];ix={d["summary"]["id"]:d for d in data};ref=ix["TRUSS_LOWER_R02"]["summary"]
    out=["# V11F — couplage à froid de la dalle fissurable au panneau","","## Résultat et niveau de vérification","",
         f"La dalle postfissurée V11E est assemblée au treillis et aux liaisons V11D : N et M sont calculés ensemble à chaque section ; contact et attaches réagissent aux déplacements indépendants. {len(data)} parcours et {sum(len(d['history']) for d in data)} états de référence ; {au['tests_passed']}/{au['test_count']} contrôles de calcul passent, dont62 régressions constitutives V11E. Ce nombre n'est pas une validation expérimentale ou historique.","",
         f"Le contrôle SPATIAL séparé est **{gate['status']}** : {gate['passing_cases']}/{gate['case_count']} cas passent toutes les exigences de comparaison4→8. Cas concernés par un échec : {', '.join(gate['failing_cases']) or 'aucun'}. Contrôle de demi-pas : {gate['half_step_status']} ; cas concernés : {', '.join(gate['half_step_failing_cases']) or 'aucun'}. Un calcul dont l'équilibre est correct peut encore être dépendant du maillage ; ces deux résultats ne sont pas fusionnés.","",
         "Aucun calcul d'avion, d'incendie, de propagation globale ou de dynamique Blender n'est modifié. Un seuil de membrure dans ce prototype ne signifie pas un effondrement du plancher.","",
         "## 1. Faits transcrits et constats directs","",
         "Les entrées conservées décrivent la paire équivalente de treillis713in de portée,80in de largeur tributaire et dalle4,35in. Les hypothèses géométriques de V11D sont reprises :16panneaux idéaux,63barres,17stations de liaison et32knuckles équivalents. La résistance et le ferraillage réels de chaque plancher ne sont pas documentés par cet ajout. Aucun PDF ni média d'archive n'est réanalysé ; empreintes des entrées et anciennes sorties conservées.","",
         "## 2. Résultats officiels et sources de méthode","",
         "Les tables déjà transcrites de sièges et de knuckles NIST sont des écrans de capacités hérités, pas de nouvelles observations ni des essais incendie reproduits. Le module E acier antérieur à20°C est conservé. Aucune chronologie NIST de dommage ou d'effondrement n'est imposée.","",
         "Le principe d'une section à chaque point d'intégration et de fonctions d'interpolation des déplacements est décrit par [OpenSees — élément à déplacements](https://opensees.berkeley.edu/OpenSees/manuals/usermanual/633.htm). Les efforts de section y satisfont un équilibre faible, au sens intégré, et pas forcément l'équilibre ponctuel exact à l'intérieur de chaque élément : [documentation actuelle](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/dispBeamColumn.html). L'aire de loi de traction Gf/largeur de bande est décrite dans [DIANA — paramètres du modèle](https://manuals.dianafea.com/d110/en/1465843-1466551-model-parameters.html). Le code ici est propre au projet ; ni OpenSees ni DIANA n'est exécuté, et notre choix Lch=poids de quadrature n'est pas présenté comme un réglage certifié par ces logiciels.","",
         "## 3. Affirmations d'archives","","Aucune affirmation nouvelle d'archive, identification vidéo ou mécanisme supplémentaire n'entre dans cette itération.","",
         "## 4. Hypothèses, discrétisation et limites de loi","",
         "Tout est à20°C, en petits déplacements. Béton et armatures reprennent exactement les lois V11E : dommage de traction avec adoucissement, fermeture élastique en compression, acier parfaitement plastique ; Ec2500ksi, fc3ksi, ft1MPa, Gf100J/m² et acier200GPa/fy400MPa sont des hypothèses. Les ratios d'acier total0/0,1/0,2/0,4% et les nappes symétriques/supérieure sont hypothétiques, parfaitement adhérents au béton. Pas d'écrasement, géométrie non linéaire, flambement postcritique, fluage, cisaillement de dalle, bac acier ou rupture d'armature.","",
         "Chaque nœud de dalle porte ux,w,theta. L'axial est linéaire et la déformée verticale est cubique : eps0 constant et kappa linéaire dans un élément. Deux points de Gauss le long de chaque élément et160fibres au milieu de bandes à travers l'épaisseur. En référence4subdivisions par panneau acier :65nœuds de dalle,64éléments,128sections et261degrés de liberté au total. Les subdivisions2/8 ne changent ni le treillis, ni les stations, ni la densité d'attaches, ni la position physique du dispositif.","",
         "Lch est le poids LONGITUDINAL du point de Gauss, soit la demi-longueur de l'élément :0,282971875/0,1414859375/0,07074296875m pour2/4/8subdivisions. Une bande entièrement fissurée dissipe bien AcGf indépendamment de sa longueur. Mais faire fissurer toutes les bandes double le nombre de bandes et l'énergie totale quand leur nombre double. Ce test isolé ne prouve donc pas l'objectivité de la localisation ou du nombre de fissures du panneau. Les dissipations calculées sont comparées séparément des flèches et des forces.","",
         "La section fournit [N,M] et sa matrice tangente couplée, sans imposer artificiellement N=0 comme dans l'essai de section V11E. L'assemblage utilise l'intégrale de Bᵀ[N,M] et de BᵀKsectionB. La charge80psf, poids propre compris, est appliquée une fois à la dalle par le vecteur réparti cohérent. Aucun ajout de masse ou de charge fictive de renfort. La bulle de charge élastique exacte de V11D n'est PAS superposée aux contraintes ni à l'énergie non linéaires ; les contraintes récupérées sont celles du champ FE approché.","",
         "La compression est vérifiée aux faces de la dalle aux extrémités des éléments, où la déformation linéaire de section peut être extrême, et non seulement aux points de Gauss intérieurs. La déformation maximale d'acier est aussi vérifiée aux extrémités. En traction, l'histoire de fissuration reste discrète aux points d'intégration.","",
         "Contact en compression et attaches tendues restent distincts ; le glissement horizontal inclut le décalage t/2 et le moment conjugué. Les capacités de membrures, sièges et attaches sont des premiers écrans nominaux : à leur franchissement, arrêt, sans suppression de barre ni propagation dynamique. Les compressions horizontales et soulèvements d'appuis non vérifiés sont signalés s'ils apparaissent.","",
         "Newton et recherche linéaire partent toujours du dernier état engagé. Les essais refusés sont annulés, puis le pas est réduit ; aucun ressort stabilisateur n'est ajouté. Une tangente non positive sous les déplacements imposés ou l'absence de convergence termine le parcours comme diagnostic, pas comme chute. La tangente est celle de ce modèle à petites déformations, sans raideur géométrique : sa positivité n'est pas la stabilité réelle de la tour.","",
         "### Chargements imposés","",
         "Deux montées de gravité : béton sans armature jusqu'à125% et hypothèse0,2% jusqu'à250%, avec arrêt au premier écran. Les autres essais partent de25% de la gravité de référence. Un déplacement de2mm est imposé à la dalle entre deux stations ; un autre dispositif abaisse le nœud8 du treillis jusqu'à100mm ou au premier écran. Ces mouvements sont des tests imposés, pas des dommages calculés d'avion. Tous leurs efforts et travaux sont inclus.","",
         "Un cycle de dalle va successivement0,−2,0,+2,0mm. Le cycle de treillis va0,−60,0mm ; son amplitude a été choisie après un premier essai monotone atteignant un écran près de68mm, afin de tester la recharge/décharge dans un domaine déjà exploré. Ce choix de test est divulgué : ce n'est ni un paramètre historique ni une prédiction aveugle d'une amplitude réelle.","",
         "## 5. Résultats dérivés","","| Cas | Fin | Gravité / référence | Déplacement imposé (mm) | Sections fissurées | Dissipation béton (J) |", "|---|---|---:|---:|---:|---:|"]
    for d in data:
        s=d["summary"];end="Borne du parcours" if s["terminal"].startswith("END_") else s["governing_kind"] if s["terminal"].startswith("FIRST_") else s["terminal"]
        out.append(f"| {s['id']} | {end} | {s['gravity_factor']:.5f} | {s['actuator_offset_m']*1000:.3f} | {s['cracked_sections']} | {s['concrete_dissipated_J']:.5f} |")
    out += ["",f"Le panneau sans armature retrouve la réponse élastique V11D avant fissuration. Le cas TRUSS_LOWER_R02 finit à déplacement imposé {ref['actuator_offset_m']*1000:.6f}mm, flèche nodale maximale de dalle {ref['max_slab_down_m']*1000:.6f}mm et {ref['cracked_sections']}sections fissurées. La somme des réactions de sièges ({ref['seat_reaction_N']:.6f}N) et de l'actionneur ({ref['actuator_reaction_N']:.6f}N) équilibre la gravité ({ref['gravity_load_N']:.6f}N). Oublier l'actionneur inventerait un déséquilibre et une charge supplémentaire.","",
            "Les nombres de sections fissurées sont des points d'intégration, pas un nombre observé de fissures, une fraction réelle endommagée ou une probabilité. Une fin de cycle avec déplacement imposé revenu à zéro peut conserver une réaction : ce n'est pas un déchargement libre, et encore moins une flèche résiduelle de tour calculée.","",
            "### Bilans et contrôles","",
            f"Sur référence, répétition, raffinements et demi-pas : résidu d'équilibre maximal {au['all_runs_residual_maxima']['equilibrium_residual']:.3e}, identité d'énergie exacte {au['all_runs_residual_maxima']['exact_energy_residual']:.3e}, écart de travail extérieur par trapèzes {100*au['all_runs_residual_maxima']['external_energy_residual']:.6f}%. Chaque incrément fait aussi l'objet d'un contrôle de travail pouvant réduire le pas. Les forces et moments sont normalisés équation par équation, sans les additionner comme des unités identiques.","",
            "Le travail matériau intègre les lois V11E exactement le long de l'incrément engagé ; on ajoute l'énergie élastique des barres/sièges/liaisons. L'intégration longitudinale multiplie les J/m par des poids en m pour obtenir des J du panneau. Le travail extérieur est calculé indépendamment avec les forces de gravité et réactions imposées, y compris les moments nodaux des charges réparties. Ce bilan isotherme ne contient ni chaleur ni chute dynamique et n'apporte aucune énergie de résistance au calcul global.","",
            "Contrôles analytiques : reproduction des champs axial/flexion et mouvements rigides ; section vectorisée identique à V11E ; inertie et solution élastique V11D avec défaut de quadrature milieu connu ; tangente globale par différences finies ; travail virtuel ; contact/recontact ; retour d'état sur échec ; conservation de la charge, de la géométrie et des unités. Il n'y a pas de revue multi-agent ni de comparaison à un solveur externe dans cette itération.","",
            "### Sensibilité spatiale4→8 — critères déclarés, pas ajustés après les résultats","",
            "| Cas | Même arrêt | Écart flèche normalisé (%) | Écart actionneur normalisé (%) | Écart béton normalisé, plancher 1 J (%) | Tous critères |", "|---|---|---:|---:|---:|---|"]
    for r in au["mesh_comparison"]:
        if r["comparison"]!="SUBDIVISIONS_4_TO_8":continue
        out.append(f"| {r['case_id']} | {r['gates']['same_terminal_and_governing_kind']} | {100*r['displacement_relative_difference']:.5f} | {100*r['actuator_force_relative_difference']:.5f} | {100*r['concrete_dissipation_relative_difference']:.5f} | {'PASS' if r['response_gate_pass'] else 'ÉCHEC'} |")
    fine_ref=next(r for r in au["mesh_comparison"] if r["comparison"]=="SUBDIVISIONS_4_TO_8" and r["case_id"]=="TRUSS_LOWER_R02")
    fine_D=fine_ref["other_concrete_dissipated_J"]
    true_D_relative=abs(fine_D-ref["concrete_dissipated_J"])/ref["concrete_dissipated_J"]
    out += ["","Comparaisons sur paramètres communs, séparées par phase/cycle, sans extrapolation après arrêt. Flèches normalisées par le maximum de la phase de référence (plancher 1 µm), forces par leur maximum (plancher 1 N), dissipation par son maximum (plancher 1 J). Pour les dissipations inférieures à 1 J, la dernière colonne numérique n'est donc PAS le pourcentage de la dissipation physique calculée. Le critère béton autorise alors un écart absolu de 0,1 J ; il ne faut pas le présenter comme une convergence relative de 10 % d'une très petite énergie.","",
            f"Exemple TRUSS_LOWER_R02 : dissipation finale {ref['concrete_dissipated_J']:.9f} J pour 4 subdivisions, contre {fine_D:.9f} J pour 8, soit {100*true_D_relative:.3f} % de la valeur de référence. Ce diagnostic compare leurs états terminaux propres, très proches mais pas strictement identiques. La figure de dommage emploie également les états terminaux propres à chaque maillage. Le contrôle sur paramètres communs reste celui déclaré dans le tableau.","",
            "## 6. Inconnues et suite","",
            "Ferraillage réel, paramètres béton/adhérence et détail de bac restent inconnus. La fissuration peut demeurer étalée entre plusieurs bandes et sensible au maillage malgré la bonne énergie d'une bande isolée. Les cas qui échouent au contrôle spatial ne doivent pas être présentés comme prédictions convergées de fissuration, d'énergie dissipée ou de résistance du plancher réel. Leurs données restent des diagnostics reproductibles, pas des résultats supprimés ou validés artificiellement.","",
            "V11G : résoudre d'abord les éventuelles dépendances du maillage/localisation mises en évidence, avec un test longitudinal indépendant et une stratégie de fissuration explicitement vérifiée, avant d'étendre le chauffage et les instabilités géométriques. Si tous les critères présents passent, compléter quand même le contrôle longitudinal de localisation/équilibre fort avant de créditer une fracture structurale. Puis couplage thermique, postflambement, assemblages avec colonnes/allèges, avion calculé et incendies spatialement résolus.","",
            f"Exécution CPU {runtime['seconds']:.3f}s ; Python{runtime['python']}, NumPy{runtime['numpy']}, Pillow{runtime['Pillow']}. Empreinte numérique : {number_digest}. Aucun logiciel installé, GPU ou Blender lancé. Les sorties antérieures sont protégées par empreinte.","",
            "## Livrables","","results_v11f.json, panel_inventory.json, path_summaries.csv, path_history.csv, section_states.csv, physical_component_forces.csv, slab_displacements.csv, rejected_trials.json, regularization_coupons.csv, convergence_comparison.json, numerical_audit.json, source_manifest.json, offline_manifest.json et synthese_v11f_panneau_fissure.png. Les historiques complets de tous les raffinements et du demi-pas sont conservés dans verification_runs.json pour permettre une vérification indépendante sans refaire le calcul.",""]
    # Editorial spacing only. No configuration, numerical value or acceptance gate changes.
    prose="\n".join(out)
    spacing={"dont62":"dont 62", "comparaison4":"comparaison 4", "treillis713in":"treillis de 713 in", ",80in":", 80 in",
             "dalle4,35in":"dalle de 4,35 in", ":16panneaux":": 16 panneaux", ",63barres":", 63 barres", ",17stations":", 17 stations",
             "et32knuckles":"et 32 knuckles", "à20°C":"à 20 °C", "Ec2500ksi":"Ec = 2500 ksi", "fc3ksi":"fc = 3 ksi",
             "ft1MPa":"ft = 1 MPa", "Gf100J/m²":"Gf = 100 J/m²", "acier200GPa/fy400MPa":"acier E = 200 GPa / fy = 400 MPa",
             "total0/0,1/0,2/0,4%":"total 0 / 0,1 / 0,2 / 0,4 %", "et160fibres":"et 160 fibres", "référence4subdivisions":"référence 4 subdivisions",
             ":65nœuds":": 65 nœuds", ",64éléments":", 64 éléments", ",128sections":", 128 sections", "et261degrés":"et 261 degrés",
             "subdivisions2/8":"subdivisions 2/8", ":0,282971875/0,1414859375/0,07074296875m":": 0,282971875 / 0,1414859375 / 0,07074296875 m",
             "pour2/4/8subdivisions":"pour 2/4/8 subdivisions", "charge80psf":"charge 80 psf", "jusqu'à125%":"jusqu'à 125 %",
             "hypothèse0,2%":"hypothèse 0,2 %", "jusqu'à250%":"jusqu'à 250 %", "de25%":"de 25 %", "de2mm":"de 2 mm",
             "jusqu'à100mm":"jusqu'à 100 mm", "va successivement0,−2,0,+2,0mm":"va successivement 0, −2, 0, +2, 0 mm",
             "va0,−60,0mm":"va 0, −60, 0 mm", "de68mm":"de 68 mm", "spatiale4→8":"spatiale 4→8",
             "}sections":"} sections"}
    for old,new in spacing.items():prose=prose.replace(old,new)
    path.write_text(prose,encoding="utf8")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",required=True);args=parser.parse_args()
    cfg=read(CONFIG);inputs,input_paths=load_inputs(cfg);output=(ROOT/args.output).resolve()
    allowed=[(ROOT/cfg["output_directory"]).resolve(),(ROOT/cfg["scratch_directory"]).resolve()]
    if not any(output==p or p in output.parents for p in allowed):raise ValueError("Outside declared output roots")
    if output.exists():raise FileExistsError("Preserve earlier run: output already exists")
    output.mkdir(parents=True)
    code=["wtc1_simulation_v8/scripts/"+f for f in ("v11f_panel_model.py","test_v11f_panel.py","run_v11f_panel_coupling.py","audit_v11f_release.py","test_v11e_section.py")]
    paths=list(dict.fromkeys([CONFIG.relative_to(ROOT).as_posix(),*input_paths.values(),*cfg["protected_files"],*code]))
    before={p:sha(ROOT/p) for p in paths};started=datetime.now(timezone.utc).isoformat();t=time.perf_counter()
    data=calculate(cfg,inputs);print("Reference14paths computed",flush=True)
    replay=calculate(cfg,inputs);print("Deterministic replay computed",flush=True)
    meshes={}
    for n in cfg["discretization"]["comparison_subdivisions"]:
        meshes[n]=calculate(cfg,inputs,n);print(f"Slab refinement{n} computed",flush=True)
    half=calculate(cfg,inputs,step=.5);print("Half-step paths computed",flush=True)
    au,coupons=audit(cfg,inputs,data,replay,meshes,half)
    runtime={"started_utc":started,"finished_utc":datetime.now(timezone.utc).isoformat(),"seconds":time.perf_counter()-t,
             "python":platform.python_version(),"numpy":np.__version__,"Pillow":pillow_version,"platform":platform.platform(),
             "executable":sys.executable,"OPENBLAS_NUM_THREADS":os.environ.get("OPENBLAS_NUM_THREADS"),"random_seed":cfg["random_seed"],"random_draw_used":False,
             "scope":"Reference/replay/refinements/tests; excludes report and figure rendering"}
    number_digest=digest(data)
    result={"iteration":"V11F","status":au["status"],"test_count":au["test_count"],"tests_passed":au["tests_passed"],
            "case_count":len(data),"state_count":sum(len(d["history"]) for d in data),"terminal_counts":dict(Counter(d["summary"]["terminal"] for d in data)),
            "summaries":[d["summary"] for d in data],"discretization_gate":au["discretization_gate"],"all_runs_residual_maxima":au["all_runs_residual_maxima"],
            "runtime":runtime,"numerical_digest_sha256":number_digest,"global_energy_credit_J":0.,"fire_solved":False,"aircraft_impact_computed":False,
            "geometrically_nonlinear":False,"blender_changed":False,"as_built_reinforcement_known":False,"counts_are_probabilities":False,"next_iteration":"V11G"}
    write_json(output/"results_v11f.json",result);write_json(output/"numerical_audit.json",au)
    write_json(output/"panel_inventory.json",[d["inventory"] for d in data])
    write_json(output/"verification_runs.json",{"mesh_runs":meshes,"half_step":half})
    write_json(output/"rejected_trials.json",[{"case_id":d["summary"]["id"],"trials":d["rejected_trials"]} for d in data])
    write_json(output/"convergence_comparison.json",{"mesh":au["mesh_comparison"],"half_step":au["half_step_comparison"]})
    for filename,key in (("path_history.csv","history"),("section_states.csv","sections"),("physical_component_forces.csv","terms"),("slab_displacements.csv","slab_nodes")):
        write_csv(output/filename,[r for d in data for r in d[key]])
    write_csv(output/"path_summaries.csv",[d["summary"] for d in data]);write_csv(output/"regularization_coupons.csv",coupons)
    write_json(output/"source_manifest.json",{"iteration":"V11F","input_and_protected_sha256":before,"method_references":cfg["method_references"],
               "source_pdf_or_media_analysis":False,"notes":"Reused frozen dimensions/capacity transcriptions and V11E hypothetical constitutive laws. No new WTC reinforcement identification."})
    figure(output/"synthese_v11f_panneau_fissure.png",data,meshes,au)
    report(output/"rapport_v11f_panneau_fissure.md",cfg,data,au,runtime,number_digest)
    after={p:sha(ROOT/p) for p in paths}
    manifest={"iteration":"V11F","implementation_status":au["status"],"discretization_status":au["discretization_gate"],
              "input_and_protected_unchanged":before==after,"input_sha256":after,
              "output_sha256":{p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()},"manifest_excludes_itself":True}
    write_json(output/"offline_manifest.json",manifest)
    print(json.dumps({"implementation_status":au["status"],"tests_passed":au["tests_passed"],"test_count":au["test_count"],
                      "mesh_gate":au["discretization_gate"],"runtime_seconds":runtime["seconds"],"source_integrity":before==after,
                      "failed_checks":[r for r in au["tests"] if not r["pass"]]},ensure_ascii=False),flush=True)
    if au["status"]!="PASS" or before!=after:raise SystemExit(1)


if __name__=="__main__":main()
