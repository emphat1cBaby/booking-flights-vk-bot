from pony.orm import Database, Required, Json
from settings import DB_CONFIG
from datetime import datetime

# psql \! chcp 1251 - смена кодировки
db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class Ticket(db.Entity):
    user_id = Required(str)
    departure_city = Required(str)
    destination_city = Required(str)
    date = Required(datetime)
    ticket_count = Required(int)
    commentary = Required(str)


db.generate_mapping(create_tables=True)
