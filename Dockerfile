# Dockerfile para Sistema de Scalping Automatizado
# Autor: Manus AI
# Data: 17 de Julho de 2025

FROM python:3.11-slim

# Metadados
LABEL maintainer="Manus AI"
LABEL version="1.0"
LABEL description="Sistema de Scalping Automatizado para Trading de Criptomoedas"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 scalping && \
    mkdir -p /app/data /app/logs /app/config && \
    chown -R scalping:scalping /app

# Copiar arquivo de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Ajustar permissões
RUN chown -R scalping:scalping /app && \
    chmod +x scripts/*.ps1 2>/dev/null || true

# Mudar para usuário não-root
USER scalping

# Criar diretórios necessários
RUN mkdir -p data/{logs,metrics,signals,alerts,suggestions,reports,historical} && \
    mkdir -p logs/{agents,performance,errors}

# Expor portas
EXPOSE 8080 8443 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Volume para persistência de dados
VOLUME ["/app/data", "/app/logs", "/app/config"]

# Comando de inicialização
CMD ["python", "-m", "agents.orchestrator_agent"]

