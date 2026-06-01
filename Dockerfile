FROM python:3.11-slim

# Install git (required by RepoRepair to clone repositories and make commits)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with user ID 1000 (Required by Hugging Face Spaces)
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user . $HOME/app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Hugging Face Spaces expose port 7860 by default
ENV PORT=7860
EXPOSE 7860

# Run the web server using our pre-configured Gunicorn setup
CMD ["gunicorn", "-c", "gunicorn.conf.py", "web_app:app"]
