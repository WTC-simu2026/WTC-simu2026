"""Preserved draft revision: clarify signed impulse identity and scope wording.

No scientific input, solve, audit, gate or numerical result is changed.
Both draft reports, original completion script and manifest are retained.
"""
from __future__ import annotations
import json
from pathlib import Path
import complete_impact_i02i_free_fracture as c
import run_impact_i02i_free_fracture as h

def revise():
    dest=h.OUT/'report_revision_r1';assert not dest.exists(),'Preserve revisions';dest.mkdir()
    before=json.loads((h.OUT/'artifact_manifest.json').read_text(encoding='utf-8'))
    for p in [c.REPORT,c.HANDOFF,h.OUT/'artifact_manifest.json',Path(c.__file__)]:
        (dest/p.name).write_bytes(p.read_bytes())
    text=c.REPORT.read_text(encoding='utf-8')
    old='À 50 ns : momentum final 1,732244 N ms, impulsion d\'appui −1,267756 N ms ; leur somme avec P0=3 est compatible. À 25 ns : 1,732142 et −1,267858 N ms.'
    new='À 50 ns : P0+Jappui=3−1,267756=1,732244 N ms, égal au momentum final sauvegardé. À 25 ns : P0+Jappui=3−1,267858=1,732142 N ms, égal au momentum final sauvegardé.'
    assert old in text;text=text.replace(old,new);c.REPORT.write_text(text,encoding='utf-8',newline='\n')
    text=c.HANDOFF.read_text(encoding='utf-8');old='Première séparation normale libre numérique :'
    assert old in text;text=text.replace(old,'Témoin neuf de séparation normale libre TYPE8 dans cette série I02I :')
    c.HANDOFF.write_text(text,encoding='utf-8',newline='\n')
    release=json.loads((h.OUT/'release_audit.json').read_text(encoding='utf-8'))
    (dest/'release_audit.json').write_bytes((h.OUT/'release_audit.json').read_bytes())
    release.update(report_sha256=h.sha(c.REPORT),handoff_sha256=h.sha(c.HANDOFF),report_revision='report_revision_r1')
    h.dump(h.OUT/'release_audit.json',release)
    h.dump(dest/'revision.json',{'created_utc':h.NOW(),'pass':True,'changes':['Clarify P0+J_support=P_final with signed numbers','Scope this TYPE8 witness to I02I, without claiming project-wide first dynamic fracture'],
        'numerical_results_changed':False,'gates_changed':False,'old_iterations_changed':False,'script_sha256':h.sha(__file__)})
    h.dump(h.OUT/'harness_after_report_revision.json',h.harness())
    paths=[h.ROOT/r['path'] for r in before['files']]+[p for p in dest.rglob('*') if p.is_file()]+[Path(__file__),h.OUT/'harness_after_report_revision.json']
    h.dump(h.OUT/'artifact_manifest.json',{'created_utc':h.NOW(),'files':[{'path':h.rel(p),'bytes':p.stat().st_size,'sha256':h.sha(p)} for p in sorted(set(paths))],
        'exclusions':before['exclusions'],'draft_preserved':'report_revision_r1/artifact_manifest.json'})
    print('Report identities clarified; draft and all numerical records preserved.',flush=True)

if __name__=='__main__':revise()
