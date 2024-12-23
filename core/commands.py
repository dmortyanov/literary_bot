from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from core.database import Session, User

async def get_commands_for_role(role: str) -> list[BotCommand]:
    """Возвращает список команд в зависимости от роли пользователя"""
    
    commands = [
        BotCommand(command="start", description="Показать информацию о боте и командах"),
        BotCommand(command="works_list", description="Показать список всех работ"),
        BotCommand(command="read_work", description="Читать конкретную работу по ID"),
        BotCommand(command="read", description="Читать доступные работы")
    ]
    
    if role == 'author' or role == 'owner':
        commands.append(
            BotCommand(command="submit_work", description="Отправить работу на модерацию")
        )
    
    if role == 'moderator' or role == 'owner':
        commands.extend([
            BotCommand(command="review", description="Просмотр работ на модерацию"),
            BotCommand(command="delete_work", description="Удалить работу")
        ])
    
    if role == 'owner':
        commands.extend([
            BotCommand(command="users", description="Список пользователей"),
            BotCommand(command="setrole", description="Установить роль пользователю"),
            BotCommand(command="init_owner", description="Инициализировать владельца бота")
        ])
    
    return commands

async def setup_commands(bot: Bot):
    """Установка команд для каждого пользователя индивидуально"""
    session = Session()
    try:
        users = session.query(User).all()
        
        for user in users:
            try:
                commands = await get_commands_for_role(user.role)
                await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=user.user_id))
            except Exception as e:
                print(f"Error setting commands for user {user.user_id}: {e}")
        
        default_commands = await get_commands_for_role('reader')
        await bot.set_my_commands(default_commands)
        
    finally:
        session.close()