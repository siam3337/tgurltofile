# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN apt-get update && \
    apt-get install -y libtorrent-rasterbar-dev && \
    pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on (optional if Flask is used for health checks)
EXPOSE 8000

# Run the bot when the container launches
CMD ["python", "bot.py"]
