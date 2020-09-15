from globals import STATUS_OK, STATUS_ERROR, CONDOR_JOB_STATES
import envvars
import logging
import tornado.ioloop
import tornado.web
from tornado.gen import coroutine
import tornado
import json
import os
from job_manager import JobManager
from datetime import datetime

# Configure logging
log_format = "%(asctime)s  %(name)8s  %(levelname)5s  %(message)s"
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler("test.log"), logging.StreamHandler()],
    format=log_format,
)
logger = logging.getLogger("main")

# Instantiate JobManager instance
jm = JobManager()

class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization")
        self.set_header("Access-Control-Allow-Methods",
                        " POST, PUT, DELETE, OPTIONS, GET")

    def options(self):
        self.set_status(204)
        self.finish()

    def getarg(self, arg, default=None):
        response = {
            'status': STATUS_OK,
            'message': ''
        }
        value = default
        try:
            # If the request encodes arguments in JSON, parse the body accordingly
            if 'Content-Type' in self.request.headers and self.request.headers['Content-Type'] in ['application/json', 'application/javascript']:
                data = tornado.escape.json_decode(self.request.body)
                if default == None:
                    # The argument is required and thus this will raise an exception if absent
                    value = data[arg]
                else:
                    # Set the value to the default
                    value = default if arg not in data else data[arg]
            # Otherwise assume the arguments are in the default content type
            else:
                # The argument is required and thus this will raise an exception if absent
                if default == None:
                    value = self.get_argument(arg)
                else:
                    value = self.get_argument(arg, default)
        except Exception as e:
            response['status'] = STATUS_ERROR
            response['message'] = str(e).strip()
            logger.error(response['message'])
            # 400 Bad Request: The server could not understand the request due to invalid syntax.
            # The assumption is that if a function uses `getarg()` to get a required parameter,
            # then the request must be a bad request if this exception occurs.
            self.set_status(400)
            self.write(json.dumps(response))
            self.finish()
            raise e
        return value


class JobHandler(BaseHandler):
    def get(self):
        response = {
            'status': STATUS_OK,
            'msg': '',
            'job': {},
        }
        job_id = self.get_query_argument('id')
        job_info = jm.status(job_id)
        if not job_info:
            response['status'] = STATUS_ERROR
            response['msg'] = 'Job not found'
            self.write(response)
            return
        response['job']['clusterId'] = job_info['ClusterId']
        response['job']['state'] = CONDOR_JOB_STATES[job_info['JobStatus']]
        if job_info['JobStatus'] == 4:
            response['job']['timeCompleted'] = datetime.fromtimestamp(job_info['CompletionDate']).strftime("%A, %B %d, %Y %I:%M:%S")
        self.write(response)

    def post(self):
        response = {
            'status': STATUS_OK,
            'msg': '',
            'job_id': None,
            'cluster_id': None,
        }
        job_type = self.getarg('type')
        job_env = self.getarg('env')
        log_dir = self.getarg('log_dir')
        # status, msg, response['job_id'], response['cluster_id'] = jm.launch(job_type, job_env, log_dir)

        status, msg, job_id = jm.register_job({
            'type': job_type,
            'env': job_env,
            'log_dir': log_dir,
        })
        if status != STATUS_OK:
            response['status'] = STATUS_ERROR
            response['msg'] = msg
            self.write(response)
            return
        response['job_id'] = job_id
        status, msg = jm.init(job_id)
        if status != STATUS_OK:
            response['status'] = STATUS_ERROR
            response['msg'] = msg
            self.write(response)
            return
        self.write(response)


class MonitorHandler(BaseHandler):
    async def post(self):
        response = {
            'status': STATUS_OK,
            'msg': '',
        }
        filename = self.getarg('filename')
        duration = self.getarg('duration')
        status, msg = await jm.monitor(filename, duration)
        if status != STATUS_OK:
            response['status'] = STATUS_ERROR
            response['msg'] = msg
        self.write(response)


class MonitorCompleteHandler(BaseHandler):
    def get(self):
        response = {
            'status': STATUS_OK,
            'msg': '',
        }
        job_id = self.getarg('id')
        logger.info('Data arrived for job "{}". Launching job...'.format(job_id))
        status, msg, response['cluster_id'] = jm.launch(job_id)
        self.write(response)


def make_app(base_path=''):
    settings = {"debug": True}
    return tornado.web.Application(
        [
            (r"{}/job".format(base_path), JobHandler),
            (r"{}/monitor/complete".format(base_path), MonitorCompleteHandler),
        ],
        **settings
    )


if __name__ == "__main__":
    app = make_app(base_path=envvars.API_BASEPATH)
    app.listen(envvars.API_PORT)
    logger.info('Running at localhost:{}{}'.format(envvars.API_PORT, envvars.API_BASEPATH))
    tornado.ioloop.IOLoop.current().start()
