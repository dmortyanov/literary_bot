from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import logging

from core.config import API_TOKEN
from core.database import Base, engine
from core.commands import setup_commands

from handlers import admin, moderator, author, reader, common
from states.states import AuthorStates, RatingStates

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

Base.metadata.create_all(engine)

def register_handlers():
    """Регистрация всех обработчиков"""

    dp.message.register(common.start_command, Command('start'))
    
    dp.message.register(admin.init_owner, Command('init_owner'))
    dp.message.register(admin.list_users, Command('users'))
    dp.message.register(admin.set_user_role, Command('setrole'))
    
    dp.message.register(moderator.review_works, Command('review'))
    dp.message.register(moderator.delete_work, Command('delete_work'))
    dp.callback_query.register(moderator.approve_work, F.data.startswith('approve_'))
    dp.callback_query.register(moderator.reject_work, F.data.startswith('reject_'))
    
    dp.message.register(author.submit_work, Command('submit_work'))
    dp.message.register(author.process_title, AuthorStates.waiting_for_title)
    dp.message.register(author.process_work_content, AuthorStates.waiting_for_content)
    
    dp.message.register(reader.works_list, Command('works_list'))
    dp.message.register(reader.read_work, Command('read_work'))
    dp.message.register(reader.read_works, Command('read'))
    dp.callback_query.register(reader.start_rating, F.data.startswith('start_rate_'))
    dp.callback_query.register(reader.process_rating, F.data.startswith('rate_'))
    dp.callback_query.register(reader.show_reviews, F.data.startswith('reviews_'))
    dp.message.register(reader.process_review, RatingStates.waiting_for_review)

async def main():
    """Главная функция запуска бота"""
    register_handlers()
    
    await setup_commands(bot)
    
    logging.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")