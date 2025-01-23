import http.server
import socketserver
import logging
import json
import urllib.parse
from http import HTTPStatus

import ycast.vtuner as vtuner
import ycast.radiobrowser as radiobrowser
import ycast.my_stations as my_stations
import ycast.generic as generic
import ycast.station_icons as station_icons

PATH_ROOT = 'ycast'
PATH_PLAY = 'play'
PATH_STATION = 'station'
PATH_SEARCH = 'search'
PATH_ICON = 'icon'
PATH_MY_STATIONS = 'my_stations'
PATH_RADIOBROWSER = 'radiobrowser'
PATH_RADIOBROWSER_COUNTRY = 'country'
PATH_RADIOBROWSER_LANGUAGE = 'language'
PATH_RADIOBROWSER_GENRE = 'genre'
PATH_RADIOBROWSER_POPULAR = 'popular'

station_tracking = False

class YCastHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        try:
            if path.startswith('/setupapp/'):
                self.handle_upstream(path, query)
            elif path.startswith('/api/'):
                self.handle_landing_api(path, query)
            elif path == '/' or path == '/' + PATH_ROOT + '/':
                self.handle_landing_root(query)
            elif path.startswith('/' + PATH_ROOT + '/' + PATH_MY_STATIONS + '/'):
                self.handle_my_stations(path, query)
            elif path.startswith('/' + PATH_ROOT + '/' + PATH_RADIOBROWSER + '/'):
                self.handle_radiobrowser(path, query)
            elif path == '/' + PATH_ROOT + '/' + PATH_PLAY:
                self.handle_get_stream_url(query)
            elif path == '/' + PATH_ROOT + '/' + PATH_STATION:
                self.handle_get_station_info(query)
            elif path == '/' + PATH_ROOT + '/' + PATH_ICON:
                self.handle_get_station_icon(query)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Path not found")
        except Exception as e:
            logging.error("Exception handling request: %s", str(e))
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error")
            
    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        try:
            if path.startswith('/api/'):
                self.handle_landing_api(path, query)            
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Path not found")
        except Exception as e:
            logging.error("Exception handling request: %s", str(e))
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error")

    def handle_upstream(self, path, query):
        logging.debug('upstream **********************')
        if 'token' in query and query['token'][0] == '0':
            self.respond_json(vtuner.get_init_token())
        elif 'search' in query:
            self.handle_station_search(query)
        elif 'statxml.asp' in path and 'id' in query:
            self.handle_get_station_info(query)
        elif 'navXML.asp' in path:
            self.handle_radiobrowser_landing()
        elif 'FavXML.asp' in path:
            self.handle_my_stations_landing()
        elif 'loginXML.asp' in path:
            self.handle_landing_root()
        else:
            logging.error("Unhandled upstream query (/setupapp/%s)", path)
            self.send_error(HTTPStatus.NOT_FOUND, "Path not found")

    def handle_landing_api(self, path, query):
        if self.command == 'GET':
            if path.endswith('stations'):
                self.handle_get_stations(query)
            elif path.endswith('bookmarks'):
                self.handle_get_bookmarks(query)
            elif path.endswith('paramlist'):
                self.handle_get_paramlist(query)
            else:
                self.send_error(HTTPStatus.NOT_IMPLEMENTED, "Not implemented: " + path)
        elif self.command == 'POST':
            content_type = self.headers.get('Content-Type')
            if content_type == 'application/json':
                self.handle_post_bookmark()
            else:
                self.send_error(HTTPStatus.BAD_REQUEST, 'Content-Type not supported!: ' + path)
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Unsupported method: ' + path)

    def handle_landing_root(self, query=None):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open('templates/index.html', 'rb') as file:
            self.wfile.write(file.read())

    def handle_my_stations(self, path, query):
        if path == '/' + PATH_ROOT + '/' + PATH_MY_STATIONS + '/':
            self.handle_my_stations_landing()
        else:
            directory = path.split('/')[-1]
            stations = my_stations.get_stations_by_category(directory)
            self.respond_vtuner_page(get_stations_page(stations, query))

    def handle_radiobrowser(self, path, query):
        if path == '/' + PATH_ROOT + '/' + PATH_RADIOBROWSER + '/':
            self.handle_radiobrowser_landing()
        elif path == '/' + PATH_ROOT + '/' + PATH_RADIOBROWSER + '/' + PATH_RADIOBROWSER_COUNTRY + '/':
            self.handle_radiobrowser_countries()
        elif path == '/' + PATH_ROOT + '/' + PATH_RADIOBROWSER + '/' + PATH_RADIOBROWSER_LANGUAGE + '/':
            self.handle_radiobrowser_languages()
        elif path == '/' + PATH_ROOT + '/' + PATH_RADIOBROWSER + '/' + PATH_RADIOBROWSER_GENRE + '/':
            self.handle_radiobrowser_genres()
        elif path == '/' + PATH_ROOT + '/' + PATH_RADIOBROWSER + '/' + PATH_RADIOBROWSER_POPULAR + '/':
            self.handle_radiobrowser_popular()
        else:
            directory = path.split('/')[-1]
            if PATH_RADIOBROWSER_COUNTRY in path:
                stations = radiobrowser.get_stations_by_country(directory)
            elif PATH_RADIOBROWSER_LANGUAGE in path:
                stations = radiobrowser.get_stations_by_language(directory)
            elif PATH_RADIOBROWSER_GENRE in path:
                stations = radiobrowser.get_stations_by_genre(directory)
            self.respond_vtuner_page(get_stations_page(stations, query))

    def handle_get_stream_url(self, query):
        stationid = query.get('id')
        if not stationid:
            logging.error("Stream URL without station ID requested")
            self.send_error(HTTPStatus.BAD_REQUEST, "Station ID required")
            return
        station = get_station_by_id(stationid[0], additional_info=True)
        if not station:
            logging.error("Could not get station with id '%s'", stationid[0])
            self.send_error(HTTPStatus.NOT_FOUND, "Station not found")
            return
        self.redirect(station.url)

    def handle_get_station_info(self, query):
        stationid = query.get('id')
        if not stationid:
            logging.error("Station info without station ID requested")
            self.send_error(HTTPStatus.BAD_REQUEST, "Station ID required")
            return
        station = get_station_by_id(stationid[0], additional_info=(not station_tracking))
        if not station:
            logging.error("Could not get station with id '%s'", stationid[0])
            self.respond_vtuner_page(vtuner.Page().add_item(vtuner.Display("Station not found")).set_count(1))
            return
        vtuner_station = station.to_vtuner()
        if station_tracking:
            vtuner_station.set_trackurl(self.headers['Host'] + PATH_ROOT + '/' + PATH_PLAY + '?id=' + vtuner_station.uid)
        vtuner_station.icon = self.headers['Host'] + PATH_ROOT + '/' + PATH_ICON + '?id=' + vtuner_station.uid
        self.respond_vtuner_page(vtuner.Page().add_item(vtuner_station).set_count(1))

    def handle_get_station_icon(self, query):
        stationid = query.get('id')
        if not stationid:
            logging.error("Station icon without station ID requested")
            self.send_error(HTTPStatus.BAD_REQUEST, "Station ID required")
            return
        station = get_station_by_id(stationid[0])
        if not station:
            logging.error("Could not get station with id '%s'", stationid[0])
            self.send_error(HTTPStatus.NOT_FOUND, "Station not found")
            return
        station_icon = station_icons.get_icon(station)
        if not station_icon:
            logging.warning("No icon information found for station with id '%s'", stationid[0])
            self.send_error(HTTPStatus.NOT_FOUND, "Icon not found")
            return
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'image/jpeg')
        self.end_headers()
        self.wfile.write(station_icon)

    def handle_get_stations(self, query):
        category = query.get('category', [None])[0]
        if not category:
            self.send_error(HTTPStatus.BAD_REQUEST, "Category parameter is required")
            return

        stations = None
        if category.endswith('voted'):
            stations = radiobrowser.get_stations_by_votes()
        elif category.endswith('language'):
            language = query.get('language', ['german'])[0]
            stations = radiobrowser.get_stations_by_language(language)
        elif category.endswith('country'):
            country = query.get('country', ['Germany'])[0]
            stations = radiobrowser.get_stations_by_country(country)
        
        if stations:
            self.respond_json([station.to_dict() for station in stations])
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Stations not found")

    def handle_get_bookmarks(self, query):
        stations = my_stations.get_all_bookmarks_stations()
        if stations:
            self.respond_json([station.to_dict() for station in stations])
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Bookmarks not found")

    def handle_get_paramlist(self, query):
        category = query.get('category', [None])[0]
        directories = None
        if category and category.endswith('language'):
            directories = radiobrowser.get_language_directories()
        elif category and category.endswith('country'):
            directories = radiobrowser.get_country_directories()
        elif category and category.endswith('voted'):
            directories = radiobrowser.get_stations_by_votes()
        if directories:
            self.respond_json([directory.to_dict() for directory in directories])
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Directories not found")

    def handle_post_bookmark(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        json_data = json.loads(post_data)
        result = my_stations.putBookmarkJson(json_data)
        self.respond_json(result)

    def handle_station_search(self, query):
        search_query = query.get('search', [''])[0]
        if not search_query or len(search_query) < 3:
            vtuner_page = vtuner.Page().add_item(vtuner.Display("Search query too short")).set_count(1)
            self.respond_vtuner_page(vtuner_page)
        else:
            stations = radiobrowser.search(search_query)
            self.respond_vtuner_page(get_stations_page(stations, query))

    def handle_my_stations_landing(self):
        directories = my_stations.get_category_directories()
        self.respond_vtuner_page(get_directories_page('my_stations_category', directories, self))

    def handle_radiobrowser_landing(self):
        page = vtuner.Page()
        page.add_item(vtuner.Directory('Genres', self.headers['Host'] + '/' + PATH_ROOT + '/' + PATH_RADIOBROWSER + '/' + PATH_RADIOBROWSER_GENRE + '/', len(radiobrowser.get_genre_directories())))
        page.add_item(vtuner.Directory('Countries', self.headers['Host'] + '/' + PATH_ROOT + '/' + PATH_RADIOBROWSER + '/' + PATH_RADIOBROWSER_COUNTRY + '/', len(radiobrowser.get_country_directories())))
        page.add_item(vtuner.Directory('Languages', self.headers['Host'] + '/' + PATH_ROOT + '/' + PATH_RADIOBROWSER + '/' + PATH_RADIOBROWSER_LANGUAGE + '/', len(radiobrowser.get_language_directories())))
        page.add_item(vtuner.Directory('Most Popular', self.headers['Host'] + '/' + PATH_ROOT + '/' + PATH_RADIOBROWSER + '/' + PATH_RADIOBROWSER_POPULAR + '/', len(radiobrowser.get_stations_by_votes())))
        page.set_count(4)
        self.respond_vtuner_page(page)

    def handle_radiobrowser_countries(self):
        directories = radiobrowser.get_country_directories()
        self.respond_vtuner_page(get_directories_page('radiobrowser_country_stations', directories, self))

    def handle_radiobrowser_languages(self):
        directories = radiobrowser.get_language_directories()
        self.respond_vtuner_page(get_directories_page('radiobrowser_language_stations', directories, self))

    def handle_radiobrowser_genres(self):
        directories = radiobrowser.get_genre_directories()
        self.respond_vtuner_page(get_directories_page('radiobrowser_genre_stations', directories, self))

    def handle_radiobrowser_popular(self):
        stations = radiobrowser.get_stations_by_votes()
        self.respond_vtuner_page(get_stations_page(stations, self))

    def respond_json(self, data):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def respond_vtuner_page(self, page):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'text/xml')
        self.end_headers()
        self.wfile.write(page.to_string().encode('utf-8'))

    def redirect(self, url):
        self.send_response(HTTPStatus.FOUND)
        self.send_header('Location', url)
        self.end_headers()

def run(config, address='0.0.0.0', port=80):
    generic.set_stations_file(config)
    handler = YCastHandler
    with socketserver.TCPServer((address, port), handler) as httpd:
        try:
            logging.info(f"Serving on {address}:{port}")
            httpd.serve_forever()
        except PermissionError:
            logging.error("No permission to create socket. Are you trying to use ports below 1024 without elevated rights?")
        except KeyboardInterrupt:
            logging.info("Server stopped by user")
            httpd.shutdown()
            
def get_directories_page(subdir, directories, request_obj):
    page = vtuner.Page()
    if len(directories) == 0:
        page.add_item(vtuner.Display("No entries found"))
        page.set_count(1)
        return page
    for directory in get_paged_elements(directories, request_obj):
        vtuner_directory = vtuner.Directory(directory.displayname,
                                            subdir + '/' + directory.name,
                                            directory.item_count)
        page.add_item(vtuner_directory)
    page.set_count(len(directories))
    return page

def get_stations_page(stations, request_obj):
    page = vtuner.Page()
    page.add_item(vtuner.Previous('/' + PATH_ROOT))
    if len(stations) == 0:
        page.add_item(vtuner.Display("No stations found"))
        page.set_count(1)
        return page
    for station in get_paged_elements(stations, request_obj):
        vtuner_station = station.to_vtuner()
        if station_tracking:
            vtuner_station.set_trackurl(PATH_ROOT + '/' + PATH_PLAY + '?id=' + vtuner_station.uid)
        vtuner_station.icon = PATH_ROOT + '/' + PATH_ICON + '?id=' + vtuner_station.uid
        page.add_item(vtuner_station)
    page.set_count(len(stations))
    return page

def get_paged_elements(items, requestargs):
    if 'startitems' in requestargs:
        offset = int(requestargs['startitems'][0]) - 1
    elif 'startItems' in requestargs:
        offset = int(requestargs['startItems'][0]) - 1
    elif 'start' in requestargs:
        offset = int(requestargs['start'][0]) - 1
    else:
        offset = 0
    if offset > len(items):
        logging.warning("Paging offset larger than item count")
        return []
    if 'enditems' in requestargs:
        limit = int(requestargs['enditems'][0])
    elif 'endItems' in requestargs:
        limit = int(requestargs['endItems'][0])
    elif 'start' in requestargs and 'howmany' in requestargs:
        limit = int(requestargs['start'][0]) - 1 + int(requestargs['howmany'][0])
    else:
        limit = len(items)
    if limit < offset:
        logging.warning("Paging limit smaller than offset")
        return []
    if limit > len(items):
        limit = len(items)
    return items[offset:limit]

def get_station_by_id(stationid, additional_info=False):
    station_id_prefix = generic.get_stationid_prefix(stationid)
    if station_id_prefix == my_stations.ID_PREFIX:
        return my_stations.get_station_by_id(stationid)
    elif station_id_prefix == radiobrowser.ID_PREFIX:
        station = radiobrowser.get_station_by_id(stationid)
        if additional_info:
            station.get_playable_url()
        return station
    return None
