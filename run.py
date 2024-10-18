from app import create_app
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == '__main__':
    print("Starting Penelope...")
    app.run(
        port=5000,          
        debug=True,         
        load_dotenv=True,   # Load environment variables from .env file
        use_reloader=False, # Disable the automatic reloader
        host="0.0.0.0",     # Allow connections from any IP address
        threaded=True       # Enable multi-threading
    )