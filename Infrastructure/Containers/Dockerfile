# ===============================
# DOCKERFILE - GÉNÉRATEUR FICP
# Container pour exécution dans Azure Container Instances
# ===============================

FROM python:3.11-slim

# Métadonnées
LABEL maintainer="DataEngineer-Certification"
LABEL description="FICP Data Generator for Azure Data Lake"
LABEL version="1.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Europe/Paris

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Création utilisateur non-root pour sécurité
RUN useradd --create-home --shell /bin/bash ficp
WORKDIR /home/ficp

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie des scripts de génération
COPY scripts/ ./scripts/
COPY config/ ./config/

# Permissions pour l'utilisateur ficp
RUN chown -R ficp:ficp /home/ficp
USER ficp

# Variables d'environnement configurables
ENV AZURE_STORAGE_ACCOUNT=""
ENV AZURE_STORAGE_CONTAINER="bronze"
ENV DATA_VOLUME="300"
ENV OUTPUT_PATH="/home/ficp/output"

# Création du dossier de sortie
RUN mkdir -p $OUTPUT_PATH

# Point d'entrée configurable
ENTRYPOINT ["python", "scripts/generate_and_upload.py"]

# Commande par défaut
CMD ["--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Exposition du port pour monitoring (optionnel)
EXPOSE 8080