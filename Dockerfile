# Use a lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Flask and Gunicorn
RUN pip install flask gunicorn

# Copy the bot script
COPY bot.py .

# Create a dummy Flask server (if not already done)
COPY server.py .

# Expose the port your app will run on
EXPOSE 8000

# Start the app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "server:app"]
