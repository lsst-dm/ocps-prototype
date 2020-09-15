from globals import STATUS_OK, STATUS_ERROR
import envvars
import argparse
import requests
import json
import yaml
import sqlite3
import random
import time
import asyncio

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


def get_job_status(job_id):
    r = requests.get(
        '{}/job'.format(config['apiBaseUrl']),
        params={
            'id': job_id
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


if __name__ == '__main__':
    # Define and parse input arguments 
    parser = argparse.ArgumentParser(description='Manage HTCondor jobs.')
    parser.add_argument(
        '--config',
        dest='config',
        type=argparse.FileType('r'),
        nargs='?',
        help='Job config file',
        required=True
    )
    parser.add_argument(
        '--duration',
        dest='duration',
        type=int,
        nargs='?',
        help='Duration in seconds',
        required=False
    )
    args = parser.parse_args()

    # Load the client config that defines the location of the Butler repo containing the data
    configPath = args.config.name
    with open(configPath, 'r') as f:
        conf = yaml.load(f, Loader=yaml.SafeLoader)

    # Request four independent jobs in rapid succession to demonstrate parallelism
    for i in range(1,2):
        # Select random image from Butler repo
        data = query_butler_repo_for_filter(conf)
        random_image = random.choice(data)
        print('Random image from selected data: {}'.format(json.dumps(random_image)))
        # Alert production job type specified
        response = post_job_ap(conf, random_image)
        cluster_id = response['cluster_id']
        job_id = response['job_id']
        print('POST /api/v1/job : {}'.format(json.dumps(response)))
