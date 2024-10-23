"""
# Inference endpoints
"""

import json
from http import HTTPStatus
from werkzeug.exceptions import BadRequest
from app.penelope.penelope import penelope_manager
from flask import Response, stream_with_context, request, Blueprint
from app.utils.response_template import penelope_response_template
inference_bp = Blueprint('inference_bp', __name__)

@inference_bp.route('/inference', methods=['POST'])
def penelope_inference():
    def stream_response(generator):
        for chunk in generator:
            yield f"data: {json.dumps(chunk)}\n\n"

    def stream_error(message, status_code):
        error_data = penelope_response_template(message, type='error')
        
        def error_generator():
            yield f"data: {json.dumps(error_data)}\n\n"
        
        return Response(
            stream_with_context(error_generator()),
            status=status_code,
            content_type='text/event-stream'
        )

    try:
        # Extract and validate request parameters
        user_prompt = request.form.get('prompt')
        user = request.form.get('user')
        files = request.files.getlist('files')
        thread_id = request.form.get('thread_id')

        if not all([user_prompt, user]):
            return stream_error("Missing required parameters: prompt or user", HTTPStatus.BAD_REQUEST)

        # Parse user data
        try:
            user_data = json.loads(user)['data']
            user_id = user_data.get('id')
            username = user_data.get('username')

            if not user_id or not username:
                return stream_error("Missing user data: id or username", HTTPStatus.BAD_REQUEST)
        except (json.JSONDecodeError, KeyError) as e:
            return stream_error(f"Invalid user data: {str(e)}", HTTPStatus.BAD_REQUEST)

        # Generate response
        try:
            generator = penelope_manager.generate_penelope_response_streaming(
                user_prompt, user_id, username, files, thread_id
            )
            return Response(
                stream_with_context(stream_response(generator)),
                content_type='text/event-stream'
            )
        except Exception as e:
            return stream_error(f"Error during response generation: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)

    except Exception as e:
        return stream_error(f"Unexpected error: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)





