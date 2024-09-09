import psutil
from http import HTTPStatus
from flask import current_app
from werkzeug.exceptions import BadRequest
from app.penelope.penelope import penelope_manager
from app.utils.response_template import response_template
from flask import Blueprint, request, render_template

feedback_bp = Blueprint('feedback_bp', __name__,
                                 template_folder='templates')


@feedback_bp.route('/update_feedback', methods=['POST'])
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

        print('message_id', message_id) 
        print('feedback', feedback)
        print(type(message_id), type(feedback))

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
                data=response.get('data'),
                status_code=HTTPStatus.OK
            )
        return response_template(
            message="Bad Request",
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




@feedback_bp.route('/', methods=['GET'])
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