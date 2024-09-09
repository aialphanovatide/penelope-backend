# Messages routes

from flask import Blueprint
from http import HTTPStatus
from config import Session, Message, File
from app.utils.response_template import response_template
from app.penelope.penelope import penelope_manager


messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/messages/<thread_id>', methods=['GET'])
def get_messages(thread_id):
    """
    Get all messages with their associated files for a thread, ordered chronologically.
    """
    try:
        with Session() as session:
            messages = session.query(Message).filter_by(thread_id=thread_id).order_by(Message.created_at.asc()).all()

            if not messages:
                return response_template(
                    message="No messages found for the thread",
                    status_code=HTTPStatus.NOT_FOUND
                )
            
            message_data = []
            for message in messages:
                message_dict = message.as_dict()
                message_files = session.query(File).filter_by(message_id=message.id).all()
                message_dict['files'] = [file.as_dict() for file in message_files]
                message_data.append(message_dict)
            
            return response_template(
                message="Messages with associated files retrieved successfully",
                data={
                    "messages": message_data
                },
                status_code=HTTPStatus.OK
            )
    except Exception as e:
        return response_template(
            message='Internal Server Error',
            error=f'An unexpected error occurred: {str(e)}',
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

