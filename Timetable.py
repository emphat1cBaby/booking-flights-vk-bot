"""
Модуль вспомогательных функций для модуля handlers.py

    get_departure_city - функция получения всех городов отправления из расписания
    get_destination_city - функция получения всех городов назначения из расписания
    reformat_city - функция обработки имен городов
    get_date - функция получения 5 ближайших к дате рейсов
    time_addition - фукнция сложения даты и времени
    get_destination - возвращает все города, куда есть рейсы из заданного города
    dict_formatter - функция форматирования словаря в строку
"""

import datetime
import csv
from pathlib import Path
import pandas
from os.path import normpath


ENDINGS = ['а', 'ь', 'е', 'ы', 'я', 'у', 'ки', 'и']
DATETIME = '%d-%m-%Y %H:%M'
DATE = '%d-%m-%Y'
TIME = '%H:%M'

BASEDIR = Path(__file__).resolve().parent


def get_departure_city():
    """
    Фукнция получения всех городов отправления

    @return: список городов из которых есть рейсы
    """
    # , при создании директорий стоит избегать использования строковых методов.
    #  Ведь, для одной ОС, разделителем в директории является "/", а в другой "\".
    #  Предлагаю создавать директорию при помощи os.path.
    #  Возможно, в таком случае, мы сможем решить без использования модуля pathlib.
    with open(file=normpath(BASEDIR/'files/flights.csv'), mode='r', encoding='utf8') as ff:
        # скипаю первую строку
        next(ff)
        reader = csv.reader(ff)
        departure = set([row[0] for row in reader])

    return list(departure)


def get_destination_city():
    """
    Функция получения всех городов назначения

    @return: множество всех городов куда есть рейсы
    """
    with open(file=normpath(BASEDIR/'files/flights.csv'), mode='r', encoding='utf8') as ff:
        next(ff)
        reader = csv.reader(ff)
        destination = set([row[1] for row in reader])

    return list(destination)


def reformat_city(cities: list):
    """
    Функция обработки названия городов

    @param cities: список городов для обработки
    @return: список имен городов, преобразованных в первую форму и с обрезанным окончанием
    """
    # Обрезаю окончания и привожу к нижнему регистру
    result = []
    for index, city in enumerate(cities):
        for end in ENDINGS:
            if city.endswith(end):
                result.append((city, city[:-len(end)]))
                break
            else:
                result.append((city, city))

    return result


def get_date(dep: str, dest: str, date: str):
    """
    Функция получения 5 ближайших к дате рейсов

    @param dep: город отправления
    @param dest: город назначения
    @param date: дата полученная от пользователя
    @return: 5 ближайших к дате рейсов
    """
    result, period_date = [[] for _ in range(2)]
    # Список именованных дней недели
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    # Просматриваю документ с распианием, ищу все полеты между городами
    with open(file=normpath(BASEDIR/'files/flights.csv'), mode='r', encoding='utf8') as ff:
        reader = csv.reader(ff)
        pairs = [row for row in reader if (dep, dest) == (row[0], row[1])]

    # Найденные пути делю на переодичные и случайные рейсы
    for depart, destin, time, period in pairs:
        if period.isdigit() or period in weekdays:
            period_date.append((time, period))
        else:
            if datetime.datetime.strptime(time, DATETIME) >= datetime.datetime.strptime(date, DATE):
                result.append(time)

    # Устанавливаю промежуток размером в месяц, начиная с введенной пользователем даты
    date_parse = datetime.datetime.strptime(date, DATE)
    last_date = date_parse + datetime.timedelta(days=30)

    days = pandas.date_range(date_parse, last_date, freq='D')
    # Среди дней ищу те, которые совпадают с переодичностью
    for day in days:
        day_parse = datetime.datetime.strptime(str(day), '%Y-%m-%d %H:%M:%S')
        day_week = weekdays[day_parse.weekday()]

        for time, day in period_date:
            if day_week == day or day_parse == day:
                result.append(time_addition(day_parse, time))

    # Сортирую по возрастанию и возвращаю 5 ближайших
    return sorted(result, key=lambda d: datetime.datetime.strptime(d, DATETIME))[:5]


def time_addition(date: datetime.date, time: datetime.time):
    """
    Фукнция сложения даты и времени

    @param date: дата в формате '%d-%m-%Y'
    @param time: время в формате '%H:%M'
    @return: сумма даты и времени в формате '%d-%m-%Y %H:%M'
    """
    deltatime = datetime.datetime.strptime(time, TIME)
    date += datetime.timedelta(hours=deltatime.hour, minutes=deltatime.minute)

    return date.strftime(DATETIME)


def get_destination(dep_city: str):
    """
    Возвращает все города, куда есть рейсы из dep_city

    @param dep_city: город отправления
    @return: множество городов в которые есть рейсы из dep_city
    """
    with open(file=normpath(BASEDIR/'files/flights.csv'), mode='r', encoding='utf8') as ff:
        reader = csv.reader(ff)
        result = [row[1] for row in reader if row[0] == dep_city]

    return set(result)


def dict_formatter(dates: dict):
    """
    Функция форматирования словаря в строку

    @param dates: словарь с датами в формате {'index': 'date'}
    @return: строка в формате
    1) date
    2) date
    3) date
    """
    return '\n'.join(f'{index}) {date}' for index, date in enumerate(dates, 1))