# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# System dependencies for psycopg2 and potentially other libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup appuser

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY pyproject.toml .
# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir uv
RUN uv sync

# Bundle app source
COPY . .

# Change ownership of the app directory
RUN chown -R appuser:appgroup /app


# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable for the Uvicorn command (can be overridden)
ENV MODULE_NAME="main"
ENV VARIABLE_NAME="app"
ENV APP_HOST="0.0.0.0"
ENV APP_PORT="8000"

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# Switch to the non-root user
USER appuser
# Run app.py when the container launches
ENTRYPOINT ["/entrypoint.sh"]
# The CMD from before will now be passed as arguments to entrypoint.sh
CMD ["uvicorn", "$MODULE_NAME:$VARIABLE_NAME", "--host", "$APP_HOST", "--port", "$APP_PORT"]
