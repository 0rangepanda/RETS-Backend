from flask import Blueprint

bp = Blueprint('manage', __name__)

from project.manage import views
