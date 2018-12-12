from ftplib import FTP
import socket
import os


# Change directories - create if it doesn't exist
def chdir(ftp, dir):
    if not directory_exists(ftp, dir):
        ftp.mkd(dir)
    else:
        ftp.mkd(dir+'_0')
    ftp.cwd(dir)

# Check if directory exists (in current location)
def directory_exists(ftp, dir):
    filelist = []
    ftp.retrlines('LIST', filelist.append)
    for f in filelist:
        if f.split()[-1] == dir and f.upper().startswith('D'):
            return True
    return False

if __name__ == "__main__":
    ftp=FTP()
    ftp.set_debuglevel(2)
    print(socket.gethostbyname('apt444.com'))
    ftp.connect(socket.gethostbyname('apt444.com'))
    ftp.login('apt444', 'g{%gvq(sM8f!')
    # create a new folder
    tmpfolder = "hahaha"
    chdir(ftp, "public_html/" + tmpfolder)

    os.chdir(os.path.abspath(os.curdir) + "/Full + Photos")
    filename = "504078_0.jpg"
    ftp.storbinary('STOR ' + filename, open(filename, 'rb'))
    ftp.quit()