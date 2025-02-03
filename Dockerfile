# Use a lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Flask and Gunicorn
RUN pip install flask gunicorn

# Copy the bot script and server.py
COPY bot.py .
COPY server.py .

# Expose port 8000
EXPOSE 8000

# Use Gunicorn to run the server with 1 worker
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "server:app"]
