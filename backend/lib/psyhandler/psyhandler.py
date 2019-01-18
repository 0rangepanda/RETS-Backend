import psycopg2
import socket
from psycopg2.extensions import adapt
from psycopg2.extensions import AsIs


class PsyHandler(object):
    """
    Connect to postgresql by psycopg2 instead of SQLAlchemy
    Only manage READING
    *WHY using this instead of SQLAlchemy (which is much more easy)
    *Raw SQL could do more optimization I guess...
    """
    # the mapping between GET params and property queries, 
    # only in this list can be parsed by GET
    # TODO: use config file? 
    PROPERTY_SEARCH_LIST = {
        "id" : ("int", "id = %s",),
        "mlsname" : ("string", "mlsname = '%s'",),
        "listingkey" : ("string", "listingkey_numeric = '%s'",),
        "listingid" : ("string", "listing_id = '%s'",),
        "city" : ("string", "city = '%s'",),
        "minlistprice" : ("float", "list_price >= %s",),
        "maxlistprice" : ("float", "list_price <= %s",),
        "bathmin" : ("int", "baths >= %s",),
        "bathmax" : ("int", "baths <= %s",),
        "bedmin" : ("int", "beds >= %s",),
        "bedmax" : ("int", "beds <= %s",),
        "status" : ("string", "status = '%s'",),
        "postalcode" : ("string", "postalcode = '%s'",),
    }

    def __init__(self, app=None, hostname=None):
        """
        app: Flask object
        """
        if app:
            self.init_app(app=app, hostname=hostname)
            
    def init_app(self, app=None, hostname=None):
        if app:
            self.port = app.config.get('POSTGRES_PORT')
            self.database = app.config.get('POSTGRES_DB')
            self.user = app.config.get('POSTGRES_USER')
            self.password = app.config.get('POSTGRES_PASSWORD')
            self.host = app.config.get('POSTGRES_HOST')
        if hostname:
            self.host = socket.gethostbyname(hostname)

    # helper functions
    def __connect(self):
        """
        Connect to db and return the cursor
        """
        conn = psycopg2.connect(
            host=self.host, port=self.port, database=self.database,
            user=self.user, password=self.password
        )
        cur = conn.cursor()
        return cur

    def __gencondition(self, querylist):
        """
        From a list of GET param generate the sql query conditions
        something like:
            WHERE a=b AND c=d AND ...
        """
        conditions = []
        for key in self.PROPERTY_SEARCH_LIST:
            if querylist.get(key):
                conditions.append(self.PROPERTY_SEARCH_LIST[key][1] % (querylist.get(key)))
        return " AND ".join(conditions)

    def __gettotal(self, table, condition):
        """
        Get total_count of a query, for paging
        """
        cur = self.__connect()
        query = "SELECT COUNT(*) FROM %s WHERE %s ;" 
        try:
            cur.execute(query, (AsIs(table), 
                                AsIs(condition), )
                       )
            total_count = cur.fetchone()
            return total_count[0]
        except Exception as e:
            return -1 # error

    def __getresult(self, cur, paging=False, total=0):
        """
        Return the sql that executed, the count of results and results
        NOTE: When use paging, need to get total record count outside
        """
        colnames = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        results = []
        while row is not None:
            results.append(row)
            row = cur.fetchone()
        
        # NOTE: if use LIMIT, cur.rowcount will return page size
        # use count(*) OVER() AS total_count instead
        if paging == False:
            total_count = cur.rowcount
        else:
            total_count = total

        cur.close()
        return {"query": str(cur.query),
                "success" : "True",
                "count": total_count,
                "results": results,
                "colnames": colnames}


    # public functions
    def get_field(self, colname, colnames, result):
        """
        For the result of self.__getresult(), colname and results are separate
        Need this method to act like a dictionary
        colname: one column name
        colnames: a list of column names
        result: one row of results
        """
        if colnames.count(colname) == 1 and len(result)==len(colnames):
            index = colnames.index(colname)
            return result[index]
        else:
            return None


    def rawquery(self, rawsql):
        """
        Run query as raw sql
        NOTE: very dangerous, only give to the highest authen user
        """
        cur = self.__connect()
        try:
            cur.execute("%s", (AsIs(rawsql),) )
            return self.__getresult(cur)
        except Exception as e:
            return {"query": str(cur.query),
                    "success" : "False",
                    "count": 0,
                    "results": None,
                    "colnames": None}


    def query(self, querylist, table):
        """
        Run simple query from a list of GET param
        """
        cur = self.__connect()
        query = "SELECT * \
                FROM %s \
                WHERE %s;" % (AsIs(table), AsIs(self.__gencondition(querylist)),)
        try:
            cur.execute(query) # (AsIs(table), AsIs(self.__gencondition(querylist)),) )
            return self.__getresult(cur)
        except Exception as e:
            return {"query": str(cur.query),
                    "success" : "False",
                    "count": 0,
                    "results": None,
                    "colnames": None}

    
    def query_property(self, select_list, query_list, orderby, paging_size=20, page_num=1):
        """
        Run query from a list of GET param, plus version
        NOTE: only for property
        :param select_list: str array
        :param query_list: str array
        :param orderby: str, default is "id"
        :param paging_size: int, default is 20
        :param page_num: int, default is 1
        :return:
        """
        offset = (page_num-1)*paging_size
        # default orderby is "id"
        orderby = "id" if not orderby else orderby
        if query_list.get('descend')=='true': # TODO: fix this
            orderby += " DESC"
        condition = self.__gencondition(query_list)
        # when query list is empty (do not consider 'descend'), return everything
        condition = "id>0" if not condition else condition
        table = "properties" # NOTE: DO NOT TOUCH IT!!!

        cur = self.__connect()
        query = "SELECT %s \
                FROM %s \
                WHERE %s \
                ORDER BY %s \
                LIMIT %s \
                OFFSET %s;"
        try:
            cur.execute(query, (AsIs(','.join(select_list) ),
                                AsIs(table),
                                AsIs(condition),
                                AsIs(orderby), 
                                AsIs(str(paging_size)), 
                                AsIs(str(offset)),  ))
            total_count = self.__gettotal(table, condition)
            return self.__getresult(cur, paging=True, total=total_count)
        except Exception as e:
            return {"query": query,
                    "success" : "False",
                    "count": 0,
                    "results": None,
                    "colnames": None}


    def distinct(self, col_name, table):
        """SELECT DISTINCT col_name from
        """
        cur = self.__connect()
        try:
            cur.execute(
                "SELECT DISTINCT %s\
                FROM %s;",
                (col_name, table,)
            )
            return self.__getresult(cur)
        except Exception as e:
            return {"query": str(cur.query),
                    "success" : "False",
                    "count": 0,
                    "results": None,
                    "colnames": None}


    def getcityfullname(self, shortname):
        """
        Given a city shortname, get fullname from cities table
        :param shortname: string
        :return: string
        """
        rawsql = "SELECT * FROM CITYS WHERE value='%s'" % (shortname)
        r = self.rawquery(rawsql)
        fullname = r["results"][0][-2]
        if not fullname:
            fullname = "Default City"
        return fullname
    
    def getcityshortname(self, fullname):
        """
        Given a city fullname, get shortname from cities table
        :param fullname: string
        :return: string
        """
        rawsql = "SELECT * FROM CITYS WHERE long_value='%s'" % (fullname)
        r = self.rawquery(rawsql)
        shortname = r["results"][0][1]
        if not shortname:
            shortname = "dc"
        return shortname











#end
