#!/bin/bash
set -euo pipefail
exec >"/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/output/aircraft_a35/build_logs/29_w3_reader_configure.log" 2>&1
cmake -S '/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate/fast_workspace_w2/source/reader' -B '/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate/fast_workspace_w2/reader_build' -Darch=linux64 -Dcom=0 -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++
