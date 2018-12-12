import configparser

class myconf(configparser.ConfigParser):
    """
    Overwrite the ConfigParser optionxform()
    then won't change everything to lowercase
    """
    def __init__(self,defaults=None):
        configparser.ConfigParser.__init__(self,defaults=None)
    
    def optionxform(self, optionstr):
        return optionstr


if __name__ == "__main__":
    """
    Test
    """
    import os, sys
    if os.path.abspath(os.curdir) not in sys.path:
        sys.path.append(os.path.abspath(os.curdir))

    conf=configparser.ConfigParser(
        interpolation=configparser.BasicInterpolation())
    conf.read("./configs/crmls.ini", encoding=None)
    print(conf.sections())
    for  i in conf.sections():
        print(conf.options(i))
        for option in  conf.options(i):
            print(option, conf.get(i,option))
    
    mconf=myconf()
    mconf.read("./configs/crmls.ini", encoding=None)
    print(mconf.sections())
    for  i in mconf.sections():
        print(mconf.options(i))
        for option in  mconf.options(i):
            print(option, mconf.get(i,option))
