from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

engine = create_engine('sqlite:///bot_database.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    role = Column(String)

class Work(Base):
    __tablename__ = 'works'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    content = Column(String)
    theme = Column(String)
    genre = Column(String)
    age_restriction = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    rating = Column(Float, default=0.0)
    ratings_count = Column(Integer, default=0)

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey('works.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    rating = Column(Integer)
    review_text = Column(String)
    created_at = Column(String)

def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()

Base.metadata.create_all(engine)