FROM python:3.11-slim

# Working directory in the container
WORKDIR /app

# Copy of the requirements file into the container
COPY requirements.txt .

# Installation of the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the application
CMD ["python", "run.py"]
