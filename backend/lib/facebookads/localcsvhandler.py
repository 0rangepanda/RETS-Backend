import csv
import os
import configparser
from ast import literal_eval

import uuid, datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom


class LocalCsvHandler(object):
    """
    Input a query result from local database, generate the facebook ads catalog xml file
    Indicate a path in input for result xml file
    This xml can be used to manually (or using api) create a catalog on fb ads
    """
    address_field = ['addr1', 'city', 'region', 'country', 'postal_code']
    special_field = ['image']
    
    def __init__(self, config_path):
        self.config = configparser.ConfigParser(interpolation=configparser.BasicInterpolation())
        self.config.read(config_path, encoding=None)
        

    def __get_name(self, item):
        """
        Generate a name for a property
        :param item: A line from self.queryres
        :return: A name (addr1+city+state+postalcode)
        """
        return item["streetname"] + ', ' + item["city"] + ', ' + \
               item["state"] + ' ' + item["postalcode"]

    def __get_availability(self, item):
        """
        Mapping CRMLS availability to FB val
        :param item: A line from self.queryres
        :return: the mapping availability (val list from fb)
        """
        s = item["status"]
        res = self.config['Availability'].get(s, 'for_rent')
        return res

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
            property[key] = item.get(val, "")
            # For some empty fields, we can give a default value
            if property[key]=="" or not property[key]:
                if key in self.config['DefaultVal']:
                    property[key] = self.config['DefaultVal'][key]
                else:
                    if hardmode:
                        return None  # early exit

        # special fields, can't be empty
        # but do not deal with image here
        for key, val in self.config['Special'].items():
            if key == 'name':
                property[key] = self.__get_name(item)
            elif key == 'availability':
                property[key] = self.__get_availability(item)
            elif key == 'image':
                if item["image"]:
                    images = literal_eval(item["image"])
                    if len(images)>0:
                        property[key] = []
                        for img in images:
                            if img["type"]=="IMAGE":
                                property[key].append(img["url"])
                else:
                    property[key] = ['fake_value']
            elif key == 'url':
                property[key] = 'http://www.fakeurl.com' # TODO: give a url
            else:
                property[key] = ''

        if hardmode and any(not property[key] for key in self.config['Special']):
            return None
        # extra fields, can be empty
        for key, val in self.config['ExtraField'].items():
            property[key] = item[val]
        return property

    def parse_all(self, queryres, hardmode=True):
        """
        Parse all in csv file and return a xml file
        :return: A dict, key->ListingId, val->the whole dict data
        """
        res = []
        for item in queryres:
            p = self.parse_property(item, hardmode=hardmode)
            if p:
                res.append(p)
        return res

    def __gen_name(self):
        """
        Generate a unique folder name with date
        :return:
        """
        prefix = "FBADS"
        uniq_id = str(uuid.uuid4())
        date_info = datetime.datetime.now().date().strftime('%Y-%m-%d')
        return prefix + '_' + date_info + '_' + uniq_id

    def gen_xml(self, all_properties, release_path):
        """
        Generate the xml file
        :param all_properties: return of self.parse_all()
        :param release_path: the path to the xml file
        :return: xml file name
        """
        filename = self.__gen_name()+ ".xml"
        listings = ET.Element('listings')
        # title
        title = ET.SubElement(listings, 'title')
        title.text = "example.com Feed"
        # link
        link = ET.SubElement(listings, 'link')
        link.set('rel', 'self')
        link.set('href', 'http://www.example.com')

        for data in all_properties:
            listing = ET.SubElement(listings, 'listing')
            for field in data.keys():
                if field not in self.address_field and field not in self.special_field:
                    xml_elem = ET.SubElement(listing, field)
                    xml_elem.text = data[field]
            # address field
            address = ET.SubElement(listing, 'address')
            address.set('format', 'simple')
            for field in self.address_field:
                xml_elem = ET.SubElement(address, 'component')
                xml_elem.text = data[field]
                xml_elem.set('name', field)
            # image field
            image = ET.SubElement(listing, 'image')
            for img in data['image']:
                xml_elem = ET.SubElement(image, 'url')
                xml_elem.text = img

        # create a new XML file with the results
        mydata = ET.tostring(listings, encoding="UTF-8")
        pretty_xml_as_string = xml.dom.minidom.parseString(mydata).toprettyxml()
        #print(pretty_xml_as_string)
        filepath = os.path.join(release_path, filename)
        myfile = open(filepath, "w")
        myfile.write(pretty_xml_as_string)
        return filename
