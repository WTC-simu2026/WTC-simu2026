"""Reproduce the static instruction localization, preserving the saved first review."""
from probe_aircraft_a48 import *
import build_aircraft_a35_mumps as bridge
import subprocess

def run():
 guard();p=subprocess.run(['wsl.exe','-d','Ubuntu','--','objdump','--disassemble=assemc_kij_',bridge.linux(BINARY)],capture_output=True,timeout=30);assert p.returncode==0;s=p.stdout.decode();m=re.search(r'([0-9a-f]+) <assemc_kij_>',s);address=int(m.group(1),16)+0x664;line=next(l for l in s.splitlines() if re.match(r'\s*'+format(address,'x')+':',l));old=read(OUT/'assembly_static_fault_offset_review.json');assert old['binary_sha256']==streamsha(BINARY) and old['instruction_address_hex']==hex(address) and old['instruction']==line.strip();dest=OUT/'static_fault_reproduction_review.json';assert not dest.exists();dump(dest,{'created_utc':now(),'pass':True,'binary_sha256':streamsha(BINARY),'function_offset_hex':hex(int(m.group(1),16)),'fault_instruction_address_hex':hex(address),'instruction':line.strip(),'same_original_instruction_review':True,'raw_disassembly_not_redistributed':True,'read_only_tool':'objdump','cap_s':30});print({'static_instruction_reproduced':True},flush=True)

if __name__=='__main__':run()
