#! /bin/bash
#
# Docs about running Alert Processing pipelines:
#   https://pipelines.lsst.io/v/daily/modules/lsst.ap.pipe/pipeline-tutorial.html
#
set -e

# Import values from environment variables
outdir="${AP_JOB_OUTPUT_DIR}"
expnum="${AP_VISIT_ID}"
ccdnum="${AP_CCD_NUM}"
repo="${AP_REPO}"
calib="${AP_CALIB}"
template="${AP_TEMPLATE}"
filter="${AP_FILTER}"

# Specify output directories and Alert Production Database (apdb) files
outputRepoDir="${outdir}/repo"
outputDbDir="${outdir}/apdb"
outputDbUrl="sqlite:///${outputDbDir}/association.db"
# Create output folders if nonexistent
mkdir -p "${outputRepoDir}"
mkdir -p "${outputDbDir}"

# Create the Alert Production Database using config overrides
make_apdb.py                                              \
	--config diaPipe.apdb.isolation_level=READ_UNCOMMITTED  \
	--config diaPipe.apdb.db_url="${outputDbUrl}"

# Run the AP pipeline
ap_pipe.py "${repo}"                                               \
	--id visit="${expnum}" ccdnum="${ccdnum}"                        \
	--calib "${calib}"                                               \
	--template "${template}"                                         \
	--config diaPipe.apdb.isolation_level=READ_UNCOMMITTED           \
	--config diaPipe.apdb.db_url="${outputDbUrl}"                    \
	--output "${outputRepoDir}"
