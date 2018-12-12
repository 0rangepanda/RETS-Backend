import psycopg2
import socket
from psycopg2.extensions import adapt
from psycopg2.extensions import AsIs

# the mapping between GET params and sql queries, 
# only in this list can be parsed by GET
# TODO: use config file? 
SEARCH_LIST = {
    "id" : "id = %s",
    "city" : "city = '%s'",
    "minlistprice" : "list_price >= %s",
    "maxlistprice" : "list_price <= %s",
    "bathmin" : "baths >= %s",
    "bathmax" : "baths <= %s",
    "bedmin" : "beds >= %s",
    "bedmax" : "beds <= %s",
    "status" : "status = '%s'",
    "postalcode" : "postalcode = '%s'",
}

class PsyHandler(object):
    """
    Connect to postgresql by psycopg2 instead of SQLAlchemy
    Only manage READING
    *WHY using this instead of SQLAlchemy (which is much more easy)
    *Raw SQL could do more optimization I guess...
    """

    def __init__(self, app, hostname=None):
        """
        app: Flask object
        """
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
        for key in SEARCH_LIST:
            if querylist.get(key):
                conditions.append(SEARCH_LIST[key] % (querylist.get(key)))
        return " AND ".join(conditions)

    def __gettotal(self, table, query_list):
        """
        Get total_count of a query, for paging
        """
        cur = self.__connect()
        query = "SELECT COUNT(*) FROM %s WHERE %s ;" 
        try:
            cur.execute(query, (AsIs(table), 
                                AsIs(self.__gencondition(query_list)), ))
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

    
    def query_plus(self, select_list, table, query_list, orderby, paging_size, page_num):
        """
        Run query from a list of GET param, plus version
        :param select_list: str array
        :param query_list: str array
        :param table: str 
        :param orderby: str
        :param paging_size: int
        :param page_num: int
        :return:
        """
        offset = (page_num-1)*paging_size
        if query_list.get('descend', 'false')=='true':
            orderby += " DESC"

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
                                AsIs(self.__gencondition(query_list)),
                                AsIs(orderby), 
                                AsIs(str(paging_size)), 
                                AsIs(str(offset)), ))
            total_count = self.__gettotal(table, query_list)
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















#end
