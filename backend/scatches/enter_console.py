import sys, os
import time

if os.path.abspath(os.curdir) not in sys.path:
    sys.path.append(os.path.abspath(os.curdir))

from project import db
from project.models import Property, User
from lib.mlshandler.crmls import CrmlsHandler
import librets

"""This scripts will setup the database and generate some data into it
for test environment
"""
print("Enter console...")

q = Property.query.all()
property1 = q[1]
kwargs = {}
kwargs['listingkey_numeric'] = q[1].listingkey_numeric
kwargs['listing_id'] = q[1].listing_id
kwargs['list_price'] = q[1].list_price
kwargs['beds'] = q[1].beds
kwargs['city'] = q[1].city

update_list = q[2].diff(kwargs)
q[2].from_dict(kwargs)
update_list1 = q[2].diff(kwargs)