import unittest
import sys
import librets

# should get from app config
TEST_URL = "https://pt.rets.crmls.org/contact/rets/login"
USR_NAME = "EZPRINT"
USR_PSWD = "!cx9HvT9"


# Given a RETS Resource, one may next find all of the classes associated
# with that resource. This is done with RetsMetadata: : GetAllClasses(),
# specifying the resource for which you want all of the classes:
def dump_all_classes(metadata, resource):

    def dump_all_tables(metadata, aClass):
        for table in metadata.GetAllTables(aClass):
            print(
                "Table name: " + table.GetSystemName() + " [" +
                table.GetStandardName() + "]"
            )

    resource_name = resource.GetResourceID()
    for aClass in metadata.GetAllClasses(resource_name):
        print(
            "Resource name: " + resource_name + " [" +
            resource.GetStandardName() + "]"
        )
        print(
            "Class name: " + aClass.GetClassName() + " [" +
            aClass.GetStandardName() + "]"
        )
        dump_all_tables(metadata, aClass)


# Certain RETS Tables will refer to RETS Lookups. These are at the same
# hierarchical level as classes, and require the RETS Resource in order to
# locate. This is done with RetsMetadata::GetAllLookups(), specifying the
# resource for which you want all of the lookups
def dump_all_lookups(metadata, resource):

    def dump_all_lookup_types(metadata, lookup):
        for lookup_type in metadata.GetAllLookupTypes(lookup):
            print(
                "Lookup value: " + lookup_type.GetValue() + " (" +
                lookup_type.GetShortValue() + ", " +
                lookup_type.GetLongValue() + ")"
            )

    resource_name = resource.GetResourceID()
    for lookup in metadata.GetAllLookups(resource_name):
        print(
            "Resource name: " + resource_name + " [" +
            resource.GetStandardName() + "]"
        )
        print(
            "Lookup name: " + lookup.GetLookupName() +
            " (" + lookup.GetVisibleName() + ")"
        )
        dump_all_lookup_types(metadata, lookup)


# Testcase
# Note: those are just example usage of librets functions
class TestLibretsFunction(unittest.TestCase):

    CLASSNAME = "Function"

    @classmethod
    def setUpClass(cls):
        print("==================================")
        print(cls.CLASSNAME, "Test Start")

    @classmethod
    def tearDownClass(cls):
        print("\n", cls.CLASSNAME, "Test End!")
        print("==================================")

    # Login and necessary settings for every testcase
    def setUp(self):
        self.session = librets.RetsSession(TEST_URL)
        if not self.session.Login(USR_NAME, USR_PSWD):
            print("Error logging in! The credential may be invalid.")

    # Logout and cleanup
    def tearDown(self):
        logout = self.session.Logout()
        print("Logout message: " + logout.GetLogoutMessage())
        print("Connect time: " + str(logout.GetConnectTime()))

    # show metadata and lookup value
    @unittest.skip("Don't need to run this every time")
    def test_metadata(self):
        print("\nMetadata test:")
        # Obtaining the RetsMetadata Class
        metadata = self.session.GetMetadata()
        # There is only one system object for metadata
        system = metadata.GetSystem()
        print("System ID: " + system.GetSystemID())
        print("Description: " + system.GetSystemDescription())
        print("Comments: " + system.GetComments())
        # show all metadata details
        for resource in metadata.GetAllResources():
            dump_all_classes(metadata, resource)
            dump_all_lookups(metadata, resource)

    # test search function
    def test_search(self):
        print("\nSearch test:")
        # create request
        request = self.session.CreateSearchRequest(
            "Property",
            "Residential",
            "(OriginalListPrice=90000),(ListingContractDate=2018-08-25)"
        )
        request.SetStandardNames(True)
        request.SetSelect("ListingKeyNumeric,ListingID,ListPrice,Beds,City")
        request.SetLimit(librets.SearchRequest.LIMIT_DEFAULT)
        request.SetOffset(librets.SearchRequest.OFFSET_NONE)
        request.SetCountType(librets.SearchRequest.RECORD_COUNT_AND_RESULTS)

        # perform search and show results
        results = self.session.Search(request)
        columns = results.GetColumns()
        print("Record count: " + str(results.GetCount()))
        while results.HasNext():
            for column in columns:
                print(column + ": " + results.GetString(column))

            # fetching image (for crmls)
            pk = results.GetString("ListingKeyNumeric")
            photo_request = self.session.CreateSearchRequest(
                "Media","Media","(ResourceRecordKeyNumeric="+pk+")"
            )
            photo_results = self.session.Search(photo_request)
            photo_columns = photo_results.GetColumns()
            print("images count: " + str(photo_results.GetCount()))
            while photo_results.HasNext():
                print("MediaURL: ", photo_results.GetString("MediaURL"))


    # for other mls, images are getted by GetObjectRequest
    @unittest.skip("Not working for CRMLS")
    def test_Getobj(self):
        print("\nGetObject test:")
        request = librets.GetObjectRequest("Property", "Photo")
        request.AddAllObjects("CV18210537")
        response = self.session.GetObject(request)
        object_descriptor = response.NextObject()
        while object_descriptor:
            object_key = object_descriptor.GetObjectKey()
            object_id = object_descriptor.GetObjectId()
            content_type = object_descriptor.GetContentType()
            description = object_descriptor.GetDescription()
            print(object_key + " object #" + str(object_id))
            #output_file_name = object_key + "-" + str(object_id) + ".jpg"
            #output_file = open(output_file_name, 'wb')
            #output_file.write(object_descriptor.GetDataAsString())
            #output_file.close()
            object_descriptor = response.NextObject()






# end
