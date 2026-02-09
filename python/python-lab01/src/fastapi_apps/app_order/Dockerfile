# Use the latest stable slim python image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY order.py .

# Expose the port FastAPI runs on
EXPOSE 7890

# Command to run the application
CMD ["uvicorn", "order:app", "--host", "0.0.0.0", "--port", "7890"]
