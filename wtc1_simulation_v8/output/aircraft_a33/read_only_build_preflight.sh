#!/bin/sh
# Read-only inventory. No installation, compilation or package download.
set +e
cat /etc/os-release
for app in cmake gcc make gfortran mpifort mpicc; do
  printf '%s: ' "$app"
  command -v "$app" || printf 'ABSENT\n'
done
dpkg-query -W -f='${Package} ${Version} ${Status}\n' '*mumps*' '*gfortran*' '*openmpi*' '*mpich*' 2>/dev/null
