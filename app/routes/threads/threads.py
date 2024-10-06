# Endpoints for threads

from flask import Blueprint, request, jsonify
from app.utils.response_template import response_template
from http import HTTPStatus
from config import Session, Thread
from app.penelope.penelope import penelope_manager


threads_bp = Blueprint('threads', __name__)

@threads_bp.route('/start_new_chat', methods=['POST'])
def start_new_chat():
    """
    Start a new chat/Thread for a user.

    This endpoint expects a JSON payload with a 'user_id' field.
    It creates a new chat thread for the specified user.

    Request JSON format:
    {
        "user_id": "some_user_id"
    }

    Returns:
        JSON response with the new thread ID and a success message.

    Responses:
        200: New chat started successfully.
        400: Bad request if user_id is missing.
        500: Internal server error if an exception occurs.
    """
    data = request.get_json()
    if not data:
        return response_template(
            message="Bad Request",
            error="No JSON data provided",
            status_code=HTTPStatus.BAD_REQUEST
        )

    user_id = data.get('user_id')
    print('user_id: ', user_id)
    
    if not user_id:
        return response_template(
            message="Bad Request",
            error="User ID is required",
            status_code=HTTPStatus.BAD_REQUEST
        )
    
    try:
        result = penelope_manager.create_new_thread(user_id)
        print('result: ', result)
        if result['success']:
            return response_template(
                message=result['message'],
                data=result['data'],
                status_code=HTTPStatus.OK
            )
        else:
            return response_template(
                error=result['message'],
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        return response_template(
            message='Internal Server Error',
            error=f'An unexpected error occurred: {str(e)}',
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@threads_bp.route('/threads/<user_id>', methods=['GET'])
def get_threads(user_id):
    """
    Get all threads for a user, ordered by creation date (newest first).

    This endpoint expects a 'user_id' in the URL.
    It retrieves all threads associated with the specified user.

    Returns:
        JSON response with the threads data.

    Responses:
        200: Threads retrieved successfully.
        400: Bad request if user_id is missing.
        500: Internal server error if an exception occurs.
    """
    with Session() as session:
        try:
            threads = session.query(Thread).filter_by(user_id=user_id).order_by(Thread.created_at.desc()).all()
            if not threads:
                return response_template(
                    message="No threads found for the user",
                    status_code=HTTPStatus.NOT_FOUND
                )
            
            thread_data = [thread.as_dict() for thread in threads]
            return response_template(
                message="Threads retrieved successfully",
                data=thread_data,
                status_code=HTTPStatus.OK
            )
        except Exception as e:
            session.rollback()
            return response_template(   
                message='Internal Server Error',
                error=f'An unexpected error occurred: {str(e)}',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )


@threads_bp.route('/threads/<thread_id>', methods=['PUT'])
def update_thread_title(thread_id):
    """
    Update the title of a thread.

    This endpoint expects a JSON payload with a 'title' field.
    It updates the title of the specified thread.

    Request JSON format:
    {
        "title": "New title for the thread"
    }

    Returns:
        JSON response with the updated thread data.

    Responses:
        200: Thread title updated successfully.
        400: Bad request if thread_id or title is missing.
        500: Internal server error if an exception occurs.
    """
    data = request.get_json()
    if not data:
        return response_template(
            message="Bad Request",
            error="No JSON data provided",
            status_code=HTTPStatus.BAD_REQUEST
        )

    title = data.get('title')
    if not title:
        return response_template(
            message="Bad Request",
            error="Title is required",
            status_code=HTTPStatus.BAD_REQUEST
        )

    try:
        with Session() as session:
            thread = session.query(Thread).filter_by(id=thread_id).first()
            if not thread:
                return response_template(
                    message="Thread not found",
                    error="Thread with the specified ID does not exist",
                    status_code=HTTPStatus.NOT_FOUND
                )
            thread.title = title
            session.commit()
            return response_template(
                message="Thread title updated successfully",
                data=thread.as_dict(),
                status_code=HTTPStatus.OK
            )
    except Exception as e:
        session.rollback()
        return response_template(
            message='Internal Server Error',
            error=f'An unexpected error occurred: {str(e)}',
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

            
