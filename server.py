from flask import Flask
from werkzeug.utils import quote as url_quote  # Use 'quote' instead of 'url_quote'

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    print("Starting Flask server on port 8000...")  # Debugging
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False, threaded=True)
