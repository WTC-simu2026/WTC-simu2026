set -eu
nm --defined-only /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate/isolated_exec/engine_linux64_gf_ompi | sed -n '/__sigeps117_mod_MOD_sigeps117$/p'
addr2line -f -C -e /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate/isolated_exec/engine_linux64_gf_ompi 0x146f33e
objdump -d --start-address=0x146f310 --stop-address=0x146f375 /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate/isolated_exec/engine_linux64_gf_ompi
