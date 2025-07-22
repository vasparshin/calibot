# Use an official Python image
FROM python:3.12-slim

WORKDIR /app

# Install uv (fast Python package installer)
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY backend/app ./app


# Install dependencies
RUN uv pip install --system --all

# Expose the port
EXPOSE 8060

# Set environment variables (or use a .env file)
ENV GOOGLE_CREDENTIALS_FILE=/app/app/credentials.json

# Start the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8060", "--reload"]

