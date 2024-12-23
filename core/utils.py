from core.database import Session, User

async def check_role(user_id: int, required_role: str) -> bool:
    """Проверка роли пользователя"""
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return False
        if user.role == 'banned':
            return False
        if user.role == 'owner':
            return True
        return user.role == required_role
    finally:
        session.close()

async def get_owner_info():
    """Получение информации о владельце"""
    session = Session()
    try:
        owner = session.query(User).filter_by(role='owner').first()
        return f"id{owner.user_id}" if owner else None
    finally:
        session.close()

def split_text(text: str, max_length: int = 4096):
    """Разделение длинного текста на части"""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]