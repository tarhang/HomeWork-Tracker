import csv
import numpy as np
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime, timedelta
from dateutil.tz import tzoffset
from math import sin, cos, atan2, sqrt, radians


class Person(object):
    def __init__(self, filename):
        self.locations = None       # to hold location info of the person
        self.start_times = None     # to hold start times of stationary periods
        self.durations = None       # to hold duration of each stationary period

        # setting up the attributes and filling the info based on the csv file
        self.__setup(filename)

    def __setup(self, filename):
        try:
            with open(filename, 'r') as csv_file:
                csv_data = csv.reader(csv_file, delimiter=';')

                # computing the number of the data lines in the csv file
                num_rows = sum(1 for row in csv_data) - 1  # -1 for header

                # creating empty arrays to hold the data
                self.locations = np.empty([num_rows, 2])
                self.start_times = [None] * num_rows
                self.durations = np.empty(num_rows)

                csv_file.seek(0)    # going back to the beginning of the file
                next(csv_data)
                i = 0

                # looping through the file, setting location, time,
                # and duration of stay location for each entry
                for line in csv_data:
                    # setting location (lat, long) info
                    lat, long = Person.__set_location(line)
                    self.locations[i, :] = lat, long

                    # setting time (year, month, day, hour, minute, timezone)
                    self.start_times[i] = Person.__set_time(line[2], lat, long)

                    # set stay duration information
                    duration = int(line[-1]) / 1000.0   # converting ms to s
                    self.durations[i] = duration

                    i += 1

        except FileNotFoundError:
            raise

    @staticmethod
    def __set_location(location):
        """ (str) -> (float, float)
        Parses the given string into two floats
        :param location: str, containing one line of the csv file
        :return: (float, float), latitude and longitude information
        """
        lat = float(location[0])
        long = float(location[1])
        return lat, long

    @staticmethod
    def __set_time(info, lat, long):
        """ (str, float, float) -> datetime

        :param info: str, indicating date and time of the form YYYYMMDDhhmmZ
        :param lat: float, latitude of the location
        :param long: float, longitude of the location
        :return: datetime, aware datetime object
        """
        # extracting time information in the csv file
        start_time = Person.__parse_start_time(info)
        year, month, day, h, m, time_zone = int(start_time['year']), \
                                            int(start_time['month']), \
                                            int(start_time['day']), \
                                            int(start_time['hour']), \
                                            int(start_time['minute']), \
                                            start_time['time_zone']

        # checking to see if the passed in info is correct.
        # Correcting if necessary
        h_tz = time_zone[:3]
        dt = datetime(year, month, day, h, m,
                      tzinfo=tzoffset('UTC' + h_tz, int(h_tz) * 3600))
        dt = Person.__check_time_zone(lat, long, dt, time_zone)
        return dt

    @staticmethod
    def __parse_start_time(start_time):
        """(str) -> {str:str}
        Given a string of date & time, parses the string to individual components
        :param start_time: str, indicating time of the form YYYYMMDDhhmmZ
        :return: dictionary, with pieces of info separated
        """
        parsed = {}
        parsed['year'] = start_time[0:4]
        parsed['month'] = start_time[4:6]
        parsed['day'] = start_time[6:8]
        parsed['hour'] = start_time[8:10]
        parsed['minute'] = start_time[10:12]
        parsed['time_zone'] = start_time[12:]
        return parsed

    @staticmethod
    def __check_time_zone(lat, long, dt, time_zone):
        """ (float, float, datetime, str) -> datetime
        Finds the correct timezone of the location at (lat, long). Then
        corrects the dt parameter to the correct timezone if necessary
        :param lat: float, latitude of the location
        :param long: float, longitude of the location
        :param dt: datetime, aware datetime object
        :param time_zone: str, offset of dt parameter from UTC
        :return: datetime, aware datetime, corrected to the appropriate timezone
        """
        # find the correct timezone and offset at the (lat, long) location
        correct_tz = TimezoneFinder().timezone_at(lat=lat, lng=long)
        correct_offset = datetime.now(tz=pytz.timezone(correct_tz)).utcoffset()

        # finding the offset passed in
        offset = timedelta(hours=int(time_zone[:3]), minutes=int(time_zone[3:]))

        # comparing the timezone info paased in (present in the csv file) to
        # the correct timezone of the (lat, long) location. Correcting the
        # time to the time of the (lat, long) location if necessary
        if correct_offset != offset:
            dt = dt.astimezone(pytz.timezone(correct_tz))

        return dt

    def __num_days(self, start, finish):
        """
        Returns the number of days with location recordings in the double
        sided inclusive period
        given
        :param start: datetime, start of the period
        :param finish: datetime, end of the period
        :return: int, number of days with location recordings in the period
        indicated by start and end
        """
        num_days = 0
        prev_date = None

        for dt in self.start_times:
            if start <= dt <= finish:
                if prev_date is None:
                    prev_date = dt.date()
                    num_days = 1
                elif dt.date() != prev_date:
                    prev_date = dt.date()
                    num_days += 1

        return num_days

    def avg_num_recordings_per_day(self):
        """ (self: Person) -> float
        Returns the average number of data recordings in a day
        :return: float, average number of data recordings in a day
        """
        num_days = self.__num_days(self.start_times[0], self.start_times[-1])
        return len(self.start_times) / num_days

    def avg_num_recordings_in_period(self, start, finish):
        """ (self: Person, datetime, datetime) -> float
        Returns the average number of places visited a day during the period
        of time provided
        :param start: datetime, indicating the start of the period
        :param finish: datetime, indicating the end of the period
        :return: float, average number of places visited per day during period
        """
        num_days = self.__num_days(start, finish)
        num_recordings = 0

        for dt in self.start_times:
            if start <= dt <= finish:
                num_recordings += 1

        return num_recordings / num_days

    def median_dist_between_coordinates(self):
        """ (self: Person) -> float
        Returns the median distance traveled between two consecutive locations
        :return: float, median distance traveled between consecutive locations
        """
        return np.median(self.__all_distances())

    def avg_dist_between_coordinate(self):
        """ (self: Person) -> float
        Returns the average distance traveled between two consecutive locations
        :return: float, average distance traveled between consecutive locations
        """
        return np.average(self.__all_distances())

    @staticmethod
    def __distance(p1, p2):
        """ (np.array, np.array) -> float
        Computes the distance, in km, between two coordinates (latitude,
        longitude) using the Haversine formula.
        :param p1: np.array, of shape (1,2) representing (latitude,
        longitude) for the first point
        :param p2: np.array, of shape (1,2) representing (latitude,
        longitude) for the second point
        :return: float, distance, in km, between the two coordinates
        """
        radius = 6373.0  # radius of the earth
        dlat = radians(p1[0] - p2[0])
        dlong = radians(p1[1] - p2[1])
        alpha = radians(p1[0])
        beta = radians(p2[0])

        # computing the distance between the current and previous coordinates
        temp = sin(dlat/2) ** 2 + cos(alpha) * cos(beta) * sin(dlong/2) ** 2
        return radius * (2 * atan2(sqrt(temp), sqrt(1 - temp)))

    def __all_distances(self):
        """ (self: Person) -> np.array
        Computes the distance travelled between consecutive locations.
        The returned array is of shape (number of places visited - 1,)
        :return: np.array, where element i is the distance between location[
        i] and location[i+1] visited
        """

        # to hold the distance between consecutive locations visited
        distances = np.zeros(self.locations.shape[0] - 1)

        # looping through the (lat, long) pairs, computing their distance
        for i in range(1, self.locations.shape[0]):
            prev = self.locations[i - 1, :]
            current = self.locations[i, :]
            distances[i - 1] = self.__distance(prev, current)

        return distances

    def median_time_at_loc(self):
        """ (self: Person) -> float
        Returns the median time spent at all locations visited
        :return: float, median time spent at a location (measured in s)
        """
        return np.median(self.durations)

    def avg_time_at_loc(self):
        """ (self: Person) -> float
        Returns the average time spent at a location
        :return: float, average time spent at a location (measured in s)
        """
        return np.average(self.durations)


if __name__ == '__main__':
    filename = 'data/person1.csv'
    p = Person(filename)

    print(p.avg_num_recordings_per_day())
    start = p.start_times[12]
    finish = p.start_times[12]
    print(p.avg_num_recordings_in_period(start, finish))
