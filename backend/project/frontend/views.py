import psycopg2

from flask import redirect, url_for, flash
from flask import render_template, Blueprint
from flask import request
from flask_login import login_required

from project import db, psydb, scheduler_settings
from project import crmhandler
from project import scheduler
from project.frontend import bp
from project.models import Property, User, City, County, Neighbor, UserFbads


@bp.route('/search/')
def search():
    """
    Property searching page
    """
    return render_template('frontend/search.html')


@bp.route('/property')
def singleproperty():
    """
    Single property page
    """
    return render_template('frontend/singlepage.html')


@bp.route('/<url>/search/')
def search_withpixel(url):
    """
    Property searching page with pixel
    """
    # query pixel by urlid
    # if urlid doesnt exist, return error page
    obj = UserFbads.query.filter_by(url=url).first()
    if obj:
        pixel = obj.fb_pixel
        return render_template('frontend/search.html', pixel=pixel)
    else:
        # error page
        return redirect(url_for('frontend.search'))


@bp.route('/<url>/property')
def singleproperty_withpixel(url):
    """
    Single property page with pixel
    """
    obj = UserFbads.query.filter_by(url=url).first()
    if obj:
        pixel = obj.fb_pixel
        return render_template('frontend/singlepage.html', pixel=pixel)
    else:
        # error page
        return redirect(url_for('frontend.search'))