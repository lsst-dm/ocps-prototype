from globals import STATUS_OK, STATUS_ERROR
import yaml
import os
import htcondor
from uuid import uuid4
import logging 

log_format = "%(asctime)s  %(name)8s  %(levelname)5s  %(message)s"
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler("test.log"), logging.StreamHandler()],
    format=log_format,
)
logger = logging.getLogger("main")


class JobManager(object):
    def __init__(self):
        with open('jobs/job_specs.yaml', 'r') as f:
            self.job_types = yaml.load(f, Loader=yaml.SafeLoader)['type']


    def launch(self, type, env, log_dir):
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
        # print('{}'.format(env))
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
    
    def status(self, cluster_id):
        schedd = htcondor.Schedd()
        # First search the jobs currently in queue (condor_q)
        attr_list = [
            'ClusterId', 
            'JobStatus',
        ]
        query_results = schedd.query(
            constraint='ClusterId =?= {}'.format(cluster_id),
            attr_list=attr_list,
        )
        # Assume only a single result
        job_status = {}
        for classad in query_results:
            job_status = {
                'active': True,
            }
            for field in attr_list:
                job_status[field] = classad[field]
        # Next search job history (condor_history)
        if not job_status:
            projection = [
                    'ClusterId', 
                    'JobStatus', 
                    'LastJobStatus', 
                    'ExitStatus', 
                    'Owner', 
                    'User', 
                    'JobStartDate', 
                    'JobCurrentStartExecutingDate', 
                    'CompletionDate', 
                    'Cmd', 
                    'Out', 
                    'UserLog', 
                    'Err', 
                ]
            query_results = schedd.history(
                requirements='ClusterId =?= {}'.format(cluster_id),
                projection=projection,
                # projection=["ClusterId", "JobStatus"],
            )
            for classad in query_results:
                print('Finished job: {}'.format(classad))
                job_status = {
                    'active': False,
                }
                for field in projection:
                    job_status[field] = classad[field]

        return job_status
