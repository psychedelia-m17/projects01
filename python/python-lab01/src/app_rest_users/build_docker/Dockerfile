# Use an official lightweight Python image
FROM python:3.14.2-slim

# Set the working directory
WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app ./app

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the app using Uvicorn (ASGI server)
# --host 0.0.0.0 is mandatory for container networking
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
