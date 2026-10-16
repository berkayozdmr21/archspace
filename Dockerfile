FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home architect
COPY backend/ backend/
COPY frontend/catalog.json frontend/home.json frontend/
COPY --from=frontend /build/dist frontend/dist/
RUN mkdir data && chown architect:architect data
USER architect
EXPOSE 8980
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8980"]
