import json

from flask import render_template, Blueprint, after_this_request
from flask import request
from flask_login import login_required
from flask_restful import Resource
from flask_restful import fields, marshal_with, reqparse
from flask import current_app as app

from project import api, db
from project import scheduler_settings
from project import psydb
from project import crmhandler
from project.models import Property, User, City, County, Neighbor

from lib.facebookads.localcsvhandler import LocalCsvHandler
from lib.utils.getimgsize import getimgsize


# 
# Single property api
class SinglePropertyApi(Resource):
    """
    Query a single property info according to mlsname and listing id
    """
    def get(self, mlsname, listingid):
        r = psydb.query({"mlsname": mlsname, "listingid": listingid}, "properties")
        res = {}
        if r['results'] and len(r['results']) > 0:
            res["success"] = "true"
            property_info = {}
            for k, v in zip(list(r['colnames']), list(r['results'][0])) :
                property_info[str(k)]= str(v)
            res["property_info"] = property_info
            # misc
            misc = eval(res["property_info"]["misc"]) 
            for k, v in misc.items():
               res["property_info"][k] = v
            # query city shortname to fullname
            res["property_info"]["city"] = psydb.getcityfullname(res["property_info"]["city"])
            res["property_info"]["county"] = psydb.getfullname("COUNTIES", res["property_info"]["county"])
        else:
            res["success"] = "false"
        return res


#
# Query property api
get_parser = reqparse.RequestParser()
query_fields = {}

# anything not in these field will not be parsing
# normal query fields
for k, v in psydb.PROPERTY_SEARCH_LIST.items():
    if v[0]=="int":
        get_parser.add_argument(k, type=int)
        query_fields[k] = fields.Integer
    elif v[0]=="string":
        get_parser.add_argument(k, type=str)
        query_fields[k] = fields.String
    elif v[0]=="float":
        get_parser.add_argument(k, type=float)
        query_fields[k] = fields.Float

# sorting fields
get_parser.add_argument("orderby", type=str)
query_fields["orderby"] = fields.String
get_parser.add_argument("descend", type=str)
query_fields["descend"] = fields.String

# paging fields
get_parser.add_argument("p", type=int)
query_fields["p"] = fields.Integer
get_parser.add_argument("page_size", type=int)
query_fields["page_size"] = fields.Integer

# or fields for nontype text search
get_parser.add_argument("or", type=str)
query_fields["or"] = fields.String

class QueryPropertyApi(Resource):
    # list of select fields in db
    select_list = [
        "id", "status", "list_price", "city", "streetname", "postalcode", 
        "listingkey_numeric", "beds", "baths", "yearbuilt", "squarefeet", 
        "pricepersquare", "listing_id", "misc", "area", "coverimage",
        "reduce_price", "reduce_percent"]

    def __init__(self):
        pass

    # TODO: complex GET params parsing
    # @marshal_with(query_fields)
    def get(self):
        args = get_parser.parse_args()
        page_num = args.get('p', 1)
        if not page_num:
            page_num = 1
        page_size = args.get('page_size', 20)
        if not page_size:
            page_size = 20
    
        res = {}
        res["query_para"] = {}
        for k, v in args.items():
            res["query_para"][k] = v
        res["query_para"]["page_size"] = page_size
        res["query_para"]["p"] = page_num
        # The input should be city full name
        if args["city"]:
            args["city"] = psydb.getcityshortname(args["city"])
        
        query = psydb.query_property(
            self.select_list, args, args.get("orderby"), page_size, page_num)
        res["query"] = query["query"]
        res["count"] = query["count"]
        res["results"] = []
        if query["results"]:
            for p in query["results"]:
                property_info = {}
                for k, v in zip(list(query['colnames']), list(p)) :
                    property_info[str(k)]= str(v)
                property_info["city"] = psydb.getcityfullname(property_info["city"])  
                property_info["status"] = crmhandler.getstatus(status=property_info["status"])
                misc = eval(property_info["misc"]) 
                for k, v in misc.items():
                    property_info[k] = v
                # TODO: should see if coverimage is avaliable
                # append
                res["results"].append(property_info)
        return res


#
# Photo api
# if table 'properties' has 'image' field, do not need this 
class PropertyPhotoApi(Resource):
    def get(self, mlsname, listingkey):
        """
        mlsname: string
        listingkey: string
        """
        res = {}
        res["count"] = 0
        res["imgs"] = []
        res["listingkey"] = listingkey
        if mlsname == "CRMLS":
            # query from db first to see if image is already there
            q = psydb.query({"listingkey": listingkey}, "properties")
            if q["colnames"] and q["results"]:
                # listingkey existing
                image = psydb.get_field("image", q["colnames"],q["results"][0]) 
                if image == "":
                    # if first time, query from crmls, then save to db (callback func)
                    image_obj = crmhandler.get_image(listingkey)
                    res["count"] = image_obj["image_count"]
                    for url, t in zip(image_obj["image_urls"], image_obj["media_types"]) :
                        res["imgs"].append({"url":url, "type":t})
                    @after_this_request
                    def update_image(response):
                        print('After request ...')
                        crmhandler.update_image(listingkey, image_obj)
                        return response
                else:
                    # return
                    imgs = eval(image)
                    res["imgs"] = imgs
                    res["count"] = len(imgs)        
        return res


# 
# Facebookads csv api
class FacebookAdsApi(Resource):
    """
    
    """
    select_list = [
        "id", "status", "list_price", "city", "streetname", "postalcode", 
        "latitude", "longitude", "neighborhood", "image",
        "beds", "baths", "yearbuilt", "listing_id", "misc", "coverimage",]

    def __init__(self):
        with app.app_context():
            self.csvhandler = LocalCsvHandler(app.config["CONFIGDIR"]+'/fbcsv_local.ini')

    def get(self):
        """
        Download a csv
        """
        args = get_parser.parse_args()
        page_num = 1
        page_size = args.get('page_size', 20)
        if not page_size:
            page_size = 1000000 # No limit
        # The input should be city short name
        query = psydb.query_property(
            self.select_list, args, args.get("orderby"), page_size, page_num)
        # handle results
        res = []
        if query["results"]:
            for p in query["results"]:
                property_info = {}
                for k, v in zip(list(query['colnames']), list(p)) :
                    property_info[str(k)]= str(v)
                property_info["city"] = psydb.getcityfullname(property_info["city"])  
                property_info["status"] = crmhandler.getstatus(status=property_info["status"])
                misc = eval(property_info["misc"]) 
                for k, v in misc.items():
                    property_info[k] = v
                res.append(property_info)
        # generate csv and save
        results = self.csvhandler.parse_all(res, hardmode=False)
        return {"res": results}

    def post(self):
        """
        Generate a csv according to post params
        """
        args = get_parser.parse_args()
        page_num = 1
        page_size = args.get('page_size', 20)
        if not page_size:
            page_size = 1000000 # No limit
        # The input should be city short name
        query = psydb.query_property(
            self.select_list, args, args.get("orderby"), page_size, page_num)
        # handle results
        res = []
        if query["results"]:
            for p in query["results"]:
                property_info = {}
                for k, v in zip(list(query['colnames']), list(p)) :
                    property_info[str(k)]= str(v)
                property_info["city"] = psydb.getcityfullname(property_info["city"])  
                #property_info["status"] = crmhandler.getstatus(status=property_info["status"])
                misc = eval(property_info["misc"]) 
                for k, v in misc.items():
                    property_info[k] = v
                res.append(property_info)
        # generate csv and save
        results = self.csvhandler.parse_all(res, hardmode=False)
        self.csvhandler.gen_xml(results, app.config["DATADIR"]+'/fbadsxml')
        return {"res": results}, 201 