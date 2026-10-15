set -eu
cd /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/output/aircraft_a91/native/FREE_Ismstr4
export OMP_NUM_THREADS=1 OMP_THREAD_LIMIT=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export OPENRADIOSS_PATH=/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a91_projected_null_candidate
export RAD_CFG_PATH=/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a91_projected_null_candidate/hm_cfg_files
exec /mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a91_projected_null_candidate/isolated_exec/engine_linux64_gf_ompi -i A67_FREE_Ismstr4_0001.rad > engine.log 2>&1
