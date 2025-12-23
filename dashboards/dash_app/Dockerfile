FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Expose port
EXPOSE 8050

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "2", "app:server"]
