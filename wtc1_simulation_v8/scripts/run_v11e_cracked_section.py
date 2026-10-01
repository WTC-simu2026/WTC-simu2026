"""CPU-only V11E reproducibility runner. Refuses an existing output folder."""
import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import v11e_section_model as physics
import test_v11e_section

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"wtc1_simulation_v8/data/v11e_cracked_section_predeclaration.json"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()
def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,allow_nan=False,separators=(",",":")).encode()).hexdigest()
def write_json(path,obj): Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
def write_csv(path,rows):
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)


def calculate(cfg,n=None,step=1.): return [physics.trace(cfg,c,n,step) for c in cfg["cases"]]


def compare(reference,other,label):
    rows=[]
    for ref,alt in zip(reference,other,strict=True):
        assert ref["summary"]["id"]==alt["summary"]["id"]
        scale=max(1.,ref["summary"]["peak_absolute_M_Nm"])
        errors=[]
        for segment in sorted(set(r["segment"] for r in ref["history"]) & set(r["segment"] for r in alt["history"])):
            if segment<0: continue  # Axial preload separately checked by force/energy balances.
            a=sorted((r for r in ref["history"] if r["segment"]==segment),key=lambda r:r["kappa_per_m"])
            b=sorted((r for r in alt["history"] if r["segment"]==segment),key=lambda r:r["kappa_per_m"])
            x=[r["kappa_per_m"] for r in b];y=[r["M_Nm"] for r in b]
            for r in a:
                if x[0]-1e-12<=r["kappa_per_m"]<=x[-1]+1e-12:
                    errors.append(abs(r["M_Nm"]-float(np.interp(r["kappa_per_m"],x,y)))/scale)
        rs=ref["summary"];os=alt["summary"]
        rows.append({"case_id":rs["id"],"comparison":label,"same_terminal":rs["terminal"]==os["terminal"],
                     "common_states_compared":len(errors),"moment_max_difference_over_reference_peak":max(errors,default=0.),
                     "terminal_curvature_difference_relative":abs(rs["last_kappa_per_m"]-os["last_kappa_per_m"])/max(1e-6,abs(rs["last_kappa_per_m"])),
                     "other_last_kappa_per_m":os["last_kappa_per_m"],"other_peak_absolute_M_Nm":os["peak_absolute_M_Nm"],
                     "other_max_external_energy_residual":os["max_external_energy_residual"]})
    return rows


def coupons(cfg):
    rows=[];c=cfg["concrete"]
    for length in (.05,.1,.2):
        mat=physics.Concrete(c["E20_ksi"]*physics.KSI,c["ft20_MPa"]*1e6,c["fc20_ksi"]*physics.KSI,c["fracture_energy_J_m2"],length)
        state=physics.zero_concrete(1);a=0.
        vertices=[0.,mat.e0,.5*(mat.e0+mat.ef),0.,-2*mat.e0,0.,mat.ef,0.,-2*mat.e0,0.]
        for seg,b in enumerate(vertices):
            for e in np.linspace(a,b,41)[1:]:
                state=physics.concrete_trial(mat,state,[e])
                rows.append({"coupon_id":f"CONCRETE_L{length}","segment":seg,"strain":float(e),"stress_Pa":float(state["stress"][0]),
                             "damage":float(state["damage"][0]),"plastic_strain":None,"Lch_m":length,
                             "stored_J_m3":float(state["stored"][0]),"dissipated_J_m3":float(state["dissipated"][0]),"work_J_m3":float(state["work"][0])})
            a=b
    s=cfg["reinforcement"];mat=physics.Steel(s["E_GPa"]*1e9,s["fy_MPa"]*1e6)
    state=physics.zero_steel(1);a=0.;ey=mat.fy/mat.E
    for seg,b in enumerate((0.,3*ey,0.,-3*ey,0.,3*ey,0.)):
        for e in np.linspace(a,b,81)[1:]:
            state=physics.steel_trial(mat,state,[e])
            rows.append({"coupon_id":"STEEL_ELASTIC_PP","segment":seg,"strain":float(e),"stress_Pa":float(state["stress"][0]),
                         "damage":None,"plastic_strain":float(state["plastic"][0]),"Lch_m":None,
                         "stored_J_m3":float(state["stored"][0]),"dissipated_J_m3":float(state["dissipated"][0]),"work_J_m3":float(state["work"][0])})
        a=b
    return rows


def audit(cfg,data,replay,meshes,half,base,previous):
    tests=test_v11e_section.run(cfg)
    def check(name,ok,evidence): tests.append({"test":name,"pass":bool(ok),"evidence":evidence})
    summaries=[d["summary"] for d in data];hist=[r for d in data for r in d["history"]]
    check("declared_14_cases_unique",len(summaries)==14 and len({r["id"] for r in summaries})==14,len(summaries))
    check("deterministic_replay_exact",digest(data)==digest(replay),digest(data))
    g=base["floor_bay"];cc=g["concrete_hypotheses"]
    check("cached_geometry_and_concrete_hypotheses_preserved",cfg["section"]["width_in"]==g["width_per_single_truss_in"]*g["single_trusses_per_pair"] and
          cfg["section"]["equivalent_thickness_in"]==g["equivalent_slab_thickness_in"] and cfg["concrete"]["E20_ksi"]==cc["elastic_modulus_20c_ksi"] and
          cfg["concrete"]["fc20_ksi"]==cc["compression_strength_20c_ksi"] and cfg["concrete"]["ft20_MPa"]==previous["slab"]["tensile_screen_20c_MPa"],"No substituted dimension or material value hidden in code")
    maxima={k:max(r[k] for r in hist) for k in ("axial_residual","exact_energy_residual","external_energy_residual")}
    for key,tol in (("axial_residual",cfg["acceptance"]["relative_axial_equilibrium"]),
                    ("exact_energy_residual",cfg["acceptance"]["relative_exact_material_energy_balance"]),
                    ("external_energy_residual",cfg["acceptance"]["external_trapezoid_energy_relative"])):
        check("all_paths_"+key,maxima[key]<=tol,{"max":maxima[key],"tolerance":tol})
    check("no_promoted_state_beyond_domain",max(r["domain_ratio"] for r in hist)<1+1e-8,max(r["domain_ratio"] for r in hist))
    check("all_path_states_one_positive_axial_root",all(r["positive_axial_roots"]==1 for r in hist),len(hist))
    check("no_global_energy_or_panel_coupling",all(r["global_energy_credit_J"]==0 for r in hist) and not cfg["panel_coupling"],"Local section only; J/m is never added to global propagation")
    check("no_damage_healing_on_all_paths",all(all(b["max_damage"]>=a["max_damage"]-1e-12 for a,b in zip(d["history"][:-1],d["history"][1:],strict=True)) for d in data),"Max-history damage never decreases")
    for field in ("concrete_dissipated_J_per_m","steel_dissipated_J_per_m"):
        minimum=min(b[field]-a[field] for d in data for a,b in zip(d["history"][:-1],d["history"][1:],strict=True))
        check("monotone_"+field,minimum>=-1e-9,minimum)
    fibers=[r for d in data for r in d["fibers"]]
    check("fiber_damage_bounds",all(-1e-12<=r["damage"]<=1+1e-12 for r in fibers if r["kind"]=="concrete"),"No negative or >1 concrete damage")
    check("reinforcement_stress_bounded_by_fy",all(abs(r["stress_Pa"])<=cfg["reinforcement"]["fy_MPa"]*1e6*(1+1e-12) for r in fibers if r["kind"]=="reinforcement"),cfg["reinforcement"]["fy_MPa"])
    check("fiber_recovery_reproduces_section_resultants",all(abs(sum(r["stress_Pa"]*r["area_m2"] for r in d["fibers"])-d["history"][-1]["N_N"])<1e-6 and
          abs(sum(-r["y_m"]*r["stress_Pa"]*r["area_m2"] for r in d["fibers"])-d["history"][-1]["M_Nm"])<1e-7 for d in data),len(data))
    indexed={d["summary"]["id"]:d for d in data}
    mirror=max(abs(a["M_Nm"]+b["M_Nm"]) for a,b in zip(indexed["MONO_TOP_REVERSED"]["history"],indexed["MONO_BOTTOM_ONLY"]["history"],strict=True))
    check("reinforcement_mirror_and_bending_sign",mirror<1e-6,mirror)
    alias=max(abs(a["M_Nm"]-b["M_Nm"]) for a,b in zip(indexed["MONO_GF50"]["history"],indexed["MONO_LCH020"]["history"],strict=True))
    check("Gf_over_Lch_nonidentifiability_visible",alias<1e-8,{"max_difference_Nm":alias,"meaning":"Same Gf/Lch gives the same stress-strain section law, not a unique material calibration"})
    comparisons=[]
    for n,result in meshes.items(): comparisons+=compare(data,result,f"FIBERS_160_TO_{n}")
    half_rows=compare(data,half,"HALF_CURVATURE_STEP")
    for label,rows,mtol,ktol in (("fiber_mesh_160_to_320",[r for r in comparisons if r["comparison"]=="FIBERS_160_TO_320"],
                                cfg["acceptance"]["mesh_160_to_320_moment_relative"],cfg["acceptance"]["mesh_160_to_320_domain_curvature_relative"]),
                               ("half_step",half_rows,cfg["acceptance"]["half_step_moment_relative"],cfg["acceptance"]["half_step_domain_curvature_relative"])):
        check(label+"_same_termination",all(r["same_terminal"] for r in rows),[r for r in rows if not r["same_terminal"]])
        check(label+"_moment_curve",all(r["common_states_compared"]>0 and r["moment_max_difference_over_reference_peak"]<=mtol for r in rows),max(r["moment_max_difference_over_reference_peak"] for r in rows))
        check(label+"_domain_curvature",max(r["terminal_curvature_difference_relative"] for r in rows)<=ktol,max(r["terminal_curvature_difference_relative"] for r in rows))
    fine=max(d["summary"]["max_external_energy_residual"] for d in half)
    check("half_step_reduces_max_external_integration_error",fine<maxima["external_energy_residual"],{"reference":maxima["external_energy_residual"],"half_step":fine})
    return {"status":"PASS" if all(t["pass"] for t in tests) else "FAIL","test_count":len(tests),"tests_passed":sum(t["pass"] for t in tests),
            "tests":tests,"path_residual_maxima":maxima,"mesh_comparison":comparisons,"half_step_comparison":half_rows,
            "independent_external_integration_note":"Endpoint trapezoidal generalized work is separate from exact material work, with finite integration error; verified again at half step. No thermal or global dynamic balance."}


def figure(path,data,audit_result):
    im=Image.new("RGB",(1600,1160),"#f1f5f8");dr=ImageDraw.Draw(im)
    def font(n,bold=False): return ImageFont.truetype("C:/Windows/Fonts/segoeui"+("b" if bold else "")+".ttf",n)
    def text(x,y,s,n=21,color="#253c50",bold=False): dr.text((x,y),s,font=font(n,bold),fill=color)
    text(45,25,"WTC 1 / V11E — résistance de dalle après fissuration",33,bold=True)
    text(45,78,"Section isolée à 20 °C. Ferraillage supposé ; ni plancher complet ni calcul d’effondrement.",23)
    dr.rounded_rectangle((35,125,1565,308),radius=16,fill="white")
    text(60,141,"Ce qui est représenté",25,bold=True)
    text(60,183,"Bande équivalente : largeur 2,032 m × épaisseur 0,11049 m.")
    text(60,219,"Béton fissurable + armatures plastifiables, parfaitement adhérentes.")
    text(60,255,"Référence : acier total 0,2 % de la section, partagé en deux nappes.")
    dr.rectangle((1110,160,1510,268),fill="#cbd4da",outline="#75868e",width=2)
    for yy in (184,244):
        for xx in range(1150,1490,65): dr.ellipse((xx-5,yy-5,xx+5,yy+5),fill="#397ca8")
    text(1100,277,"Schéma hypothétique, non à l’échelle",15)
    indexed={d["summary"]["id"]:d for d in data}
    def chart(box,title,xlo,xhi,ylo,yhi,xlabel,ylabel):
        x,y,w,h=box;dr.rounded_rectangle((x-35,y-95,x+w+35,y+h+85),radius=15,fill="white")
        text(x-12,y-81,title,25,bold=True);text(x-12,y-43,ylabel,17)
        def xy(a,b):return (x+w*(a-xlo)/(xhi-xlo),y+h-h*(b-ylo)/(yhi-ylo))
        for i in range(5):
            xv=xlo+(xhi-xlo)*i/4;yv=ylo+(yhi-ylo)*i/4
            xx,yy=xy(xv,yv)
            dr.line((xx,y,xx,y+h),fill="#dce5eb");dr.line((x,yy,x+w,yy),fill="#dce5eb")
            text(xx-19,y+h+8,f"{xv:.2f}",16);text(x-39,yy-10,f"{yv:g}",16)
        text(x+120,y+h+44,xlabel,19)
        return xy
    xy=chart((92,435,635,326),"Même section, plusieurs taux d’armatures",0,.08,0,20,"Courbure imposée (1/m)","Moment résistant de la bande (kN·m)")
    for name,color in (("MONO_PLAIN","#8a969d"),("MONO_RHO01","#9a6eab"),("MONO_REFERENCE","#287fb1"),("MONO_RHO04","#c0813a")):
        dr.line([xy(r["kappa_per_m"],r["M_Nm"]/1000) for r in indexed[name]["history"]],fill=color,width=4)
    for i,(label,color) in enumerate((("Sans armature","#8a969d"),("0,1 %","#9a6eab"),("0,2 %","#287fb1"),("0,4 %","#c0813a"))):
        text(81+i*171,860,label,19,color,bold=True)
    xy2=chart((889,435,610,326),"Chargements alternés / référence 0,2 %",-.05,.05,-12,12,"Courbure imposée (1/m)","Moment (kN·m), positif et négatif")
    dr.line([xy2(r["kappa_per_m"],r["M_Nm"]/1000) for r in indexed["CYCLE_REFERENCE"]["history"]],fill="#287fb1",width=3)
    text(872,860,"Retour à courbure nulle ≠ retour à moment nul.",20)
    dr.rounded_rectangle((35,920,1565,1124),radius=16,fill="white")
    text(60,937,f"{audit_result['tests_passed']}/{audit_result['test_count']} contrôles numériques et analytiques réussis",26,bold=True)
    text(60,983,"Fissuration, plastification des armatures et limite en compression restent distinctes.",23)
    text(60,1024,"Le découpage et les pas sont raffinés ; les énergies sont comptées par mètre de longueur.",21)
    text(60,1065,"Les courbes sont conditionnelles aux hypothèses. Aucun verdict historique ni mise à jour Blender.",21,color="#8c5343")
    im.save(path)


def report(path,cfg,data,au,runtime,number_digest):
    ix={d["summary"]["id"]:d for d in data};ref=ix["MONO_REFERENCE"];cyc=ix["CYCLE_REFERENCE"]
    fine=[r for r in au["mesh_comparison"] if r["comparison"]=="FIBERS_160_TO_320"]
    out=["# V11E — section de dalle après fissuration", "", "## Résultat et périmètre", "",
         f"La section peut maintenant franchir une première fissure, reprendre des efforts dans les armatures et suivre des chargements alternés. {len(data)} parcours, {sum(len(d['history']) for d in data)} états et {au['tests_passed']}/{au['test_count']} contrôles passent. Il s'agit d'une vérification numérique de lois hypothétiques, pas d'une validation expérimentale ou d'un verdict sur l'effondrement du WTC1.", "",
         "V11D, le panneau, le calcul réduit V11B et Blender restent inchangés. V11E fournit une bibliothèque de section avec essais/validation avant couplage. Aucun déplacement de plancher, impact d'avion, incendie ou capacité globale nouvelle n'est déduit de ces courbes.","",
         "## 1. Faits transcrits ou directement constatés", "",
         "Les entrées locales V11A/V11D contiennent une bande équivalente de 80 in (2,032 m) de largeur et 4,35 in (0,11049 m) d'épaisseur. Ce sont les dimensions du modèle d'exemple déjà transcrit, pas une section réelle de dalle-bac-armature reconstruite. La présente itération ne relit aucune archive ni aucun PDF source et n'ajoute aucun ferraillage documenté. Les fichiers protégés sont contrôlés par empreinte avant/après.", "",
         "## 2. Résultats de modèles officiels et références de méthode", "",
         "Aucun résultat NIST d'effondrement ou de feu n'entre dans la loi de section. Les capacités de knuckles de V11D ne sont pas activées ici. La géométrie équivalente reste héritée de l'exemple NIST local, donc n'est pas une identification géométrique indépendante.", "",
         "La documentation primaire [DIANA — traction](https://manuals.dianafea.com/d108/en/1219784-1221375-total-strain-crack-models.html) décrit une famille de lois adoucissantes associées à une énergie de fissuration et une largeur de bande. Elle distingue aussi ouverture, déchargement sécant et fermeture en compression : [DIANA — états de fissure](https://manuals.dianafea.com/d102/Theory/Theorych74.html). Ces idées guident une simplification unidimensionnelle explicitement écrite ci-dessous, sans exécuter ni reproduire tout DIANA. La documentation [OpenSees — ElasticPP](https://opensees.berkeley.edu/OpenSees/manuals/usermanual/171.htm) définit la famille élastique-parfaitement plastique retenue pour l'acier ; OpenSees n'est pas exécuté. Aucun de ces documents ne donne les paramètres réels du ferraillage WTC1. Sources consultées le 6 septembre 2026.", ""]
    out += ["", "## 3. Affirmations d'archives locales", "", "Aucune nouvelle affirmation d'archive, analyse vidéo, identification de dommage ou hypothèse de mécanisme supplémentaire n'est introduite.", "",
            "## 4. Hypothèses du modèle", "",
            "Tout est isotherme à 20 °C. Béton : E = 2 500 ksi, fc = 3 ksi, ft = 1 MPa, déjà hypothétiques en V11A/V11D. Compression linéaire jusqu'au seul écran fc ; au-delà, arrêt, sans loi d'écrasement. Traction adoucissante avec Gf = 50/100/150 J/m² et longueur de bande Lch = 0,05/0,10/0,20 m selon les variantes. Ces nombres ne sont ni mesurés sur le WTC ni ajustés pour imposer un résultat.", "",
            "Armatures : E = 200 GPa, fy = 400 MPa, aire totale 0/0,1/0,2/0,4 % de la section brute. Positions possibles : une nappe supérieure, une inférieure, ou deux nappes symétriques partageant l'aire totale. Les centres sont à 25 mm des faces. Grade, aires et positions sont supposés ; aucune correspondance à un plan de construction n'est revendiquée. Adhérence parfaite, pas de glissement acier-béton, bac acier, effort tranchant, membrane transverse, fatigue, rupture ou flambement des armatures. Le seuil de déformation acier de 1 % limite le domaine choisi, ce n'est pas une déformation de rupture mesurée.", "",
            "Le béton est intégré en 160 bandes au milieu de chacune, avec raffinements 80 et 320. Son aire totale est uniformément réduite de l'aire d'acier : Ac + As = A brute. Ce remplacement diffus évite un ajout d'aire, mais ne reproduit pas les trous des barres. La longueur Lch est LONGITUDINALE, indépendante du nombre de fibres dans l'épaisseur ; elle n'est ni l'épaisseur de dalle ni la hauteur d'une fibre.", "",
            "### Lois, signes et énergie", "",
            "Déformation plane : eps(y) = eps0 − y kappa, y vers le haut ; traction positive. N = somme(A sigma), M = −somme(A y sigma). La matrice tangente est la somme des A Et [1,−y]ᵀ[1,−y]. N est en N, M en N·m, kappa en m⁻¹. Le travail de section N d(eps0) + M d(kappa) est en J/m de longueur, pas en J d'un étage.", "",
            "Béton : e0 = ft/E ; ef = 2 Gf/(ft Lch) > e0. Enveloppe sigma = E eps jusqu'à e0, puis ft (ef−eps)/(ef−e0), puis zéro. r est le maximum historique de traction ; déchargement/rechargement par la sécante E(1−d) = sigma_enveloppe(r)/r. Compression sigma = E eps après fermeture à eps = 0, sans effacer r. Il n'y a pas de restauration de résistance en traction ni de plancher artificiel de contrainte. Cette fermeture réversible ne modélise ni frottement des lèvres ni déformation permanente du béton en compression.", "",
            "Énergie stockée béton psi = sigma eps/2 ; dissipation D(r) = ft ef/(2(ef−e0)) × bornage(r−e0, 0, ef−e0). À ouverture complète, D = Gf/Lch, pré-pic compris. Le travail est calculé séparément par intégration exacte des segments de contrainte, pas défini par psi + D. La plasticité parfaite d'acier conserve eps_p ; retour de sigma à ±fy, D incrémentale = fy |delta eps_p|, psi = sigma²/(2E). Les cycles vérifient l'irréversibilité et W = psi + D.", "",
            "La courbure est imposée et l'effort axial est nul, sauf un cas avec précompression de 5 % fc Ac. Les changements de pente de l'équation axiale sont énumérés pour trouver toutes les racines à tangente axiale positive : une seule est requise. Une racine multiple ou absente arrête le parcours comme non résolu ; aucune stabilisation n'est ajoutée. Les intervalles neutres sans raideur sont comptés à part. Cette règle de suivi quasistatique n'est pas une preuve de stabilité dynamique, notamment sur une branche où le moment diminue.", "",
            "Les essais de recherche d'équilibre ne modifient jamais l'état engagé. La compression maximale est récupérée aux FACES extérieures exactes de la bande, pas au milieu de la première fibre intérieure. Les seuils fc/1 % sont localisés par subdivision du dernier incrément ; fissuration et plastification sont enregistrées mais n'arrêtent pas la section. Leurs premières courbures publiées sont les premiers échantillons détectés, pas des seuils continus de même précision que la limite de domaine.", "",
            "## 5. Résultats dérivés", "", "### Parcours de section", "",
            "| Cas | Fin | Courbure finale (m⁻¹) | Moment final (kN·m) | Maximum absolu échantillonné (kN·m) |", "|---|---|---:|---:|---:|"]
    for d in data:
        s=d["summary"];ending="Borne du parcours" if s["terminal"]=="END_WITHIN_DECLARED_SECTION_DOMAIN" else "Limite compression" if s["terminal"]=="CONCRETE_COMPRESSION_DOMAIN" else s["terminal"]
        out.append(f"| {s['id']} | {ending} | {s['last_kappa_per_m']:.6f} | {s['last_M_Nm']/1000:.3f} | {s['peak_absolute_M_Nm']/1000:.3f} |")
    out += ["",f"À la même courbure imposée 0,08 m⁻¹, le moment final vaut {ix['MONO_PLAIN']['summary']['last_M_Nm']/1000:.3f} kN·m sans armature, {ix['MONO_RHO01']['summary']['last_M_Nm']/1000:.3f} à 0,1 %, {ref['summary']['last_M_Nm']/1000:.3f} à 0,2 % et {ix['MONO_RHO04']['summary']['last_M_Nm']/1000:.3f} à 0,4 %. Ce sont des réponses d'une section isolée au chargement imposé, pas des charges admissibles de plancher. L'effet de position est marqué : une nappe supérieure donne une autre réponse qu'une nappe inférieure sous le même signe de flexion ; inverser simultanément nappe et courbure reproduit le cas miroir.","",
            f"Le parcours cyclique de référence termine à courbure nulle avec un moment de {cyc['summary']['last_M_Nm']:.3f} N·m encore fourni par le dispositif qui impose la courbure. Ce n'est PAS un état libre de tout moment, ni la flèche résiduelle d'un plancher déchargé. Les dissipations finales sont {cyc['summary']['last_concrete_dissipation_J_per_m']:.3f} J/m pour le béton et {cyc['summary']['last_steel_dissipation_J_per_m']:.3f} J/m pour l'acier ; elles ne sont transférées à aucun calcul de propagation.","",
            "Les variantes Gf=50 avec Lch=0,10 et Gf=100 avec Lch=0,20 ont exactement le même rapport Gf/Lch et la même courbe de section. Ce test rend visible une non-identifiabilité : une courbe contrainte-déformation seule ne détermine pas séparément ces deux paramètres. Le contrôle de travail Gf est effectué séparément sur une bande de longueur déclarée.","",
            "### Vérifications et reproduction", "",
            f"{au['tests_passed']}/{au['test_count']} contrôles réussis, dont {len(test_v11e_section.run(cfg))} contrôles analytiques et d'intégration séparée : enveloppes, fermeture/recharge, énergie de fissuration, plasticité alternée, section élastique, section pré-fissurée armée avec axe neutre analytique, tangente par différences finies, travail des efforts généralisés, racines comparées à une bissection indépendante et arrêts aux limites. Il n'y a pas de relecture par un agent indépendant ni de confrontation à un autre solveur dans cette itération.","",
            f"Résidus relatifs maximaux : équilibre axial {au['path_residual_maxima']['axial_residual']:.3e}, identité énergétique exacte des matériaux {au['path_residual_maxima']['exact_energy_residual']:.3e}. Le travail extérieur calculé séparément par trapèzes présente une erreur maximale de {100*au['path_residual_maxima']['external_energy_residual']:.4f} %, contrôlée par un calcul à demi-pas. Cette petite erreur d'intégration n'est pas une précision physique sur le WTC.","",
            f"Raffinement 160→320 : écart maximal des moments {100*max(r['moment_max_difference_over_reference_peak'] for r in fine):.5f} % du pic de référence, et écart de courbure terminale {100*max(r['terminal_curvature_difference_relative'] for r in fine):.5f} %. Demi-pas : écarts correspondants {100*max(r['moment_max_difference_over_reference_peak'] for r in au['half_step_comparison']):.5f} % et {100*max(r['terminal_curvature_difference_relative'] for r in au['half_step_comparison']):.5f} %. Comparaison par segment cyclique et domaine de courbure commun, sans comparer des branches de cycles différentes ni extrapoler après une limite.","",
            f"Exécution CPU : {runtime['seconds']:.3f} s, Python {runtime['python']}, NumPy {runtime['numpy']}. Empreinte de reproduction numérique : {number_digest}. Configuration et scripts hachés dans le manifeste ; résultats antérieurs conservés. Aucun GPU, logiciel installé ni Blender lancé.","",
            "## 6. Limites, contradictions et suite", "",
            "La résistance réelle après fissuration reste indéterminée sans ferraillage, adhérence, courbes béton/acier et géométrie de bac mieux documentés. Les vérifications passent pour les lois déclarées ; elles ne certifient pas leur représentativité historique. Une borne de parcours atteinte sans écran franchi ne prouve pas la survie du plancher, et le franchissement de fc ne prouve pas son effondrement. Pas de chauffage/cycles thermiques, fluage, écrasement, fracture d'armature, durée, vitesse, cisaillement, interaction 3D ou localisation longitudinale résolue.","",
            "Prochaine V11F : intégrer cette section trial/commit dans le panneau V11D avec le contact et les attaches ; récupérer d'abord le cas élastique, puis vérifier l'équilibre et le travail du panneau postfissuré. Choisir et justifier la longueur de fissuration longitudinale lors du maillage ; ne pas utiliser les 160 fibres comme 160 fissures. Traiter les branches adoucissantes, retours d'état et convergence avant d'en tirer une redistribution ou une rupture d'attache. Puis géométrie non linéaire, postflambement, liaisons colonnes/allèges, impact calculé et incendies, sans issue prédéfinie.","",
            "## Fichiers", "", "results_v11e.json ; section_inventory.json ; section_summaries.csv ; section_history.csv ; section_fibers.csv ; cycle_vertices.csv ; material_coupons.csv ; convergence_comparison.csv ; numerical_audit.json ; source_manifest.json ; offline_manifest.json ; synthese_v11e_section_fissuree.png. Code : v11e_section_model.py, test_v11e_section.py et run_v11e_cracked_section.py. Toute répétition utilise un nouveau dossier, jamais une sortie existante.",""]
    path.write_text("\n".join(out),encoding="utf8")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",required=True);args=parser.parse_args()
    output=(ROOT/args.output).resolve();cfg=read(CFG)
    allowed=[(ROOT/cfg["scratch_directory"]).resolve(),(ROOT/cfg["output_directory"]).resolve()]
    if not any(output==p or p in output.parents for p in allowed): raise ValueError("Output outside declared V11E folders")
    if output.exists(): raise FileExistsError("Preserve earlier attempt: output folder already exists")
    output.mkdir(parents=True)
    paths=list(dict.fromkeys([cfg["base_configuration"],cfg["previous_configuration"],*cfg["protected_files"],
              CFG.relative_to(ROOT).as_posix(),"wtc1_simulation_v8/scripts/v11e_section_model.py",
              "wtc1_simulation_v8/scripts/test_v11e_section.py","wtc1_simulation_v8/scripts/run_v11e_cracked_section.py"]))
    before={p:sha(ROOT/p) for p in paths};started=datetime.now(timezone.utc).isoformat();tic=time.perf_counter()
    data=calculate(cfg);print("Reference sections computed",flush=True)
    replay=calculate(cfg);print("Deterministic replay computed",flush=True)
    meshes={n:calculate(cfg,n) for n in cfg["section"]["verification_concrete_fibers"]};print("Fiber refinements computed",flush=True)
    half=calculate(cfg,step=.5);print("Half-step paths computed",flush=True)
    au=audit(cfg,data,replay,meshes,half,read(ROOT/cfg["base_configuration"]),read(ROOT/cfg["previous_configuration"]))
    runtime={"started_utc":started,"finished_utc":datetime.now(timezone.utc).isoformat(),"seconds":time.perf_counter()-tic,
             "python":platform.python_version(),"numpy":np.__version__,"platform":platform.platform(),"executable":sys.executable,
             "random_seed":cfg["random_seed"],"random_draw_used":False,"gpu":False,
             "timing_scope":"Numerical reference, replay, refinements and audit; excludes report/figure generation"}
    numbers=digest(data)
    source_manifest={"iteration":"V11E","inputs_and_protected_sha256":before,"method_references":cfg["method_sources"],
                     "source_archive_reread":False,"source_pdf_reread":False,"web_method_reference_consultation":True,
                     "provenance":"Dimension and Ec/fc/ft reuse checked against old configurations; new reinforcement/Gf/Lch are explicit hypotheses."}
    summaries=[d["summary"] for d in data]
    results={"iteration":"V11E","scope":"ISOTHERMAL_LOCAL_SECTION_NOT_PANEL_OR_COLLAPSE","status":au["status"],
             "runtime":runtime,"case_count":len(data),"state_count":sum(len(d["history"]) for d in data),
             "terminal_counts":dict(Counter(s["terminal"] for s in summaries)),"test_count":au["test_count"],"tests_passed":au["tests_passed"],
             "summaries":summaries,"path_residual_maxima":au["path_residual_maxima"],"numerical_digest_sha256":numbers,
             "global_energy_credit_J":0.,"panel_coupled":False,"fire_solved":False,"blender_changed":False,
             "as_built_reinforcement_known":False,"counts_are_probabilities":False,"next_iteration":"V11F"}
    write_json(output/"results_v11e.json",results);write_json(output/"numerical_audit.json",au)
    write_json(output/"section_inventory.json",[d["inventory"] for d in data]);write_json(output/"source_manifest.json",source_manifest)
    for filename,rows in (("section_summaries.csv",summaries),("section_history.csv",[r for d in data for r in d["history"]]),
                          ("section_fibers.csv",[r for d in data for r in d["fibers"]]),("cycle_vertices.csv",[r for d in data for r in d["vertices"]]),
                          ("material_coupons.csv",coupons(cfg)),("convergence_comparison.csv",au["mesh_comparison"]+au["half_step_comparison"])):
        write_csv(output/filename,rows)
    figure(output/"synthese_v11e_section_fissuree.png",data,au)
    report(output/"rapport_v11e_section_fissuree.md",cfg,data,au,runtime,numbers)
    after={p:sha(ROOT/p) for p in paths}
    manifest={"iteration":"V11E","status":"PASS" if before==after and au["status"]=="PASS" else "FAIL",
              "inputs_and_protected_unchanged":before==after,"input_sha256":after,
              "output_sha256":{p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()},
              "manifest_excludes_itself":True,"numerical_digest_sha256":numbers}
    write_json(output/"offline_manifest.json",manifest)
    print(json.dumps({"status":manifest["status"],"tests":au["test_count"],"passed":au["tests_passed"],"seconds":runtime["seconds"],
                      "failed_tests":[t for t in au["tests"] if not t["pass"]],"output":str(output)},ensure_ascii=False),flush=True)
    if manifest["status"]!="PASS": raise SystemExit(1)


if __name__=="__main__":main()
