"""Reproduce V11G without changing existing output directories or V11F mechanics."""
import argparse
import csv
import hashlib
import json
import os
import platform
import sys
import time
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,__version__ as pillow_version
import v11g_localization_model as physics
import test_v11g_localization

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/"wtc1_simulation_v8/data/v11g_localization_predeclaration.json"


def read(path):return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")


def panel_inputs(cfg):
    directory=ROOT/cfg["panel_directory"]
    result=read(directory/"results_v11f.json")
    inventory={r["case"]["id"]:r for r in read(directory/"panel_inventory.json")}
    groups={}
    for key,filename in (("sections","section_states.csv"),("terms","physical_component_forces.csv")):
        group=defaultdict(list)
        with (directory/filename).open(encoding="utf-8-sig",newline="") as stream:
            for row in csv.DictReader(stream):group[row["case_id"]].append(row)
        groups[key]=group
    reference=[{"summary":s,"inventory":inventory[s["id"]],**{k:g[s["id"]] for k,g in groups.items()}} for s in result["summaries"]]
    fine=read(directory/"verification_runs.json")["mesh_runs"]
    return reference,{"2":fine["2"],"4":reference,"8":fine["8"]}


def bars(cfg,si,step=1.):
    return [physics.localized_bar(cfg,si,L,n,p,step) for L in cfg["bar"]["lengths_m"]
            for n in cfg["bar"]["cells"] for p in ("monotonic","cyclic")]


def figure(path,bar_data,negative,panels,tests,gate):
    im=Image.new("RGB",(1600,1120),"#f1f5f8");d=ImageDraw.Draw(im)
    def text(x,y,s,size=21,color="#263d50",bold=False):
        f=ImageFont.truetype("C:/Windows/Fonts/segoeui"+("b" if bold else "")+".ttf",size)
        d.text((x,y),s,font=f,fill=color)
    text(44,26,"WTC 1 / V11G — énergie de fracture et localisation",34,bold=True)
    text(45,80,"Benchmark générique à froid ; le panneau V11F et l’animation restent inchangés.",24)
    d.rounded_rectangle((35,135,1565,283),radius=16,fill="white")
    text(61,151,"Une fissure choisie : même énergie après raffinement du maillage.",26,bold=True)
    text(61,197,"Barre de 100 cm², béton hypothétique : énergie complète de 1 J pour cette fissure.",22)
    text(61,236,"La position et le nombre de fissures sont imposés dans cet essai, pas prédits pour le WTC.",21)
    def chart(x,y,w,h,title,xmax,ymax,xlabel,ylabel):
        d.rounded_rectangle((x-48,y-93,x+w+32,y+h+92),radius=14,fill="white")
        text(x-15,y-77,title,24,bold=True);text(x-15,y-41,ylabel,18)
        def xy(a,b):return x+w*a/xmax,y+h-h*b/ymax
        for j in range(5):
            xx,yy=xy(xmax*j/4,ymax*j/4)
            d.line((xx,y,xx,y+h),fill="#dce4eb");d.line((x,yy,x+w,yy),fill="#dce4eb")
            text(xx-12,y+h+10,f"{xmax*j/4:g}",16);text(x-43,yy-10,f"{ymax*j/4:g}",16)
        text(x+72,y+h+49,xlabel,19)
        return xy
    xy=chart(94,418,620,305,"Parcours effort-déplacement",.5,12,"Déplacement total des extrémités (mm)","Effort de traction (kN)")
    for length,color in ((2.,"#247dab"),(8.,"#b67332")):
        selected=[b for b in bar_data if b["summary"]["length_m"]==length and b["summary"]["path"]=="monotonic"]
        for b in selected:
            d.line([xy(r["end_displacement_m"]*1000,r["force_N"]/1000) for r in b["history"]],fill=color,width=3)
        branch=[r for r in selected[0]["history"] if r["phase"]=="opening_0"]
        start=np.array(xy(branch[24]["end_displacement_m"]*1000,branch[24]["force_N"]/1000))
        end=np.array(xy(branch[32]["end_displacement_m"]*1000,branch[32]["force_N"]/1000))
        tangent=(end-start)/np.linalg.norm(end-start);normal=np.array([-tangent[1],tangent[0]])
        d.polygon([tuple(end),tuple(end-15*tangent+7*normal),tuple(end-15*tangent-7*normal)],fill=color)
    text(75,825,"Bleu : barre 2 m   Ocre : barre 8 m",20)
    text(75,853,"Quatre maillages superposés ; flèches : sens du parcours.",16)
    xy2=chart(889,418,606,305,"Témoin : fissuration uniforme forcée",140,140,"Nombre de bandes numériques actives", "Énergie totale dissipée (J)")
    points=sorted((r["simultaneous_numerical_bands"],r["D_J"]) for r in negative)
    d.line([xy2(a,b) for a,b in points],fill="#b67332",width=4)
    for a,b in points:
        px,py=xy2(a,b);d.ellipse((px-4,py-4,px+4,py+4),fill="#b67332")
    d.line((xy2(0,1),xy2(140,1)),fill="#247dab",width=3)
    text(866,825,"Référence bleue : 1 J pour une seule fissure",20)
    d.rounded_rectangle((35,885,1565,1088),radius=16,fill="white")
    text(60,904,f"{sum(t['pass'] for t in tests)}/{len(tests)} contrôles de calcul réussis",27,bold=True)
    text(60,949,f"Efforts locaux V11F : {gate['passing_cases']}/14 cas sous les seuils choisis au maillage fin.",24,bold=True)
    text(60,991,"Une loi correctement normalisée ne suffit pas à prédire le nombre de fissures d’un panneau.",21)
    text(60,1032,"Pas de simulation d’impact, d’incendie ou d’effondrement ajoutée dans ce benchmark.",21)
    im.save(path)


def report(path,cfg,result,bar_data,negative,panels):
    si=result["material_input_ledger"]["SI"]
    first=bar_data[0]["summary"];gate=result["panel_sampled_pointwise_gate"]
    out=["# V11G — localisation longitudinale et équilibre local","","## Résultat","",
         f"Le benchmark à une seule zone de fissuration choisie passe sur {len(bar_data)} parcours : deux longueurs, quatre maillages et deux histoires de chargement. {result['tests_passed']}/{result['test_count']} contrôles numériques passent. Le travail extérieur, l'énergie stockée et la dissipation sont vérifiés séparément. La rupture complète consomme {first['target_single_fracture_energy_J']:.6f} J pour cette section générique de 0,01 m², indépendamment de la largeur numérique de sa bande.","",
         f"Le diagnostic séparé des efforts locaux du panneau V11F est {gate['status']} : {gate['passing_cases']}/14 cas passent au maillage 8 les seuils choisis de 5 % pour N et M aux points de Gauss. Éventuels cas au-dessus : {', '.join(gate['failing_cases']) or 'aucun'}. Ces critères locaux sont nouveaux ; ils ne remplacent pas les comparaisons globales V11F, qui restent enregistrées telles quelles.","",
         "Le témoin de déformation uniforme forcée dissipe une énergie proportionnelle au nombre de bandes. Il est rejeté comme représentation d'une seule fissure. Le benchmark ne choisit pas spontanément une fissure, ne valide pas la fracture complète du panneau et ne modifie ni la mécanique V11F ni l'animation.","",
         "## 1. Constats et données transcrites","",
         "Les résultats V11F, leurs entrées et leurs empreintes sont relus, sans nouvel examen de PDF, photo, vidéo ou archive. Le contrôle porte sur les états terminaux déjà sauvegardés des 14 parcours aux maillages 2, 4 et 8. Les forces de contact et d'attaches et les réactions des actionneurs sont celles de ces calculs, pas de nouvelles mesures.","",
         "## 2. Résultats officiels et sources de méthode","",
         "Aucun résultat historique officiel supplémentaire n'est introduit. Les héritages NIST du panneau restent dépendants des transcriptions et hypothèses antérieures. Le rapport de l'énergie de traction à la largeur de bande est décrit dans [DIANA — paramètres du modèle](https://manuals.dianafea.com/d110/en/1465843-1466551-model-parameters.html). La distinction entre équilibre intégré et ponctuel des efforts de section est explicite dans [OpenSees — élément à déplacements](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/dispBeamColumn.html). Aucun de ces logiciels n'est exécuté ; les formules et contrôles ci-dessous appartiennent au projet.","",
         "## 3. Archives","","Aucune nouvelle affirmation d'archive ou identification de mécanisme ne participe à V11G.","",
         "## 4. Hypothèses et dérivation du benchmark","",
         "Barres génériques de 2 m et 8 m, section 0,01 m² (100 cm²), à 20 °C. Ces dimensions sont des choix d'essai, pas des composants WTC identifiés. E = 2500 ksi, ft = 1 MPa et Gf = 100 J/m² reprennent les hypothèses V11E ; fc = 3 ksi est conservé dans les données, mais aucune compression n'est exercée ici. Les unités originales et leur conversion sont enregistrées dans material_input_ledger.json.","",
         "Une seule cellule centrale est autorisée à fissurer ; les autres sont élastiques. Les maillages impairs 9 / 17 / 33 / 65 gardent sa position au milieu de la barre. Sa largeur h = L/n est numérique, pas une largeur physique de fissure mesurée. Ce test vérifie une stratégie à fissure sélectionnée, pas une loi capable d'en découvrir le nombre ou la position.","",
         "La loi V11E inchangée est intégrée dans cette bande. Son ouverture inélastique est w = h(ε − σ/E), et sa déformation totale reste ε. Après le pic, on résout cette relation par Newton encadré depuis le dernier état engagé, puis on impose l'équilibre en série : même force dans toutes les cellules. Leurs déplacements sont reconstruits et les résidus nodaux vérifiés. Aucun essai numérique refusé n'est engagé.","",
         "Comparateur fermé, dérivé séparément : wc = 2Gf/ft ; σ = ft(1 − w/wc) entre 0 et wc ; P = Aσ ; déplacement total Δ = Lσ/E + w. La décharge/recharge suit une sécante en ouverture jusqu'à l'ouverture maximale déjà atteinte. L'intégrale de la traction sur l'ouverture est Gf. À séparation complète, l'énergie stockée est nulle et le travail extérieur net comme la dissipation valent AGf.","",
         f"Ici wc = {first['critical_opening_m']*1000:.6f} mm. La dérivée dΔ/dw après le pic vaut 1 − L/Lcrit, avec Lcrit = 2EGf/ft² = {first['critical_bar_length_m']:.9f} m. La barre de 2 m adoucit avec Δ croissant ; celle de 8 m a un retour en déplacement (snapback). L'ouverture est un paramètre de continuation pour suivre les états d'équilibre, pas un vérin intérieur auquel on aurait oublié d'attribuer un travail. Ce parcours ne prouve pas sa stabilité sous un chargement physique libre ni une dynamique de rupture.","",
         "Montée élastique jusqu'au pic, puis ouverture monotone 0 / wc / 1,1wc ; cycle 0 / 0,75wc / 0 / 0,75wc / wc / 1,1wc. Les sommets sont inclus explicitement pour le bilan de travail par trapèzes. Le demi-pas et la répétition exacte sont calculés. Pas d'armature, adhérence, flexion, chaleur, vitesse ou paramètres ajustés à l'effondrement.","",
         "### Témoin volontairement non localisé","",
         "La même déformation est imposée à toutes les cellules. Avec g points identiques par cellule et Lch = L/(n·g), l'énergie finale vaut n·g·AGf. Deux points partageant le même champ axial constant peuvent donc représenter deux bandes dissipatives malgré l'unique cellule ; ils ne constituent pas automatiquement deux fissures physiques. Ce témoin représente une branche homogène forcée, pas une prédiction de fissuration spontanée.","",
         "| Cellules | Points par cellule | Bandes simultanées | Dissipation (J) | Une seule fissure ? |","|---:|---:|---:|---:|---|"]
    for row in negative:out.append(f"| {row['cells']} | {row['gauss_per_cell']} | {row['simultaneous_numerical_bands']} | {row['D_J']:.6f} | Interprétation rejetée |")
    out += ["","## 5. Résultats dérivés et contrôle du panneau","",
            "| Longueur | Cellules | Parcours | États | Dissipation finale (J) | Retour en déplacement au premier adoucissement ? |","|---:|---:|---|---:|---:|---|"]
    for data in bar_data:
        s=data["summary"]
        out.append(f"| {s['length_m']:g} m | {s['cells']} | {s['path']} | {s['state_count']} | {s['final_dissipation_J']:.9f} | {'Oui' if s['observed_postpeak_negative_delta_steps'] else 'Non'} |")
    out += ["",f"Erreur maximale de travail extérieur, divisée par l'énergie physique AGf : {result['bar_residual_maxima']['external_energy_error_relative_AGf']:.3e}. Écart maximal de force au comparateur, divisé par Aft : {result['bar_residual_maxima']['force_error_relative_Aft']:.3e}. Ces normalisations sont fixées par le problème, pas par un plancher d'énergie arbitraire.","",
            "### Équilibre intégré et efforts locaux V11F","",
            "Sur la dalle seule, le contact et les attaches exercent l'opposé de leurs efforts internes enregistrés. Chaque attache horizontale apporte aussi le couple −e·F. On ajoute la gravité répartie et l'actionneur de dalle lorsqu'il existe ; l'actionneur du treillis n'est pas appliqué une seconde fois à la dalle. Les bilans horizontaux, verticaux et de moments sont vérifiés sans mélanger N et N·m.","",
            "La reconstruction statique par une coupe à x donne N(x) = −ΣFx à gauche et M(x) = ΣFy(x − xi) − ΣC + qx²/2. Les sauts dus aux actions ponctuelles sont conservés. On compare ce champ équilibré aux N/M constitutifs aux mêmes points de Gauss. Un second calcul assemble les efforts constitutifs aux nœuds avec leurs fonctions de forme et la charge répartie cohérente pour vérifier l'équilibre faible.","",
            "Le champ récupéré est seulement un diagnostic. Il n'est pas substitué aux contraintes issues des matériaux et ne fournit aucune énergie, résistance ou redistribution supplémentaire au modèle.","",
            "| Cas | Maillage | Écart N max / pic N équilibré (%) | Écart M max / pic M équilibré (%) | Résidu nodal normalisé | Critères locaux |","|---|---:|---:|---:|---:|---|"]
    for p in panels:
        s=p["summary"]
        out.append(f"| {s['case_id']} | {s['subdivisions']} | {100*s['N_max_relative']:.6f} | {100*s['M_max_relative']:.6f} | {s['weak_nodal_relative']:.3e} | {'PASS' if s['sampled_pointwise_gate_pass'] else 'Au-dessus'} |")
    interpolation_gaps={n:max(p['summary']['uniform_q_linear_M_interpolation_endpoint_gap_Nm'] for p in panels if p['summary']['subdivisions']==n) for n in (2,4,8)}
    out += ["","Normalisation séparée par le pic absolu du champ équilibré de chaque cas/maillage : plancher 1 N pour N et 1 N·m pour M. Les écarts sont évalués seulement aux points de Gauss terminaux, pas partout ni à tous les instants. Chaque maillage a son propre état d'arrêt, généralement très proche mais pas strictement identique ; ne pas confondre ce diagnostic avec une comparaison à déplacement final exactement égal.","",
            "**Pourquoi les écarts M affichés sont-ils presque nuls ?** Avec deux points de Gauss, une charge q constante et aucune action ponctuelle à l'intérieur de la cellule, le moment quadratique équilibré et son interpolant linéaire passent par les mêmes valeurs aux deux points. Ce résultat est structurel à l'échantillonnage, pas une validation indépendante de tous les moments de matériau. Aux extrémités de cellule, leur écart vaut |q|·dx²/12, qui n'est pas nul. Un contrôle analytique supplémentaire confirme cet angle mort.","",
            f"L'écart d'interpolation d'extrémité ainsi calculé atteint au maximum {interpolation_gaps[2]:.6f} / {interpolation_gaps[4]:.6f} / {interpolation_gaps[8]:.6f} N·m sur les maillages 2 / 4 / 8. C'est une comparaison avec l'interpolant linéaire des valeurs de Gauss, PAS une contrainte constitutive postfissurée récupérée entre les points. On ne l'ajoute ni aux énergies ni aux résistances, et les critères initiaux restent inchangés.","",
            f"Résidu nodal maximal reconstruit : {result['panel_weak_nodal_maximum']:.3e}. Des défauts volontaires (oubli du couple excentré ou de l'actionneur de dalle) sont détectés par les contrôles. Un bon équilibre global ne suffit donc pas à garantir les efforts locaux, et un écart local de formulation faible n'est pas automatiquement une erreur de convergence de Newton.","",
            "## 6. Inconnues et suite","",
            "La barre démontre une normalisation cohérente de l'énergie pour une seule fissure sélectionnée. Elle ne transfère pas cette validation à la flexion fissurée du panneau V11F : une stratégie de localisation en flexion, les interactions d'armature/adhérence et les fissures multiples restent à vérifier avant d'utiliser sa séparation complète comme résistance globale. Les 42 états de panneau servent à borner les efforts locaux de leurs parcours actuels, pas la propagation d'un effondrement.","",
            result["next_objective"],"",
            f"Exécution finale : {result['runtime']['seconds']:.3f} s sur CPU ; Python {result['runtime']['python']}, NumPy {result['runtime']['numpy']}, Pillow {result['runtime']['Pillow']}. Graine {cfg['random_seed']}, sans tirage aléatoire. Empreinte numérique : {result['numerical_digest_sha256']}. Aucune installation, archive modifiée, revue multi-agent ou dynamique Blender exécutée.","",
            "## Livrables","",
            "results_v11g.json, bar_paths.json, bar_half_step_paths.json, uniform_damage_controls.json, panel_equilibrium_recovery.json, material_input_ledger.json, numerical_audit.json, source_manifest.json, offline_manifest.json et synthese_v11g_localisation.png. L'audit séparé des fichiers sauvegardés est ajouté dans release_audit.json avant publication locale.",""]
    path.write_text("\n".join(out),encoding="utf8")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",required=True);args=parser.parse_args()
    cfg=read(CONFIG);directory=(ROOT/args.output).resolve()
    roots=[(ROOT/cfg[key]).resolve() for key in ("output_directory","scratch_directory")]
    if not any(directory==p or p in directory.parents for p in roots):raise ValueError("Outside V11G output roots")
    if directory.exists():raise FileExistsError("Preserve previous output; choose a new directory")
    previous=ROOT/cfg["panel_directory"]
    manifest=read(previous/"offline_manifest.json")
    expected={**manifest["input_sha256"],**{(previous/filename).relative_to(ROOT).as_posix():h for filename,h in manifest["output_sha256"].items()}}
    integrity={p:sha(ROOT/p)==h for p,h in expected.items()}
    if not all(integrity.values()):raise ValueError("V11F input/output hash mismatch")
    code=["wtc1_simulation_v8/scripts/"+p for p in ("v11g_localization_model.py","test_v11g_localization.py","run_v11g_localization.py","audit_v11g_release.py")]
    paths=list(dict.fromkeys([CONFIG.relative_to(ROOT).as_posix(),*expected,*code,
          (previous/"offline_manifest.json").relative_to(ROOT).as_posix(),(previous/"release_audit.json").relative_to(ROOT).as_posix()]))
    before={p:sha(ROOT/p) for p in paths}
    directory.mkdir(parents=True)
    started=datetime.now(timezone.utc).isoformat();start=time.perf_counter()
    ledger=physics.material_inputs(read(ROOT/cfg["section_configuration"]));si=ledger["SI"]
    panel_cfg=read(ROOT/cfg["panel_configuration"])
    eccentricity=read(ROOT/panel_cfg["panel_configuration"])["slab"]["attachment_eccentricity_fraction_of_thickness"]
    data=bars(cfg,si);print("16 localized reference paths computed",flush=True)
    replay=bars(cfg,si);print("Exact replay computed",flush=True)
    half=bars(cfg,si,.5);print("Half-step paths computed",flush=True)
    negative=physics.uniform_negative_control(cfg,si)
    original,meshes=panel_inputs(cfg)
    panels=[physics.panel_recovery(p,f"MESH_{n}",eccentricity,cfg["acceptance"]) for n,run in meshes.items() for p in run]
    tests,comparisons=test_v11g_localization.run(cfg,si,data,replay,half,negative,panels,original,eccentricity)
    tests.append({"test":"exact_deterministic_replay","pass":digest(data)==digest(replay),"evidence":digest(data)})
    tests.append({"test":"forty_two_cached_panels","pass":len(panels)==42,"evidence":len(panels)})
    fine=[p["summary"] for p in panels if p["summary"]["subdivisions"]==8]
    gate={"status":"PASS" if all(p["sampled_pointwise_gate_pass"] for p in fine) else "LOCAL_SECTION_DISCREPANCY_ABOVE_GATE",
          "passing_cases":sum(p["sampled_pointwise_gate_pass"] for p in fine),"case_count":len(fine),
          "failing_cases":[p["case_id"] for p in fine if not p["sampled_pointwise_gate_pass"]],
          "limits":{"N_relative":cfg["acceptance"]["panel_fine_pointwise_N_relative"],"M_relative":cfg["acceptance"]["panel_fine_pointwise_M_relative"]},
          "scope":"Sampled terminal resultants only; not complete-fracture localization or historical accuracy"}
    next_objective=("V11H : commencer le couplage thermomécanique borné, avec dilatation libre/empêchée et gradient de dalle, propriétés thermiques explicites et bilans adaptés. Préserver le contrôle froid V11F et limiter les revendications au domaine vérifié ; la localisation en flexion après fracture complète reste non validée. Ensuite instabilités géométriques, assemblages, impact calculé et feux spatialement résolus."
                    if gate["status"]=="PASS" else
                    "V11H : traiter d'abord les cas dont les efforts locaux dépassent les seuils, par raffinement longitudinal ou formulation adaptée et comparaison à état de chargement commun, sans modifier V11F ni élargir les tolérances après calcul. Puis commencer un couplage thermomécanique borné ; la fracture complète en flexion et la tour restent non validées.")
    runtime={"started_utc":started,"finished_utc":datetime.now(timezone.utc).isoformat(),"seconds":time.perf_counter()-start,
             "python":platform.python_version(),"numpy":np.__version__,"Pillow":pillow_version,"executable":sys.executable,
             "OPENBLAS_NUM_THREADS":os.environ.get("OPENBLAS_NUM_THREADS"),"scope":"Reference/replay/half-step/negative controls/panel recovery/tests, before report rendering"}
    maxima={key:max(row[key] for run in (data,replay,half) for b in run for row in b["history"])
            for key in data[0]["summary"]["maxima"]}
    result={"iteration":"V11G","status":"PASS" if all(t["pass"] for t in tests) else "FAIL",
            "test_count":len(tests),"tests_passed":sum(t["pass"] for t in tests),"bar_case_count":len(data),
            "bar_state_count":sum(len(b["history"]) for b in data),"uniform_negative_control_count":len(negative),"panel_terminal_count":len(panels),
            "bar_summaries":[b["summary"] for b in data],"bar_residual_maxima":maxima,"material_input_ledger":ledger,
            "panel_sampled_pointwise_gate":gate,"panel_weak_nodal_maximum":max(p["summary"]["weak_nodal_relative"] for p in panels),
            "runtime":runtime,"numerical_digest_sha256":digest({"bars":data,"negative":negative,"panels":panels}),
            "single_selected_bar_crack_validated":True,"full_panel_fracture_localization_validated":False,
            "panel_mechanics_changed":False,"global_energy_credit_J":0.,"fire_solved":False,"blender_changed":False,
            "aircraft_impact_computed":False,"as_built_material_known":False,"counts_are_probabilities":False,
            "next_iteration":"V11H","next_objective":next_objective}
    write(directory/"results_v11g.json",result);write(directory/"bar_paths.json",data);write(directory/"bar_half_step_paths.json",half)
    write(directory/"uniform_damage_controls.json",negative);write(directory/"panel_equilibrium_recovery.json",panels)
    write(directory/"material_input_ledger.json",ledger);write(directory/"numerical_audit.json",{"tests":tests,"test_count":len(tests),"half_step_comparisons":comparisons})
    write(directory/"source_manifest.json",{"iteration":"V11G","input_and_protected_sha256":before,"previous_V11F_expected_hashes":expected,
              "method_references":cfg["method_references"],"new_archive_or_pdf_analysis":False,"external_solver_or_multiagent_validation":False})
    figure(directory/"synthese_v11g_localisation.png",data,negative,panels,tests,gate)
    report(directory/"rapport_v11g_localisation.md",cfg,result,data,negative,panels)
    after={p:sha(ROOT/p) for p in paths}
    write(directory/"offline_manifest.json",{"iteration":"V11G","input_sha256":after,"input_and_protected_unchanged":before==after,
          "implementation_status":result["status"],"panel_pointwise_gate":gate,
          "output_sha256":{p.name:sha(p) for p in sorted(directory.iterdir()) if p.is_file()},"self_excluded":True})
    print(json.dumps({"status":result["status"],"tests":result["test_count"],"bar_states":result["bar_state_count"],"runtime_seconds":runtime["seconds"],
          "bar_maxima":maxima,"pointwise_gate":gate,"source_integrity":before==after,
          "failed_tests":[t for t in tests if not t["pass"]]},ensure_ascii=False),flush=True)
    if result["status"]!="PASS" or before!=after:raise SystemExit(1)


if __name__=="__main__":main()
