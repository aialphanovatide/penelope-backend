import os
import json
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
from flasgger import Swagger

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.static_folder = 'static'
    app.secret_key = os.urandom(24)

    swagger_template_path = os.path.join(app.root_path, 'static', 'swagger.json')

    # Swagger configuration
    with open(swagger_template_path, 'r') as f:
        swagger_template = json.load(f)

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'swagger',
                "route": '/swagger.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs/",
        "title": "Penelope",
        "description": "API for Penelope",
        "swagger_ui_config": {
            "docExpansion": "none",
            "tagsSorter": "alpha"
        }
    }

    swagger = Swagger(app, template=swagger_template, config=swagger_config)
    
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

