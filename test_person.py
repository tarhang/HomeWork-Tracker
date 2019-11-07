import unittest
from person import Person
from datetime import datetime
from dateutil.tz import tzoffset


class TestPerson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename1 = 'data/person1.csv'
        cls.p1 = Person(filename1)

    def test_init(self):
        # asserting initializations
        self.assertEqual(len(self.p1.durations), 549)
        self.assertEqual(self.p1.locations.shape, (549, 2))
        self.assertEqual(len(self.p1.durations), 549)

        # asserting array contents
        self.assertEqual(self.p1.locations[0, 0], -49.326958)
        self.assertEqual(self.p1.start_times[0],
                         datetime(2013, 12, 25, 11, 47,
                                  tzinfo=tzoffset('d', -10800)))
        self.assertEqual(self.p1.durations[0], 1186.491)

        # asserting fake input
        fake_filename = 'data/fake.csv'
        self.assertRaises(FileNotFoundError, Person, fake_filename)

    def test_avg_num_recordings_per_day(self):
        avg_num_places = 6.949367088607595
        self.assertAlmostEqual(self.p1.avg_num_recordings_per_day(), avg_num_places)

    def test_avg_num_recordings_in_period(self):
        s = self.p1.start_times[12]
        f1 = self.p1.start_times[12]
        f2 = self.p1.start_times[13]

        self.assertAlmostEqual(self.p1.avg_num_recordings_in_period(s, f1), 1)
        self.assertAlmostEqual(self.p1.avg_num_recordings_in_period(s, f2), 2)

    def test_median_dist_between_coordinates(self):
        med_d = 0.46527191751212393
        self.assertAlmostEqual(self.p1.median_dist_between_coordinates(),med_d)

    def test_avg_dist_between_coordinate(self):
        avg_dist = 34.738759700908595
        self.assertAlmostEqual(self.p1.avg_dist_between_coordinate(), avg_dist)

    def test_median_time_at_loc(self):
        med_time = 1186.491
        self.assertAlmostEqual(self.p1.median_time_at_loc(), med_time)

    def test_avg_time_at_loc(self):
        avg_time = 10420.86867941712
        self.assertAlmostEqual(self.p1.avg_time_at_loc(), avg_time)


if __name__ == '__main__':
    unittest.main()
