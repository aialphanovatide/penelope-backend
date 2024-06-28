from flask import Flask
from app.routes.penelope.penelope import penelope
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    app.name = 'penelope'
    app.register_blueprint(penelope)
    
    return app

