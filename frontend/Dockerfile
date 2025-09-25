# Multi-stage build for optimized production image
FROM node:18-slim AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM node:18-slim AS production

WORKDIR /app

# Install only serve globally for serving static files
RUN npm install -g serve@14.2.1

# Copy built app from builder stage
COPY --from=builder /app/build ./build

# Create non-root user
RUN useradd -r -u 1001 appuser
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Start the app
CMD ["serve", "-s", "build", "-l", "3000"]
