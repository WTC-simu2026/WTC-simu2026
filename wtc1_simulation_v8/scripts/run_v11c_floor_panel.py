"""Reproducible V11C release. Refuses existing output; CPU, no source writes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import platform
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import v11c_panel_model as physics

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT/"wtc1_simulation_v8/data/v11c_floor_panel_predeclaration.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def write_json(path,value):
    with Path(path).open("x",encoding="utf-8",newline="\n") as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write("\n")


def write_csv(path,rows):
    with Path(path).open("x",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def calculate(cfg,base,transfer,seats,refinement=1.):
    summaries,histories,events,term_rows,displacements,release_rows = [],[],[],[],[],[]
    definitions=[]
    for index,(k,strength,mode) in enumerate(itertools.product(
            cfg["bond"]["stiffness_per_equivalent_knuckle_N_m"],cfg["bond"]["remaining_strength_factors"],
            cfg["cold_paths"]["horizontal_modes"]),1):
        common={"bond_k_N_m":k,"bond_strength_factor":strength,"horizontal_mode":mode}
        definitions.append((f"COLD-{index:02d}","PROPORTIONAL_COLD_GRAVITY",common,
            lambda p, common=common: {**common,"gravity_factor":p},
            cfg["cold_paths"]["load_factor_end"],cfg["cold_paths"]["step"]*refinement))
    for item in cfg["thermal_paths"]:
        def make(p,item=item):
            return {"gravity_factor":item["gravity_factor"],"horizontal_mode":item["horizontal_mode"],
                "steel_c":20+p*(item["steel_end_c"]-20),"slab_c":20+p*(item["slab_end_c"]-20),
                "support_c":20+p*(item["support_end_c"]-20),"right_anchor_x_m":p*item["right_anchor_x_end_m"]}
        definitions.append((item["id"],"PRESCRIBED_TEMPERATURE_OR_SUPPORT_AFTER_COLD_PRELOAD",item,
            make,1.,cfg["thermal_path_step_fraction"]*refinement))
    for path_id,path_kind,common,make,end,step in definitions:
        summary,history,last,release = physics.trace_path(path_id,cfg,base,transfer,seats,make,end,step)
        summaries.append({"path_kind":path_kind,**summary})
        histories.extend(history)
        if summary["first_event_bracket"] is not None:
            events.append({"path_id":path_id,"parameter_low":summary["first_event_bracket"][0],
                "parameter_high":summary["first_event_bracket"][1],"governing_id":summary["governing_id"],
                "governing_kind":summary["governing_kind"],"governing_DCR_high":summary["max_DCR"],
                "first_crossing_is_step_bracketed_not_global_root_guarantee":True})
        for term in last["terms"]:
            term_rows.append({"path_id":path_id,"parameter":summary["parameter"],"term_id":term["id"],
                "kind":term["kind"],"stiffness_N_m":term["k"],"eigenextension_or_anchor_m":term["e0"],
                "elastic_extension_m":term["extension_m"],"force_N":term["force_N"],"DCR":term["DCR"],
                "strain_energy_J":term["strain_energy_J"],"state":term["state"],
                "effective_knuckles":term.get("equivalent_knuckles"),
                "shear_capacity_N":term.get("cap_abs_N"),"slab_vertical_tie_still_perfect":True})
        model=last["model"]
        for i,(x,y) in enumerate(model["nodes"]):
            displacements.append({"path_id":path_id,"node_id":i,"x_m":float(x),"y_m":float(y),
                "ux_steel_m":float(last["u"][2*i]),"uy_steel_m":float(last["u"][2*i+1]),
                "ux_slab_m":float(last["u"][model["steel_dofs"]+i]) if i<=model["panels"] else None})
        if release is not None:
            release_rows.append(release)
    return {"path_summaries":summaries,"path_history":histories,"first_events":events,
            "terminal_component_forces":term_rows,"terminal_displacements":displacements,
            "bond_release_diagnostics":release_rows}


def checks(cfg,data,refined,replay_digest,extra):
    tests=list(extra)
    def check(name,ok,evidence):
        tests.append({"test":name,"pass":bool(ok),"evidence":evidence})
    rows=data["path_history"]
    releases=[r["post_state"] for r in data["bond_release_diagnostics"] if r.get("post_state")]
    all_states=rows+releases
    eq=max(r["equilibrium_residual"] for r in all_states)
    en=max(r["energy_identity_residual"] for r in all_states)
    check("all_path_state_equilibria",eq<cfg["acceptance"]["relative_equilibrium_tolerance"],eq)
    check("all_path_algebraic_strain_energy_identities",en<cfg["acceptance"]["relative_state_energy_identity_tolerance"],en)
    check("22_predeclared_paths",len(data["path_summaries"])==22,len(data["path_summaries"]))
    check("deterministic_replay_exact",digest(data)==replay_digest,digest(data))
    check("no_gravity_or_capacity_state_beyond_first_event_released_as_valid",
          all(r["max_DCR"]<1+1e-6 for r in rows if r["state"]=="BELOW_FIRST_NOMINAL_LIMIT"),len(rows))
    check("all_first_event_brackets_small",all(e["parameter_high"]-e["parameter_low"]<=1e-7 for e in data["first_events"]),len(data["first_events"]))
    refine={r["path_id"]:r for r in refined["path_summaries"]}
    changes=[{"path_id":r["path_id"],"parameter_change":abs(r["parameter"]-refine[r["path_id"]]["parameter"]),
              "same_family":r["governing_kind"]==refine[r["path_id"]]["governing_kind"],
              "same_terminal":r["state"]==refine[r["path_id"]]["state"]} for r in data["path_summaries"]]
    check("half_parameter_step_same_first_limit_family_and_terminal",all(r["same_family"] and r["same_terminal"] for r in changes),changes)
    check("half_parameter_step_first_event_change_below_2e_7",max(r["parameter_change"] for r in changes)<2e-7,max(r["parameter_change"] for r in changes))
    check("no_source_based_tensile_concrete_force",all(r["force_N"]<=1e-5 for r in data["terminal_component_forces"] if r["kind"]=="slab"),"Compression-only law")
    check("no_global_energy_credit",all(r["global_energy_credit_J"]==0 for r in all_states),"No addition to V11B")
    check("no_unnoticed_uplift_or_large_displacement_in_published_paths",not any(r["unsupported_vertical_uplift"] or r["large_displacement_warning"] for r in all_states),len(all_states))
    check("all_release_events_first_horizontal_bond_limit",all(next(s for s in data["path_summaries"] if s["path_id"]==r["path_id"])["governing_kind"]=="bond" for r in data["bond_release_diagnostics"]),len(data["bond_release_diagnostics"]))
    return {"status":"PASS" if all(t["pass"] for t in tests) else "FAIL",
        "tests_passed":sum(t["pass"] for t in tests),"test_count":len(tests),"tests":tests,
        "maximum_equilibrium_residual":eq,"maximum_state_energy_identity_residual":en,
        "parameter_refinement":changes,"not_dynamic_or_heat_energy_balance":True}


def figure(path,data,cfg):
    im=Image.new("RGB",(1600,1170),"#f2f5f8")
    d=ImageDraw.Draw(im)
    fontpath=Path("C:/Windows/Fonts/segoeui.ttf")
    boldpath=Path("C:/Windows/Fonts/segoeuib.ttf")
    def font(size,bold=False): return ImageFont.truetype(str(boldpath if bold else fontpath),size)
    def text(x,y,s,size=22,fill="#1c3046",bold=False): d.text((x,y),s,font=font(size,bold),fill=fill)
    text(55,28,"WTC 1 / V11C - dalle et treillis à liaison déformable",34,bold=True)
    text(55,79,"Prototype plan symétrique de deux treillis. Hypothèses visibles, aucun calcul d'effondrement global.",22)
    d.rounded_rectangle((40,122,1560,412),radius=12,fill="white")
    text(65,138,"Liaisons explicites : glissement horizontal ; attache verticale encore parfaite",25,bold=True)
    nodes,members=physics.warren_geometry(cfg["panel"]["span_in"]*physics.IN,29*physics.IN,16)
    x0,x1,yt,yb=120,1450,240,335
    def xx(x): return x0+(x1-x0)*x/(cfg["panel"]["span_in"]*physics.IN)
    for i,j,kind in members:
        d.line((xx(nodes[i,0]),yt if nodes[i,1]==0 else yb,xx(nodes[j,0]),yt if nodes[j,1]==0 else yb),fill="#447f9f",width=3)
    d.line((x0,205,x1,205),fill="#b38341",width=9)
    for i in range(17):
        x=xx(nodes[i,0]); d.line((x,211,x,232),fill="#cf633f",width=4)
    for x in (x0,x1):
        d.line((x,244,x-8,256,x+8,268,x-8,280,x,292),fill="#1c3046",width=3)
        d.line((x-22,298,x+22,298),fill="#1c3046",width=3)
    text(65,356,"Portée 18,110 m | largeur équivalente 2,032 m | 32 attaches équivalentes : densité supposée",22)
    text(65,385,"Schéma non à l'échelle : l'écart dalle-treillis dessiné n'ajoute aucun bras de levier au calcul.",17)
    # Cold service load curves, full reference strength, roller support.
    d.rounded_rectangle((40,432,850,891),radius=12,fill="white")
    text(65,450,"À froid : effet de la raideur des attaches",25,bold=True)
    selected=[r for r in data["path_summaries"] if r["path_kind"]=="PROPORTIONAL_COLD_GRAVITY" and r["bond_strength_factor"]==1 and r["horizontal_mode"]=="roller"]
    palette=["#cb7143","#297eab","#50986c"]
    ax,ay,aw,ah=135,782,650,225
    xmax=max(r["max_down_m"]*1000 for r in selected)*1.1
    ymax=100*cfg["cold_paths"]["load_factor_end"]
    for k in range(6):
        x=ax+aw*k/5; d.line((x,ay-ah,x,ay),fill="#dde5ed",width=1)
        text(x-16,ay+8,f"{xmax*k/5:.0f}",18)
    for k in range(6):
        y=ay-ah*k/5; d.line((ax,y,ax+aw,y),fill="#dde5ed",width=1)
        text(ax-53,y-12,f"{ymax*k/5:.0f}",18)
    text(65,515,"Charge / référence (%)",19)
    text(305,827,"Flèche maximale (mm)",20)
    for j,row in enumerate(selected):
        pts=[r for r in data["path_history"] if r["path_id"]==row["path_id"]]
        coords=[(ax+aw*r["max_down_m"]*1000/xmax,ay-ah*100*r["gravity_factor"]/ymax) for r in pts]
        d.line(coords,fill=palette[j],width=4)
        d.ellipse((coords[-1][0]-5,coords[-1][1]-5,coords[-1][0]+5,coords[-1][1]+5),fill=palette[j])
        text(110+j*234,488,f"K = {row['bond_k_N_m']/1e6:g} MN/m",19,fill=palette[j])
    d.rounded_rectangle((870,432,1560,891),radius=12,fill="white")
    text(895,450,"Chauffage / mouvement d'appui imposés",25,bold=True)
    translations={"UNIFORM_ROLLER":"Acier + dalle chauds / appui libre",
        "UNIFORM_RESTRAINED":"Acier + dalle chauds / retenu",
        "STEEL_HOT_SLAB_COOL":"Acier plus chaud que la dalle",
        "SUPPORT_OPENING_COLD":"Écartement d'appui / froid"}
    for j,row in enumerate(r for r in data["path_summaries"] if r["path_kind"]!="PROPORTIONAL_COLD_GRAVITY"):
        y=505+j*89
        text(895,y,translations[row["path_id"]],22,bold=True)
        if row["path_id"]=="SUPPORT_OPENING_COLD":
            value=f"Appui : {row['right_anchor_x_m']*1000:.2f} mm"
        else:
            value=f"Acier : {row['steel_c']:.1f} °C / dalle : {row['slab_c']:.1f} °C"
        text(895,y+30,value,20)
        family={"top_chord":"membrure supérieure","seat_h":"traction d'appui","web":"diagonale","bond":"attache"}.get(row["governing_kind"],row["governing_kind"])
        reached=row["state"].startswith("FIRST")
        label=f"Premier seuil : {family}" if reached else "Fin du parcours : aucun seuil vérifié franchi"
        text(895,y+54,label,18,fill="#995031" if reached else "#357750")
    d.rounded_rectangle((40,915,1560,1137),radius=12,fill="#1c3046")
    text(65,932,"Ce qui est calculé - et ce qui ne l'est pas",25,fill="white",bold=True)
    text(65,980,"Efforts, glissement, appuis, dilatation et premier seuil local. Rupture horizontale : diagnostic séparé.",23,fill="white")
    text(65,1020,"Pas de flexion de dalle, de décollement vertical, de chaînette, de flambement après seuil ou de dynamique.",22,fill="white")
    text(65,1060,"Températures prescrites, sans durée ni feu résolu. Les seuils ci-dessus ne sont pas ceux du WTC réel.",22,fill="white")
    im.save(path)


def report(data,audit,seconds):
    rows=data["path_summaries"]
    counts=Counter(r["governing_kind"] for r in rows if r["state"].startswith("FIRST"))
    endcount=sum(r["state"].startswith("PARAMETER_END") for r in rows)
    table="\n".join(f"| {r['path_id']} | {r['steel_c']:.2f} | {r['slab_c']:.2f} | {r['right_anchor_x_m']*1000:.3f} | {r['max_down_m']*1000:.2f} | "+("Premier seuil : "+r['governing_kind'] if r['state'].startswith('FIRST') else "Fin sans seuil vérifié franchi")+" |" for r in rows if r["path_kind"]!="PROPORTIONAL_COLD_GRAVITY")
    cold="\n".join(f"| {r['bond_k_N_m']/1e6:g} | {r['parameter']:.6f} | {r['max_down_m']*1000:.2f} | {r['max_slip_m']*1000:.3f} | {r['state']} |" for r in rows if r["path_kind"]=="PROPORTIONAL_COLD_GRAVITY" and r["bond_strength_factor"]==1 and r["horizontal_mode"]=="roller")
    return f"""# WTC 1 - V11C : dalle, treillis et liaisons déformables

## Résultat utilisable

V11C construit une paire symétrique de treillis de 713 in (18,1102 m) avec une dalle axiale distincte, 17 stations de glissement horizontal et des appuis déformables. Les 17 stations représentent **32 attaches équivalentes supposées**, pas un nombre de knuckles réels relevé sur plans. Les sollicitations de la dalle, des barres et des liaisons sont calculées séparément. Aucune résistance V11C n'est ajoutée à V11B ni au film Blender.

22 chemins pré-déclarés sont exécutés : 18 chargements froids et quatre sollicitations thermiques/d'appui. {endcount} arrivent à la limite de chargement sans dépasser les seuils vérifiés ; les autres atteignent un premier seuil nominal ({dict(counts)}). Ces comptes décrivent les cas choisis, pas des probabilités historiques. La réponse s'arrête au premier seuil : aucune barre qui flambe ou plastifie n'est prolongée artificiellement dans son régime élastique.

## 1. Faits directement transcrits ou vérifiés

La géométrie de référence C32T1, les sections de cornières, le diamètre uniforme de diagonale, la dalle équivalente de 4,35 in et la largeur de 40 in par treillis sont repris de V11A avec leurs limites. Les 16 panneaux Warren et l'affectation de cette géométrie à la paire restent idéalisés.

Le chapitre knuckle de [NIST NCSTAR 1-6C](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-6c.pdf), pages imprimées 61-68, a fait l'objet d'une lecture bornée. Le tableau 5-7 (page 67, PDF 115 local) a été contrôlé visuellement. Les unités sont conservées dans la configuration : 1 kip = 4448,221615 N ; 1 in = 0,0254 m. La copie source n'est pas modifiée.

## 2. Résultats et hypothèses d'un modèle officiel réutilisés

Les capacités longitudinales d'une attache reprises du tableau sont 30/24/19/15 kip aux températures moyennes du **béton** 20-300/450/600/750 °C. Le NIST les estime à partir d'essais, de calculs et de jugement thermique ; ce ne sont pas des essais incendie de chaque attache construite. Le modèle interpole les valeurs sans les indexer sur la température de l'acier. Les données d'arrachement vertical sont conservées comme référence mais **non activées** ici.

Les graphiques publiés concernent des modèles de deux attaches. Ils ne donnent pas à V11C une loi individuelle as-built vérifiée : raideur et rupture fragile restent des hypothèses. Les capacités des sièges viennent des tableaux déjà transcrits en V11A, appliquées une seule fois à la paire ; les valeurs horizontales ne sont utilisées qu'en traction. Aucun domaine d'interaction traction verticale/horizontale n'est validé.

## 3. Informations provenant des archives locales

Aucune nouvelle lecture de l'archive source. La nomenclature complète de chaque plancher, les positions réelles d'attaches et les assemblages de rive restent non reconstruits. Les détails de siège intérieur 15 / extérieur 1013 sont des alternatives déclarées, non une identification du siège réel associé à C32T1.

## 4. Hypothèses propres au modèle

### Structure et liaisons

Une paire de treillis identiques est condensée en un treillis plan avec EA, aire, inertie et charge doublés. La largeur chargée est 80 in. La référence 80 psf contient déjà le poids propre : aucun second poids propre n'est ajouté. La symétrie impose une même réponse aux deux treillis ; torsion, transfert transversal et ouverture de plancher sont absents.

La dalle possède un déplacement axial indépendant à chaque nœud supérieur. Elle ne travaille qu'en compression ; en traction son effort, sa rigidité et sa charge thermique sont nuls. Aucun béton tendu ni armature n'est crédité. La dalle est ramenée à l'axe supérieur du treillis : excentricité, flexion et cisaillement de dalle ne sont pas résolus. Son lien vertical reste parfait, même dans le diagnostic de rupture horizontale. Cela limite fortement ce diagnostic après dommage.

Les ressorts de cisaillement transmettent un effort selon le glissement entre dalle et acier. Leur raideur et leur capacité sont pondérées par longueur tributaire, demi-poids aux extrémités. Le pas d'attaches équivalent est supposé 713/16 in et reste fixe si le nombre de panneaux de test change. La somme de raideur et de capacité ne varie donc pas artificiellement avec ce nombre. Changer les panneaux Warren change néanmoins la structure physique : ce n'est pas une convergence du maillage réel.

Raideurs testées : 1/10/100 MN/m par attache équivalente ; facteurs de résistance 0,05/0,25/1. Ces facteurs ne représentent pas des dommages calculés de l'avion. Le facteur réduit seulement la résistance, pas aussi la raideur. Le modèle n'est pas ajusté pour retrouver une durée ou un effondrement.

Les appuis verticaux et horizontaux retenus valent 100 MN/m par paire. Le cas roulant ne possède aucun ressort horizontal à droite. Aucun contreventement latéral du cordon n'est automatiquement déduit des attaches : les barres comprimées sont contrôlées par le minimum Euler/écrasement, sans postflambement. Le mode de contreventement idéal sert seulement à comparer V11A dans les tests.

### Température, limites et rupture

Acier, dalle et siège peuvent recevoir trois températures prescrites différentes, dans le domaine 20-600 °C. Les coefficients constants de dilatation supposés sont 12 et 10 micromètres par mètre et kelvin pour acier et béton. Ec, fc et réductions thermiques du béton restent ceux des hypothèses V11A. Pas de gradients dans chaque barre, de feu, de transfert thermique, de fluage ni d'horloge réelle.

Les quatre chemins commencent après une charge froide de 0,5 fois la référence, vérifiée avant chauffage/déplacement. Le premier franchissement est encadré par pas puis affiné par dichotomie. Une répétition avec pas divisé par deux contrôle le premier seuil détecté ; ce n'est pas une preuve contre tout maximum non échantillonné. La traction horizontale et la compression aux sièges sont distinguées : la résistance horizontale en compression est inconnue, donc une poussée élastique calculée n'est pas une capacité vérifiée.

À un premier seuil d'attache, les ressorts horizontaux concernés peuvent être supprimés et le même chargement rééquilibré dans un **diagnostic statique séparé**. Si un autre seuil est dépassé, le résultat est marqué non admissible comme continuation. Aucune suppression de barre, boucle de ruine ou trajectoire dynamique n'est appliquée. Les énergies avant/après et l'énergie stockée dans le ressort retiré sont distinctes ; aucune différence n'est baptisée énergie dissipée de rupture.

L'identité vérifiée est 2U = u·f + u_prescrit·réaction - somme(N·extension_propre). Elle inclut les extensions thermiques et les positions d'ancrage dans extension_propre. C'est une identité d'état élastique, **pas un bilan de chaleur ou d'énergie dynamique** ; E varie avec la température sans intégration du travail thermique.

## 5. Résultats dérivés

### Trois raideurs de liaison, résistance de référence entière, appui roulant

Les valeurs ci-dessous correspondent à la fin du chemin autorisé (jusqu'à 1,25 fois 80 psf), ou à son premier seuil. Elles ne sont pas toutes mesurées au même effort si l'un des chemins s'arrête avant.

| K par attache (MN/m) | Facteur de charge final | Flèche finale (mm) | Glissement max (mm) | État |
|---:|---:|---:|---:|---|
{cold}

### Chemins thermiques et déplacement imposé

Valeurs à la fin du chemin ou au premier écran nominal ; aucune température critique de la tour réelle n'est identifiée.

| Chemin | Acier (°C) | Dalle (°C) | Déplacement d'ancrage (mm) | Flèche (mm) | État final du modèle |
|---|---:|---:|---:|---:|---|
{table}

Le cas roulant chauffé atteint la borne de 600 °C **sans franchissement** : la membrure la plus sollicitée n'est donc pas présentée comme rompue à cette température. Les seuils plus bas des cas retenus dépendent notamment des ressorts d'appui supposés et du cordon supérieur sans maintien latéral crédité ; ils ne constituent pas des températures critiques mesurées ou établies du plancher réel.

Les pertes de liaison donnent {len(data['bond_release_diagnostics'])} diagnostics de retrait de ressorts. Les sorties composant par composant permettent de distinguer une rupture d'attache d'un seuil de barre. Une absence de dépassement parmi les critères implementés n'est pas une preuve de résistance d'un plancher réel.

### Vérification

**{audit['tests_passed']}/{audit['test_count']} contrôles passent.** Sur les parcours et diagnostics de retrait, résidu relatif maximal d'équilibre {audit['maximum_equilibrium_residual']:.3e} ; identité d'énergie d'état {audit['maximum_state_energy_identity_residual']:.3e}. Tests analytiques indépendants, limites de liaison, charge doublée, signes de traction/compression, index thermique, pondération des attaches, répétition exacte et pas de parcours divisé par deux sont inclus. Le contrôle analytique de dilatation libre complète, d'énergie théorique nulle, présente séparément un écart d'identité inférieur à 1e-9 J. Exécution CPU, répétition et raffinement : {seconds:.2f} s, Python {platform.python_version()}, NumPy {np.__version__}. Aucun logiciel installé, aucun GPU ou Blender lancé.

## 6. Contradictions, informations manquantes et suite

V11C fait progresser le transfert d'efforts local, pas encore le bâtiment entier. Les capacités NIST des attaches et les propriétés de dalle du prototype n'ont pas la même base matérielle : les conserver comme dépendance/hypothèse distinctes, pas comme calibration cohérente du béton réel. Les rigidités de liaison ne sont pas une extraction des courbes d'essai. Aucune conclusion « effondrement nécessaire » ou « impossible » n'en découle.

Restent prioritaires : liaison verticale et décollement, flexion/fissuration de dalle et armatures ; géométrie non linéaire et réponse après premier flambement ; assemblages de rive et appuis fournis par colonnes/allèges ; couplage aux composants spatiaux. **V11D : ajouter et tester la flexion de dalle et son contact/arrachement vertical dans un panneau borné, avant toute propagation globale.** Les entrées de l'impact 767 et des incendies doivent ensuite être calculées, sans issue prédéfinie. V11B reste inchangée ; le film V10Z conserve son ancien pilote.

## Livrables

Configuration et scripts V11C ; inventaire des nœuds, degrés de liberté, barres, attaches et appuis du prototype ; synthèse graphique ; résumés des 22 parcours, historiques, premiers événements, efforts terminaux et déplacements ; diagnostics de rupture horizontale ; tests numériques ; manifestes des sources et sorties. Toute reprise utilise le handoff V11C et le nouvel état, sans réexécuter les anciennes itérations.
"""


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    args=parser.parse_args()
    cfg=read(CONFIG)
    out=(ROOT/(args.output_dir or cfg["output_directory"])).resolve()
    allowed=(ROOT/cfg["output_directory"]).resolve()
    scratch=(ROOT/cfg["scratch_directory"]).resolve()
    if out!=allowed and not out.is_relative_to(scratch):
        raise ValueError("Output outside declared V11C paths")
    if out.exists():
        raise FileExistsError("Preserve existing iteration/attempt; choose a fresh directory")
    inputs=list(dict.fromkeys([cfg["base_configuration"],cfg["transfer"],cfg["seats"],cfg["source_pdf_review"]["path"],*cfg["protected_files"]]))
    protected=[{"path":p,"sha256_before":sha(ROOT/p)} for p in inputs]
    out.mkdir(parents=True)
    start=time.perf_counter()
    start_utc=datetime.now(timezone.utc).isoformat()
    base,transfer,seats=read(ROOT/cfg["base_configuration"]),read(ROOT/cfg["transfer"]),read(ROOT/cfg["seats"])["floor_truss_seats"]
    data=calculate(cfg,base,transfer,seats)
    replay_digest=digest(calculate(cfg,base,transfer,seats))
    refined=calculate(cfg,base,transfer,seats,.5)
    import test_v11c_independent
    import test_v11c_regression
    independent=test_v11c_independent.run_checks()
    extra=[{"test":r["name"],"pass":r["pass"],"evidence":r["evidence"]} for r in independent["checks"]]
    extra+=test_v11c_regression.run(cfg,base,transfer,seats)
    audit=checks(cfg,data,refined,replay_digest,extra)
    elapsed=time.perf_counter()-start
    write_json(out/"numerical_audit.json",audit)
    if audit["status"]!="PASS":
        print(json.dumps({"status":"FAIL","failed":[r for r in audit["tests"] if not r["pass"]]},indent=2))
        raise RuntimeError("Numerical gate failed; draft retained, no release")
    for name,value in data.items():
        if name=="bond_release_diagnostics":
            write_json(out/(name+".json"),value)
        else:
            write_csv(out/(name+".csv"),value)
    reference=physics.build_panel(cfg,base,transfer,seats,{})
    write_json(out/"panel_inventory.json",{
        "iteration":"V11C","status":"IDEALIZED_SYMMETRIC_PAIR_NOT_AS_BUILT",
        "nodes_steel_x_y_m":reference["nodes"].tolist(),
        "steel_members_i_j_family":[list(m) for m in reference["members"]],
        "steel_dof_count":reference["steel_dofs"],"total_dof_count":reference["size"],
        "slab_scalar_dofs":list(range(reference["steel_dofs"],reference["size"])),
        "slab_station_x_m":reference["nodes"][:reference["panels"]+1,0].tolist(),
        "terms_reference_cold_roller":reference["terms"],
        "gravity_force_N_reference":reference["force"].tolist(),
        "prescribed_kinematics":"Slab axial line co-located at top chord; vertical displacement shared, no eccentricity, no plate/shell bending",
        "complete_floor_count_or_placement":None,"global_solver_coupling":False})
    figure(out/"synthese_v11c_plancher.png",data,cfg)
    with (out/"rapport_v11c_plancher.md").open("x",encoding="utf-8") as stream:
        stream.write(report(data,audit,elapsed))
    source_image=ROOT/"tmp/v11c_floor_panel/source_pages/ncstar1-6c_p115.png"
    if source_image.is_file():
        shutil.copyfile(source_image,out/"source_table_5_7.png")
    for entry in protected:
        entry["sha256_after"]=sha(ROOT/entry["path"])
        entry["unchanged"]=entry["sha256_before"]==entry["sha256_after"]
    if not all(r["unchanged"] for r in protected):
        raise RuntimeError("Input/source/protected file changed")
    script_names=["v11c_panel_model.py","run_v11c_floor_panel.py","test_v11c_independent.py","test_v11c_regression.py"]
    code=[{"path":str(CONFIG.relative_to(ROOT)).replace("\\","/"),"sha256":sha(CONFIG)}]
    code += [{"path":"wtc1_simulation_v8/scripts/"+n,"sha256":sha(ROOT/"wtc1_simulation_v8/scripts"/n)} for n in script_names]
    manifest={"iteration":"V11C","source_and_protected_files":protected,"code_and_configuration":code,
        "pdf_read_window":cfg["source_pdf_review"],"table_visually_checked":True,
        "renderer":"Poppler 110 dpi; substitution warnings, table readable",
        "new_source_classification":cfg["bond"]["source_status"],"source_url":cfg["bond"]["source_url"]}
    write_json(out/"source_manifest.json",manifest)
    results={"iteration":"V11C","status":"PASS_EXPLORATORY_PANEL_NOT_AS_BUILT_OR_GLOBAL_VALIDATION",
        "path_count":len(data["path_summaries"]),"path_point_count":len(data["path_history"]),
        "first_event_count":len(data["first_events"]),"bond_release_diagnostic_count":len(data["bond_release_diagnostics"]),
        "numerical_checks_passed":audit["tests_passed"],"numerical_checks_total":audit["test_count"],
        "maximum_equilibrium_residual":audit["maximum_equilibrium_residual"],
        "maximum_state_energy_identity_residual":audit["maximum_state_energy_identity_residual"],
        "numerical_digest_sha256":digest(data),"path_summaries":data["path_summaries"],
        "execution":{"start_utc":start_utc,"end_utc":datetime.now(timezone.utc).isoformat(),
            "seconds_including_replay_refinement_tests":elapsed,"python":platform.python_version(),"numpy":np.__version__,"cpu_only":True},
        "global_collapse_coupled":False,"vertical_connection_failure_implemented":False,
        "slab_bending_implemented":False,"impact_independently_computed":False,"fire_computed":False,
        "historical_collapse_verdict":None,"blender_changed":False,"source_and_protected_files_unchanged":True}
    write_json(out/"results_v11c.json",results)
    files=[{"path":str(p.relative_to(out)).replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(out.rglob("*")) if p.is_file()]
    write_json(out/"offline_manifest.json",{"iteration":"V11C","files":files,"self_excluded":True})
    print(json.dumps({k:v for k,v in results.items() if k!="path_summaries"},indent=2))


if __name__=="__main__":
    main()
