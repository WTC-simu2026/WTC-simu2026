"""Read-only ELF/provenance audit and pre-Engine launch failure classification."""
from probe_aircraft_a44_legacy import ROOT,OUT,CFG,BINARY,CAND,read,dump,rel,now,streamsha,guard
import struct

def elf():
 guard();b=BINARY.read_bytes();h=struct.unpack_from('<16sHHIQQQIHHHHHH',b);assert h[0][:6]==b'\x7fELF\x02\x01' and h[2]==62;sections=[struct.unpack_from('<IIQQQQIIQQ',b,h[6]+i*h[11]) for i in range(h[12])];symbols=[];needed=[]
 def ztext(table,offset):return table[offset:table.index(b'\0',offset)].decode('ascii')
 for sec in sections:
  if sec[1] in [2,11]:
   strings=sections[sec[6]];table=b[strings[4]:strings[4]+strings[5]]
   for i in range(0,sec[5],sec[9]):
    row=struct.unpack_from('<IBBHQQ',b,sec[4]+i)
    if row[0]:symbols.append({'name':ztext(table,row[0]),'defined':row[3]!=0,'dynamic':sec[1]==11})
  if sec[1]==6:
   strings=sections[sec[6]];table=b[strings[4]:strings[4]+strings[5]]
   for i in range(0,sec[5],sec[9]):
    tag,value=struct.unpack_from('<qQ',b,sec[4]+i)
    if tag==1:needed.append(ztext(table,value))
 legacy=[r for r in symbols if r['name']=='sigeps117_' and r['defined']];modern=[r for r in symbols if '__sigeps117_mod_MOD_sigeps117' in r['name']];mumps=[r for r in symbols if r['dynamic'] and not r['defined'] and 'dmumps' in r['name'].lower()];assert legacy and not modern and mumps and any('dmumps' in n for n in needed);build=read(OUT/'build_finished.json');old=read(OUT/'protected_binaries_before.json');assert all(streamsha(ROOT/r['path'])==r['sha256'] for r in old['files']);verify=read(OUT/'source_and_dependency_verification.json');assert verify['pass'];statuses=[read(p) for p in sorted((OUT/'build_logs').glob('*.execution.json'))];assert all(r['exit_code']==0 for r in statuses);assert 'not found' not in (OUT/'build_logs/07_export.log').read_text()
 dump(OUT/'candidate_binary_static_review.json',{'created_utc':now(),'pass':True,'ELF_class':64,'ELF_byte_order':'little','machine':'x86_64','binary_sha256':streamsha(BINARY),'bytes':len(b),'source_pin':build['source_pin'],'source_and_dependency_blobs_verified':len(verify['files']),'old_LAW117_defined_symbol':legacy,'new_LAW117_module_symbol_absent':True,'referenced_MUMPS_dynamic_symbols':mumps,'needed_shared_libraries':needed,'loader_dependencies_all_resolved_in_build_export_log':True,'build_all_steps_exit0':True,'build_wall_s':build['wall_s'],'within_authorized_hour':build['within_hour'],'old_binaries_unchanged':True,'software_installations':0,'mechanical_source_patches':0,'native_execution_test_pass':False,'native_compatibility_qualified':False,'whole_insertion_ready':False});print({'ELF_and_source_pass':True,'legacy_LAW117_symbol':legacy[0]['name'],'MUMPS_referenced':[r['name'] for r in mumps],'old_binaries_preserved':True},flush=True)

def classify():
 guard();cases=[]
 for d in sorted((OUT/'w0').iterdir()):
  execution=read(d/'engine.log.execution.json');text=(d/'engine.launcher.log').read_bytes().decode('utf-16-le',errors='replace');assert 'Wsl/E_ACCESSDENIED' in text and execution['exit_code']==4294967295;assert not (d/'engine.log').exists();cases.append({'case':d.name,'wrapper_exit_code':execution['exit_code'],'classified_failure':'WSL access denied before Engine starts','Engine_executed':False,'native_physical_gate_assessed':False,'launcher_error_text':text,'retained_original_completion_review':rel(d/'completion.json')})
 assert len(cases)==4;dump(OUT/'native_launch_environment_review.json',{'created_utc':now(),'cases':cases,'native_launch_attempts':4,'actual_Engine_executions':0,'actual_converters':0,'all_failures_before_Engine':True,'Windows_WSL_status_also_denied':True,'build_success_unchanged':True,'physical_solver_failure_inferred':False,'blocking_condition':'Current execution environment refuses WSL. Existing human authorization covers build and tests; no additional build consent needed.','no_permission_boundary_bypass_attempted':True,'recovery':'Restore WSL access through execution environment, then use fresh control directories. Do not rebuild or replace the completed Engine.','objective1_complete':False});print({'launch_failures_classified':4,'Engine_executions':0,'new_blocker':'WSL access'},flush=True)

if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('action',choices=['elf','classify']);globals()[p.parse_args().action]()
