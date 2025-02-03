# Use a lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Flask for a dummy web server
RUN pip install flask

# Copy bot script and server script
COPY bot.py .
COPY server.py .

# Expose port 8000 for Koyeb
EXPOSE 8000

# Run the Telegram bot and Flask server in parallel
CMD ["sh", "-c", "python server.py & python bot.py"]
