import logging
import os
import hashlib
import sys
import json

USER_AGENT = 'YCast'

VAR_PATH = ''
CACHE_PATH = ''
stations_file_by_config = ''

class Directory:
    def __init__(self, name, item_count, displayname=None):
        self.name = name
        self.item_count = item_count
        self.displayname = displayname or name

    def to_dict(self):
        return {'name': self.name, 'displayname': self.displayname, 'count': self.item_count}

def mk_writeable_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as ex:
        logging.error("Could not create base folder (%s) because of access permissions: %s", path, ex)
        return None
    return path

def init_base_dir(path_element):
    global VAR_PATH, CACHE_PATH
    logging.info('Initialize base directory %s', path_element)
    logging.debug('    HOME: %s', os.path.expanduser("~"))
    logging.debug('     PWD: %s', os.getcwd())

    var_dir = None
    home_dir = os.path.expanduser("~") + path_element

    if not os.getcwd().endswith('/ycast'):
        logging.info('Trying Home-Dir: %s', home_dir)
        var_dir = mk_writeable_dir(home_dir)

    if var_dir is None:
        if len(os.getcwd()) < 6:
            logging.error("len(PWD) < 6 (PWD is too short): '%s'", os.getcwd())
        else:
            work_dir = os.getcwd() + path_element
            logging.info('Trying Work-Dir: %s', work_dir)
            var_dir = mk_writeable_dir(work_dir)

        if var_dir is None:
            sys.exit('YCast: ###### No usable directory found #######, I give up....')

    logging.info('Using var directory: %s', var_dir)
    VAR_PATH = var_dir
    CACHE_PATH = os.path.join(var_dir, 'cache')

def generate_stationid_with_prefix(uid, prefix):
    if not prefix or len(prefix) != 2:
        logging.error("Invalid station prefix length (must be 2)")
        return None
    if not uid:
        logging.error("Missing station id for full station id generation")
        return None
    return f'{prefix}_{uid}'

def get_stationid_prefix(uid):
    if len(uid) < 4:
        logging.error("Could not extract stationid (Invalid station id length)")
        return None
    return uid[:2]

def get_stationid_without_prefix(uid):
    if len(uid) < 4:
        logging.error("Could not extract stationid (Invalid station id length)")
        return None
    return uid[3:]

def get_cache_path(cache_name):
    cache_path = os.path.join(CACHE_PATH, cache_name) if cache_name else CACHE_PATH
    try:
        os.makedirs(cache_path, exist_ok=True)
    except PermissionError:
        logging.error("Could not create cache folders (%s) because of access permissions", cache_path)
        return None
    return cache_path

def get_var_path():
    try:
        os.makedirs(VAR_PATH, exist_ok=True)
    except PermissionError:
        logging.error("Could not create cache folders (%s) because of access permissions", VAR_PATH)
        return None
    return VAR_PATH

def get_stations_file():
    return stations_file_by_config or os.path.join(get_var_path(), 'stations.json')

def set_stations_file(stations_file):
    global stations_file_by_config
    if stations_file:
        stations_file_by_config = stations_file

def get_checksum(feed, charlimit=12):
    hash_feed = feed.encode()
    digest = hashlib.md5(hash_feed).digest()
    xor_fold = bytearray(digest[:8])
    for i, b in enumerate(digest[8:]):
        xor_fold[i] ^= b
    return ''.join(format(x, '02x') for x in xor_fold)[:charlimit].upper()

def read_json_file(file_name):
    try:
        with open(file_name, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning("JSON file '%s' not found", file_name)
    except json.JSONDecodeError as e:
        logging.error("JSON format error in '%s':\n    %s", file_name, e)
    return None

def write_json_file(file_name, dictionary):
    try:
        with open(file_name, 'w') as f:
            json.dump(dictionary, f, indent=4)
            return True
    except json.JSONDecodeError as e:
        logging.error("JSON format error in '%s':\n    %s", file_name, e)
    except Exception as ex:
        logging.error("File not written '%s':\n    %s", file_name, ex)
    return False

def read_lines_txt_file(file_name):
    try:
        with open(file_name, 'r') as f:
            return f.readlines()
    except FileNotFoundError:
        logging.warning("TXT file '%s' not found", file_name)
    return None

def write_lines_txt_file(file_name, line_list):
    try:
        with open(file_name, 'w') as f:
            f.writelines(line_list)
            return True
    except Exception as ex:
        logging.error("File not written '%s':\n    %s", file_name, ex)
    return False

def get_json_attr(json_obj, attr):
    try:
        return json_obj[attr]
    except KeyError as ex:
        logging.debug("json: attr '%s' not found: %s", attr, ex)
        return None