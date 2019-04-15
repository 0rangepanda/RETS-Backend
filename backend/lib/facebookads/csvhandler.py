import csv
import os
import configparser


class CrmlsCsvHandler(object):
    """
    Input a csv file from CRMLS, generate the facebook ads catalog xml file
    Indicate a path in input for result xml file
    This xml can be used to manually create a catalog on fb ads
    """
    def __init__(self, csvfile_path, config_path):
        self.reader = csv.reader(open(csvfile_path, "r"))
        self.config = configparser.ConfigParser(interpolation=configparser.BasicInterpolation())
        self.config.read(config_path, encoding=None)
        self.colname_list = {}
        # pop out the first line (colname line)
        for index, colname in enumerate(next(self.reader)):
            self.colname_list[colname] = index

    def __get_addr1(self, item):
        """
        Merge and generate the full street name
        :param item:
        :return: the full street name
        """
        addr1 = []
        namelist = self.config['Special']['addr1'].split('\n')
        for name in namelist:
            value = item[self.colname_list[name]]
            if value:
                addr1.append(value)
        return " ".join(addr1)

    def __get_name(self, item):
        """
        Generate a name for a property
        :param item: A line from csv file
        :return: A name (addr1+city+state+postalcode)
        """
        addr1 = self.__get_addr1(item)
        return addr1 + ', ' + item[self.colname_list['City']] + ', ' + \
               item[self.colname_list['StateOrProvince']] + ' ' + \
               item[self.colname_list['PostalCode']]

    def __get_availability(self, item):
        """
        Mapping CRMLS availability to FB val
        :param item: A line from csv file
        :return: the mapping availability (val list from fb)
        """
        colname_in_csv = self.config['Special']['availability']
        val_in_csv = item[self.colname_list[colname_in_csv]]
        val_for_fb = self.config['Availability'].get(val_in_csv, "")
        return val_for_fb


    # public functions
    def parse_property(self, item, hardmode=True):
        """
        Parse the data of a property
        :param item: A line from csv file
        :param hardmode: if True, discard not complete property, else don't discard and let FB do the check
        :return: A dict
        """
        property = {}
        # necessary fields, if doesn't have, abandon this item
        for key, val in self.config['ColumnMapping'].items():
            property[key] = item[self.colname_list[val]]
            # For some empty fields, we can give a default value
            if not property[key]:
                if key in self.config['DefaultVal']:
                    property[key] = self.config['DefaultVal'][key]
                else:
                    if hardmode:
                        return None  # early exit

        # special fields, can't be empty
        # but do not deal with image here
        for key, val in self.config['Special'].items():
            if key == 'addr1':
                property[key] = self.__get_addr1(item)
            elif key == 'name':
                property[key] = self.__get_name(item)
            elif key == 'availability':
                property[key] = self.__get_availability(item)
            elif key == 'image':
                property[key] = ['fake_value']
            elif key == 'url':
                property[key] = 'http://www.fakeurl.com' # TODO: give a url
            else:
                property[key] = ''

        if hardmode and any(not property[key] for key in self.config['Special']):
            return None
        # extra fields, can be empty
        for key, val in self.config['ExtraField'].items():
            property[key] = item[self.colname_list[val]]
        return property

    def parse_all(self, hardmode=True):
        """
        Parse all in csv file and return a xml file
        :return: A dict, key->ListingId, val->the whole dict data
        """
        res = {}
        for item in self.reader:
            p = self.parse_property(item, hardmode=hardmode)
            if p:
                res[p['home_listing_id']] = p
        return res






