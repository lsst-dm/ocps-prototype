from globals import STATUS_OK, STATUS_ERROR
import sqlite3
import os

class DbConnector(object):
    def __init__(self, sqliteDbFilePath=None, read_only=True):
        self.db_file = sqliteDbFilePath
        self.read_only = read_only
        self.db_conn = None
        self.db_cursor = None


    def open():
        # Acquire a database handle
        if read_only:
            self.db_conn = sqlite3.connect('file:{}?mode=ro'.format(self.db_file), uri=True)
        else:
            self.db_conn = sqlite3.connect('file:{}'.format(self.db_file), uri=True)
        # Store a cursor instance for convenience
        self.db_cursor = self.db_conn.cursor()


    def close(db):
        # Commit any remaining changes and close the connection
        self.db_conn.commit()
        self.db_conn.close()

