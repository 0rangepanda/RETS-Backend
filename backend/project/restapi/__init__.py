from flask import Blueprint

bp = Blueprint('restapi', __name__)

from project.restapi import views
