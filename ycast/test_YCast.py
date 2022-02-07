import json
import logging
import os
import unittest
from io import StringIO

import flask

from ycast import my_filter, generic, radiobrowser, my_recentlystation


class MyTestCase(unittest.TestCase):

    logging.getLogger().setLevel(logging.DEBUG)

    def test_verify_values(self):
        assert my_filter.verify_value(None, None)
        assert my_filter.verify_value('', '')
        assert my_filter.verify_value(None, '')
        assert my_filter.verify_value(3, 3)
        assert my_filter.verify_value('3', 3)
        assert my_filter.verify_value('3', '3')
        assert my_filter.verify_value('3,4,5,6', '5')

        assert not my_filter.verify_value('', None)
        assert not my_filter.verify_value('', '3')
        assert not my_filter.verify_value(3, 4)
        assert not my_filter.verify_value('3', 4)
        assert not my_filter.verify_value('4', '3')
        assert not my_filter.verify_value('3,4,5,6', '9')

    def test_init_filter(self):
        my_filter.begin_filter()

        for elem in my_filter.filter_dictionary:
            logging.warning("Name filtertype: %s", elem)
            filter_param = my_filter.filter_dictionary[elem]
            if filter_param:
                for par in filter_param:
                    logging.warning("    Name paramter: %s", par)
            else:
                logging.warning("    <empty list>")

    def test_valid_station(self):
        my_filter.begin_filter()
        test_lines = generic.readlns_txt_file(generic.get_var_path()+"/test.json")

        test_lines = radiobrowser.get_stations_by_votes()

        io = StringIO(test_lines[0])
        stations_json = json.load(io)
        count = 0
        for station_json in stations_json:
            if my_filter.check_station(station_json):
                station = radiobrowser.Station(station_json)
                count = count + 1

        my_filter.end_filter()

    def test_life_popular_station(self):
        # hard test for filter
        stations = radiobrowser.get_stations_by_votes(10000000)
        logging.info("Stations (%d)", len(stations))

    def test_get_languages(self):
        result = radiobrowser.get_language_directories()
        assert len(result) == 3

    def test_get_countries(self):
        result = radiobrowser.get_country_directories()
        assert len(result) == 4

    def test_get_genre(self):
        result = radiobrowser.get_genre_directories()
        assert len(result) < 300

    def test_get_limits(self):
        result = my_filter.get_limit('irgendwas',20)
        assert result == 20

    def test_jsonable_classes(self):
        generic.init_base_dir('.ycast')
        my_filter.init_filter_file()
        stations = radiobrowser.get_stations_by_country('Germany')
        station = stations[0]
        text = station.to_vtuner()
        response = station.toJson()
        response = json.dumps(station, skipkeys= True)

        assert response is not None

    def test_recently_hit(self):

        try:
            os.remove(my_recentlystation.get_recently_file())
        except Exception:
            pass

        result = my_recentlystation.get_stations_by_vote()
        assert len(result) == 0

        result = my_recentlystation.get_recently_stations_dictionary()
        assert result is None

        i = 0
        while i < 10:
            my_recentlystation.signal_station_selected('NAME ' + str(i), 'http://dummy/' + str(i),
                                                       'http://icon' + str(i))
            i = i+1

        result = my_recentlystation.get_recently_stations_dictionary()
        assert my_recentlystation.directory_name()
        assert result[my_recentlystation.directory_name()]

        my_recentlystation.signal_station_selected('Konverenz: Sport', 'http://dummy/' + str(i),
                                                   'http://icon' + str(i))
        my_recentlystation.signal_station_selected('Konverenz: Sport', 'http://dummy/' + str(i),
                                                   'http://icon' + str(i))
        my_recentlystation.signal_station_selected('Konverenz: Sport', 'http://dummy/' + str(i),
                                                   'http://icon' + str(i))

        i = 6
        while i < 17:
            my_recentlystation.signal_station_selected('NAME ' + str(i), 'http://dummy/' + str(i),
                                                       'http://icon' + str(i))
            i = i+1

        result = my_recentlystation.get_recently_stations_dictionary()
        assert result[my_recentlystation.directory_name()]

        result = my_recentlystation.get_stations_by_vote()
        assert len(result) == 5

        j = 0
        while j < 6:
            i = 6
            while i < 9:
                my_recentlystation.signal_station_selected('NAME ' + str(i), 'http://dummy/' + str(i),
                                                           'http://icon' + str(i))
                i = i+1
            j = j+1
        result = my_recentlystation.get_stations_by_vote()
        assert len(result) == 5


if __name__ == '__main__':
    unittest.main()
