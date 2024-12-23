from aiogram.fsm.state import State, StatesGroup

class AuthorStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()

class ModeratorStates(StatesGroup):
    review_work = State()

class RatingStates(StatesGroup):
    waiting_for_rating = State()
    waiting_for_review = State()