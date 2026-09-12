# Builds the frontend, then packages it alongside the backend so one process
# serves both the API and the static frontend - no separate frontend host, no
# CORS to configure for a typical deployment.

FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Leave unset for the default (same-origin) setup below; override only if the
# frontend will be served from a different origin than the API.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM python:3.13-slim AS backend
WORKDIR /app/backend
COPY backend/ ./
# Editable install: app/main.py computes the frontend dist path relative to its
# own __file__, which only stays correct if the source tree isn't copied into
# site-packages by a normal (non-editable) install.
RUN pip install --no-cache-dir -e .
COPY --from=frontend-build /frontend/dist /app/frontend/dist

# STORAGE_ROOT and DATABASE_URL default to paths relative to /app/backend (this
# image's working directory), which is NOT persisted across deploys/restarts on
# most hosts. Point both at a mounted persistent volume via env vars in your
# deployment platform (e.g. Railway: mount a volume at /data, then set
# DATABASE_URL=sqlite:////data/synthia.db and STORAGE_ROOT=/data/uploads).

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
