from app import create_app
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == '__main__':
    app.run(port=5000, debug=True, load_dotenv=True, use_reloader=False, host="0.0.0.0")