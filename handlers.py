"""
Модуль хэндлеров проверки сообщений пользователей

    telephone_number - проверка правильности номера телефона
    count - проверка количества покупаемых билетов
    date - проверка правильности даты
    confirmation - проверка сообщения о подтверждении данных
    departure_city - проверка города отправления
    destination_city - проверка города назначения
    comment - проверка комментария
    flight_number - проверка номера рейса
    restart - проверка ответа о рестарте сценария
"""

import re
import datetime
from pathlib import Path

import Timetable as tt
from ticket_create import TicketCreator

re_count = re.compile(r'\b[1-5]\b')
re_date = re.compile(r'\b(?:0?[1-9]|[12][0-9]|3[01])-(?:0?[1-9]|1[0-2])-([0-2][0-9][0-9][0-9])\b')
re_phone = re.compile(r'\b\+?[78][-(]?\d{3}\)?-?\d{3}-?\d{2}-?\d{2}\b')

BASEDIR = Path(__file__).resolve().parent


def telephone_number(string, context):
    """
    Хэндлер проверки правильности ввода номера телефона

    @param string: сообщение пользователя
    @param context: словарь для хранения полученной информации
    @return: True - если в сообщении присутствует номер телефона
    """
    string = '8' + string if len(string) == 10 else string
    telephone = re.search(re_phone, string)
    if telephone:
        context['telephone_number'] = telephone[0]
        return True
    return False


def count(string, context):
    """
    Хэндлер проверки правильности ввода количества билетов для покупки

    @param string:
    @param context:
    @return: True - если сообщение содержит число от 1 до 5
    """
    ticket_count = re.search(re_count, string)
    if ticket_count:
        context['ticket_count'] = ticket_count[0]
        return True
    return False


def date(string, context):
    """
    Хэндлер проверки наличия даты в сообщении пользователя и её правильности

    @param string: сообщение пользователя
    @param context: словарь для хранения полученной информации
    @return: True - если в сообщении присутствует дата позднее текущей в нужном формате
    """
    departure_date = re.search(re_date, string)
    if departure_date:
        # На случай, если пользователь введет несуществующую дату
        date = datetime.datetime.strptime(departure_date[0], tt.DATE)
        if date.date() >= datetime.datetime.now().date():
            context['departure_date'] = departure_date[0]
            context['suitable_flights'] = tt.get_date(context['departure_city'], context['destination_city'],
                                                      departure_date[0])
            context['flights_to_print'] = tt.dict_formatter(context['suitable_flights'])
            return True

    return False


def confirmation(string, context):
    """
    Хэндлер проверки правильности ответа пользователя на сообщение о подтверждении данных

    @param string: сообщение пользователя
    @param context: словарь для хранения полученной информации
    @return: True - если ответом является 'да' или 'нет'
    """
    if string.lower() in ['да', 'нет']:
        context['can_continue'] = string.lower() == 'да'
        return True
    return False


def departure_city(string, context):
    """
    Хэндлер проверки наличия в сообщении города отправления

    @param string: сообщение пользователя
    @param context: словарь для хранения полученной информации
    @return: True - если в сообщении присутствует город отправления в доступных формах
    """
    cities = tt.get_departure_city()
    context['departure'] = list(set(cities))
    for city, reformat in tt.reformat_city(cities):
        departure_city = re.search(r'\b{}'.format(reformat.lower()), string.lower())
        if departure_city:
            context['departure_city'] = city
            context['destination'] = list(tt.get_destination(city))
            return True
    return False


def destination_city(string, context):
    """
    Хэндлер проверки наличия в сообщении города назначения и рейса между ним и городом отправления

    @param string: сообщение пользователя
    @param context: словарь для хранения полученной информации
    @return: True - если в сообщении присутствует город назначения в доступных формах и есть рейс до него
    """
    cities = tt.get_destination_city()
    for city, reformat in tt.reformat_city(cities):
        destination_city = re.search(r'\b{}'.format(reformat.lower()), string.lower())
        if destination_city:
            context['destination_city'] = city
            return True
    return False


def comment(string, context):
    """
    Хэндлер проверки правильности ввода комментария

    @param string: сообщение пользователя
    @param context: словарь для хранения полученной информации
    @return: True - если длина сообщения меньше или равно 40
    """
    if len(string) < 41:
        context['commentary'] = 'Комментарий пропущен' if string == '/skip' else string
        return True
    return False


def flight_number(string, context):
    """
    Хэндлер проверки правильности ввода номера рейса

    @param string: сообщение пользователя
    @param context: словарь для хранения полученной информации
    @return: True - если сообщение содержит число от 1 до 5
    """
    flight_number = re.search(re_count, string)
    if flight_number:
        number = flight_number[0]
        context['date'] = context['suitable_flights'][int(number) - 1]
        return True
    return False


def restart(string, context):
    """
    Хэндлер проверки правильности ответа пользователя на сообщение о рестарте сценария

    @param string: сообщение пользователя
    @param context: словарь для хранения полученной информации
    @return: True - если ответом является 'да' или 'нет'
    """
    if string in ['да', 'нет']:
        context['restart'] = 'ticket_buy' if string == 'да' else None
        context['can_continue'] = True
        return True
    return False


def generate_image(string, context):
    ticket = TicketCreator(context)
    return ticket.create()

