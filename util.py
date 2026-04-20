from aiogram.fsm.state import State, StatesGroup

# === СОСТОЯНИЯ ДЛЯ FSM ===
class WithdrawStates(StatesGroup):
    waiting_amount = State()
    waiting_method = State()
    waiting_details = State()
    waiting_confirm = State()

class ReviewStates(StatesGroup):
    waiting_rating = State()
    waiting_comment = State()
    waiting_anonymous = State()

class SupportStates(StatesGroup):
    waiting_message = State()
