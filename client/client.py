from globals import STATUS_OK, STATUS_ERROR
import envvars
import requests
import json
import yaml
import sqlite3
import random
import time

# Import credentials and config from environment variables
config = {
    'apiBaseUrl': '{}://{}:{}{}'.format(envvars.API_PROTOCOL, envvars.API_DOMAIN, envvars.API_PORT, envvars.API_BASEPATH),
}


def db_open_conn(db_file='', read_only=True):
    if read_only:
        db = sqlite3.connect('file:{}?mode=ro'.format(db_file), uri=True)
    else:
        db = sqlite3.connect('file:{}'.format(db_file), uri=True)
    return [db, db.cursor()]


def db_close_conn(db):
    db.commit()
    db.close()


def get_job():
    r = requests.get(
        '{}/job'.format(config['apiBaseUrl'])
    )
    response = r.json()
    return response

def get_job_status(job_id):
    r = requests.get(
        '{}/job'.format(config['apiBaseUrl']),
        params={
            'id': job_id
        }
    )
    response = r.json()
    return response


def post_job(type=''):
    r = requests.post(
        '{}/job'.format(config['apiBaseUrl']),
        data={
            'type': type,
        }
    )
    response = r.json()
    return response


def post_job_ap(conf, image):
    r = requests.post(
        '{}/job'.format(config['apiBaseUrl']),
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
    response = r.json()
    return response


def query_butler_repo_for_filter(conf):

    db_file = conf['data']['db']
    filter = conf['data']['filter']

    [db_conn, db_cursor] = db_open_conn(db_file=db_file)

    ccd_nums = []
    visit_ids = []
    # minId = (0,)
    results = db_cursor.execute(
        'SELECT id,visit,ccd,ccdnum FROM raw WHERE filter=?', (filter,))
    data = []
    for row in results:
        # print('ID: {}\tVISIT: {}\tCCD: {}\tccd_num: {}'.format(*row))
        row_id = row[0]
        visit_id = row[1]
        ccd = row[2]
        ccdnum = row[3]
        if ccd != ccdnum:
            print('Mismatched CCD and ccd_num:')
            print('\tID: {}\tVISIT: {}\tCCD: {}\tccd_num: {}'.format(*row))
            import sys
            sys.exit()
        data.append({
            'row_id': row_id,
            'visit_id': visit_id,
            'ccd': ccd,
            'filter': filter,
        })
    db_close_conn(db_conn)
    return data

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='Manage HTCondor jobs.')
    parser.add_argument(
        '--config',
        dest='config',
        type=argparse.FileType('r'),
        nargs='?',
        help='Job config file',
        required=True
    )
    args = parser.parse_args()

    # Load the client config that defines the location of the Butler repo containing the data
    configPath = args.config.name
    with open(configPath, 'r') as f:
        conf = yaml.load(f, Loader=yaml.SafeLoader)

    # # API endpoint test: GET /job
    # response = get_job()
    # print('get_job: \n{}'.format(json.dumps(response, indent=2)))

    # # API endpoint test: POST /job
    # # No job info provided
    # response = post_job()
    # print('post_job: \n{}'.format(json.dumps(response, indent=2)))


    # API endpoint test: POST /job
    # Select random image from Butler repo
    data = query_butler_repo_for_filter(conf)
    random_image = random.choice(data)
    print('Random image from selected data: \n{}'.format(json.dumps(random_image, indent=2)))
    # Alert production job type specified
    response = post_job_ap(conf, random_image)
    cluster_id = response['cluster_id']
    job_id = response['job_id']
    print('POST /api/v1/job : \n{}'.format(json.dumps(response, indent=2)))

    # # API endpoint test: GET /job
    # response = get_job_status(response['cluster_id'])
    # print('get_job_status: \n{}'.format(json.dumps(response, indent=2)))

    print('Polling status of job: GET /api/v1/job?id={} ...'.format(job_id), end='')
    max_loops = 100
    idx = 0
    while idx < max_loops:
        idx = idx + 1
        response = get_job_status(job_id)
        if response['status'] != STATUS_OK or response['job']['state'] in ['completed', 'removed', 'held', 'suspended']:
            break
        print('.', end='', sep='', flush=True)
        time.sleep(10)
    print('\nJob Status ({}): \n{}'.format(job_id, json.dumps(response, indent=2)))

    # # API endpoint test: GET /job
    # response = get_job_status(307)
    # print('get_job_status: \n{}'.format(json.dumps(response, indent=2)))
