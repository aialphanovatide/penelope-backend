from http import HTTPStatus
from werkzeug.exceptions import BadRequest
from app.penelope.penelope import penelope_manager
from app.utils.response_template import response_template
from flask import Blueprint, request, jsonify, render_template_string, render_template
import psutil
from flask import current_app

feedback_new_chat_bp = Blueprint('feedback_new_chat_bp', __name__,
                                 template_folder='templates')


@feedback_new_chat_bp.route('/update_feedback', methods=['POST'])
def update_feedback():
    """
    Route to update feedback for a specific message.

    This endpoint expects a JSON payload with 'message_id' (str) and 'feedback' (bool).
    It updates the feedback status of the given message and returns a success message upon completion.

    Request JSON format:
    {
        "message_id": "some_message_id",
        "feedback": true/false
    }

    Responses:
        200: Feedback updated successfully.
        400: Bad request with an explanation of the error.
        500: Internal server error.
    """
    try:
        data = request.json
        message_id = data.get('message_id')
        feedback = data.get('feedback')

        if message_id is None or feedback is None:
            return response_template(
                message="Missing required parameters",
                error="Both message_id and feedback are required",
                status_code=HTTPStatus.BAD_REQUEST
            )

        response = penelope_manager.update_message_feedback(message_id, feedback)
        if response['success']:
            return response_template(
                message=response.get('message'),
                status_code=HTTPStatus.OK
            )
        return response_template(
            error=response.get('message', 'Unknown error occurred'),
            status_code=HTTPStatus.BAD_REQUEST
        )

    except BadRequest as br:
        return response_template(
            message="Bad Request",
            error=str(br),
            status_code=HTTPStatus.BAD_REQUEST
        )
    except Exception as e:
        return response_template(
            message="Internal Server Error",
            error=f"An unexpected error occurred: {str(e)}",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )



@feedback_new_chat_bp.route('/start_new_chat', methods=['POST'])
def start_new_chat():
    """
    Start a new chat for a user.

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
    
    if not user_id:
        return response_template(
            message="Bad Request",
            error="User ID is required",
            status_code=HTTPStatus.BAD_REQUEST
        )
    
    try:
        result = penelope_manager.start_new_chat(user_id)
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


@feedback_new_chat_bp.route('/', methods=['GET'])
def welcome():
    """
    Welcome route to render a simple welcome message with system metrics.

    This endpoint does not take any parameters and returns a welcome HTML page
    containing various system metrics.

    Returns:
        flask.Response: A rendered HTML template with system metrics.

    Metrics included:
        - CPU usage
        - Memory usage
        - Number of active threads
        - System uptime
        - Count of registered routes

    Response:
        200: Welcome page rendered successfully with system metrics.
    """
    metrics = {
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'active_threads': len(psutil.Process().threads()),
        'uptime': int(psutil.boot_time()),
        'routes_count': len(current_app.url_map._rules)
    }
    return render_template('template.html', metrics=metrics)