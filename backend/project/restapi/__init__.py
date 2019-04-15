from flask import Blueprint

bp = Blueprint('restapi', __name__)

from project.restapi import manage_apis, property_apis
from project import api

# property apis
api.add_resource(property_apis.SinglePropertyApi, '/api/property', '/api/property/<string:mlsname>/<string:listingid>')
api.add_resource(property_apis.PropertyPhotoApi, '/api/propertyphoto', '/api/propertyphoto/<string:mlsname>/<string:listingkey>')
api.add_resource(property_apis.QueryPropertyApi, '/api/query')
api.add_resource(property_apis.FacebookAdsApi, '/api/facebookads')

# manage apis
api.add_resource(manage_apis.UpdatecityApi, '/api/updatecity')
api.add_resource(manage_apis.ManageCacheApi, '/api/cache')
api.add_resource(manage_apis.SchedulerApi, '/api/scheduler')
api.add_resource(manage_apis.UserFbadsApi, '/api/userfbads')
