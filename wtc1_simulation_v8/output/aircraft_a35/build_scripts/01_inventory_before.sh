#!/bin/bash
set -euo pipefail
date -u
uname -a
cat /etc/os-release
cmake --version
gcc --version
dpkg-query -W -f='${binary:Package}	${Version}	${Status}\n' > '/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/output/aircraft_a35/package_inventory_before.txt'

