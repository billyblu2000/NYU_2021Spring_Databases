from datetime import timedelta

# PROJECT
HOST = '127.0.0.1'
PORT = 5000
DEBUG = True
SECRET_KEY = 'secret_key'


# APP
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

# DATABASE
DB_HOST = '192.168.64.2'
DB_USER = 'root'
DB_PASS = '1234'
DB_NAME = 'project'
