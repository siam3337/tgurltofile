from flask import Flask
from urllib.parse import quote as url_quote  # Update this import

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    print("Starting Flask server on port 8000...")  # Debugging (Optional)
    # Flask's app.run() is removed, Gunicorn will run the app in production
