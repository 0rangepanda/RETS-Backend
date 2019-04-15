import os
import sqlite3
import logging
import datetime
#from datetime import datetime
from logging.handlers import SMTPHandler
from logging.handlers import RotatingFileHandler

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
from flask_apscheduler import APScheduler
from flask.logging import default_handler

# my lib
from lib.psyhandler.psyhandler import PsyHandler
#from lib.mlshandler.crmls import CrmlsHandler

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
migrate = Migrate()
babel = Babel()
api = Api()
cors = CORS()
scheduler = APScheduler()
psydb = PsyHandler()

# after db
from lib.mlshandler.crmls import CrmlsHandler
crmhandler = CrmlsHandler()

# cache
scheduler_settings = {
    "day": "",
    "time": "",
} 

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.app_context().push()
    app.config.from_pyfile('flask.cfg')

    db.init_app(app)
    db.app = app
    migrate.init_app(app, db)
    
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    api.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    scheduler.init_app(app)
    if scheduler.state==0:
        scheduler.start()

    if app.config['ENV'] == "development":
        psydb.init_app(app=app, hostname="postgres")
    elif app.config['ENV'] == "production":
        psydb.init_app(app=app)

    # crmhandler
    crm_config_path = app.config["TOP_LEVEL_DIR"]+"/configs/crmls.ini"
    crmhandler.init_app(config_path=crm_config_path, logfile_path=app.config["LOGDIR"], db=db)

    # loggers
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename=app.config["LOGDIR"]+"/app.log", level=logging.DEBUG, format=LOG_FORMAT)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    root_handler = RotatingFileHandler(filename=os.path.join(app.config["LOGDIR"], "app.log"))
    root_handler.setFormatter(formatter)
    root_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(root_handler)


    # ... no changes to blueprint registration
    # blueprints
    from project.manage import bp as manage_bp
    from project.auth import bp as auth_bp
    from project.frontend import bp as frontend_bp
    from project.facebookads import bp as facebookads_bp


    app.register_blueprint(frontend_bp, url_prefix='/')
    app.register_blueprint(manage_bp, url_prefix='/manage')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(facebookads_bp, url_prefix='/facebookads')

    #import project.restapi.views
    #from project.restapi import *
    #from project.restapi import bp as restapi_bp
    #app.register_blueprint(restapi_bp, url_prefix='/api')

    #if not app.debug and not app.testing:
        # ... no changes to logging setup
    #    pass

    # set cache
    scheduler_settings["day"] = "Saturday" 
    scheduler_settings["time"] = "0:00"

    # one normal intervaled job, one for one-time update
    # TODO: reschdule of this does not finished. Maybe use 'cron'
    scheduler.add_job(func=getproperties, trigger='interval', hours=24*7, 
        start_date=datetime.datetime.now()+datetime.timedelta(hours=10000000), args=[app.logger, db], id="daily_job")
    app.logger.info("job list:" + str(scheduler.get_jobs()) )
    
    #scheduler.modify_job("onetime_job", trigger='interval', start_date=datetime.datetime.now()+datetime.timedelta(seconds=10000))
    #app.logger.info("job list123:" + str(scheduler.get_jobs()) )
    return app


def getproperties(logger, db):
    """
    Scheduled job
    """
    logger.info("Update job started!")
    cityvalue_list = []
    query = psydb.rawquery("SELECT value FROM CITYS WHERE in_update=True")
    allcity = query["results"]
    for city in allcity:
        cityvalue_list.append(city[0])
    col_name = "city"
    crmhandler.update_all_mt(col_name, cityvalue_list, threads=1, create=False)
    return True


# Things must do AFTER create_app() called
import project.restapi


