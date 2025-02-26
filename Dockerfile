# Use an official Python runtime as a base image
FROM python:3.11

# Install system dependencies (Tesseract OCR & Poppler for PDFs)
RUN apt-get update && apt-get install -y tesseract-ocr poppler-utils

# Set the working directory in the container
WORKDIR /app

# Copy the application files to the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Streamlit port
EXPOSE 8000

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]
