#!/bin/bash
set -euo pipefail
exec >"/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/output/aircraft_a35/build_logs/31_w3_starter_configure.log" 2>&1
cmake -S '/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate/fast_workspace_w2/source/starter' -B '/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate/fast_workspace_w2/starter_build' -Darch=linux64_gf -Dprecision=dp -Ddebug=0 -Dno_python=0 -Dstatic_link=0 -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DEXEC_NAME=starter_linux64_gf -DUSE_OPEN_READER=1
