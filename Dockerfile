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

# Copy server.py for Flask
COPY server.py .

# Expose port 8000
EXPOSE 8000

# Set the command to run the application
CMD ["python", "server.py"]
