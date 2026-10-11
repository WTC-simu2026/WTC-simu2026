#!/bin/bash
set -euo pipefail
exec >"/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/output/aircraft_a35/build_logs/28_w3_engine_compile.log" 2>&1
cmake --build '/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate/fast_workspace_w2/engine_build' --parallel 6
