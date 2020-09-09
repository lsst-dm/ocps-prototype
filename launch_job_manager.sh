#! /bin/bash
#
set -e

# Change working directory to script location
scriptPath="$(readlink -f "$0")"
scriptDir="$(dirname "${scriptPath}")"
cd "${scriptDir}/server" || exit 1

# Load the sofware and environment configuration
source "/software/lsstsw/stack3/loadLSST.bash"
setup lsst_distrib
export PYTHONPATH=$PYTHONPATH:/usr/lib64/python3.6/site-packages

python server.py

exit 0
