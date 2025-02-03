# Use a lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Flask for a dummy web server
RUN pip install flask

# Copy the bot script
COPY bot.py .

# Create a dummy Flask server
RUN echo 'from flask import Flask; app = Flask(__name__); @app.route("/")\ndef home(): return "Bot is running!"; app.run(host="0.0.0.0", port=8000)' > server.py

# Expose port 8080
EXPOSE 8000

# Run the Telegram bot and the Flask web server in parallel
CMD ["sh", "-c", "python bot.py & python server.py"]
