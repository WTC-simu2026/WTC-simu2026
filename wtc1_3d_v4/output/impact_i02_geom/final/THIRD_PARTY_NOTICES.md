# Third-party model and modification notice

Aircraft graphics source: Flightradar24/fr24-3d-models, with FlightGear/FGMEMBERS ancestry credited by the publisher.

Repository: https://github.com/Flightradar24/fr24-3d-models
Pinned revision: dd53267690c6a4ecbb290a3acf0284333a5d68a9
Selected aircraft: models/b762.glb; source/b762/767-200.blend; source/b762/762.zip.

The publisher identifies this aircraft as Boeing 767-200 and licenses the aircraft models under GNU GPL version 2. The original README and full LICENSE are retained verbatim in the source package; a verbatim license copy accompanies these derived files. This is the publisher's license declaration, not an independent certification of every upstream contribution. No endorsement by Boeing, FlightGear or Flightradar24 is implied.

Modifications made 2026-09-10 in this research workspace: decoded glTF 1.0 scene geometry with node transforms; permuted axes cyclically; replaced visual materials with neutral display materials; retained source length scale; removed 126 zero-area triangles (threshold 1e-12 m²) from derived display files only, with source indices recorded; created a clean Blender scene, a glTF 2.0 binary model, inspection views and measurement audits. Source files are unmodified. No airline textures are reproduced in the derived neutral scene.

The derived model and its rendering/conversion scripts are made available under GPL-2.0. Source assets, conversion scripts and this modification notice are included in the delivery ZIP, without any warranty. See LICENSE_GPL2.txt for the full license terms.

These are graphics surfaces, not an engineering finite-element reconstruction: no mechanical material properties, structural skin thickness, mass allocation, physical joints, fuel or failure model are supplied. Zero mechanical credit has been assigned in the harness. Length and span differ from Boeing airport-planning dimensions; see rapport_impact_i02_geom.md. No impact outcome is implied.
