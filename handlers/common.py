from aiogram import types
from aiogram.filters import Command
from core.database import Session, User
from core.config import ROLES

async def start_command(message: types.Message):
    """Обработчик команды /start"""
    session = Session()
    try:
        # проверка пользователя в базе
        user = session.query(User).filter_by(user_id=message.from_user.id).first()
        if not user:
            # выдача роли читателя при старте
            user = User(user_id=message.from_user.id, role='reader')
            session.add(user)
            session.commit()
            role = 'reader'
        else:
            role = user.role

        commands = [
            "/start - Показать это сообщение",
            "/works_list - Показать список всех работ",
            "/read_work <id> - Читать конкретную работу",
            "/read - Читать доступные работы"
        ]

        if role == 'author' or role == 'owner':
            commands.append("\nКоманды автора:")
            commands.append("/submit_work - Отправить работу на модерацию")

        if role == 'moderator' or role == 'owner':
            commands.append("\nКоманды модератора:")
            commands.append("/review - Просмотреть работы на модерации")
            commands.append("/delete_work <id> - Удалить работу")

        if role == 'owner':
            commands.append("\nКоманды владельца:")
            commands.append("/users - Список пользователей")
            commands.append("/setrole <username/id> <role> - Установить роль пользователю")

        welcome_text = (
            f"👋 Здравствуйте, {message.from_user.first_name}!\n\n"
            f"Добро пожаловать в бот для публикации и чтения литературных работ.\n"
            f"Ваша текущая роль: {ROLES.get(role, role)}\n\n"
            f"📝 Доступные вам команды:\n"
            f"{chr(10).join(commands)}\n\n"
        )

        if role != 'owner':
            welcome_text += (
                f"❗️ Для получения роли автора или модератора "
                f"обратитесь к владельцу бота."
            )
        else:
            welcome_text += (
                f"📌 Роли в системе:\n"
                f"• Читатель - может читать и оценивать работы\n"
                f"• Автор - может публиковать свои работы\n"
                f"• Модератор - проверяет работы перед публикацией\n"
                f"• Владелец - управляет ролями пользователей"
            )

        if role == 'banned':
            welcome_text = (
                f"⛔️ Вы заблокированы в системе.\n"
                f"Для разблокировки обратитесь к владельцу бота."
            )

        await message.reply(welcome_text)
        
    finally:
        session.close()
