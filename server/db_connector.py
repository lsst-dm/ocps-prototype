from globals import STATUS_OK, STATUS_ERROR
import sqlite3
import os
from pathlib import Path
import json

class DbConnector(object):
    def __init__(self, sqliteDbFilePath=None, read_only=True):
        self.db_file = sqliteDbFilePath
        self.read_only = read_only
        self.db_conn = None
        self.db_cursor = None
        self.init()


    def open(self):
        # Acquire a database handle
        if self.read_only:
            self.db_conn = sqlite3.connect('file:{}?mode=ro'.format(self.db_file), uri=True)
        else:
            self.db_conn = sqlite3.connect('file:{}'.format(self.db_file), uri=True)
        # Store a cursor instance for convenience
        self.db_cursor = self.db_conn.cursor()


    def close(self):
        # Commit any remaining changes and close the connection
        self.db_conn.commit()
        self.db_conn.close()

    def init(self):
        if not os.path.isfile(self.db_file):
            Path(self.db_file).touch()
        self.open()
        # Create table
        sql = '''
        CREATE TABLE IF NOT EXISTS `job`(
            `id` INTEGER PRIMARY KEY,
            `type` varchar(50) NOT NULL,
            `uuid` TEXT NOT NULL,
            `cluster_id` INTEGER,
            `status` TEXT NOT NULL,
            `time_submit` datetime DEFAULT 0,
            `time_start` datetime DEFAULT 0,
            `time_complete` datetime DEFAULT 0,
            `spec` MEDIUMTEXT NOT NULL,
            `msg` MEDIUMTEXT NOT NULL
        )
        '''
        self.db_cursor.execute(sql)
        self.close()

    def get_job_info(self, job_id):
        job_info = {
            'type': None,
            'spec': None
        }
        self.open()
        sql = '''
        SELECT `type`,`spec` FROM `job` WHERE `uuid` = ?
        '''
        results = self.db_cursor.execute(sql, (
            job_id,
        ))
        for row in results:
            job_info['type'] = row[0]
            job_info['spec'] = json.loads(row[1])
        self.close()
        return job_info