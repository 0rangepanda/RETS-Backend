import os
import time

class uploadfile():
    """
    """

    def __init__(self, name, pdir, type=None, size=None, not_allowed_msg=''):
        self.name = name
        self.dir = pdir
        self.type = type
        self.size = size
        self.not_allowed_msg = not_allowed_msg
        self.url = "data/%s" % name
        self.thumbnail_url = "thumbnail/%s" % name
        self.delete_url = "delete/%s" % name
        self.delete_type = "DELETE"
        # get createtime
        os.environ['TZ'] = 'America/Los_Angeles'
        time.tzset()
        self.t = os.path.getctime(os.path.join(self.dir, name))
        self.createtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.t))


    def is_image(self):
        fileName, fileExtension = os.path.splitext(self.name.lower())
        if fileExtension in ['.jpg', '.png', '.jpeg', '.bmp']:
            return True
        return False


    def get_file(self):
        if self.type != None:
            # POST an image
            if self.type.startswith('image'):
                return {"name": self.name,
                        "type": self.type,
                        "size": self.size, 
                        "url": self.url, 
                        "thumbnailUrl": self.thumbnail_url,
                        "deleteUrl": self.delete_url, 
                        "deleteType": self.delete_type,
                        "createtime": self.createtime,
                        "t": self.t,}
            
            # POST an normal file
            elif self.not_allowed_msg == '':
                return {"name": self.name,
                        "type": self.type,
                        "size": self.size, 
                        "url": self.url, 
                        "deleteUrl": self.delete_url, 
                        "deleteType": self.delete_type,
                        "createtime": self.createtime,
                        "t": self.t,}

            # File type is not allowed
            else:
                return {"error": self.not_allowed_msg,
                        "name": self.name,
                        "type": self.type,
                        "size": self.size,}

        # GET image from disk
        elif self.is_image():
            return {"name": self.name,
                    "size": self.size, 
                    "url": self.url, 
                    "thumbnailUrl": self.thumbnail_url,
                    "deleteUrl": self.delete_url, 
                    "deleteType": self.delete_type,
                    "createtime": self.createtime,
                    "t": self.t,}
        
        # GET normal file from disk
        else:
            return {"name": self.name,
                    "size": self.size, 
                    "url": self.url, 
                    "deleteUrl": self.delete_url, 
                    "deleteType": self.delete_type,
                    "createtime": self.createtime,
                    "t": self.t,}
