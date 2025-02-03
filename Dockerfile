# Use a lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Flask to create a dummy web server
RUN pip install flask

# Copy bot script
COPY bot.py .

# Create a dummy Flask server to keep Koyeb happy
COPY <<EOF /app/server.py
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
EOF

# Run the Telegram bot and dummy Flask server in parallel
CMD ["sh", "-c", "python bot.py & python server.py"]
