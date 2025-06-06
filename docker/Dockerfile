FROM ghcr.io/astral-sh/uv:debian

# Install git
RUN apt-get update && apt-get install -y git

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the package
RUN uv venv --python 3.12
RUN uv pip install -e /app

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["/usr/local/bin/uv", "run", "hatchling"]
