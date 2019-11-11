from flask import Flask
from flask_cors import CORS
#from peewee import *
#from peewee_migrate import Router

from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    #db.close()

    return app
