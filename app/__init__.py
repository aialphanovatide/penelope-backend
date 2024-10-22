from flask import Flask
from app.routes.feedback.feedback import feedback_bp
from app.routes.inference.inference import inference_bp
from app.routes.register.register import register_bp
from app.routes.threads.threads import threads_bp
from app.routes.messages.messages import messages_bp
from app.routes.image.image import image_bp
from app.routes.agent.agent import agent_bp
from app.routes.metrics.healthcheck import healthcheck_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    app.name = 'penelope'
    app.register_blueprint(feedback_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(inference_bp)
    app.register_blueprint(register_bp)
    app.register_blueprint(threads_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(healthcheck_bp)
    return app

