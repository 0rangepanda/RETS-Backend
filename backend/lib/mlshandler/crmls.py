import librets
import configparser
import sqlite3
from copy import deepcopy

from project.models import Property
from lib.utils.configcase import myconf


class CrmlsHandler(object):
    """
    This handler is capable to query all field
    If want to change db schema, just need to modify model.py and the config file
    Every column in model.py must be in config file [SelectField]
    and every column name should have correct name mapping with CRMLS column name
    """

    def __new__(cls, config_path, logfile_path, database):
        """
        Should check all field in our db also in config file [SelectField]
        If not, should not do anything with this obj
        """
        return super(CrmlsHandler, cls).__new__(cls)

    def __init__(self, config_path, logfile_path, database):
        """
        self.config = configparser.ConfigParser(
                interpolation=configparser.BasicInterpolation())
        """
        self.config = myconf()
        self.config.read(config_path, encoding=None)

        self.LOGIN_URL = self.config['Authentication']['LOGIN_URL']
        self.USR_NAME = self.config['Authentication']['USR_NAME']
        self.USR_PSWD = self.config['Authentication']['USR_PSWD']
        self.SelectField = self.config['SelectField']
        self.ExtraField = self.config['ExtraField']

        self.status = {}
        for k, v in self.config['Status'].items():
            self.status[k] = v

        self.logfile_path=logfile_path
        self.database=database
        self.mlsname = "CRMLS"

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
            print("Error logging in! The credential may be invalid.")
            return None
        return session

    def __logout(self, session):
        """
        Logout function, logout the input session
        :param session:
        :return: boolean
        """
        logout=session.Logout()
        print("Logout message: " + logout.GetLogoutMessage())
        print("Connect time: " + str(logout.GetConnectTime()))
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
        return " ".join(streetname)


    # public functions
    def getstatus(self):
        """
        Get the dict of all status (something like A : Active)
        :return: a dict
        """
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
            print(self.__streetname(results))
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


    def update_one(self, col_name, value):
        """
        Perform updating from MLS
            update only one column value a time
            query -> compare -> update
            [city] is a good choice

        :param col_name: a column name in local db
        :param value: a value of this column
        :return: number of updated records
        """
        # query from database and read into memory
        # TODO: use string of column name
        # NOTE: each value in data_in_db is a <class: 'Property'> object
        query_properties = Property.query.filter_by(city=value).all()
        data_in_db = {}
        for p in query_properties:
            data_in_db[p.listingkey_numeric] = p

        # query from mls
        querystr = "(%s=%s)" % (col_name, value, )
        print(querystr)
        session = self.__login()
        select = ",".join(self.SelectField.values()) + "," + ",".join(self.ExtraField.values())
        results = self.__query(session, querystr, select)

        # for each record, check hash then decide if need to update
        create_count, update_count = 0, 0
        while results.HasNext():
            kwargs={}
            # NOTE: HERE do extra thing to each record (like streetname!)
            kwargs["mlsname"] = self.mlsname
            for key in self.SelectField:
                kwargs[key]=results.GetString(self.SelectField[key])
                if not kwargs[key]:
                    kwargs[key] = None
            # TODO: avoid empty column, but is there better solution?

            # compare
            property_in_db = data_in_db.get(kwargs['listingkey_numeric'], None)
            if not property_in_db:
                # new record -> create
                prty = Property(**kwargs)
                self.database.session.add(prty)
                create_count += 1
            else:
                # existing record 
                # NOTE: can get diff list now
                # TODO: update and logging
                update_list = property_in_db.diff(kwargs)
                if update_list:
                    # diff record -> update
                    property_in_db.from_dict(kwargs)
                    update_count += 1
                    print(update_list) # this line goes to logging

        self.database.session.commit()
        self.__logout(session)
        return create_count, update_count


    def update_all(self, col_name, value_list):
        """
        Driver function of update_one
        Open a in-memory db for each updating
        :param col_name:
        :param value_list:
        :return:
        """
        # we want one log for each updating
        total_create, total_update = 0, 0
        for value in value_list:
            create_count, update_count = self.update_one(col_name, value)
            total_create += create_count
            total_update += update_count
            print("[%s] create: %s,  update: %s"
                  % (value, create_count, update_count,))
        print("Total create: %s,  update: %s" % (total_create, total_update,))
        return True


    def get_image(self, ListingId):
        """
        Given a ListingId, get all image URLS of the property from crmls
        :param ListingId:
        :return: image counts and all urls list
        """
        image_urls = []
        image_count = 0
        # query from mls
        querystr = "(ListingId=%s)" % (ListingId,)
        session = self.__login()
        results = self.__query(session, querystr, "ListingKeyNumeric")

        # fetching image (for crmls)
        while results.HasNext():
            pk = results.GetString("ListingKeyNumeric")
            photo_request = session.CreateSearchRequest(
                "Media", "Media", "(ResourceRecordKeyNumeric=" + pk + ")"
            )
            photo_results = session.Search(photo_request)
            image_count = photo_results.GetCount()
            #photo_columns = photo_results.GetColumns()
            #print("images count: " + str(photo_results.GetCount()))
            while photo_results.HasNext():
                print("MediaURL: ", photo_results.GetString("MediaURL"))
                image_urls.append(photo_results.GetString("MediaURL"))

        self.__logout(session)
        return {"image_count": image_count,
                "image_urls": image_urls}




##
