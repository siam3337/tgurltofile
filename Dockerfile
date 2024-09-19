# Use a base image with Python installed
FROM python:3.9-slim

# Set the working directory
WORKDIR /bot

# Install ffmpeg and other necessary packages
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Command to run the bot and web server
CMD ["python", "bot.py"]
