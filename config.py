import os
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Text, Boolean
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
    """
    Represents a user in the system.

    Columns:
    - id (String): Primary key, unique identifier for the user.
    - username (String): Unique username, max 50 characters.
    - email (String): Unique email address, max 120 characters.
    - picture (String): URL or path to user's profile picture.
    - password_hash (String): Hashed password, max 255 characters.
    - created_at (DateTime): Timestamp of user creation.
    - updated_at (DateTime): Timestamp of last user update.
    - is_active (Boolean): Indicates if the user account is active.

    Relationships:
    - threads: One-to-many relationship with Thread model.

    Methods:
    - as_dict(): Returns a dictionary representation of the user, excluding password_hash.
    """
     
    __tablename__ = 'users'

    id = Column(String(255), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    picture = Column(String)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)

    threads = relationship('Thread', back_populates='user', cascade="all, delete-orphan")
    files = relationship('File', back_populates='user', cascade="all, delete-orphan")


    def as_dict(self):
            return {
                column.name: getattr(self, column.name)
                for column in self.__table__.columns
                if column.name != 'password_hash'
            }
    
class Thread(Base):
    """
    Represents a conversation thread.

    Columns:
    - id (String): Primary key, 32-character unique identifier for the thread.
    - user_id (String): Foreign key referencing the User model.
    - title (String): Human-readable name to identify the thread.
    - created_at (DateTime): Timestamp of thread creation.
    - updated_at (DateTime): Timestamp of last thread update.
    - is_active (Boolean): Indicates if this is the user's current active thread.

    Relationships:
    - user: Many-to-one relationship with User model.
    - messages: One-to-many relationship with Message model.

    Methods:
    - as_dict(): Returns a dictionary representation of the thread.
    """
        
    __tablename__ = 'threads'

    id = Column(String(32), primary_key=True)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)

    user = relationship('User', back_populates='threads')
    files = relationship('File', back_populates='thread', cascade="all, delete-orphan")
    messages = relationship('Message', back_populates='thread', cascade="all, delete-orphan")

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 
class Message(Base):
    """
    Represents a message within a thread.

    Columns:
    - id (String): Primary key, 40-character unique identifier for the message.
    - thread_id (String): Foreign key referencing the Thread model.
    - role (String): Role of the message sender ('user', 'assistant', or 'system').
    - content (Text): The content of the message.
    - feedback (Text): Any feedback associated with the message.
    - token_count (Integer): Count of tokens in the message.
    - created_at (DateTime): Timestamp of message creation.
    - updated_at (DateTime): Timestamp of last message update.

    Relationships:
    - thread: Many-to-one relationship with Thread model.
    - files: One-to-many relationship with File model.

    Methods:
    - as_dict(): Returns a dictionary representation of the message.
    """
        
    __tablename__ = 'messages'

    id = Column(String(40), primary_key=True)
    thread_id = Column(String(32), ForeignKey('threads.id'), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', or 'system'
    content = Column(Text, nullable=False)
    feedback = Column(Text)
    token_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    thread = relationship('Thread', back_populates='messages')
    files = relationship('File', back_populates='message', cascade="all, delete-orphan")

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Assistant(Base):
    """
    Represents an AI assistant.

    Columns:
    - id (Integer): Primary key, auto-incrementing identifier for the assistant.
    - openai_assistant_id (String): Unique identifier from OpenAI for the assistant.
    - name (String): Name of the assistant.
    - description (Text): Description of the assistant's capabilities or purpose.
    - created_at (DateTime): Timestamp of assistant creation.
    - updated_at (DateTime): Timestamp of last assistant update.

    Methods:
    - as_dict(): Returns a dictionary representation of the assistant.
    """
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
    """
    Represents a file in the system.

    Columns:
    - id (Integer): Primary key, auto-incrementing identifier for the file.
    - openai_file_id (String): Unique identifier from OpenAI for the file.
    - filename (String): Name of the file.
    - purpose (String): Purpose or type of the file (e.g., 'fine-tune', 'assistants').
    - mime_type (String): MIME type of the file.
    - size (Integer): Size of the file in bytes.
    - created_at (DateTime): Timestamp of file creation.
    - updated_at (DateTime): Timestamp of last file update.
    - user_id (String): Foreign key referencing the User model.
    - thread_id (String): Foreign key referencing the Thread model.
    - message_id (String): Foreign key referencing the Message model.

    Relationships:
    - user: Many-to-one relationship with User model.
    - thread: Many-to-one relationship with Thread model.
    - message: Many-to-one relationship with Message model.

    Methods:
    - as_dict(): Returns a dictionary representation of the file.
    """
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    openai_file_id = Column(String(255), unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    purpose = Column(String(50), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    thread_id = Column(String(32), ForeignKey('threads.id'), nullable=True)
    message_id = Column(String(40), ForeignKey('messages.id'), nullable=True)

    user = relationship("User", back_populates="files")
    thread = relationship("Thread", back_populates="files")
    message = relationship("Message", back_populates="files")

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


# with Session() as session:
#     test_user = session.query(User).filter_by(username="testUser").first()
#     if not test_user:
#         test_user = User(
#             id='107742922884470008787',
#             username = "testUser",
#             email = "daviddflix@gmail.com",
#             password_hash='google signin'
#         )
#         session.add(test_user)
#         session.commit()
#         print('--- Test User Created ---')
#     print('- Test user already exist -')