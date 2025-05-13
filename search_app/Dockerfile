FROM python:3.12-slim AS builder

WORKDIR /app

# Copy only requirements.txt first
COPY requirements.txt .

# Install dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# -------- New Stage --------
FROM python:3.12-slim

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy the rest of the code
COPY . .

# Set environment variables
ENV FLASK_APP=searchApp.py
ENV FLASK_ENV=development

# Start Flask
CMD ["flask", "run", "--host=0.0.0.0"]