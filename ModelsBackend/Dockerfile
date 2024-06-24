FROM python:3.11

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app

COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Download NLTK 'punkt' resource
RUN python3 -c "import nltk; nltk.download('punkt')"

# Make port 8000 available to the world outside this container
EXPOSE $BACKEND_PORT

CMD [ "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
