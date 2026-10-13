set -eu
export OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1
export OPENRADIOSS_PATH=/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate
export RAD_CFG_PATH=/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/hm_cfg_files
exec python3 /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/scripts/trace_aircraft_a53_write_watch_linux.py /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/output/aircraft_a53/WHOLE_REFERENCE_GRAPH_WRITE_WATCH/instrumentation_config.json
