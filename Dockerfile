# Utiliser une image Python slim
FROM python:3.13.2-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirement.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirement.txt && \
    pip install --no-cache-dir fastapi uvicorn[standard] requests

# Copier tous les fichiers du projet
COPY . .


# Copy MLflow run (artifacts + metadata) to the flat /app/model convenience path
# ✅ Créer le répertoire et copier tous les artifacts
RUN mkdir -p /app/model

# Copier le modèle complet (répertoire entier si nécessaire)
COPY mlruns/1/models/m-064588f47a05402dbe61ac998f0471dc/artifacts/model.pkl /app/model/model.pkl


EXPOSE 8000

# Healthcheck pour Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# Lancer l'API
CMD ["python", "main.py"]
