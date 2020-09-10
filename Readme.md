Rubin prompt processing system prototype
========================================

Job Type Specification
----------------------

The available job types are defined in a `jobs/job_specs.yaml` file that looks like

```yaml
type:
    # Alert Production pipeline: https://pipelines.lsst.io/v/daily/modules/lsst.ap.pipe/index.html
    ap:
        # The script to be executed by HTCondor
        script: "jobs/ap_job.sh"
        # Environment variables required by the job script
        env:
            - "AP_JOB_OUTPUT_DIR"
            - "AP_VISIT_ID"
            - "AP_CCD_NUM"
            - "AP_REPO"
            - "AP_TEMPLATE"
            - "AP_CALIB"
            - "AP_FILTER"
    # Additional job type definitions...
```

This example shows a definition for a job type `ap`. The `script` parameter (YAML scalar node) specifies the script that will be executed by HTCondor. The `env` declares the environment variables that must be specified when submitting a job.

The script parameter will be revised to require specification of immutable code for reproducibility. For example, a git repo URL (from some controlled location) and specific git commit hash would suffice.

Server - OCPS Job Manager
----------------------

Server configuration can be customized using environment variables:
```sh
API_PORT
API_BASEPATH
API_DOMAIN
API_PROTOCOL
```

Launch the API server, listening by default on port 8080:
```sh
bash launch_job_manager.sh 
```


Client - OCSP CSC
----------------------

As currently envisioned, the data (e.g. camera images) that form the input to the prompt processing jobs will be transferred from the OCS by an independent system; thus the input data is assumed to be accessible to the Job Manager as a Butler repo residing on some locally mounted storage.

The prototype client parses a config file to get the information needed to demonstrate the Job Manager API.

Construct the client config file `config.yaml` similar to this:

```sh
cat > config.yaml << EOF

data:
  repo:     "/datasets/des_sn/repo_Y3/"
  template: "/datasets/des_sn/repo_Y3/templates/"
  db:       "/datasets/des_sn/repo_Y3/registry.sqlite3"
  calib:    "/datasets/des_sn/calib/"
  filter:   "g"
job:
  output_dir: './output'
  log_dir:    './logs'

EOF
```

The client demo will use the values to compose the HTTP request according to the Job Manager API Specification

Run the client demo using the wrapper script `run_client.sh`, which configures the software environment using the LSST Software Stack.

```sh
bash run_client.sh 
```


Job Manager API Specification
----------------------

### `POST /api/v1/job`

Submit a job to the HTCondor queue for processing.

Python example:

```python
    r = requests.post(
        '/api/v1/job',
        json={
            'type': 'ap',
            'env': {
                'AP_JOB_OUTPUT_DIR': conf['job']['output_dir'],
                'AP_VISIT_ID': image['visit_id'],
                'AP_CCD_NUM': image['ccd'],
                'AP_REPO': conf['data']['repo'],
                'AP_TEMPLATE': conf['data']['template'],
                'AP_CALIB': conf['data']['calib'],
                'AP_FILTER': conf['data']['filter'],
            },
            'log_dir': conf['job']['log_dir'],
        }
    )
```

### `GET /api/v1/job?id=123`

Get information and status for an existing job. 

