import datetime as dt
import random
from io import BytesIO
from pathlib import Path
from PIL import ImageDraw, Image, ImageFont
from os.path import normpath


BASEDIR = Path(__file__).resolve().parent


class TicketCreator:
    TIMEFORMAT = '%d-%m-%Y %H:%M'
    FLITHS = ['SU9', 'RI11', 'JS08', 'BY3', 'KO5', 'CV11']

    TEXT_POSITIONS = {
        # при создании директорий стоит избегать использования строковых методов.
        #  Ведь, для одной ОС, разделителем в директории является "/", а в другой "\".
        #  Предлагаю создавать директорию при помощи os.path.
        #  Возможно, в таком случае, мы сможем решить без использования модуля pathlib.
        #  какая-то проблема с getcwd в os.path, хотя пути абсолютно одинаковые, поэтому pathlib пришлось оставить,
        #  добавил normpath для разных ОС


        #  Такой фариант упростил бы нашу реализацию =)
        #  os.path.abspath('files/Roboto-Bold.ttf')
        #  os.path.abspath сам добавит текущую директорию к 'files/Roboto-Bold.ttf'.
        #  я, честно, пробовал огромное количество вариантов с модулем os.path, если использовать abspath,
        #  то выбрасывает ошибку
        #  Error
        #  Traceback (most recent call last):
        #   File "C:\Users\Dmitry\PycharmProjects\python_base\chat_bot\tests\tests.py", line 127, in test_image_generation
        #     image = ticket.create()
        #   File "C:\Users\Dmitry\PycharmProjects\python_base\chat_bot\ticket_create.py", line 69, in create
        #     font = ImageFont.truetype(normpath(fp), 18)
        #   File "C:\Users\Dmitry\PycharmProjects\python_base\chat_bot\venv\lib\site-packages\PIL\ImageFont.py", line 855, in truetype
        #     return freetype(font)
        #   File "C:\Users\Dmitry\PycharmProjects\python_base\chat_bot\venv\lib\site-packages\PIL\ImageFont.py", line 852, in freetype
        #     return FreeTypeFont(font, size, index, encoding, layout_engine)
        #   File "C:\Users\Dmitry\PycharmProjects\python_base\chat_bot\venv\lib\site-packages\PIL\ImageFont.py", line 211, in __init__
        #     self.font = core.getfont(
        #     OSError: cannot open resource
        #     И использовать модуль pathlib не моя идея, нашел здесь https://btfr.cc/ba3n
        #     Так что трогать пути здесь страшное дело, что не сделаешь, все поломается))


        # Странно при проверке os.path.abspath('files/Roboto-Bold.ttf') отдаёт такой же результат как
        # и str(BASEDIR/'files/Roboto-Bold.ttf')

        str(BASEDIR/'files/Roboto-Bold.ttf'): {
            'board': [(110, 220)],
            'last_call': [(115, 305)],
            'seat': [(335, 305), (775, 310)],
            'flight': [(535, 310)]
        },
        str(BASEDIR/'files/Roboto-Regular.ttf'): {
            'name': [(333, 123), (783, 123)],
            'dep': [(335, 180), (900, 240)],
            'des': [(535, 180), (900, 305)],
            'date': [(330, 240), (900, 185)],
            'time': [(535, 240), (785, 190)],
            'flight': [(785, 245)]
        }
    }

    def __init__(self, data: dict):
        self.data = data

    def generate_tickets(self):
        datetime = dt.datetime.strptime(self.data['date'], self.TIMEFORMAT)
        board, last_call = (datetime - dt.timedelta(minutes=40)).time(), (datetime - dt.timedelta(minutes=20)).time()
        seats = random.sample(range(1, 55), int(self.data['ticket_count']))

        # пожалуйста, обратите внимание, в этом месте кода, сейчас получаем ошибку.
        #  Т.к. в словаре self.data отсутствует ключ user_name.
        #  возможно вы в прошлый раз не закончили сценарий и user_name не добавился в context, потому что
        #  он единственный раз добавляется во время запуска start_scenario, вот код из bot.py
        #  user = self.api.users.get(user_ids=user_id)[0]
        #  self.send_step(step, user_id, text, context={})
        #  UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step,
        #            context=dict(can_continue=True, user_name=f"{user['first_name']} {user['last_name']}"))
        return {'name': self.data['user_name'],
                'dep': self.data['departure_city'],
                'des': self.data['destination_city'],
                'date': datetime.date().strftime('%d-%m-%Y'),
                'time': datetime.time().strftime('%H:%M'),
                'seat': ', '.join(str(seat) for seat in seats) if isinstance(seats, list) else seats,
                'flight': random.choice(self.FLITHS),
                'board': board.strftime('%H:%M'),
                'last_call': last_call.strftime('%H:%M')}

    def create(self):
        image = Image.open(normpath(BASEDIR/'files/ticket.jpg'))
        draw = ImageDraw.Draw(image)
        data_image = self.generate_tickets()

        for fp, elements in self.TEXT_POSITIONS.items():
            font = ImageFont.truetype(normpath(fp), 18)
            for name, positions in elements.items():
                for pos in positions:
                    draw.text(pos, str(data_image[name]), font=font, fill=(0, 0, 0))

        temp_file = BytesIO()
        image.save(temp_file, 'png')
        temp_file.seek(0)

        return temp_file


if __name__ == '__main__':
    TicketCreator({})
