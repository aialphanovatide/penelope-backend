from flask import Flask
from app.routes.feedback_new_chat.feedback_new_chat import feedback_new_chat_bp
from app.routes.register.register import register_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    app.name = 'penelope'
    app.register_blueprint(feedback_new_chat_bp)
    app.register_blueprint(register_bp)
    return app

