"""Finish from cached correct R2 source/cards; explicitly allow renamed BEGIN/TITLE, no regeneration or native run."""
import prepare_aircraft_a70_zero_residual_r2 as prepared
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from prepare_aircraft_a66_current_area_r1 import sections
from pathlib import Path
import ast,json

def main():
    assert not prepared.PLAN.exists();source=Path(prepared.__file__);text=source.read_text(encoding='utf8')
    old="['/BEGIN','/INIVEL/TRA/500','/END']";new="['/BEGIN','/TITLE','/INIVEL/TRA/500','/END']";assert text.count(old)==1
    tree=ast.parse(text.replace(old,new));function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    tail=[n for n in function.body if n.lineno>=47];assert isinstance(tail[0],ast.Assert)
    ctx=dict(vars(prepared));local=ROOT/'wtc1_simulation_v8/output/aircraft_a67/native/FREE_Ismstr4';name=read(local/'generation.json')['name']
    ctx.update(local=local,name=name,rst=local/(name+'_0000_0001.rst'),card=local/(name+'_0001.rad'),starter=local/(name+'_0000.rad'),
        base=ROOT/'wtc1_simulation_v8/openradioss_runtime/a68_check_semantics_audit/imp_solv.F',
        dest=prepared.PRIVATE/'imp_solv.proposed.F',diff=prepared.PRIVATE/'initial_Newmark_zero_residual.patch',
        fc=prepared.PREP/'FREE_INITIAL_ZERO_CHECK'/(name+'_0001.rad'),sc=prepared.PREP/'STATIC_INITIAL_ZERO_CHECK'/(name+'_0001.rad'),
        loadedname='A71_STATIC_POSITIVE_LOAD_CHECK',loadedstarter=prepared.PREP/'STATIC_POSITIVE_LOAD_CHECK/A71_STATIC_POSITIVE_LOAD_CHECK_0000.rad',
        loadedcard=prepared.PREP/'STATIC_POSITIVE_LOAD_CHECK/A71_STATIC_POSITIVE_LOAD_CHECK_0001.rad')
    ctx['parsed']=sections(ctx['loadedstarter'])
    dump(prepared.PREP/'preparation_failed_r2.json',{'created_utc':now(),'failure':'Guard compared the intentionally renamed TITLE as if mechanical data',
        'source_patch_applied':False,'compiled':False,'new_native':0,'source_and_native_cards_correct_but_not_sealed':True,'script_sha256':sha(source)})
    before=ctx['base'].read_text(encoding='utf8');after=ctx['dest'].read_text(encoding='utf8')
    added="        ELSEIF(IDYNA==2.AND.IQSTAT==0.AND.TIME==ZERO.AND.\n     .         R2==ZERO) THEN\n          WRITE(IOUT,*)' ** INITIAL DYNAMIC RESIDUAL IS ZERO **'\n"
    assert after.count(added)==1 and after.replace(added,'')==before
    exec(compile(ast.Module(body=tail,type_ignores=[]),str(source)+'#cached_finish','exec'),ctx)
    dump(prepared.PREP/'preparation_finish_r3.json',{'created_utc':now(),'pass':True,'correct_R2_source_and_cards_reused':True,
        'BEGIN_and_TITLE_intentionally_renamed_only':True,'mechanical_card_comparison_pass':True,'old_R0_R1_R2_failures_preserved':True,
        'source_applied':False,'new_native':0,'new_compilation':False,'source_sha256':sha(ctx['dest']),'plan_sha256':sha(prepared.PLAN)})

if __name__=='__main__':main()
