# ==========================================
# Stage 1: Build frontend
# ==========================================
FROM node:22-alpine AS frontend-build

WORKDIR /app/frontend

# Install dependencies first (layer cache)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Backend + serve frontend static
# ==========================================
FROM python:3.11-slim AS production

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app/backend

# Install Python dependencies first (layer cache)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy backend source
COPY backend/ ./

# Copy frontend build output
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Create data directory (will be overridden by volume mount)
RUN mkdir -p /app/backend/data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
