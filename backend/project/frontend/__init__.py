from flask import Blueprint

bp = Blueprint('frontend', __name__)

from project.frontend import views
