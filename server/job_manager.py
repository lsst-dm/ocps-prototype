from globals import STATUS_OK, STATUS_ERROR
import yaml
import os
import htcondor
from uuid import uuid4

class JobManager(object):
    def __init__(self):
        with open('jobs/job_specs.yaml', 'r') as f:
            self.job_types = yaml.load(f, Loader=yaml.SafeLoader)['type']


    def launch_job(self, type, env, log_dir):
        status = STATUS_OK
        msg = ''
        job_id = ''
        cluster_id = ''
        # Error and return if job type is not defined
        if type in self.job_types:
            status = STATUS_OK
        else:
            msg = 'Invalid job type'
            status = STATUS_ERROR
            return status, msg
        # Load environment variables required for the job
        print('{}'.format(env))
        for envvar in self.job_types[type]['env']:
            # print('{}'.format(env[envvar]))
            os.environ[envvar] = '{}'.format(env[envvar])
        # return status, msg, job_id, cluster_id

        # Generate unique identifier for this job for JobManager
        job_id = str(uuid4()).replace("-", "")
        # Create the output log directory if it does not exist
        os.makedirs(log_dir, exist_ok=True)
        # Submit the HTCondor job
        htcondor_job = htcondor.Submit({
            "executable": self.job_types[type]['script'],      # the program to run on the execute node
            "output": "{}/{}.out".format(log_dir, job_id),            # anything the job prints to standard output will end up in this file
            "error":  "{}/{}.err".format(log_dir, job_id),            # anything the job prints to standard error will end up in this file
            "log":    "{}/{}.log".format(log_dir, job_id),            # this file will contain a record of what happened to the job
            "getenv": "True",
        })
        htcondor_schedd = htcondor.Schedd()          # get the Python representation of the scheduler
        with htcondor_schedd.transaction() as txn:   # open a transaction, represented by `txn`
            cluster_id = htcondor_job.queue(txn)     # queues one job in the current transaction; returns job's ClusterID
        if not isinstance(cluster_id, int):
            msg = 'Error submitting Condor job'
            status = STATUS_ERROR
        return status, msg, job_id, cluster_id
