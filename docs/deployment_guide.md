# Guia de Deployment - Sistema de Scalping Automatizado

**Autor:** Manus AI  
**Data:** 17 de Julho de 2025  
**Versão:** 1.0  

## Introdução

Este guia fornece instruções detalhadas para deployment do Sistema de Scalping Automatizado em ambiente de produção. O sistema foi projetado para operar de forma autônoma e escalável, com monitoramento contínuo e recuperação automática de falhas.

## Pré-requisitos

### Requisitos de Sistema

#### Hardware Mínimo
- **CPU:** 4 cores, 2.5GHz ou superior
- **RAM:** 8GB (recomendado 16GB)
- **Armazenamento:** 50GB SSD
- **Rede:** Conexão estável com latência < 50ms para exchanges

#### Hardware Recomendado para Produção
- **CPU:** 8 cores, 3.0GHz ou superior
- **RAM:** 32GB
- **Armazenamento:** 200GB NVMe SSD
- **Rede:** Conexão dedicada com latência < 10ms
- **Backup:** Sistema RAID 1 ou backup automático

#### Software
- **Sistema Operacional:** Windows 10/11 Pro ou Windows Server 2019/2022
- **Python:** 3.11.0 ou superior
- **PowerShell:** 5.1 ou superior
- **Git:** Versão mais recente
- **Antivírus:** Configurado com exceções para o sistema

### Dependências Python

```bash
# Instalar dependências principais
pip install -r requirements.txt

# Dependências adicionais para produção
pip install gunicorn supervisor psutil
```

### Configuração de Rede

#### Portas Necessárias
- **8080:** Interface web de monitoramento
- **8443:** API REST (HTTPS)
- **9090:** Métricas Prometheus (opcional)

#### Configuração de Firewall
```powershell
# Abrir portas necessárias
New-NetFirewallRule -DisplayName "Scalping System Web" -Direction Inbound -Protocol TCP -LocalPort 8080
New-NetFirewallRule -DisplayName "Scalping System API" -Direction Inbound -Protocol TCP -LocalPort 8443
```

## Configuração de Ambiente

### Variáveis de Ambiente

Criar arquivo `.env` na raiz do projeto:

```env
# Configurações de Produção
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Configurações de Exchange
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET=false

# Configurações de Banco de Dados
DATABASE_URL=sqlite:///data/scalping_system.db
REDIS_URL=redis://localhost:6379/0

# Configurações de Notificação
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
DISCORD_WEBHOOK_URL=your_discord_webhook

# Configurações de Segurança
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
API_RATE_LIMIT=1000

# Configurações de Performance
MAX_WORKERS=4
BATCH_SIZE=100
CACHE_TTL=300
```

### Configuração de Logging

Criar arquivo `logging.conf`:

```ini
[loggers]
keys=root,scalping

[handlers]
keys=consoleHandler,fileHandler,rotatingFileHandler

[formatters]
keys=simpleFormatter,detailedFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_scalping]
level=DEBUG
handlers=fileHandler,rotatingFileHandler
qualname=scalping
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=detailedFormatter
args=('data/logs/scalping.log',)

[handler_rotatingFileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=detailedFormatter
args=('data/logs/scalping_rotating.log', 'a', 10485760, 5)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_detailedFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s
```

## Deployment Manual

### Passo 1: Preparação do Ambiente

```powershell
# Criar diretório de produção
mkdir C:\ScalpingSystem
cd C:\ScalpingSystem

# Clonar repositório
git clone https://github.com/esdrastrade/Market_Manus.git .

# Criar ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### Passo 2: Configuração

```powershell
# Copiar configurações de exemplo
copy config\trading_config.example.json config\trading_config.json
copy config\risk_parameters.example.json config\risk_parameters.json
copy config\exchange_settings.example.json config\exchange_settings.json

# Editar configurações com suas credenciais
notepad config\exchange_settings.json
```

### Passo 3: Inicialização

```powershell
# Executar script de deployment
.\scripts\deploy.ps1 -Environment production -AutoStart

# Verificar status
.\scripts\monitor.ps1 -Dashboard
```

### Passo 4: Validação

```powershell
# Executar testes de produção
python tests\run_tests.py --integration --performance

# Verificar conectividade com exchange
python -c "from agents.market_analysis_agent import MarketAnalysisAgent; agent = MarketAnalysisAgent(); print('Conectividade OK' if agent.test_connection() else 'Erro de conexão')"
```

## Deployment com Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar usuário não-root
RUN useradd -m -u 1000 scalping && chown -R scalping:scalping /app
USER scalping

# Expor portas
EXPOSE 8080 8443

# Comando de inicialização
CMD ["python", "-m", "agents.orchestrator_agent"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  scalping-system:
    build: .
    container_name: scalping-system
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "8443:8443"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    env_file:
      - .env
    depends_on:
      - redis
      - prometheus

  redis:
    image: redis:7-alpine
    container_name: scalping-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus:latest
    container_name: scalping-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    container_name: scalping-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123

volumes:
  redis_data:
  prometheus_data:
  grafana_data:
```

### Comandos Docker

```bash
# Build e inicialização
docker-compose up -d --build

# Verificar logs
docker-compose logs -f scalping-system

# Parar sistema
docker-compose down

# Atualizar sistema
docker-compose pull && docker-compose up -d
```

## Configuração de Monitoramento

### Prometheus Configuration

Criar arquivo `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'scalping-system'
    static_configs:
      - targets: ['scalping-system:9090']
    scrape_interval: 5s
    metrics_path: /metrics

  - job_name: 'system-metrics'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboards

Criar arquivo `monitoring/grafana/dashboards/scalping-dashboard.json`:

```json
{
  "dashboard": {
    "title": "Sistema de Scalping - Monitoramento",
    "panels": [
      {
        "title": "Sinais Gerados por Hora",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(scalping_signals_total[1h])",
            "legendFormat": "Sinais/hora"
          }
        ]
      },
      {
        "title": "Taxa de Sucesso",
        "type": "singlestat",
        "targets": [
          {
            "expr": "scalping_success_rate",
            "legendFormat": "Taxa de Sucesso"
          }
        ]
      },
      {
        "title": "P&L Diário",
        "type": "graph",
        "targets": [
          {
            "expr": "scalping_daily_pnl",
            "legendFormat": "P&L"
          }
        ]
      }
    ]
  }
}
```

## Configuração de Backup

### Script de Backup Automático

```powershell
# backup_scheduler.ps1
param(
    [string]$BackupPath = "C:\Backups\ScalpingSystem",
    [int]$RetentionDays = 30
)

# Criar diretório de backup
if (!(Test-Path $BackupPath)) {
    New-Item -ItemType Directory -Path $BackupPath -Force
}

# Timestamp para backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $BackupPath "backup_$timestamp"

# Criar backup
New-Item -ItemType Directory -Path $backupDir -Force

# Backup de dados
Copy-Item -Path "C:\ScalpingSystem\data" -Destination "$backupDir\data" -Recurse -Force

# Backup de configurações
Copy-Item -Path "C:\ScalpingSystem\config" -Destination "$backupDir\config" -Recurse -Force

# Backup de logs (últimos 7 dias)
$logFiles = Get-ChildItem "C:\ScalpingSystem\data\logs" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) }
$logBackupDir = Join-Path $backupDir "logs"
New-Item -ItemType Directory -Path $logBackupDir -Force
$logFiles | Copy-Item -Destination $logBackupDir -Force

# Compactar backup
Compress-Archive -Path $backupDir -DestinationPath "$backupDir.zip" -Force
Remove-Item -Path $backupDir -Recurse -Force

# Limpeza de backups antigos
$oldBackups = Get-ChildItem $BackupPath -Filter "backup_*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) }
$oldBackups | Remove-Item -Force

Write-Host "Backup concluído: $backupDir.zip"
```

### Agendamento de Backup

```powershell
# Criar tarefa agendada para backup diário
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\ScalpingSystem\scripts\backup_scheduler.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "02:00"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "ScalpingSystemBackup" -Action $action -Trigger $trigger -Settings $settings -Description "Backup diário do Sistema de Scalping"
```

## Configuração de Segurança

### Configuração de SSL/TLS

```powershell
# Gerar certificado auto-assinado para desenvolvimento
$cert = New-SelfSignedCertificate -DnsName "localhost" -CertStoreLocation "cert:\LocalMachine\My"

# Para produção, usar certificado válido
# Configurar no arquivo config/ssl_config.json
```

### Configuração de Autenticação

```json
{
  "authentication": {
    "enabled": true,
    "method": "jwt",
    "token_expiry": 3600,
    "refresh_token_expiry": 86400,
    "allowed_ips": ["127.0.0.1", "192.168.1.0/24"],
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60,
      "burst_limit": 10
    }
  },
  "api_keys": {
    "admin": "your_admin_api_key",
    "readonly": "your_readonly_api_key"
  }
}
```

## Otimização de Performance

### Configuração de Cache

```json
{
  "cache": {
    "enabled": true,
    "backend": "redis",
    "default_ttl": 300,
    "max_memory": "256mb",
    "eviction_policy": "allkeys-lru",
    "key_prefix": "scalping:",
    "compression": true
  }
}
```

### Configuração de Pool de Conexões

```json
{
  "connection_pools": {
    "exchange_api": {
      "max_connections": 10,
      "max_keepalive_connections": 5,
      "keepalive_expiry": 30,
      "timeout": 10,
      "retries": 3
    },
    "database": {
      "pool_size": 5,
      "max_overflow": 10,
      "pool_timeout": 30,
      "pool_recycle": 3600
    }
  }
}
```

## Troubleshooting

### Problemas Comuns

#### 1. Erro de Conectividade com Exchange

**Sintomas:**
- Mensagens de erro "Connection timeout"
- Falha na obtenção de dados de mercado

**Soluções:**
```powershell
# Verificar conectividade
Test-NetConnection api.binance.com -Port 443

# Verificar configuração de proxy
netsh winhttp show proxy

# Testar credenciais
python -c "import ccxt; exchange = ccxt.binance({'apiKey': 'your_key', 'secret': 'your_secret', 'sandbox': True}); print(exchange.fetch_balance())"
```

#### 2. Alto Uso de Memória

**Sintomas:**
- Sistema lento
- Erros de "Out of Memory"

**Soluções:**
```powershell
# Verificar uso de memória
Get-Process -Name python | Select-Object ProcessName, WorkingSet, VirtualMemorySize

# Ajustar configurações
# Reduzir BATCH_SIZE no arquivo .env
# Aumentar CACHE_TTL para reduzir recálculos
```

#### 3. Falhas de Agentes

**Sintomas:**
- Agentes param de responder
- Logs mostram exceções

**Soluções:**
```powershell
# Reiniciar agentes específicos
.\scripts\monitor.ps1 -RestartAgent MarketAnalysisAgent

# Verificar logs detalhados
Get-Content data\logs\scalping.log -Tail 100 | Where-Object { $_ -match "ERROR" }

# Executar diagnóstico
python -m agents.orchestrator_agent --diagnose
```

### Logs de Diagnóstico

#### Localização dos Logs
- **Sistema:** `data/logs/scalping.log`
- **Agentes:** `data/logs/agents/`
- **Performance:** `data/logs/performance/`
- **Erros:** `data/logs/errors/`

#### Comandos Úteis de Log

```powershell
# Monitorar logs em tempo real
Get-Content data\logs\scalping.log -Wait -Tail 50

# Filtrar erros críticos
Select-String -Path "data\logs\*.log" -Pattern "CRITICAL|ERROR" | Select-Object -Last 20

# Analisar performance
Select-String -Path "data\logs\performance\*.log" -Pattern "execution_time" | Measure-Object
```

## Checklist de Produção

### Pré-Deployment

- [ ] Configurações de produção validadas
- [ ] Credenciais de API configuradas e testadas
- [ ] Testes de integração executados com sucesso
- [ ] Backup automático configurado
- [ ] Monitoramento configurado
- [ ] Alertas configurados
- [ ] Documentação atualizada
- [ ] Plano de rollback preparado

### Pós-Deployment

- [ ] Sistema iniciado com sucesso
- [ ] Todos os agentes funcionando
- [ ] Conectividade com exchange confirmada
- [ ] Métricas sendo coletadas
- [ ] Alertas funcionando
- [ ] Backup executado com sucesso
- [ ] Performance dentro dos parâmetros
- [ ] Logs sendo gerados corretamente

### Monitoramento Contínuo

- [ ] Verificação diária de logs
- [ ] Análise semanal de performance
- [ ] Revisão mensal de configurações
- [ ] Backup mensal completo
- [ ] Atualização trimestral de dependências
- [ ] Auditoria semestral de segurança

## Manutenção

### Rotinas Diárias

```powershell
# Script de verificação diária
.\scripts\daily_check.ps1
```

### Rotinas Semanais

```powershell
# Análise de performance semanal
.\scripts\weekly_analysis.ps1

# Limpeza de logs antigos
.\scripts\cleanup_logs.ps1 -DaysToKeep 30
```

### Rotinas Mensais

```powershell
# Backup completo mensal
.\scripts\full_backup.ps1

# Atualização de dependências
pip list --outdated
pip install --upgrade package_name
```

## Suporte e Contato

### Documentação Adicional
- **API Reference:** `docs/api_reference.md`
- **Configuration Guide:** `docs/configuration_guide.md`
- **Troubleshooting:** `docs/troubleshooting.md`

### Logs de Mudanças
- **CHANGELOG.md:** Histórico de versões e mudanças

### Suporte Técnico
- **GitHub Issues:** https://github.com/esdrastrade/Market_Manus/issues
- **Documentação Online:** https://github.com/esdrastrade/Market_Manus/wiki

---

**Nota:** Este guia deve ser atualizado conforme novas versões e melhorias são implementadas no sistema.

