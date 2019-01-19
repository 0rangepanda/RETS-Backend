import os
import sqlite3

from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from flask_restful import Api
from flask_cors import CORS

# my lib
from lib.psyhandler.psyhandler import PsyHandler
#from lib.mlshandler.crmls import CrmlsHandler

"""
# config
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('flask.cfg')
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
babel = Babel(app)
api = Api(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

# use hostname when using pgsql by docker and the two container are in the same docker network
# in production env
if app.config['ENV'] == "development":
    psydb = PsyHandler()
    psydb.init_app(app=app, hostname="postgres")
    # psydb = PsyHandler(app, hostname="postgres") 
elif app.config['ENV'] == "production":
    psydb = PsyHandler(app) 

# Crmls Handler
# NOTE: CrmlsHandler uses the db schema, so must import after db create
from lib.mlshandler.crmls import CrmlsHandler
config_path = app.config["TOP_LEVEL_DIR"]+"/configs/crmls.ini"
logfile_path = app.config["TOP_LEVEL_DIR"]+"./log"
crmhandler = CrmlsHandler(config_path=config_path, logfile_path=logfile_path, db=db)

# blueprints
from project.manage import bp as manage_bp
app.register_blueprint(manage_bp, url_prefix='/manage')

import project.restapi.views
#from project.restapi import bp as restapi_bp
#app.register_blueprint(restapi_bp, url_prefix='/api')

from project.auth import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

"""

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()
api = Api()
cors = CORS()
psydb = PsyHandler()
from lib.mlshandler.crmls import CrmlsHandler
crmhandler = CrmlsHandler()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('flask.cfg')

    db.init_app(app)
    #migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    api.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    if app.config['ENV'] == "development":
        psydb.init_app(app=app, hostname="postgres")
    elif app.config['ENV'] == "production":
        psydb.init_app(app=app)
    config_path = app.config["TOP_LEVEL_DIR"]+"/configs/crmls.ini"
    logfile_path = app.config["TOP_LEVEL_DIR"]+"./log"
    crmhandler.init_app(config_path=config_path, logfile_path=logfile_path, db=db)

    # ... no changes to blueprint registration
    # blueprints
    from project.manage import bp as manage_bp
    from project.auth import bp as auth_bp
    app.register_blueprint(manage_bp, url_prefix='/manage')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    #import project.restapi.views
    #from project.restapi import *
    #from project.restapi import bp as restapi_bp
    #app.register_blueprint(restapi_bp, url_prefix='/api')

    #if not app.debug and not app.testing:
        # ... no changes to logging setup
    #    pass
    return app

# Things must do AFTER create_app() called
import project.restapi


