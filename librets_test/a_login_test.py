import unittest
import sys,librets

# should get from app config
TEST_URL = "https://pt.rets.crmls.org/contact/rets/login"
USR_NAME = "EZPRINT"
USR_PSWD = "!cx9HvT9"

class TestLibretsLogin(unittest.TestCase):
    CLASSNAME = "Login"

    @classmethod
    def setUpClass(cls):
        print("==================================")
        print(cls.CLASSNAME, "Test Start")

    @classmethod
    def tearDownClass(cls):
        print("\n", cls.CLASSNAME, "Test End!")
        print("==================================")


    def test_login(self):
        session = librets.RetsSession(TEST_URL)
        # if have user agent account
        # session.SetUserAgentAuthType(librets.USER_AGENT_AUTH_RETS_1_7)
        # session.SetUserAgentPassword("YourPassword")
        if not session.Login(USR_NAME, USR_PSWD):
            print("Error logging in! The credential may be invalid.")

        # logout
        logout = session.Logout()
        print("Billing info: " + logout.GetBillingInfo())
        print("Logout message: " + logout.GetLogoutMessage())
        print("Connect time: " + str(logout.GetConnectTime()))

        print("Login Test Passed!\n")
