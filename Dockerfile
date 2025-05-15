# Dockerfile for Compiler Backend Project
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install ply flask flask-cors requests

# Copy project files
COPY . .

# Command to run tests or application
CMD ["python", "-m", "unittest", "discover", "tests"]
