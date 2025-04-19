# Use a slim Python base image
FROM python:alpine

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
