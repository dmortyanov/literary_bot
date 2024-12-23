from aiogram import Bot, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from core.database import Session, Work, User, Review
from core.utils import split_text
from states.states import RatingStates
from datetime import datetime

async def read_works(message: types.Message):
    session = Session()
    try:
        works = session.query(Work).filter_by(is_approved=True).all()
        if not works:
            await message.reply("Нет доступных работ для чтения.")
            return
        
        text = "📚 Доступные работы:\n\n"
        for work in works:
            author = session.query(User).filter_by(id=work.author_id).first()
            try:
                author_info = await message.bot.get_chat(author.user_id)
                author_mention = f"@{author_info.username}" if author_info.username else f"id{author.user_id}"
            except:
                author_mention = f"id{author.user_id}"
            
            rating_display = f"⭐{work.rating:.1f}" if work.ratings_count > 0 else "Нет оценок"
            text += (f"ID: {work.id}\n"
                    f"📖 Название: {work.title}\n"
                    f"✍️ Автор: {author_mention}\n"
                    f"📊 Рейтинг: {rating_display} ({work.ratings_count} оценок)\n\n")
        
        for part in split_text(text):
            await message.answer(part)
                
    finally:
        session.close()

async def rate_work(message: types.Message, state: FSMContext):
    try:
        work_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply("Используйте формат: /rate_work <id работы>")
        return
    
    session = Session()
    try:
        work = session.query(Work).filter_by(id=work_id, is_approved=True).first()
        if not work:
            await message.reply("Работа не найдена или не одобрена модератором.")
            return
        
        await state.update_data(work_id=work_id)
        
        buttons = [
            [types.InlineKeyboardButton(text=f"{'⭐' * i}", callback_data=f"rate_{i}")]
            for i in range(1, 6)
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.reply("Оцените работу от 1 до 5 звезд:", reply_markup=keyboard)
        await state.set_state(RatingStates.waiting_for_rating)
        
    finally:
        session.close()

async def process_rating(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split('_')[1])
    
    data = await state.get_data()
    work_id = data.get('work_id')
    
    await state.update_data(rating=rating, work_id=work_id)
    
    await callback.message.answer("Напишите свой отзыв о работе (или отправьте 'пропустить'):")
    await state.set_state(RatingStates.waiting_for_review)
    await callback.answer()

async def process_review(message: types.Message, state: FSMContext):
    session = Session()
    try:
        data = await state.get_data()
        work_id = data.get('work_id')
        rating = data.get('rating')
        
        if not work_id or not rating:
            await message.reply("Произошла ошибка. Пожалуйста, начните оценку заново.")
            await state.clear()
            return
            
        review_text = message.text if message.text.lower() != 'пропустить' else None
        
        work = session.query(Work).filter_by(id=work_id).first()
        user = session.query(User).filter_by(user_id=message.from_user.id).first()
        
        if work and user:
            if review_text:
                review = Review(
                    work_id=work_id,
                    user_id=user.id,
                    rating=rating,
                    review_text=review_text,
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                session.add(review)
            
            new_rating = (work.rating * work.ratings_count + rating) / (work.ratings_count + 1)
            work.rating = round(new_rating, 2)
            work.ratings_count += 1
            session.commit()
            
            response = f"Спасибо за вашу оценку! Текущий рейтинг работы: {work.rating}⭐ ({work.ratings_count} оценок)"
            if review_text:
                response += f"\nВаш отзыв сохранен: {review_text}"
            
            await message.reply(response)
            
            # уведомление автора
            author = session.query(User).filter_by(id=work.author_id).first()
            if author:
                notification = (
                    f"📊 Ваша работа '{work.title}' получила новую оценку: {rating}⭐\n"
                    f"Текущий рейтинг: {work.rating}⭐ ({work.ratings_count} оценок)"
                )
                if review_text:
                    notification += f"\nОтзыв: {review_text}"
                try:
                    await message.bot.send_message(author.user_id, notification)
                except:
                    pass
        
        await state.clear()
        
    finally:
        session.close()

async def works_list(message: types.Message):
    session = Session()
    try:
        works = session.query(Work).filter_by(is_approved=True).all()
        if not works:
            await message.reply("Нет доступных работ для чтения.")
            return
        
        text = "📚 Список доступных работ:\n\n"
        for work in works:
            rating_display = f"⭐{work.rating:.1f}" if work.ratings_count > 0 else "Нет оценок"
            text += f"ID: {work.id} - {work.title} ({rating_display}, {work.ratings_count} оценок)\n"
        
        text += "\nДля чтения конкретной работы используйте команду /read_work <id работы>"
        await message.answer(text)
        
    finally:
        session.close()

async def read_work(message: types.Message):
    try:
        work_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply("Используйте формат: /read_work <id работы>")
        return
    
    session = Session()
    try:
        work = session.query(Work).filter_by(id=work_id, is_approved=True).first()
        if not work:
            await message.reply("Работа не найдена или не одобрена модератором.")
            return
            
        # инфа об авторе
        author = session.query(User).filter_by(id=work.author_id).first()
        try:
            author_info = await message.bot.get_chat(author.user_id)
            author_mention = f"@{author_info.username}" if author_info.username else f"id{author.user_id}"
        except:
            author_mention = f"id{author.user_id}"
            
        header = (
            f"📖 {work.title}\n"
            f"✍️ Автор: {author_mention}\n"
            f"⭐ Рейтинг: {work.rating:.1f} ({work.ratings_count} оценок)\n"
            f"➖➖➖➖➖➖➖➖➖➖\n\n"
        )
        
        full_text = header + work.content
        
        # разбитие сообщения на части
        for part in split_text(full_text):
            await message.answer(part)
        
        # проверка на оценку пользователем
        user = session.query(User).filter_by(user_id=message.from_user.id).first()
        existing_review = session.query(Review).filter_by(
            work_id=work_id,
            user_id=user.id
        ).first()
        
        buttons = []
        if not existing_review:
            buttons.append([types.InlineKeyboardButton(text="Оценить работу", callback_data=f"start_rate_{work_id}")])
        buttons.append([types.InlineKeyboardButton(text="Посмотреть отзывы", callback_data=f"reviews_{work_id}")])
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            "Выберите действие:" if not existing_review else "Вы уже оценили эту работу. Можете посмотреть отзывы:",
            reply_markup=keyboard
        )
        
    finally:
        session.close()

async def start_rating(callback: types.CallbackQuery):
    try:
        parts = callback.data.split('_')
        if len(parts) != 3:  # проверяем что формат "start_rate_ID"
            await callback.answer("Неверный формат данных", show_alert=True)
            return
            
        work_id = int(parts[2])  # берем ID из третьей части
        
        session = Session()
        try:
            # Проверяем, не оценивал ли пользователь уже эту работу
            user = session.query(User).filter_by(user_id=callback.from_user.id).first()
            existing_review = session.query(Review).filter_by(
                work_id=work_id,
                user_id=user.id
            ).first()
            
            if existing_review:
                await callback.message.answer("Вы уже оценивали эту работу!")
                await callback.answer()
                return
            
            buttons = [
                [types.InlineKeyboardButton(text="⭐", callback_data=f"rate_1_{work_id}"),
                 types.InlineKeyboardButton(text="⭐⭐", callback_data=f"rate_2_{work_id}"),
                 types.InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rate_3_{work_id}"),
                 types.InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rate_4_{work_id}"),
                 types.InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rate_5_{work_id}")]
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
            await callback.message.answer("Выберите оценку:", reply_markup=keyboard)
            await callback.answer()
            
        finally:
            session.close()
            
    except ValueError:
        await callback.answer("Ошибка при обработке ID работы", show_alert=True)
        return

async def process_rating(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split('_')
    rating = int(parts[1])
    work_id = int(parts[2])
    
    session = Session()
    try:
        # Проверяем, не оценивал ли пользователь уже эту работу
        user = session.query(User).filter_by(user_id=callback.from_user.id).first()
        existing_review = session.query(Review).filter_by(
            work_id=work_id,
            user_id=user.id
        ).first()
        
        if existing_review:
            await callback.message.answer("Вы уже оценивали эту работу!")
            await callback.answer()
            return
        
        await state.update_data(rating=rating, work_id=work_id)
        await callback.message.answer("Напишите свой отзыв о работе (или отправьте 'пропустить'):")
        await state.set_state(RatingStates.waiting_for_review)
        await callback.answer()
        
    finally:
        session.close()

async def show_reviews(callback: types.CallbackQuery):
    work_id = int(callback.data.split('_')[1])
    session = Session()
    try:
        reviews = session.query(Review).filter_by(work_id=work_id).all()
        if not reviews:
            await callback.message.answer("К этой работе пока нет отзывов.")
            await callback.answer()
            return
        
        text = "📝 Отзывы к работе:\n\n"
        for review in reviews:
            user = session.query(User).filter_by(id=review.user_id).first()
            try:
                user_info = await callback.bot.get_chat(user.user_id)
                user_mention = f"@{user_info.username}" if user_info.username else f"id{user.user_id}"
            except:
                user_mention = f"id{user.user_id}"
            
            text += (f"От: {user_mention}\n"
                    f"Оценка: {'⭐' * review.rating}\n"
                    f"Дата: {review.created_at}\n"
                    f"Отзыв: {review.review_text}\n\n")
        
        for part in split_text(text):
            await callback.message.answer(part)
        
        await callback.answer()
        
    finally:
        session.close()