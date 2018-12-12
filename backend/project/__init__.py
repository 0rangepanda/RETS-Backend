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

# my lib
from lib.psyhandler.psyhandler import PsyHandler

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

psydb = PsyHandler(app, hostname="postgres")

# Crmls Handler
# NOTE: CrmlsHandler uses the db schema, so must import after db create
from lib.mlshandler.crmls import CrmlsHandler
config_path = app.config["TOP_LEVEL_DIR"]+"/configs/crmls.ini"
logfile_path = app.config["TOP_LEVEL_DIR"]+"./log"

crmhandler = CrmlsHandler(config_path, logfile_path, db)

# blueprints
from project.manage import bp as manage_bp
app.register_blueprint(manage_bp, url_prefix='/manage')

from project.auth import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

