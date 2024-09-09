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
    user_prompt = request.form['prompt']
    behaviour = request.form['behaviour']
    user = request.form['user']
    files = request.files.getlist('files')
    thread_id = request.form['thread_id']

    print(f"Prompt: {user_prompt}")
    print(f"Behaviour: {behaviour}")
    print(f"User: {user}")
    print(f"Files: {files}")   
    print(f"Thread ID: {thread_id}")

    required_params = {'prompt': user_prompt, 'behaviour': behaviour, 'user': user}
    missing_params = [param for param, value in required_params.items() if not value]

    if missing_params:
        raise BadRequest(f"Missing required parameters: {', '.join(missing_params)}")
    
    user_data = parse_user_data(user)
    user_id = user_data['id']
    username = user_data['username']

    print(f"User ID: {user_id}")
    print(f"Username: {username}")

    try:
        if behaviour == 'multi-model':
            print(f"\nGenerating multi-model response")
            generator = generate_multi_model_response(user_prompt, 
                                                      user_id, 
                                                      username, 
                                                      files,
                                                      thread_id
                                                      )
        else:
            print(f"\nGenerating penelope response")
            generator = generate_penelope_response(user_prompt, 
                                                   user_id, 
                                                   username, 
                                                   files,
                                                   thread_id
                                                   )

        def stream_generator():
            try:
                for chunk in generator:
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                print(f"\nError during generation: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return Response(stream_with_context(stream_generator()), 
                        content_type='text/event-stream',
                       )

    except (BadRequest, Exception) as e:
        error_type = "BadRequest" if isinstance(e, BadRequest) else "Unexpected"
        print(f"{error_type} - error: {str(e)}")
        
        def error_stream():
            error_data = json.dumps({'type': 'error', 'content': str(e)})
            yield f"data: {error_data}\n\n"
        
        return Response(
            stream_with_context(error_stream()),
            content_type='text/event-stream',
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )

def parse_user_data(user: str):
    try:
        # Parse the entire JSON string
        response_data = json.loads(user)
        
        # Check if the parsed data has the expected structure
        if 'data' not in response_data or not isinstance(response_data['data'], dict):
            raise BadRequest("Invalid user data structure")
        
        user_data = response_data['data']
        
        user_id = user_data.get('id')
        username = user_data.get('username')
        
        if not user_id and not username:
            raise BadRequest("Missing user data: id or username")
        
        return {'id': user_id, 'username': username}
    
    except json.JSONDecodeError as e:
        raise BadRequest(f"Failed to parse user data: {str(e)}")
    except KeyError as e:
        raise BadRequest(f"Missing expected key in user data: {str(e)}")
    except Exception as e:
        raise BadRequest(f"Error processing user data: {str(e)}")

def generate_multi_model_response(user_prompt, user_id, username, files):
    for response in penelope_manager.generate_penelope_response_streaming(user_prompt, user_id, username, files):
        yield response
    
    for response in penelope_manager.generate_multi_ai_response(user_prompt, user_id, files):
        yield response

def generate_penelope_response(user_prompt, user_id, username, files, thread_id):
    for response in penelope_manager.generate_penelope_response_streaming(user_prompt, user_id, username, files, thread_id):
        yield response

