# Use a lightweight Python image
FROM python:3.9-slim  

# Set working directory
WORKDIR /app  

# Copy dependencies
COPY requirements.txt .  

# Install dependencies, including Flask & Gunicorn
RUN pip install --no-cache-dir -r requirements.txt  
RUN pip install gunicorn flask  

# Copy application files
COPY bot.py .  
COPY server.py .  

# Expose the Flask port
EXPOSE 8000  

# Run the Flask app using Gunicorn
CMD gunicorn --bind 0.0.0.0:8000 server:app & python bot.py
