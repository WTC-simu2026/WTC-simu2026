set -eu
export OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1
export OPENRADIOSS_PATH=/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate
export RAD_CFG_PATH=/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/hm_cfg_files
exec python3 /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/scripts/trace_aircraft_a49_linux.py /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/output/aircraft_a52/WHOLE_PAIRED_SPARSE_FAULT_TRACE/instrumentation_config.json
