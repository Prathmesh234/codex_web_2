FROM node:18-slim

# Install bash, Node dependencies, and essentials
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        bash git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Copy package files and install dependencies (including morgan)
COPY package*.json ./
RUN npm install --omit=dev morgan

# Copy start script and app code
COPY start.sh index.js ./
RUN chmod +x start.sh

# Create developer user and projects directory
RUN useradd -m -s /usr/bin/bash developer \
 && mkdir -p /projects \
 && chown -R developer:developer /app /projects

# Switch to developer user and set PATH
USER developer
ENV PATH="/usr/bin:$PATH"
WORKDIR /projects
EXPOSE 3000

# Start via bash
CMD ["bash", "/app/start.sh"]