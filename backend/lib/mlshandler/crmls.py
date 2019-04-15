import os
import librets
import configparser
import sqlite3
import concurrent.futures
import time
import logging
import uuid

from multiprocessing  import Queue
from datetime import datetime
from copy import deepcopy

from project.models import Property
from lib.utils.configcase import myconf
from lib.utils.getimgsize import getimgsize


class CrmlsHandler(object):
    """
    This handler is capable to query all field
    If want to change db schema, just need to modify model.py and the config file
    Every column in model.py must be in config file [SelectField]
    and every column name should have correct name mapping with CRMLS column name
    """
    """
    def __new__(cls, config_path, logfile_path, database):
        #Should check all field in our db also in config file [SelectField]
        #If not, should not do anything with this obj
        return super(CrmlsHandler, cls).__new__(cls)
    """

    def __init__(self, config_path=None, logfile_path=None, db=None, app=None):
        """
        self.config = configparser.ConfigParser(
                interpolation=configparser.BasicInterpolation())
        """
        if config_path and logfile_path and db:
            self.init_app(config_path=config_path, logfile_path=logfile_path, db=db, app=app)
    
    def init_app(self, config_path=None, logfile_path=None, db=None, app=None):
        """
        app is for app.app_context()
        """
        if config_path and logfile_path and db:
            self.config = myconf()
            self.config.read(config_path, encoding=None)
            self.LOGIN_URL = self.config['Authentication']['LOGIN_URL']
            self.USR_NAME  = self.config['Authentication']['USR_NAME']
            self.USR_PSWD  = self.config['Authentication']['USR_PSWD']
            self.SelectField = self.config['SelectField']
            self.ExtraField  = self.config['ExtraField']
            self.NotNullableField = self.config['NotNullableField']
            self.logfile_path = logfile_path
            self.database = db
            self.mlsname = "CRMLS"
            self.app = app 
            self.status = {}
            for k, v in self.config['Status'].items():
                self.status[k] = v
            # create a new log file each time
            self.writeQueue = Queue()
            return True
        else:
            return False

    # helper functions
    def __validate_SelectField(self, SelectField, database):
        """
        Should check all field in our db also in config file [SelectField]
        If not, should not do anything with this obj
        :param SelectField:
        :param database:
        :return:
        """
        print(",".join(self.SelectField))
        return None

    def __login(self):
        """
        Login function, return the session obj
        :return: session
        """
        session=librets.RetsSession(self.LOGIN_URL)
        if not session.Login(self.USR_NAME, self.USR_PSWD):
            self.writeQueue.put("Error login in! The credential may be invalid.")
            return None
        return session

    def __logout(self, session):
        """
        Logout function, logout the input session
        :param session:
        :return: boolean
        """
        logout=session.Logout()
        self.writeQueue.put("Logout message: " + logout.GetLogoutMessage())
        self.writeQueue.put("Connect time: " + str(logout.GetConnectTime()))
        return True


    def __query(self, session, querystr, SelectField, limit=None):
        """
        Wrapper of query from crmls
        :param session: A librets session
        :param querystr: 
        :param SelectField: a string separate by ','
        :param limit: Result count limit
        :return: query results (usage: while results.HasNext() ...)
        """
        request=session.CreateSearchRequest(
            "Property",
            "Residential",
            querystr
        )
        request.SetStandardNames(True)
        request.SetOffset(librets.SearchRequest.OFFSET_NONE)
        request.SetSelect(SelectField)
        request.SetCountType(librets.SearchRequest.RECORD_COUNT_AND_RESULTS)
        if limit:
            request.SetLimit(limit)
        # perform search and save results to db
        results=session.Search(request)
        return results


    def __streetname(self, results):
        """
        In CRMLS streetname = StreetName + StreetDirPrefix + StreetSuffixModifier + StreetSuffix + StreetDirSuffix +
        StreetNumber
        :param results: ONE searching result from CRMLS (return of self.__query)
        :return: streetname (str)
        """
        streetname = []
        field = ["StreetNumberNumeric","StreetDirPrefix","StreetDirSuffix",
                 "StreetName","StreetSuffixModifier","StreetSuffix","StreetNumber",]
        for key in field:
            streetname.append(results.GetString(key))
        streetname = " ".join(streetname)
        # remove extra and leading&tailing space 
        return " ".join(streetname.split())

    def __misc(self, results):
        """
        Convert everything in self.Extrafield into a Json string
        """
        res = {}
        for key in self.ExtraField:
            res[key] = results.GetString(self.ExtraField[key])
        return str(res)

    ##
    # public functions
    def login(self):
        return self.__login()

    def query(self, querystr, limit=1, session=None):
        """
        A wrapper of self.__query()
        """
        if session==None:
            fsession = self.__login()
        else:
            fsession = session
        select = ",".join(self.SelectField.values()) + "," + ",".join(self.ExtraField.values())
        results = self.__query(fsession, querystr, select, limit=limit)
        res = []
        while results.HasNext():
            kwargs={} 
            for key in self.SelectField:
                kwargs[key]=results.GetString(self.SelectField[key])
                if not kwargs[key]:
                    kwargs[key] = ""
            for key in self.ExtraField:
                kwargs[key]=results.GetString(self.ExtraField[key])
                if not kwargs[key]:
                    kwargs[key] = ""
            res.append(kwargs)
        if session==None:
            self.__logout(fsession)
        return res
    

    def query_with_select(self, querystr, select_field, limit=1, session=None):
        """
        A wrapper of self.__query() with implicit fields
        """
        if session==None:
            fsession = self.__login()
        else:
            fsession = session
        select = ",".join(select_field)
        results = self.__query(fsession, querystr, select, limit=limit)
        res = []
        while results.HasNext():
            kwargs={} 
            for key in select_field:
                kwargs[key]=results.GetString(key)
            res.append(kwargs)
        if session==None:
            self.__logout(fsession)
        return res


    def getstatus(self, status=None):
        """
        Get the dict of all status (something like A : Active)
        :return: a dict
        """
        if status:
            return self.status.get(status, None)
        else:
            return self.status

    def create_table(self, limit=1000):
        """
        Pull data from MLS for the first time
        When testing, set a limit to save disk space
        :param limit:
        :return:
        """
        session = self.__login()
        #results = self.__query(session, "*", self.SelectField, limit=limit)
        s = ",".join(self.SelectField.values()) + "," + ",".join(self.ExtraField.values())
        results = self.__query(session, "*", s, limit=limit)

        while results.HasNext():
            self.writeQueue.put(self.__streetname(results))
            kwargs={}
            kwargs["mlsname"] = self.mlsname
            for key in self.SelectField:
                kwargs[key] = results.GetString(self.SelectField[key])
                if not kwargs[key]:
                    kwargs[key] = None
            prty=Property(**kwargs)
            self.database.session.add(prty)

        self.database.session.commit()
        self.__logout(session)
        return True


    def update_one(self, col_name, value, create=False):
        """
        Perform updating from MLS
            update only one column value a time
            query -> compare -> update
            [city] is a good choice
            [listing_id] can be used to update single property
        :param col_name: a column name in local db
        :param value: a value of this column
        :param create: true if first time (do not need to query)
        :return: number of updated records
        """
        # query from database and read into memory
        # TODO: use string of column name
        # NOTE: each value in data_in_db is a <class: 'Property'> object
        query_properties = Property.query.filter_by(city=value).all() # NOTE: hardcode city here
        data_in_db = {}
        for p in query_properties:
            data_in_db[p.listingkey_numeric] = p

        # query from mls
        querystr = "(%s=%s)" % (col_name, value, ) # commonly col_name=city
        #logging.info("Update colum: "+querystr)
        self.writeQueue.put("Update colum: "+querystr)
        session = self.__login()
        select = ",".join(self.SelectField.values()) + "," + ",".join(self.ExtraField.values())
        results = self.__query(session, querystr, select)

        # for each record, check hash then decide if need to update
        create_count, update_count, abandon_count = 0, 0, 0
        while results.HasNext():
            abandon = False
            kwargs={}
            for key in self.SelectField:
                kwargs[key]=results.GetString(self.SelectField[key])
                # Avoid empty string here
                if not kwargs[key]:
                    if key in self.NotNullableField:
                        abandon = True # abandon this record
                    else:
                        kwargs[key] = None
            if abandon:
                abandon_count += 1
                continue
            # NOTE: HERE do extra thing to each record (like streetname!)
            kwargs["mlsname"] = self.mlsname
            kwargs["streetname"] = self.__streetname(results)
            kwargs["misc"] = self.__misc(results)
    
            # compare and update
            # skip this step for frist time
            property_in_db = data_in_db.get(kwargs['listingkey_numeric'], None) if create==False else None
            if not property_in_db:
                # new record -> create
                prty = Property(**kwargs)
                self.database.session.add(prty)
                create_count += 1
            else:
                # existing record 
                # NOTE: can get diff list now
                update_list = property_in_db.diff(kwargs)
                if update_list:
                    # diff record -> update
                    property_in_db.from_dict(kwargs)
                    update_count += 1
                    self.writeQueue.put("Update info for property "+ kwargs['listing_id']+ ": "+ str(update_list)) 
        self.database.session.commit()
        self.__logout(session)
        return create_count, update_count, abandon_count

    def update_one_with_context(self, col_name, val, create=False):
        """
        If running outside views, need app_context() 
        """
        if self.app:
            with self.app.app_context():
                return self.update_one(col_name, val, create=create)
        else:
            return self.update_one(col_name, val, create=create)

    def update_all(self, col_name, value_list, create=False):
        """
        Driver function of update_one
        Open a in-memory db for each updating
        :param col_name:
        :param value_list:
        :return: if success
        """
        # we want one log for each updating
        total_create, total_update, total_abandon = 0, 0, 0
        for value in value_list:
            create_count, update_count, abandon_count = self.update_one_with_context(col_name, value, create=create)
            total_create += create_count
            total_update += update_count
            total_abandon += abandon_count
            self.writeQueue.put("[%s] create: %s,  update: %s, abandon: %s"
                  % (value, create_count, update_count, abandon_count, ))
        self.writeQueue.put("Total create: %s,  update: %s, abandon: %s" 
            % (total_create, total_update, total_abandon, ))
        return True

    def update_all_mt(self, col_name, value_list, threads=1, create=False):
        """
        Multithread Driver function of update_one
        If running outside views, need app_context() for each thread
        :param col_name:
        :param value_list:
        :return: if success
        """
        # clear queue
        self.writeQueue = Queue()
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            future_updateone = {executor.submit(self.update_one_with_context, col_name, val): val for val in value_list}
            for future in concurrent.futures.as_completed(future_updateone):
                val = future_updateone[future]
                create_count, update_count, abandon_count = future.result()
                self.writeQueue.put("[%s] create: %s,  update: %s, abandon: %s" 
                      % (val, create_count, update_count, abandon_count, ))
        # create new log file and write to log file
        outFile = open(os.path.join(self.logfile_path, "crm_update.log."+str(uuid.uuid1()) ),'w+')
        dt = datetime.now()
        outFile.write(dt.strftime( '%Y-%m-%d %H:%M:%S' ) + "\n")
        while self.writeQueue.qsize():
            outFile.write(self.writeQueue.get() + "\n")
        outFile.flush()
        outFile.close()
        return True

    ##
    # Image related
    def get_image(self, listingkey_numeric):
        """
        Given a ListingId, get all image URLS of the property from crmls
        :param ListingId:
        :return: image counts and all urls list
        """
        image_urls, media_types = [], []
        image_count = 0
        # query from mls
        session = self.__login()
        pk = listingkey_numeric
        photo_request = session.CreateSearchRequest(
            "Media", "Media", "(ResourceRecordKeyNumeric=" + pk + ")"
        )
        photo_results = session.Search(photo_request)
        image_count = photo_results.GetCount()
        #photo_columns = photo_results.GetColumns()
        #print("images count: " + str(photo_results.GetCount()))
        while photo_results.HasNext():
            url = photo_results.GetString("MediaURL")
            mediatype = photo_results.GetString("MediaType")
            image_urls.append(url)
            media_types.append(mediatype)
        self.__logout(session)
        return {"image_count": image_count,
                "image_urls": image_urls,
                "media_types": media_types}

    
    # Update one property image AFTER self.get_image() is called
    def update_image(self, listingkey_numeric, image):
        """
        Update one property image AFTER self.get_image() is called
        :param listingkey_numeric: 
        :param image_urls: a list of image urls
        """
        image_urls = image["image_urls"]
        media_types = image["media_types"]
        p = Property.query.filter_by(listingkey_numeric=listingkey_numeric).first()
        if not p or len(media_types)==0 or len(image_urls)==0:
            return False
        img, cover = [], ""
        for url, t in zip(image_urls, media_types) :
            img.append({"url":url, "type":t})
            if t=='IMAGE' and cover=="":
                cover = str(url)
            """
            # get size of each img, turn this off to make it faster
            if t=='IMAGE':
                imgsize = getimgsize(url)
                img.append({"url":url, "type":t, "width":imgsize[0], "height":imgsize[1]})
            """ 
        p.coverimage = cover
        p.image = str(img)
        self.database.session.commit()
        return True

    # Too slow, try not to use these two
    def __update_image(self, query_properties_list):
        """
        Update the image field for a list of Property obj
        :param query_properties_list: a list of Property obj
        """
        session = self.__login()
        for p in query_properties_list:
            image_urls = []
            image_count = 0
            photo_request = session.CreateSearchRequest(
                "Media", "Media", "(ResourceRecordKeyNumeric=" + p.listingkey_numeric + ")"
            )
            photo_results = session.Search(photo_request)
            image_count = photo_results.GetCount()
            while photo_results.HasNext():
                url = photo_results.GetString("MediaURL")
                image_urls.append(url)
            if image_count>0:
                p.coverimage = str(image_urls[0])
        self.__logout(session)
        return None

    
    def update_allimage(self, col_name, value_list):
        """
        After init data, update the image field for all properties
        """
        if col_name=="city":
            for value in value_list:
                query_properties = Property.query.filter_by(city=value).all()
                self.__update_image(query_properties)
        self.database.session.commit()
        return None


##
