import datetime
import requests
import vk_api
from pony.orm import db_session
from vk_api.bot_longpoll import VkBotLongPoll
import random
import logging
import handlers
from models import UserState, Ticket

try:
    import settings
except ImportError:
    exit('DO cp settings.py.default to settings.py')

log = logging.getLogger("bot")


def create_log():
    file_handler = logging.FileHandler(filename='logger.log', encoding='UTF8')
    file_handler_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt='%d-%m-%Y %H:%M')
    file_handler.setFormatter(file_handler_formatter)
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler_formatter = logging.Formatter("%(levelname)s %(message)s")
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(stream_handler_formatter)

    log.addHandler(file_handler)
    log.addHandler(stream_handler)

    log.setLevel(logging.DEBUG)


class Bot:

    def __init__(self, token, group_id):
        self.token = token
        self.group_id = group_id

        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)

        self.api = self.vk.get_api()

    def run(self):
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception:
                log.exception("event handling error")

    @db_session
    def on_event(self, event):
        if event.type != vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW:
            log.info('Unknown event %s', event.type)
            return
        user_id = event.object.message['peer_id']
        text = event.object.message['text']

        state = UserState.get(user_id=str(user_id))
        # Команда, позволяющая пользователю выйти с любой стадии сценария
        if text == '/exit':
            if state is not None:
                self.exit_from_state(user_id, state)
            else:
                self.send_message('На данный момент вы не находитесь ни в каком сценарии', user_id)
        else:
            # Ищем интенты
            for intent in settings.INTENTS:
                # Если находим
                if any(token in text.lower() for token in intent['tokens']):
                    # Если можно обойтись коротким ответом, отвечаем, не выходя их текущего сценария
                    if intent['answer']:
                        self.send_message(intent['answer'], user_id)
                    else:
                        # Иначе покидаем текущий сценарий
                        if state is not None:
                            self.exit_from_state(user_id, state)
                        # Начинаем новый
                        self.scenario_start(intent['scenario'], user_id, text)
                    break
            else:
                # Если не находим интенты, продолжаем текущий сценарий, либо возвращем default answer
                if state is not None:
                    self.continue_scenario(user_id, text, state=state)
                else:
                    self.send_message(settings.DEFAULT_ANSWER, user_id)

    def scenario_start(self, scenario_name, user_id, text):
        scenario = settings.SCENARIO[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        user = self.api.users.get(user_ids=user_id)[0]
        self.send_step(step, user_id, text, context={})
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step,
                  context=dict(can_continue=True, user_name=f"{user['first_name']} {user['last_name']}"))

    def continue_scenario(self, user_id, text, state):
        step = settings.SCENARIO[state.scenario_name]['steps'][state.step_name]

        handler = getattr(handlers, step['handler'])
        if handler(string=text, context=state.context):
            # Проверяю небоходим ли рестарт сценария
            if 'restart' in state.context:
                # Если да, запускаю сценарий заново
                if state.context['restart'] is not None:
                    self.scenario_start(state.context['restart'], user_id, text)
                # Если пользователь отказался, покидаю сценарий
                else:
                    self.exit_from_state(user_id, state)
            # Рестарт не нужен
            else:
                # Определяю следующий шаг
                next_step_name = step['next_step'] if state.context['can_continue'] else 'restart'
                next_step = settings.SCENARIO[state.scenario_name]['steps'][next_step_name]

                self.send_step(next_step, user_id, text, state.context)
                # проверяю can_continue чтобы сработал шаг 'return'
                if next_step['next_step'] or not state.context['can_continue']:
                    state.step_name = next_step_name
                else:
                    Ticket(user_id=str(user_id),
                           departure_city=state.context['departure_city'],
                           destination_city=state.context['destination_city'],
                           date=datetime.datetime.strptime(state.context['date'], '%d-%m-%Y %H:%M'),
                           ticket_count=state.context['ticket_count'],
                           commentary=state.context['commentary'])
                    state.delete()
        else:
            self.send_message(step['failure_text'].format(**state.context), user_id)

    def exit_from_state(self, user_id, state):
        self.send_message('Вы успешно вышли из сценария', user_id)
        state.delete()

    def send_message(self, text_to_send, user_id):
        self.api.messages.send(message=text_to_send,
                               random_id=random.randint(0, 2 ** 20),
                               peer_id=user_id)

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)
        attachment = f"photo{image_data[0]['owner_id']}_{image_data[0]['id']}"

        self.api.messages.send(attachment=attachment,
                               random_id=random.randint(0, 2 ** 20),
                               peer_id=user_id)

    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_message(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(image, user_id)


if __name__ == "__main__":
    create_log()
    bot = Bot(settings.TOKEN, settings.GROUP_ID)
    bot.run()


