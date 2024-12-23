from aiogram import Bot, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from core.database import Session, Work, User
from core.utils import check_role, get_owner_info
from datetime import datetime

async def review_works(message: types.Message):
    if not await check_role(message.from_user.id, 'moderator'):
        owner_info = await get_owner_info()
        if owner_info:
            await message.reply(f"У вас нет прав для проверки работ. Обратитесь к владельцу бота ({owner_info})")
        else:
            await message.reply("Система еще не настроена. Владелец не назначен.")
        return
    
    session = Session()
    try:
        works = session.query(Work).filter_by(is_approved=False).all()
        if not works:
            await message.reply("Нет работ для проверки.")
            return
            
        for work in works:
            buttons = [
                [
                    types.InlineKeyboardButton(text="Одобрено", callback_data=f"approve_{work.id}"),
                    types.InlineKeyboardButton(text="Отказано", callback_data=f"reject_{work.id}")
                ]
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
            
            # Ограничиваем длину контента
            max_content_length = 3500  # Оставляем запас для заголовка и форматирования
            content = work.content
            if len(content) > max_content_length:
                content = content[:max_content_length] + "...\n[Текст слишком длинный. Показана только часть]"
            
            try:
                await message.reply(
                    f"Работа: {work.title}\n\n{content}", 
                    reply_markup=keyboard
                )
            except Exception as e:
                await message.reply(
                    f"Ошибка при отправке работы '{work.title}' (ID: {work.id}). "
                    f"Возможно, сообщение слишком длинное."
                )
    finally:
        session.close()

async def approve_work(callback: types.CallbackQuery):
    session = Session()
    try:
        work_id = int(callback.data.split('_')[1])
        work = session.query(Work).filter_by(id=work_id).first()
        if work:
            work.is_approved = True
            session.commit()
            await callback.message.answer(f"Работа '{work.title}' одобрена.")
            
            # уведомление автора
            author = session.query(User).filter_by(id=work.author_id).first()
            if author:
                try:
                    await callback.bot.send_message(
                        author.user_id,
                        f"✅ Ваша работа '{work.title}' была одобрена модератором!"
                    )
                except:
                    pass
                    
        await callback.answer()
    finally:
        session.close()

async def reject_work(callback: types.CallbackQuery):
    session = Session()
    try:
        work_id = int(callback.data.split('_')[1])
        work = session.query(Work).filter_by(id=work_id).first()
        if work:
            title = work.title
            author_id = work.author_id
            session.delete(work)
            session.commit()
            await callback.message.answer(f"Работа '{title}' отклонена.")
            
            # уведомление автора
            author = session.query(User).filter_by(id=author_id).first()
            if author:
                try:
                    await callback.bot.send_message(
                        author.user_id,
                        f"❌ Ваша работа '{title}' была отклонена модератором."
                    )
                except:
                    pass
                    
        await callback.answer()
    finally:
        session.close()

async def delete_work(message: types.Message):
    if not await check_role(message.from_user.id, 'moderator'):
        owner_info = await get_owner_info()
        if owner_info:
            await message.reply(f"У вас нет прав для удаления работ. Обратитесь к владельцу бота ({owner_info})")
        else:
            await message.reply("Система еще не настроена. Владелец не назначен.")
        return
    
    try:
        _, work_id = message.text.split()
        work_id = int(work_id)
    except (ValueError, IndexError):
        await message.reply("Используйте формат: /delete_work <id работы>")
        return
    
    session = Session()
    try:
        work = session.query(Work).filter_by(id=work_id).first()
        if not work:
            await message.reply("Работа с указанным ID не найдена.")
            return
        
        title = work.title
        session.delete(work)
        session.commit()
        
        await message.reply(f"Работа '{title}' (ID: {work_id}) успешно удалена.")
    finally:
        session.close()