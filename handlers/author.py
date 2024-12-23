from aiogram import Bot, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from core.database import Session, Work, User
from core.utils import check_role, get_owner_info
from states.states import AuthorStates
from core.config import MAX_WORK_LENGTH

# Изменим константу на более безопасное значение
MAX_WORK_LENGTH = 3500  # Можно вынести в config.py

async def submit_work(message: types.Message, state: FSMContext):
    if not await check_role(message.from_user.id, 'author'):
        owner_info = await get_owner_info()
        if owner_info:
            await message.reply(
                f"У вас нет прав для публикации работ. "
                f"Обратитесь к владельцу бота ({owner_info}) для получения роли автора."
            )
        else:
            await message.reply("Система еще не настроена. Владелец не назначен.")
        return
    
    await message.reply(
        "Введите название вашей работы:\n"
        f"(Максимальная длина текста работы - {MAX_WORK_LENGTH} символов)"
    )
    await state.set_state(AuthorStates.waiting_for_title)

async def process_title(message: types.Message, state: FSMContext):
    if len(message.text) > 100:
        await message.reply("Название слишком длинное. Максимальная длина - 100 символов.")
        return
        
    await state.update_data(title=message.text)
    await message.reply(
        "Теперь отправьте содержание вашей работы.\n"
        f"Вы можете:\n"
        f"1. Написать текст напрямую\n"
        f"2. Отправить текстовый файл (.txt)\n"
        f"Максимальная длина текста - {MAX_WORK_LENGTH} символов"
    )
    await state.set_state(AuthorStates.waiting_for_content)

async def process_work_content(message: types.Message, state: FSMContext):
    content = ""
    
    # Обработка текстового сообщения
    if message.text:
        content = message.text
    
    # Обработка файла
    elif message.document:
        try:
            # Проверяем расширение файла
            if not message.document.file_name.lower().endswith('.txt'):
                await message.reply(
                    "Пожалуйста, отправьте текстовый файл в формате .txt"
                )
                return
                
            # Скачиваем файл
            file = await message.bot.get_file(message.document.file_id)
            file_path = file.file_path
            downloaded_file = await message.bot.download_file(file_path)
            
            # Читаем содержимое файла
            content = downloaded_file.read().decode('utf-8')
        except Exception as e:
            await message.reply(
                "Произошла ошибка при чтении файла. "
                "Убедитесь, что файл в формате UTF-8 и попробуйте снова."
            )
            return
    else:
        await message.reply(
            "Пожалуйста, отправьте текст работы или текстовый файл (.txt)"
        )
        return

    # Проверка длины контента
    if len(content) > MAX_WORK_LENGTH:
        await message.reply(
            f"Текст работы слишком длинный.\n"
            f"Максимальная длина - {MAX_WORK_LENGTH} символов.\n"
            f"Ваш текст: {len(content)} символов."
        )
        return
        
    session = Session()
    try:
        data = await state.get_data()
        title = data['title']
        
        user = session.query(User).filter_by(user_id=message.from_user.id).first()
        work = Work(author_id=user.id, title=title, content=content, is_approved=False)
        session.add(work)
        session.commit()
        
        await state.clear()
        await message.reply(
            "Ваша работа отправлена на проверку модератору.\n"
            f"Длина текста: {len(content)} символов."
        )
        
        # уведомление модераторов
        moderators = session.query(User).filter_by(role='moderator').all()
        notification = (
            f"📝 Новая работа на проверку!\n"
            f"Название: {title}\n"
            f"Автор: @{message.from_user.username or message.from_user.id}\n"
            f"Длина текста: {len(content)} символов"
        )
        
        for moderator in moderators:
            try:
                await message.bot.send_message(moderator.user_id, notification)
            except:
                continue
                
    finally:
        session.close()