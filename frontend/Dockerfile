# syntax=docker/dockerfile:1

# ---- Build Stage ----
FROM node:20-bullseye-slim AS build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build && npm prune --production

# ---- Runtime Stage ----
FROM node:20-bullseye-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Set production environment
ENV NODE_ENV=production
ENV PORT=3000
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_OPTIONS=--dns-result-order=ipv4first

# Copy application from build stage
COPY --from=build /app ./

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Start Next.js with explicit binding to all interfaces
CMD ["sh", "-c", "echo 'Starting Next.js...'; echo 'Node:' $(node -v); ls -la | head; echo 'Executing: npx next start -p 3000 -H 0.0.0.0'; exec npx next start -p 3000 -H 0.0.0.0 2>&1"]
