import datetime
import unittest
from copy import deepcopy
from unittest.mock import patch, Mock
from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent
import settings
from bot import Bot
import ticket_create as tc


def isolate_db(funk):
    def wrapper(*args, **kwargs):
        with db_session:
            funk(*args, **kwargs)
            rollback()

    return wrapper


class MyTestCase(unittest.TestCase):
    RAW_EVENT = {'type': 'message_new', 'object': {'message': {'peer_id': 177327125, 'text': ''}},
                 'group_id': 200916670}

    TEST_DATA = {'user_name': 'Дмитрий Смирнов',
                 'departure_city': 'Москва',
                 'destination_city': 'Берлин',
                 'date': '10-08-2021 07:54',
                 'ticket_count': 1}

    INPUTS = ['asdasd',
              'купить',
              'фывфывф',
              'москва',
              'берлин',
              datetime.datetime.now().strftime('%d-%m-%Y'),
              '1',
              '3',
              '/skip',
              'да',
              '89087413254']

    EXPECTED_OUTPUTS = [settings.DEFAULT_ANSWER,
                        settings.SCENARIO['ticket_buy']['steps']['step1']['text'],
                        settings.SCENARIO['ticket_buy']['steps']['step1']['failure_text'].format(departure=['Москва']),
                        settings.SCENARIO['ticket_buy']['steps']['step2']['text'],
                        settings.SCENARIO['ticket_buy']['steps']['step3']['text'],

                        #  По идее, в будущем тесты работать не будут =)
                        #  В таких случаях используют дату отталкиваясь от текущего дня.
                        #  1. Предлагаю в хендлер добавить проверку на текущую или прошлую дату.
                        #  2. Привязать тест к относительной дате. (текущая дата. Через модуль datetime)

                        #  что-то я ничего не понял) Вы имеете ввиду запретить пользователю бронировать билеты на
                        #  текущий день и отвести его под тесты? Если да, то я не очень понимаю как это сделать, потому
                        #  что хендлер в любом случае должен будет вернуть True для продолжения сценария. Может стоит
                        #  использовать какой-то специальный код для хэндлера, по типу "%test%", который он будет
                        #  получать вместо даты и возвращать True и записывать в "suitable_flights" фиксированный список?
                        #  И не могли бы вы объяснить почему тест не рабочий, а то я не очень понимаю)

                        settings.SCENARIO['ticket_buy']['steps']['step4']['text'].format(flights_to_print=
                                                                                         '1) 10-11-2001 23:10'),
                        settings.SCENARIO['ticket_buy']['steps']['step5']['text'],
                        settings.SCENARIO['ticket_buy']['steps']['step6']['text'],
                        settings.SCENARIO['ticket_buy']['steps']['step7']['text'].format(departure_city='Москва',
                                                                                         destination_city='Берлин',
                                                                                         date='10-11-2001 23:10',
                                                                                         ticket_count='3',
                                                                                         commentary='Комментарий пропущен'),
                        settings.SCENARIO['ticket_buy']['steps']['step8']['text'],
                        settings.SCENARIO['ticket_buy']['steps']['step9']['text']]

    def tests_run(self):
        count = 5
        events = [{}] * count
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = Mock(return_value=events)

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call({})
                assert bot.on_event.call_count == count

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            with patch('Timetable.get_departure_city', return_value=['Москва']):
                with patch('Timetable.get_date', return_value=['10-11-2001 23:10']):
                    bot = Bot('', '')
                    bot.api = api_mock
                    api_mock.users.get = Mock(return_value=[{'first_name': '', 'last_name': ''}])
                    bot.send_image = Mock()
                    bot.run()

        assert bot.send_image.call_count == 1
        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])

        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_image_generation(self):
        with patch('random.sample', return_value='27'):
            with patch('random.choice', return_value='RI11'):
                ticket = tc.TicketCreator(self.TEST_DATA)
                image = ticket.create()

        with open('../files/ticket_example.png', 'rb') as expected_image:
            expected_bytes = expected_image.read()

        assert image.read() == expected_bytes


if __name__ == '__main__':
    unittest.main()
