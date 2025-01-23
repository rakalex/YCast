import logging
import urllib.request
import urllib.parse
import os

import ycast.generic as generic
from ycast import __version__

MAX_SIZE = 290
CACHE_NAME = 'icons'

def get_icon(station):
    cache_path = generic.get_cache_path(CACHE_NAME)
    if not cache_path:
        return None

    # make icon filename from favicon address
    station_icon_file = cache_path + '/' + generic.get_checksum(station.icon) + '.jpg'
    if not os.path.exists(station_icon_file):
        logging.debug("Station icon cache miss. Fetching and converting station icon for station id '%s'", station.id)
        headers = {'User-Agent': generic.USER_AGENT + '/' + __version__}

        try:
            url = urllib.parse.urlparse(station.icon)
            request = urllib.request.Request(station.icon, headers=headers)
            response = urllib.request.urlopen(request, timeout=5)
        except Exception as err:
            logging.debug("Connection to station icon URL failed (%s)", err)
            return None

        if response.status != 200:
            logging.debug("Could not get station icon data from %s (HTML status %s)",
                          station.icon, response.status)
            return None

        try:
            image_data = response.read()
            # Simulate image processing by resizing and converting to JPEG format manually
            # This example assumes the image is in a format that can be handled directly
            from PIL import Image
            from io import BytesIO
            image = Image.open(BytesIO(image_data))
            image = image.convert("RGB")
            if image.size[0] > image.size[1]:
                ratio = MAX_SIZE / image.size[0]
            else:
                ratio = MAX_SIZE / image.size[1]
            image = image.resize((int(image.size[0] * ratio), int(image.size[1] * ratio)), Image.Resampling.LANCZOS)
            image.save(station_icon_file, format="JPEG")
        except Exception as e:
            logging.error("Station icon conversion error (%s)", e)
            return None

    try:
        with open(station_icon_file, 'rb') as file:
            image_conv = file.read()
    except PermissionError:
        logging.error("Could not access station icon file in cache (%s) because of access permissions",
                      station_icon_file)
        return None
    return image_conv