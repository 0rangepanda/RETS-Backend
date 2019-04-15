import os
import psycopg2

from flask import render_template, Blueprint
from flask import request, redirect, url_for, send_from_directory
from flask_login import login_required
from flask import current_app as app

from project import db, psydb
from project import crmhandler
from project.facebookads import bp

import simplejson, traceback
from werkzeug import secure_filename

from lib.facebookads.crmlsziphandler import CrmlsZipHandler
from lib.facebookads.upload_file import uploadfile


#------------------------------ FROM LOCAL DB  ----------------------------------------------------#
@bp.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():
    fbadsxml_path = app.config["DATADIR"]+'/fbadsxml'
    if request.method == 'POST':
        return None
    if request.method == 'GET':
        # get all file in directory
        files = [f for f in os.listdir(fbadsxml_path) if
                 os.path.isfile(os.path.join(fbadsxml_path, f)) ]

        file_display = []

        for f in files:
            size = os.path.getsize(os.path.join(fbadsxml_path, f))
            file_saved = uploadfile(name=f, pdir=fbadsxml_path, size=size)
            file_display.append(file_saved.get_file())

        file_display.sort(key=lambda k: -k['t'])

        return simplejson.dumps({"files": file_display})
    return redirect(url_for('download'))


@bp.route("/delete/<string:filename>", methods=['DELETE'])
@login_required
def delete(filename):
    """
    Delete file
    :param filename:
    :return:
    """
    fbadsxml_path = app.config["DATADIR"]+'/fbadsxml'
    file_path = os.path.join(fbadsxml_path, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return simplejson.dumps({filename: 'True'})
        except:
            return simplejson.dumps({filename: 'False'})


@bp.route("/data/<string:filename>", methods=['GET'])
@login_required
def get_file(filename):
    fbadsxml_path = app.config["DATADIR"]+'/fbadsxml'
    return send_from_directory(os.path.join(fbadsxml_path), filename=filename)

    
@bp.route('/download', methods=['GET', 'POST'])
@login_required
def download():
    #files = [f for f in os.listdir(app.config["DATADIR"]+'/fbadsxml') ]
    return render_template('facebookads/download.html')

#------------------------------ FROM CRMLS  ----------------------------------------------------#
