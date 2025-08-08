# Use an official Python image
FROM python:3.12-slim

WORKDIR /app

# Install uv (fast Python package installer)
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock requirements.txt ./
COPY backend/app ./app

# Install dependencies explicitly
RUN uv pip install --system backoff>=2.2.1
RUN uv pip install --system 'litellm[proxy]>=1.61.16'

# Install all dependencies
RUN uv pip install --system --editable .

# Expose the port
EXPOSE 8060

# Set environment variables (or use a .env file)
ENV GOOGLE_CREDENTIALS_FILE=/app/app/credentials.json

# Start the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8060"]

