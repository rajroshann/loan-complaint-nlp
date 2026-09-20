# Start from a minimal, official Python 3.12 image - "slim" means it excludes
# a lot of OS-level tooling you don't need, keeping the final image smaller
# and faster to build/deploy than the full python:3.12 image.
FROM python:3.12-slim 

# All following commands run from this folder inside the container -
# equivalent to "cd /app" for everything after this line.
WORKDIR /app

# Copy ONLY requirements.txt first, before the rest of your code. This is a
# deliberate ordering trick: Docker caches each instruction as a "layer," and
# only re-runs a layer if the files it depends on changed. Since your code
# changes far more often than your dependencies, this ordering means "pip
# install" (the slow step) gets skipped on rebuilds where you only edited a
# .py file - it reuses the cached layer instead of reinstalling everything.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# One-time NLTK data download - baked into the image itself, so the
# container never needs internet access to fetch this at startup.
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('punkt_tab')"

# NOW copy the rest of your actual application code - this happens last
# specifically because of the caching behavior described above.
COPY . .

# Documents which port this container listens on. This line is informational
# for humans/tools reading the Dockerfile - it does NOT actually publish the
# port; that's docker-compose's/Render's job.
EXPOSE 8000

# Shell form (not the more common ["array", "form"]) is required here
# specifically so ${PORT:-8000} gets expanded by the shell at container
# startup. Render assigns a dynamic port via the PORT environment variable
# at runtime - hardcoding 8000 would break on Render, since it wouldn't be
# listening on the port Render actually expects. Locally, where PORT isn't
# set, it falls back to 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]