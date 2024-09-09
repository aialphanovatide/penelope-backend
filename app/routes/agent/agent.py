# Agent endpoints to create, update, delete, get agents using OpenAI API

from flask import Blueprint, request, jsonify
from app.penelope.penelope import penelope_manager
from app.utils.response_template import method_response_template

agent_bp = Blueprint('agent', __name__)

@agent_bp.route('/agents', methods=['GET'])
def get_agents():
    try:
        result = penelope_manager.assistant_manager.list_assistants()
        if result['success']:
            return method_response_template(message="Successfully retrieved assistants", 
                                             data=result['data'], 
                                             success=True), 200
        else:
            return method_response_template(message=result['message'], 
                                             data=None, 
                                             success=False), 400
    except Exception as e:
        return method_response_template(message=str(e), 
                                         data=None, 
                                         success=False), 500

@agent_bp.route('/agents/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    try:
        data = request.json
        if not data:
            return method_response_template(message='No data provided', 
                                             data=None, 
                                             success=False), 400
        
        allowed_fields = ['description', 'temperature', 'top_p', 'instructions', 'name']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return method_response_template(message='No valid update fields provided', 
                                             data=None, 
                                             success=False), 400
        
        result = penelope_manager.assistant_manager.update_assistant(agent_id, **update_data)
        if result['success']:
            return method_response_template(message="Successfully updated assistant", 
                                             data=result['data'], 
                                             success=True), 200
        else:
            return method_response_template(message=result['message'], 
                                             data=None, 
                                             success=False), 400
    except Exception as e:
        return method_response_template(message=f'Failed to update assistant: {str(e)}', 
                                         data=None, 
                                         success=False), 500



