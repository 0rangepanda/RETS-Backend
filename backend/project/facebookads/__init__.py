from flask import Blueprint

bp = Blueprint('facebookads', __name__)

from project.facebookads import views
