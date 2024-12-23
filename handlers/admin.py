from aiogram import types
from aiogram.filters import Command
from core.database import Session, User
from core.config import ROLES
from core.utils import check_role, split_text, get_owner_info

async def init_owner(message: types.Message):
    session = Session()
    try:
        owner = session.query(User).filter_by(role='owner').first()
        if owner:
            await message.reply("Владелец бота уже назначен.")
            return
        
        user = User(user_id=message.from_user.id, role='owner')
        session.add(user)
        session.commit()
        await message.reply("Вы назначены владельцем бота.")
    finally:
        session.close()

async def list_users(message: types.Message):
    if not await check_role(message.from_user.id, 'owner'):
        await message.reply("У вас нет прав для просмотра списка пользователей.")
        return
    
    session = Session()
    try:
        users = session.query(User).all()
        if not users:
            await message.reply("В базе данных нет зарегистрированных пользователей.")
            return
        
        text = "👥 Список пользователей:\n\n"
        for user in users:
            try:
                user_info = await message.bot.get_chat(user.user_id)
                username = f"@{user_info.username}" if user_info.username else f"id{user.user_id}"
                name = user_info.full_name
            except:
                username = f"id{user.user_id}"
                name = "Неизвестно"
            
            text += (
                f"• {name} ({username})\n"
                f"  Роль: {ROLES.get(user.role, user.role)}\n"
                f"  ID: {user.user_id}\n"
                f"  Для выдачи роли: /setrole {user.user_id} <роль>\n\n"
            )
        
        text += (
            "📝 Доступные роли:\n"
            "• reader - читатель\n"
            "• author - автор\n"
            "• moderator - модератор\n"
            "• banned - заблокированный\n\n"
            "Пример: /setrole 123456789 author"
        )
        
        for part in split_text(text):
            await message.answer(part)
            
    finally:
        session.close()

async def set_user_role(message: types.Message):
    if not await check_role(message.from_user.id, 'owner'):
        await message.reply("У вас нет прав на выполнение этой команды.")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.reply("Неверный формат команды. Используйте: /setrole <user_id/username> <role>")
            return
        
        _, user_identifier, role = parts
        
        if role not in ROLES:
            await message.reply(f"Недопустимая роль. Доступные роли: {', '.join(ROLES.keys())}")
            return
            
        session = Session()
        try:
            if user_identifier.startswith('@'):
                username = user_identifier[1:]
                try:
                    user_info = await message.bot.get_chat(username)
                    user_id = user_info.id
                except:
                    await message.reply("Пользователь не найден.")
                    return
            else:
                try:
                    user_id = int(user_identifier)
                except ValueError:
                    await message.reply("Неверный формат ID пользователя.")
                    return
            
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                user = User(user_id=user_id, role=role)
                session.add(user)
            else:
                user.role = role
            session.commit()
            
            await message.reply(f"Роль {ROLES[role]} успешно установлена.")
            
            # уведомление того, кому назначили роль
            try:
                if role == 'banned':
                    notification = f"⛔️ Вы были заблокированы в системе."
                else:
                    notification = f"🔄 Ваша роль была изменена на: {ROLES[role]}"
                await message.bot.send_message(user_id, notification)
            except:
                pass
            
        finally:
            session.close()
            
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")