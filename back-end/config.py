import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    DATABASE = {
        'name': 'postgres',
        'engine': 'peewee.PostgresqlDatabase',
        'user': 'postgres',
        'password': 'postgres',
        'host': 'localhost'
    }
    DEBUG = True
    SECRET_KEY = 'ssshhhh'