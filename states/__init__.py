# States package
from aiogram.fsm.state import State, StatesGroup

class MailStates(StatesGroup):
    confirm_replacement = State()
    confirm_deletion = State()
