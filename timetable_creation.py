"""
Модуль генерации расписания
"""
import requests
from bs4 import BeautifulSoup
import re
import itertools
import random
import csv
import time
import datetime
from dateutil.rrule import rrule, MONTHLY, DAILY


class Flight:
    """
    Класс рейса между двумя городами.
    Хранит города отправления и назначения, а также расписания полетов.
    """

    def __init__(self, destination_city, departure_city, start_date, end_date):
        self.destination_city = destination_city
        self.departure_city = departure_city

        self.flight_time = TimeCreator(start_date, end_date)
        self.period_date, self.random_date = self.flight_time.generate()


class TimeCreator:
    """
    Класс генерации расписания рейсов.
    Генерирует случайные даты. Переодичные: 2 по неделям и 2 по месяцам, и 5 случайных.
    Главные функции: random_weekdays, random_monthdays, random_days и generate.
    """

    WEEKDAYS = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    TIMEFORMAT = '%d-%m-%Y %H:%M'

    def __init__(self, start_date, end_date):
        self.start_date, self.end_date = start_date, end_date
        self.weekdays, self.monthdays, self.days_random = [[] for _ in range(3)]

    def random_weekdays(self):
        """
        Фукнция генерации двух случайных дней недели

        @return: две пары в формате (weekdays, time)
        """
        weekdays = random.sample(list(TimeCreator.WEEKDAYS.values()), 2)
        self.weekdays = [(day, self.random_date()) for day in weekdays]

    def random_monthdays(self):
        """
        Фукнция генерации двух случайных дней месяца

        @return: две пары в формате (monthday, time)
        """
        monthdays = random.sample(range(1, 29), 2)
        self.monthdays = [(day, self.random_date()) for day in monthdays]

    def random_days(self):
        """
        Фукнция генерации пяти случайных дат, которые не совпадают с переодичными

        @return: 5 случайных дат в формате '%d-%m-%Y %H:%M'
        """
        if not self.weekdays:
            self.random_weekdays()
        if not self.monthdays:
            self.random_monthdays()

        rand_days = []
        months = self.get_month()
        for index in range(len(months) - 1):
            days = [day for day in self.get_days(months[index], months[index + 1], '%Y-%m-%d')]

            available_date = [datetime.datetime.strftime(day, '%d-%m-%Y') for day in days
                              if day.day not in [day for day, time in self.monthdays] and
                              TimeCreator.WEEKDAYS[day.weekday()] not in [weekday for weekday, time in self.weekdays]]
            rand_days.extend(random.sample(available_date, 5))

        self.days_random = rand_days

    def generate(self):
        """
        Главная функция генерации дат для одной пары городов

        @return: список дат вылетов для одной пары городов
        """
        self.random_weekdays()
        self.random_monthdays()
        self.random_days()

        random_days = self.time_append(self.days_random)

        return self.weekdays + self.monthdays, random_days

    @staticmethod
    def random_date(start='25-02-2021 00:00', end='25-02-2021 23:59', mode='time'):
        """
        Функция генерации случайной даты и время

        @param start: нижняя граница генерации
        @param end: верхняя граница генерации
        @param mode: формат генерации (TIME, DATE, DATETIME)
        @return: в зависимости от mode возвращает дату, время или дата+время
        """
        formats = {'date': '%d-%m-%Y', 'time': '%H:%M', 'datetime': '%d-%m-%Y %H:%M'}

        stime = time.mktime(time.strptime(start, TimeCreator.TIMEFORMAT))
        etime = time.mktime(time.strptime(end, TimeCreator.TIMEFORMAT))

        ptime = stime + random.random() * (etime - stime)

        return time.strftime(formats[mode], time.localtime(ptime))

    def get_month(self):
        """
        Функция получения всех месяцев между двумя датами

        @return: список, содержащий первый день каждого месяца между self.start и self.end
        """
        date_start = datetime.datetime.strptime(self.start_date, TimeCreator.TIMEFORMAT)
        date_end = datetime.datetime.strptime(self.end_date, TimeCreator.TIMEFORMAT)

        months = [dt for dt in rrule(MONTHLY, dtstart=date_start, until=date_end)]
        return [datetime.date(dt.year, dt.month, 1) for dt in months]

    def time_append(self, dates, repeat=False):
        """
        Функция прибавления к дате случайного времени

        @param dates: список дат
        @param repeat: формат прибавления (repeat == True: ко всем датам прибавляется одно время)
        @return: список элементов в формате дата+время
        """
        if repeat:
            timedelta = self.random_date()
            return [' '.join([date, timedelta]) for date in dates]
        else:
            return [' '.join([date, self.random_date()]) for date in dates]

    def get_days(self, start=None, end=None, time_format='%d-%m-%Y %H:%M'):
        """
        Фукнция получения всех дней между двумя датами

        @param start: нижняя граница генерации
        @param end: верхняя граница генерации
        @param time_format: формат генерируемых дат
        @return: список всех дней между заданными датами
        """
        start = start or self.start_date
        end = end or self.end_date

        if isinstance(start, datetime.date):
            start = datetime.date.strftime(start, time_format)
            end = datetime.date.strftime(end, time_format)

        return [dt for dt in rrule(freq=DAILY,
                                   dtstart=datetime.datetime.strptime(start, time_format),
                                   until=datetime.datetime.strptime(end, time_format))]


class TimetableCreator:
    """
    Главный класс генерации расписания между 2 рейсами.
    Создает случайное расписания для рейсов между 100 крупнейшими городами Европы.
    """

    URL = "https://ru.wikipedia.org/wiki/%D0%93%D0%BE%D1%80%D0%BE%D0%B4%D0%B0_%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D1%8B_%D1%81_%D0%BD%D0%B0%D1%81%D0%B5%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5%D0%BC_%D0%B1%D0%BE%D0%BB%D0%B5%D0%B5_500_%D1%82%D1%8B%D1%81%D1%8F%D1%87_%D1%87%D0%B5%D0%BB%D0%BE%D0%B2%D0%B5%D0%BA"
    fieldnames = ['departure_city', 'destination_city', 'date', 'frequency']

    def __init__(self, start, end, output_file="flights.csv"):
        self.start, self.end, self.output_file = start, end, output_file
        self.result = []

    @staticmethod
    def get_cities_pair():
        """
        Фукнция генерации пар из 100 крупнейших городов Европы

        @return: список комбинаций пар из 100 крупнейших городов Европы
        """
        r = requests.get(TimetableCreator.URL)
        soup = BeautifulSoup(r.text, 'html.parser')

        rows = [row for row in soup.find_all('td')]
        cities = [rows[i].text.strip() for i in range(1, len(rows), 5)]

        # Обрезаем все лишнее в названии городов и удаляю города, названия которых состоят из
        # нескольких слов(будет сложно находить в тексте при помощи re)
        for index, city in enumerate(cities):
            if city.count('-') or city.count(' '):
                cities.remove(city)

            space_index = re.search(r'\s[\(|\[]', city)
            if space_index:
                cities[index] = city[:space_index.start()]

        # Получаем список всех комбинаций между городами
        combinations = list(itertools.combinations(cities, 2))
        # По заданию между некоторыми городами не должно быть связей, удаляю 100 случайных путей
        for _ in range(100):
            combinations.remove(random.choice(combinations))
        # Добавляем зеркальные пути
        return combinations + [(sec, fir) for fir, sec in combinations]

    @staticmethod
    def flight_timetable(pair):
        """
        Фукнция генерации расписания для 1 пары городов

        @param pair: пара городов
        @return: список, содержащий расписания для пары городов
        """
        depar, dest = pair.destination_city, pair.departure_city
        period_date, random_date = pair.period_date, pair.random_date

        for_period = [{'departure_city': depar, 'destination_city': dest,
                               'date': date, 'frequency': period} for period, date in period_date]
        for_rand = [{'departure_city': depar, 'destination_city': dest,
                     'date': date, 'frequency': None} for date in random_date]

        return for_period + for_rand

    def pair_timetable(self):
        """
        Фукнция генерации рейсов между двумя всеми парами городов

        @return: список с рейсами между всеми городами
        """
        result = []
        for dest, depar in self.get_cities_pair():
            result.append(Flight(dest, depar, self.start, self.end))
        return result

    def generation(self):
        """
        Фукнция генерации расписания для всех ресов и его записи в файл
        """
        for pair in self.pair_timetable():
            self.result += self.flight_timetable(pair)

        with open(file=self.output_file, mode='w', encoding='utf8', newline='') as ff:
            writer = csv.DictWriter(ff, TimetableCreator.fieldnames)
            writer.writeheader()
            writer.writerows(self.result)


if __name__ == '__main__':
    timetable = TimetableCreator('10-04-2021 00:00', '10-10-2021 00:00')
    timetable.generation()