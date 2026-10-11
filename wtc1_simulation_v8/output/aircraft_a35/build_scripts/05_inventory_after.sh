#!/bin/bash
set -euo pipefail
dpkg-query -W -f='${binary:Package}	${Version}	${Status}\n' > '/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/output/aircraft_a35/package_inventory_after.txt'
gfortran --version
mpifort --showme
mpicc --showme
find /usr/lib/x86_64-linux-gnu -maxdepth 3 \( -name '*mumps*' -o -name '*pord*' -o -name '*scalapack*' -o -name '*lapack*' -o -name '*blas*' -o -name '*tmglib*' \) -print
ls /usr/include/*mumps*
