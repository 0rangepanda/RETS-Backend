import psycopg2

from flask import render_template, Blueprint
from flask import request
from flask_login import login_required

from project import app, db, psydb
from project import crmhandler
from project.manage import bp


@bp.route('/')
@bp.route('/index')
def index():
    return render_template('manage/index.html')


@bp.route('/rawquery', methods=['GET'])
@login_required
def rawquery():
    """
    Query by raw sql, no need to login to db server :)
    :return:
    """
    if request.args.get("sql"):
        res = psydb.rawquery(request.args.get("sql"))
        return render_template('manage/rawquery.html', res=res)
    else:
        return render_template('manage/rawquery.html')


@bp.route('/search', methods=['GET'])
@login_required
def search():
    """
    Query by params form properties
    :return:
    """
    def __paging_url(getargs):
        """
        Keep query url without paging params
        """
        banlist = ["p", "page_size"]
        paging_url = []
        for key, val in getargs.items():
            if key not in banlist:
                paging_url.append(key+"="+val)
        return "&".join(paging_url)

    status_list = crmhandler.getstatus() # dict of status k-v
    # list of sortable fields
    orderby_list = {
        "list_price": "List Price", 
        "yearbuilt": "Year Built", 
        "squarefeet": "Square Feet",
        "pricepersquare": "Price per Square",
    } 
    # list of select fields
    select_list = ["id", "status", "list_price", "city", "streetname", "postalcode", "beds", "baths", 
                   "yearbuilt", "squarefeet", "pricepersquare"]                     
    
    # all args needed by searching page except for searching result
    args = {
        "status" : status_list,
        "orderby" : orderby_list,
        "getargs" : request.args,
    } 
    if any(request.args[item] for item in request.args):
        #res = psydb.query(request.args, "properties")
        page_num = int(request.args.get('p', '1'))
        if not page_num:
            page_num = 1
        page_size = int(request.args.get('page_size', '20'))
        if not page_size:
            page_size = 20
    
        res = psydb.query_plus(select_list, "properties", request.args, request.args["orderby"], page_size, page_num)
        paging = {
            "url": __paging_url(request.args),
            "total": int(res["count"]), 
            "page_size": int(page_size), 
            "curr_page": int(page_num)
        }
        return render_template('manage/search.html', args=args, res=res, paging=paging)
    else:
        return render_template('manage/search.html', args=args)


@bp.route('/property/<int:id>')
def propertyinfo(id):
    """
    View of single property
    """
    res = psydb.query({"id": id}, "properties")
    image = crmhandler.get_image(res["results"][0][3])
    return render_template('manage/property.html', res=res, image=image)


@bp.route('/dbinfo', methods=['GET'])
@login_required
def databaseInfo():
    """
    Show db information
    :return:
    """
    return render_template('manage/search.html')


@bp.route('/cityshortname', methods=['GET'])
@login_required
def cityshortname():
    """
    Lookup city full name by shortname (CRMLS for now)
    :return:
    """
    pass
    """
    if any(request.args[item] for item in request.args):
        res = psydb.query(request.args, "properties")
        return render_template('manage/city.html', res=res)
    else:
        return render_template('manage/city.html')
    """


@bp.route('/imageurl', methods=['GET'])
@login_required
def getimageurl():
    """
    Query image url by ListingId
    :return:
    """
    if request.args.get("sql"):
        res = psydb.rawquery(request.args.get("sql"))
        return render_template('manage/rawquery.html', res=res)
    else:
        return render_template('manage/rawquery.html')
