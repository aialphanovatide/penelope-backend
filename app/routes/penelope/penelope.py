import os
from flask import Blueprint, request, jsonify
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