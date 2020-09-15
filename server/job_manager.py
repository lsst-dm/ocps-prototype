from globals import STATUS_OK, STATUS_ERROR, CONDOR_JOB_STATES
import envvars
import yaml
import os
import htcondor
from uuid import uuid4
import logging
from db_connector import DbConnector
import datetime
import json
import time
import asyncio
import subprocess

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
        dbFilePath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "../db",
            "job_manager.sqlite"
        )
        os.makedirs(os.path.dirname(dbFilePath), exist_ok=True)
        self.db = DbConnector(dbFilePath, read_only=False)


    def register_job(self, job_info):
        status = STATUS_OK
        msg = ''
        job_id = None

        self.db.open()
        try:
            # Generate unique identifier for this job for JobManager
            job_id = str(uuid4()).replace("-", "")
            # Error and return if job type is not defined
            job_type = job_info['type']
            if job_type in self.job_types:
                status = STATUS_OK
            else:
                status = STATUS_ERROR
                msg = 'Invalid job type'
                self.db.close()
                return status, msg
            job_spec = {
                "executable": self.job_types[job_type]['script'],      # the program to run on the execute node
                "output": "{}/{}.out".format(job_info['log_dir'], job_id),            # anything the job prints to standard output will end up in this file
                "error":  "{}/{}.err".format(job_info['log_dir'], job_id),            # anything the job prints to standard error will end up in this file
                "log":    "{}/{}.log".format(job_info['log_dir'], job_id),            # this file will contain a record of what happened to the job
                "env": job_info['env'],
                "getenv": "True",
            }
            # Add new record to job table
            # TODO: Ensure that the job_id is not already present in the table
            sql = '''
            INSERT INTO `job` (
                `type`, 
                `uuid`, 
                `cluster_id`, 
                `status`,
                `time_submit`,
                `spec`,
                `msg`
            )
            VALUES (?,?,?,?,?,?,?)
            '''
            self.db.db_cursor.execute(sql, (
                job_type,
                job_id,
                None,
                'init',
                datetime.datetime.utcnow(),
                json.dumps(job_spec),
                '',
            ))
        except Exception as e:
            status = STATUS_ERROR
            msg = str(e).strip()
        self.db.close()
        return status, msg, job_id


    def init(self, job_id):
        status = STATUS_OK
        msg = ''
        # Get the job info from the database
        job_info = self.db.get_job_info(job_id)
        # Launch a subprocess that will monitor the data repo for the input data required for the pipeline job. 
        # When the data arrives, launch the job using the JobManager API
        api_url = '{}://{}:{}{}/monitor/complete'.format(envvars.API_PROTOCOL, envvars.API_DOMAIN, envvars.API_PORT, envvars.API_BASEPATH)
        subprocess.Popen(['python', 'monitor.py', '--id', job_id, '--type', job_info['type'], '--api_url', api_url])
        return status, msg


    def launch(self, job_id):
        status = STATUS_OK
        msg = ''
        cluster_id = ''
        # Get the job info from the database
        job_info = self.db.get_job_info(job_id)
        # Load environment variables required for the job
        env = job_info['spec']['env']
        executable = job_info['spec']['executable']
        log_path = job_info['spec']['log']
        out_path = job_info['spec']['output']
        err_path = job_info['spec']['error']
        for envvar in self.job_types[job_info['type']]['env']:
            os.environ[envvar] = '{}'.format(env[envvar])
        # Create the output log directory if it does not exist
        os.makedirs(log_path, exist_ok=True)
        job_spec = {
            "executable": executable,      # the program to run on the execute node
            "output": out_path,            # anything the job prints to standard output will end up in this file
            "error":  err_path,            # anything the job prints to standard error will end up in this file
            "log":    log_path,            # this file will contain a record of what happened to the job
            "getenv": "True",
        }
        # Submit the HTCondor job
        htcondor_job = htcondor.Submit(job_spec)
        htcondor_schedd = htcondor.Schedd()          # get the Python representation of the scheduler
        with htcondor_schedd.transaction() as txn:   # open a transaction, represented by `txn`
            cluster_id = htcondor_job.queue(txn)     # queues one job in the current transaction; returns job's ClusterID
        if not isinstance(cluster_id, int):
            msg = 'Error submitting Condor job'
            status = STATUS_ERROR
            self.update_job(job_id, updates={
                'msg': msg,
            })
        else:
            self.update_job(job_id, updates={
                'cluster_id': cluster_id,
                'status': 'submitted',
            })
        return status, msg, cluster_id
    

    def status(self, job_id):
        cluster_id = self.get_cluster_id(job_id)
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
                print('Update for active job:')
            self.update_job(job_id, updates={
                'status': CONDOR_JOB_STATES[job_status['JobStatus']],
            })
        # Next search job history (condor_history)
        if not job_status:
            print('Job is no longer active.')
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
                print('Update for completed job:')
                self.update_job(job_id, updates={
                    'status': CONDOR_JOB_STATES[job_status['JobStatus']],
                    'time_start': datetime.datetime.fromtimestamp(job_status['JobStartDate']),
                    'time_complete': datetime.datetime.fromtimestamp(job_status['CompletionDate'])
                })
        return job_status


    def update_job(self, job_id, updates={}):
        self.db.open()
        for column in updates:
            if column != 'uuid':
                sql = '''
                UPDATE `job` SET `{}` = ? WHERE `uuid` = ?
                '''.format(column)
                self.db.db_cursor.execute(sql, (
                    updates[column],
                    job_id
                ))
                print('Updated column "{}" with value "{}"'.format(column, updates[column]))
        self.db.close()
    

    def get_cluster_id(self, job_id):
        self.db.open()
        sql = '''
        SELECT `cluster_id` FROM `job` WHERE `uuid` = ?
        '''
        results = self.db.db_cursor.execute(sql, (
            job_id,
        ))
        for row in results:
            cluster_id = row[0]
        self.db.close()
        return cluster_id

    async def monitor(self, filename, duration=5):
        status = STATUS_OK
        msg = ''
        print('Monitoring file "{}" for {} seconds...'.format(filename, duration))
        await asyncio.sleep(duration)
        print('Monitoring complete for file "{}".'.format(filename))
        return status, msg