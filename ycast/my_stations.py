import logging
import ycast.vtuner as vtuner
import ycast.generic as generic

ID_PREFIX = "MY"

class Station:
    def __init__(self, name, url, category, icon):
        self.id = generic.generate_stationid_with_prefix(
            generic.get_checksum(name + url), ID_PREFIX)
        self.name = name
        self.url = url
        self.tag = category
        self.icon = icon

    def to_vtuner(self):
        return vtuner.Station(
            self.id, self.name, self.tag, self.url, self.icon,
            self.tag, None, None, None, None
        )

    def to_dict(self):
        return {
            'name': self.name,
            'url': self.url,
            'icon': self.icon,
            'description': self.tag
        }

def get_station_by_id(vtune_id):
    stations_yaml = get_stations_json()
    if stations_yaml:
        for category in stations_yaml:
            for station in get_stations_by_category(category):
                if vtune_id == station.id:
                    return station
    return None

def get_stations_json():
    return generic.read_json_file(generic.get_stations_file())

def get_category_directories():
    stations_yaml = get_stations_json()
    categories = []
    if stations_yaml:
        for category in stations_yaml:
            category_length = len(get_stations_by_category(category))
            categories.append(generic.Directory(category, category_length))
    return categories

def get_stations_by_category(category):
    stations_yaml = get_stations_json()
    stations = []
    if stations_yaml and category in stations_yaml:
        for station_name, station_urls in stations_yaml[category].items():
            param_list = station_urls.split('|')
            station_url = param_list[0]
            station_icon = param_list[1] if len(param_list) > 1 else None
            stations.append(Station(station_name, station_url, category, station_icon))
    return stations

def get_all_bookmarks_stations():
    bookmarks_category = generic.read_json_file(generic.get_stations_file())
    stations = []
    if bookmarks_category:
        for category, stations_dict in bookmarks_category.items():
            for station_name, station_urls in stations_dict.items():
                param_list = station_urls.split('|')
                station_url = param_list[0]
                station_icon = param_list[1] if len(param_list) > 1 else None
                stations.append(Station(station_name, station_url, category, station_icon))
    return stations

def put_bookmark_json(elements):
    bookmarks = {}
    for station_json in elements:
        logging.debug("%s ... %s", station_json['description'], station_json['name'])
        category = station_json['description']
        if category not in bookmarks:
            bookmarks[category] = {}
        logging.debug(station_json)
        station_entry = station_json['url']
        if station_json['icon']:
            station_entry += "|" + station_json['icon']
        bookmarks[category][station_json['name']] = station_entry

    generic.write_json_file(generic.get_stations_file(), bookmarks)
    return elements