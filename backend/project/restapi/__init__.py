from flask import Blueprint

bp = Blueprint('restapi', __name__)

from project.restapi import views
from project import api

api.add_resource(views.SinglePropertyApi, '/api/property', '/api/property/<string:mlsname>/<string:listingid>')
api.add_resource(views.PropertyPhotoApi, '/api/propertyphoto', '/api/propertyphoto/<string:mlsname>/<string:listingkey>')
api.add_resource(views.QueryPropertyApi, '/api/query')