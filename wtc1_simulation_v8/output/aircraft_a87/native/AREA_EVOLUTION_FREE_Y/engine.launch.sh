set -eu
cd /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/output/aircraft_a87/native/AREA_EVOLUTION_FREE_Y
export OMP_NUM_THREADS=1 OMP_THREAD_LIMIT=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export OPENRADIOSS_PATH=/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a87_null_relative_candidate
export RAD_CFG_PATH=/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a87_null_relative_candidate/hm_cfg_files
exec /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a87_null_relative_candidate/isolated_exec/engine_linux64_gf_ompi -i A67_AREA_EVOLUTION_FREE_Y_0001.rad > engine.log 2>&1
