import os
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()  

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)

    threads = relationship('Thread', back_populates='user', cascade="all, delete-orphan")

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 

class Thread(Base):
    __tablename__ = 'threads'

    id = Column(String(32), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    user = relationship('User', back_populates='threads')
    messages = relationship('Message', back_populates='thread')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 

class Message(Base):
    __tablename__ = 'messages'

    id = Column(String(32), primary_key=True)
    thread_id = Column(String(32), ForeignKey('threads.id'), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', or 'system'
    content = Column(Text, nullable=False)
    feedback = Column(Boolean)
    created_at = Column(DateTime, default=datetime.now())

    thread = relationship('Thread', back_populates='messages')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 

class Assistant(Base):
    __tablename__ = 'assistants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    openai_assistant_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 

class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    openai_file_id = Column(String(255), unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    purpose = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 
    

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


with Session() as session:
    test_user = session.query(User).filter_by(username="testUser").first()
    if not test_user:
        test_user = User(
            username = "testUser",
            email = "daviddflix@gmail.com",
            password_hash = "admin123"
        )
        session.add(test_user)
        session.commit()
        print('--- Test User Created ---')
    print('- Test user already exist -')