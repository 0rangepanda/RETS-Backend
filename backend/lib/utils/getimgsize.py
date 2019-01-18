from PIL import Image
import requests
import io

def getimgsize(url):
    """

    """
    try:
        response = requests.get(url)
        img = Image.open(io.BytesIO(response.content))
        return img.size
    except expression as identifier:
        return (0,0)
    