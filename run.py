from app import create_app
from dotenv import load_dotenv

load_dotenv()

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    app.run(
        port=5000,          
        debug=True,         
        load_dotenv=True,   # Load environment variables from .env file
        use_reloader=True, # Disable the automatic reloader
        host="0.0.0.0",     # Allow connections from any IP address
        threaded=True       # Enable multi-threading
    )