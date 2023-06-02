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
