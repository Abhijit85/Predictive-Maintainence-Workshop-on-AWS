FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip \
    curl \
    build-essential \
    python3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# AWS-CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && ./aws/install && rm -rf awscliv2.zip aws/

# Set working directory
WORKDIR /app

COPY backend/ ./backend/
RUN pip install --upgrade pip && pip install -r backend/requirements.txt --no-cache-dir

COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "fastapi_mcp.py"]
