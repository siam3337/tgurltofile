# Use a lightweight Python image
FROM python:3.9-slim

CMD ["sh", "-c", "python bot.py & python -m http.server 8080"]

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot script
COPY bot.py .

# Run the bot
CMD ["python", "bot.py"]
