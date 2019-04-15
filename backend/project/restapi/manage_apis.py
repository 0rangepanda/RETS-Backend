import json
import uuid
import logging, sys, traceback
import datetime
from datetime import datetime as dt

from flask import render_template, Blueprint, after_this_request
from flask import request
from flask import copy_current_request_context
from flask_login import login_required
from flask_restful import Resource
from flask_restful import fields, marshal_with, reqparse
from flask import current_app as app

from project import api, db, scheduler
from project import scheduler_settings
from project import psydb
from project import crmhandler
from project import getproperties
from project.models import Property, User, City, County, Neighbor, UserFbads

from lib.facebookads.localcsvhandler import LocalCsvHandler
from lib.utils.getimgsize import getimgsize


# 
# Update City List manage api
class UpdatecityApi(Resource):
    """
    Update City List manage api, post to change it in db
    """

    def __init__(self):
        pass
    
    def get(self):
        """
        For test
        """
        return {"res": ""}
    
    
    def post(self):
        """
        Post the Update City List and make change in database
        """
        json_data = request.get_json()
        cityset = set()
        for data in json_data:
            cityset.add(data["name"])
        
        allcity = City.query.all()
        for city in allcity:
            if city.value in cityset:
                city.in_update=True
            else:
                city.in_update=False
        db.session.commit()
        return {"res": json_data}, 201 


# 
# Cache manage api
cache_get_parser = reqparse.RequestParser()
cache_get_parser.add_argument("scheduler_settings", type=list)

class ManageCacheApi(Resource):
    """
    Cache manage, get method to get, post method to change
    """

    def __init__(self):
        pass
    
    def get(self):
        """
        For test
        """
        res = {}
        res["scheduler_settings"] = scheduler_settings
        return res
    
    
    def post(self):
        """
        Post the Update City List and make change in database
        """
        #args = cache_get_parser.parse_args()
        json_data = request.get_json()
        if "scheduler_settings" in json_data:
            scheduler_settings["day"] = json_data["scheduler_settings"]["day"]
            scheduler_settings["time"] = json_data["scheduler_settings"]["time"]
        # TODO:
        # reschdule
        # scheduler.modify_job("daily_job", trigger='interval', start_date=start_date)
        return {}, 201


# 
# Scheduler manage api
class SchedulerApi(Resource):
    """
    Scheduler manage
    get method: to get infos, 
    post method: 
    """

    def __init__(self):
        pass
    
    @login_required
    def get(self):
        """
        Get scheduler infos, 
        STATE_STOPPED = 0: constant indicating a scheduler’s stopped state
        STATE_RUNNING = 1: constant indicating a scheduler’s running state (started and processing jobs)
        STATE_PAUSED = 2: constant indicating a scheduler’s paused state (started but not processing jobs)
        """
        res = {}
        res["STATE"] = scheduler.state
        return res

    
    @login_required
    def post(self):
        """
        """   
        json_data = request.get_json()
        action = json_data.get("action", "")
        if action=="do_update":
            # Schedule a one time update job
            try:
                start_date = dt.now()+datetime.timedelta(seconds=5)
                uid = uuid.uuid1() #need a unique id 
                scheduler.add_job(func=getproperties, trigger='date', 
                    run_date=start_date, args=[app.logger, db], id="onetime_job_"+str(uid))
                app.logger.info("Schedule the update job now!" + str(start_date))
            except NameError:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                app.logger.debug(''.join('!! ' + line for line in lines))
            
        elif action=="start":
            # Start the configured executors and job stores and begin processing scheduled jobs.
            scheduler.start()
        elif action=="shutdown":
            # Shuts down the scheduler, along with its executors and job stores.
            # Does not interrupt any currently running jobs.
            scheduler.shutdown()
        elif action=="pause":
            # Pause job processing in the scheduler.
            # This will prevent the scheduler from waking up to do job processing until resume() is called. 
            # It will not however stop any already running job processing.
            scheduler.pause()
        elif action=="resume":
            # Resume job processing in the scheduler.
            scheduler.resume()
        else:
            pass
        return {}, 201


# UserFbadsApi manage api
class UserFbadsApi(Resource):
    """
    UserFbadsApi manage
    """
    def __init__(self):
        pass
    
    @login_required
    def get(self):
        """
        """
        obj_id = request.args.get("id", "")
        if not obj_id:
            return {"msg":"No id!"}
        obj = UserFbads.query.filter_by(id=obj_id).first()
        res = {}
        res["id"] = obj.id
        res["url"] = obj.url if obj.url else ""
        res["pixel"] = obj.fb_pixel if obj.fb_pixel else ""
        return res

    @login_required
    def put(self):
        """
        """  
        json_data = request.get_json()
        url = json_data.get("url", "")
        pixel = json_data.get("pixel", "")
        userfb = UserFbads(url=url, fb_pixel=pixel)
        # userfb.user = user.id
        db.session.add(userfb)
        db.session.commit()
        return {"success": "true"}, 201

    
    @login_required
    def post(self):
        """
        """   
        json_data = request.get_json()
        obj_id = json_data.get("id", "")
        url = json_data.get("url", "")
        pixel = json_data.get("pixel", "")
        obj = UserFbads.query.filter_by(id=obj_id).first()
        obj.url = url
        obj.fb_pixel = pixel
        db.session.commit()
        return {"success": "true"}, 201

    
    @login_required
    def delete(self):
        """
        """   
        json_data = request.get_json()
        obj_id = json_data.get("id", "")
        obj = UserFbads.query.filter_by(id=obj_id).first()
        db.session.delete(obj)
        db.session.commit()
        return {}, 201
