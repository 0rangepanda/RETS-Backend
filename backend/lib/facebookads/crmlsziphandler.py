import os, errno
import shutil
import configparser
import zipfile
import uuid, datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom

from ftplib import FTP
import socket

from .csvhandler import CrmlsCsvHandler


def chdir(ftp, dir):
    """
    Change directories - create if it doesn't exist
    :param ftp:
    :param dir:
    :return:
    """
    if not directory_exists(ftp, dir):
        ftp.mkd(dir)
    else:
        return False
    ftp.cwd(dir)
    return True


def directory_exists(ftp, dir):
    """
    Check if directory exists (in current location)
    :param ftp:
    :param dir:
    :return:
    """
    filelist = []
    ftp.retrlines('LIST', filelist.append)
    for f in filelist:
        if f.split()[-1] == dir and f.upper().startswith('D'):
            return True
    return False


class CrmlsZipHandler(object):
    """
    Input a zipfile from CRMLS, generate the facebook ads catalog xml file
    """
    # some config for xml
    address_field = ['addr1', 'city', 'region', 'country', 'postal_code']
    special_field = ['image']

    def __init__(self, zipfile_path, config_path, release_path, unzip_path):
        """
        Init
        :param zipfile_path:
        :param config_path:
        :param release_path: the dir to release the final xml file
        :param unzip_path: the dir to unzip the zipfile
        """
        self.__zipfile_path = zipfile_path
        self.__config_path = config_path
        self.__release_path = release_path
        self.__unzip_path = unzip_path
        self.__zfile = zipfile.ZipFile(zipfile_path, 'r')
        self.__filelist = self.__zfile.namelist()
        # config
        self.config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        self.config.read(config_path, encoding=None)
        self.__uniqid = self.__gen_name()

    def __gen_name(self):
        """
        Generate a unique folder name with date
        :return:
        """
        prefix = "FBADS"
        uniq_id = str(uuid.uuid4())
        date_info = datetime.datetime.now().date().strftime('%Y-%m-%d')
        return prefix + '_' + date_info + '_' + uniq_id

    def __upload_image(self, folder_name, image_path_list):
        """
        upload all image in list to a ftp server
        :param image_path_list: a list of images
        :return: the url suffix of all images
        (can be access in the Internet by suffix+image_filename)
        """
        try:
            ftp = FTP()
            ftp.set_debuglevel(2)
            ftp.connect(socket.gethostbyname(self.config['FTPserver']['host']))
            ftp.login(self.config['FTPserver']['username'],
                      self.config['FTPserver']['password'])
            # create a new folder
            # dir "public_html/" is for cpanel only
            chdir(ftp, "public_html/" + folder_name)
            unzip_path = os.path.join(self.__unzip_path, self.__uniqid)
            os.chdir(unzip_path)
            for filename in image_path_list:
                ftp.storbinary('STOR ' + filename, open(filename, 'rb'))
            ftp.quit()
        except Exception as e:
            return False
        return True

    def __handle_csv(self, csvfile_path):
        """
        Call class CrmlsCsvHandler
        :param filename:
        :return:
        """
        csvhlder = CrmlsCsvHandler(csvfile_path, self.__config_path)
        return csvhlder.parse_all(hardmode=True)

    def __gen_xml(self, all_properties, file_name):
        """
        Generate the xml file
        :param all_properties: input data
        :param file_name: the file name is [file_name] + ".xml"
        :return: xml file name
        """
        listings = ET.Element('listings')
        # title
        title = ET.SubElement(listings, 'title')
        title.text = "example.com Feed"
        # link
        link = ET.SubElement(listings, 'link')
        link.set('rel', 'self')
        link.set('href', 'http://www.example.com')

        for listing_id, data in all_properties.items():
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
        filepath = os.path.join(self.__release_path, file_name + ".xml")
        myfile = open(filepath, "w")
        myfile.write(pretty_xml_as_string)
        return filepath

    def __cleanup(self):
        """

        :return:
        """
        #shutil.rmtree(unzip_path)
        #os.remove(file_path)
        return None

    # public functions
    def unzip(self):
        """
        Unzip the zipfile to path:[self.__unzip_path]/[self.__uniqid]/
        Should create a new folder
        :return: True if success
        """
        # try to make dir, if exist return False
        try:
            unzip_path = os.path.join(self.__unzip_path, self.__uniqid)
            #shutil.rmtree(unzip_path)
            os.makedirs(unzip_path, exist_ok=True)
        except OSError as e:
            return False
            #if e.errno == errno.EEXIST: return False anyway

        # unzip
        for filename in self.__filelist:
            data = self.__zfile.read(filename)
            file = open(os.path.join(unzip_path, filename), 'w+b')
            file.write(data)
            file.close()
        return True

    def handle(self):
        """
        Generate the xml file for facebook ad catalog
        :return: xml xmlfile_name if success
        """
        # handle csv
        csv_count = 0
        for filename in self.__zfile.namelist():
            suffix = os.path.splitext(filename)[-1]
            if suffix == ".csv":
                csv_count += 1
                unzip_path = os.path.join(self.__unzip_path, self.__uniqid)
                csv_path = os.path.join(unzip_path, filename)
                all_properties = self.__handle_csv(csv_path)
        # if not exactly 1 csv file, return
        if csv_count != 1:
            return False

        # handle img
        # folder_name = self.__folder_name()
        image_url_suffix = 'http://' + self.config['FTPserver']['host'] + '/' + self.__uniqid + '/'
        image_path_list = []
        for filename in self.__zfile.namelist():
            prefix = os.path.splitext(filename)[0]
            suffix = os.path.splitext(filename)[-1]
            listing_id = prefix.split('_')[0]
            if suffix == ".jpg":
                if prefix[-2:] == "_0": # the first image
                    p = all_properties.get(listing_id)
                    if p:  # must be a valid property
                        image_path_list.append(filename)
                        p['image'] = [image_url_suffix+filename]
                # TODO: what to do with other images?

        # generate xml
        #print(image_path_list)
        #for listing_id, data in all_properties.items():
        #   print(data)

        try:
            self.__upload_image(self.__uniqid, image_path_list)
            xml_path = self.__gen_xml(all_properties, self.__uniqid)
            #self.__cleanup()
            return xml_path
        except Exception as e:
            #self.__cleanup()
            return None

















#