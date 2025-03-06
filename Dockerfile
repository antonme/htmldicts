FROM python:3.11-slim

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8100

# Command to run the application
CMD ["uvicorn", "app.api.api:app", "--host", "0.0.0.0", "--port", "8100"] 