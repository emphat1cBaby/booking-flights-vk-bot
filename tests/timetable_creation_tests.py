import unittest
from unittest.mock import patch
from timetable_creation import TimetableCreator
import os


class MyTestCase(unittest.TestCase):
    EXMPL_ARR = ([('Wednesday', '07:34'), (16, '21:44')], ['24-04-2021 18:08'])
    CITIES = [('Москва', 'Берлин'), ('Берлин', 'Москва')]

    RESULT_FILE = 'result.csv'

    def test(self):
        with patch('timetable_creation.TimetableCreator.get_cities_pair', return_value=self.CITIES):
            with patch('timetable_creation.TimeCreator.generate', return_value=self.EXMPL_ARR):
                timetable = TimetableCreator('10-04-2021 00:00', '10-10-2021 00:00', self.RESULT_FILE)
                timetable.generation()

        with open('../files/expected.csv', 'rb') as ff:
            with open(self.RESULT_FILE, 'rb') as sf:
                assert ff.read() == sf.read()

        os.remove(self.RESULT_FILE)

if __name__ == '__main__':
    unittest.main()
