#!/bin/bash
set -euo pipefail
apt-get --simulate install --no-install-recommends gfortran libopenmpi-dev libmumps-dev libscalapack-openmpi-dev liblapack-dev libtmglib-dev
