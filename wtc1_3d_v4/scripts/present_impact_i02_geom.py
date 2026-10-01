"""Annotated inspection sheet from saved 3D renders; no generative imagery."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]; render=ROOT/'wtc1_3d_v4/renders/impact_i02_geom/final'
font_path='C:/Windows/Fonts/arial.ttf'
def f(s): return ImageFont.truetype(font_path,s)
im=Image.new('RGB',(1440,1000),'#12212d'); d=ImageDraw.Draw(im)
d.text((28,20),'767-200 | Modele 3D importe et controle',font=f(32),fill='white')
d.rectangle((0,72,1440,119),fill='#924437'); d.text((28,81),'GEOMETRIE VISUELLE UNIQUEMENT - PAS UNE SIMULATION DE RESISTANCE',font=f(24),fill='white')
im.paste(Image.open(render/'perspective.png').resize((930,620)),(15,130))
d.text((970,155),'Modele complet en surface',font=f(25),fill='white')
lines=['Fuselage, ailes, empennages,','moteurs et surfaces mobiles.','','Longueur mesuree : 50,37 m','Reference Boeing : 48,51 m','','Envergure mesuree : 46,31 m','Reference Boeing : 47,57 m','','Aucun etirement correctif.','Les ecarts restent signales.','','Ni masse ni resistance deduites','de cette enveloppe graphique.']
for i,t in enumerate(lines): d.text((970,205+i*31),t,font=f(21),fill=('#f2c47e' if i in [3,4,6,7] else '#dae3eb'))
im.paste(Image.open(render/'plan.png').resize((480,320)),(10,665))
im.paste(Image.open(render/'front.png').resize((480,320)),(490,665))
d.text((30,675),'Vue de dessus',font=f(21),fill='white'); d.text((510,675),'Vue de face',font=f(21),fill='white')
d.text((970,785),'155 ensembles graphiques',font=f(22),fill='white'); d.text((970,818),'12 521 triangles conserves',font=f(22),fill='white')
d.text((970,870),'Source : Flightradar24 / FlightGear',font=f(19),fill='#c0ccd6'); d.text((970,899),'GitHub - licence GPLv2 conservee',font=f(19),fill='#c0ccd6')
d.text((970,940),'IMPACT-I02-GEOM | 10-09-2026',font=f(19),fill='#c0ccd6')
im.save(render/'B762_apercu_annote.png')
print('Inspection sheet saved')
