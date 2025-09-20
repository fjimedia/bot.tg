from aiogram.fsm.state import StatesGroup, State

class States(StatesGroup):
    select_channel = State()    # Выбор канала
    select_duration = State()   # Выбор длительности
    enter_media = State()       # Добавление медиа (новое состояние)
    enter_text = State()        # Ввод текста объявления