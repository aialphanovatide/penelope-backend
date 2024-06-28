import os
from flask import Blueprint, request, jsonify, render_template_string
from app.penelope.penelope import penelope_manager
from werkzeug.exceptions import BadRequest
from config import Session
from http import HTTPStatus

penelope = Blueprint('penelope', __name__)

assistant_id = os.getenv('ASSISTANT_ID')

@penelope.route('/inference', methods=['POST'])
def penelope_inference():
    try:
        user_input = request.get_json()

        if not user_input or 'input' not in user_input:
            raise BadRequest("No input data provided or 'input' field is missing")

        user_message = user_input.get('input')
        if not isinstance(user_message, str) or not user_message.strip():
            raise BadRequest("Input must be a non-empty string")

        user_id = user_input.get('user_id', 1)  # Default to 1 if not provided

        output = penelope_manager.interact_with_assistant(
            user_message=user_message,
            assistant_id=assistant_id,
            user_id=user_id
        )

        if output:
            return jsonify({
                "success": True,
                "response": output
            }), HTTPStatus.OK
        else:
            return jsonify({
                "success": False,
                "response": None,
                "error": "No response generated"
            }), HTTPStatus.NO_CONTENT

    except BadRequest as br:
        return jsonify({
            "success": False,
            "error": str(br)
        }), HTTPStatus.BAD_REQUEST

    except Exception as e:
        # Log the exception here
        print(f"An error occurred: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An internal server error occurred"
        }), HTTPStatus.INTERNAL_SERVER_ERROR
    


@penelope.route('/update_feedback/<string:message_id>', methods=['POST'])
def update_feedback(message_id):
    try:
        data = request.get_json()
        feedback = data.get('feedback')

        # Validate the input
        if feedback is None or not isinstance(feedback, bool):
            return jsonify({"error": "Invalid feedback value. Must be a boolean."}), HTTPStatus.OK

        # Update the feedback
        penelope_manager.update_message_feedback(message_id, feedback)
        return jsonify({"message": f"Feedback updated for message {message_id}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
    


@penelope.route('/', methods=['GET'])
def welcome():
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