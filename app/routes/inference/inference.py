"""
# Inference endpoint    
"""
import json
from flask import Blueprint, request, jsonify
from config import Session, User
from werkzeug.exceptions import BadRequest
from http import HTTPStatus
from app.penelope.penelope import penelope_manager
from flask import Response, stream_with_context
from app.utils.response_template import response_template

inference_bp = Blueprint('inference_bp', __name__)

@inference_bp.route('/inference', methods=['POST'])
def penelope_inference():
    try:
        user_prompt = request.form.get('prompt')
        behaviour = request.form.get('behaviour')
        user = request.form.get('user')
        files = request.files.getlist('files')

        required_params = {'prompt': user_prompt, 'behaviour': behaviour, 'user': user}
        missing_params = [param for param, value in required_params.items() if not value]

        if missing_params:
            raise BadRequest(f"Missing required parameters: {', '.join(missing_params)}")
        
        user_data = parse_user_data(user)
        user_id = user_data['id']
        username = user_data['username']

        def generate():
            try:
                if behaviour == 'multi-model':
                    yield from generate_multi_model_response(user_prompt, user_id, username, files)
                else:
                    yield from generate_penelope_response(user_prompt, user_id, username, files)
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return Response(stream_with_context(generate()), content_type='text/event-stream')

    except BadRequest as br:
        return error_response("Bad Request", str(br), HTTPStatus.BAD_REQUEST)
    except Exception as e:
        return error_response("Internal Server Error", str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

def parse_user_data(user):
    try:
        user_data = json.loads(user)
        user_id = user_data.get('id')
        username = user_data.get('username')
        if not user_id and not username:
            raise BadRequest("Missing user data: id or username")
        return {'id': user_id, 'username': username}
    except json.JSONDecodeError as e:
        raise BadRequest(f"Failed to parse user data: {str(e)}")

def generate_multi_model_response(user_prompt, user_id, username, files):
    for response in penelope_manager.generate_penelope_response_streaming(user_prompt, user_id, username, files):
        yield f"data: {json.dumps({'type': 'multi_ai', 'service': 'penelope', 'content': response['penelope'], 'id': response['id']})}\n\n"
    
    for response in penelope_manager.generate_multi_ai_response(user_prompt, user_id, files):
        for service, content in response.items():
            if service != 'id':
                yield f"data: {json.dumps({'type': 'multi_ai', 'service': service, 'content': content, 'id': response['id']})}\n\n"

def generate_penelope_response(user_prompt, user_id, username, files):
    for response in penelope_manager.generate_penelope_response_streaming(user_prompt, user_id, username, files):
        yield f"data: {json.dumps({'type': 'multi_ai', 'service': 'penelope', 'content': response['penelope'], 'id': response['id']})}\n\n"

def error_response(message, error, status):
    return response_template(message=message, error=error, status=status)

