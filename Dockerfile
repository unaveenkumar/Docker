# Base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirement.txt

# Expose the application port
EXPOSE 5000

# Command to run the application
CMD ["python", "flask_app.py"]