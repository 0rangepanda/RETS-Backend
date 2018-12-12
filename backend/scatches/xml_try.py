import xml.etree.ElementTree as ET
import xml.dom.minidom


# create the file structure
listings = ET.Element('listings')
title = ET.SubElement(listings, 'title')
title.text = "example.com Feed"

link = ET.SubElement(listings, 'link')
link.set('rel', 'self')
link.set('href', 'http://www.example.com')

listing = ET.SubElement(listings, 'listing')
item1 = ET.SubElement(listing, 'item')
item2 = ET.SubElement(listing, 'item')
item1.set('name','item1')
item2.set('name','item2')
item1.text = 'item1abc'
item2.text = 'item2abc'

# create a new XML file with the results
mydata = ET.tostring(listings, encoding="UTF-8")
pretty_xml_as_string = xml.dom.minidom.parseString(mydata).toprettyxml()
print(pretty_xml_as_string)
myfile = open("items2.xml", "w")
myfile.write(pretty_xml_as_string)