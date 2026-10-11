#!/bin/bash
set -euo pipefail
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gfortran libopenmpi-dev libmumps-dev libscalapack-openmpi-dev liblapack-dev libtmglib-dev
