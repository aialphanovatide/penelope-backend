from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Message(Base):
    __tablename__ = 'message'

    id = Column(String, primary_key=True)
    thread_id = Column(String, ForeignKey('thread.id'))
    role = Column(String)
    content = Column(String)
    feedback = Column(String)  # New column

    thread = relationship("Thread", back_populates="messages")