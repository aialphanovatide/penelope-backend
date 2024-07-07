import os
import json
from http import HTTPStatus
from werkzeug.exceptions import BadRequest
from app.penelope.penelope import penelope_manager
from flask import Blueprint, request, jsonify, render_template_string, Response, stream_with_context

penelope = Blueprint('penelope', __name__)

assistant_id = os.getenv('ASSISTANT_ID')

@penelope.route('/inference', methods=['POST'])
def penelope_inference():
    try:
        data = request.json
        user_prompt = data.get('prompt')
        behaviour = data.get('behaviour')
        user_id = data.get('user_id')
        files = request.files.getlist('files')

        if not all([user_prompt, behaviour, user_id]):
            raise BadRequest("Missing parameters")

        def generate():
            try:
                if behaviour == 'multi-model':
                    # Generate response from Penelope
                    for response in penelope_manager.generate_penelope_response_streaming(assistant_id, user_prompt, user_id, files):
                        yield f"data: {json.dumps({'type': 'penelope', 'content': response})}\n\n"
                    
                    # Generate responses from multiple AI services
                    for response in penelope_manager.generate_multi_ai_response(user_prompt, user_id=user_id):
                        for service, content in response.items():
                            yield f"data: {json.dumps({'type': 'multi_ai', 'service': service, 'content': content})}\n\n"

                else:
                    for response in penelope_manager.generate_penelope_response_streaming(assistant_id, user_prompt, user_id):
                        yield f"data: {json.dumps({'type': 'penelope', 'content': response})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            finally:
                yield "data: [DONE]\n\n"

        return Response(stream_with_context(generate()), content_type='text/event-stream')

    except BadRequest as br:
        penelope_manager.rollback()
        return jsonify({"error": str(br)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        penelope_manager.rollback()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR


@penelope.route('/update_feedback', methods=['POST'])
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
            raise BadRequest("Missing message_id or feedback")

        if not isinstance(feedback, bool):
            raise BadRequest("Feedback must be a boolean value")

        penelope_manager.update_message_feedback(message_id, feedback)

        return jsonify({"status": "success", "message": f"Feedback updated for message {message_id}"}), 200

    except BadRequest as br:
        penelope_manager.rollback()
        return jsonify({"error": str(br)}), 400
    except Exception as e:
        penelope_manager.rollback()  # Rollback the transaction in case of an error
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500



@penelope.route('/', methods=['GET'])
def welcome():
    """
    Welcome route to render a simple welcome message.

    This endpoint does not take any parameters and returns a welcome HTML page.

    Response:
        200: Welcome page rendered successfully.
    """
    return render_template_string("""
                            <!DOCTYPE html>
                            <html lang="en">
                            <head>
                                <meta charset="UTF-8">
                                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                <title>Welcome</title>
                                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
                                <style>
                                    body {
                                        font-family: Arial, sans-serif;
                                        background-color: #f4f4f9;
                                        display: flex;
                                        justify-content: center;
                                        align-items: center;
                                        height: 100vh;
                                        margin: 0;
                                    }
                                    .welcome-container {
                                        text-align: center;
                                        background: white;
                                        padding: 30px;
                                        border-radius: 10px;
                                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                                    }
                                    .welcome-container h1 {
                                        color: #333;
                                    }
                                    .welcome-container p {
                                        color: #666;
                                    }
                                    .welcome-container .btn {
                                        display: inline-block;
                                        margin-top: 20px;
                                        padding: 10px 20px;
                                        font-size: 16px;
                                        color: white;
                                        background-color: #007BFF;
                                        border: none;
                                        border-radius: 5px;
                                        text-decoration: none;
                                        cursor: pointer;
                                        transition: background-color 0.3s;
                                    }
                                    .welcome-container .btn:hover {
                                        background-color: #0056b3;
                                    }
                                </style>
                            </head>
                            <body>
                                <div class="welcome-container">
                                    <h1>Welcome to the Server!</h1>
                                    <p>We're glad to have you here.</p>
                                    <a href="#" class="btn">Get Started</a>
                                </div>
                            </body>
                            </html>
                            """)