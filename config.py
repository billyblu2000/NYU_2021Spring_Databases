import os
from datetime import timedelta

# PROJECT
HOST = '127.0.0.1'
PORT = 5000
DEBUG = False
SECRET_KEY = 'secret_key'

# APP
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
ROOT_DIR = os.path.abspath(__file__)[:-9]
ADMIN = ['billy', 'Billy', 'Ian', 'ian']

# DATABASE
DB_REMOTE = True
if DB_REMOTE:
    DB_CONFIG = {
        'host': '49.232.139.17',
        'user': 'user',
        'password': None,
        'db': 'project'}
else:
    DB_CONFIG = {
        'host': '192.168.64.2',
        'user': 'root',
        'password': '1234',
        'db': 'project'}
