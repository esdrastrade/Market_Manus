# Guia de Troubleshooting - Sistema de Scalping Automatizado

**Autor:** Manus AI  
**Data:** 17 de Julho de 2025  
**Versão:** 1.0  

## Introdução

Este guia fornece soluções para problemas comuns que podem ocorrer durante a operação do Sistema de Scalping Automatizado. Os problemas estão organizados por categoria e incluem sintomas, causas prováveis e soluções detalhadas.

## Problemas de Conectividade

### 1. Falha de Conexão com Exchange

#### Sintomas
- Mensagens de erro "Connection timeout" ou "Connection refused"
- Agente MarketAnalysisAgent para de funcionar
- Logs mostram erros de rede repetidos

#### Causas Prováveis
- Problemas de conectividade de rede
- Credenciais de API inválidas ou expiradas
- Rate limiting da exchange
- Firewall bloqueando conexões

#### Soluções

**Verificar Conectividade Básica:**
```powershell
# Testar conectividade com Binance
Test-NetConnection api.binance.com -Port 443

# Verificar DNS
nslookup api.binance.com

# Testar com curl
curl -I https://api.binance.com/api/v3/ping
```

**Verificar Credenciais:**
```python
# Testar credenciais da API
import ccxt

try:
    exchange = ccxt.binance({
        'apiKey': 'your_api_key',
        'secret': 'your_secret',
        'sandbox': True  # Para teste
    })
    
    balance = exchange.fetch_balance()
    print("Credenciais válidas!")
    
except ccxt.AuthenticationError:
    print("Credenciais inválidas!")
except Exception as e:
    print(f"Erro: {e}")
```

**Verificar Rate Limiting:**
```powershell
# Verificar logs de rate limiting
Select-String -Path "data\logs\*.log" -Pattern "rate.limit|429|too.many.requests"

# Ajustar configurações de rate limiting
# Editar config/exchange_settings.json
```

### 2. Problemas de Proxy/Firewall

#### Sintomas
- Conexões HTTPS falham
- Timeouts intermitentes
- Erro "SSL certificate verify failed"

#### Soluções

**Configurar Proxy:**
```powershell
# Verificar configuração de proxy
netsh winhttp show proxy

# Configurar proxy se necessário
netsh winhttp set proxy proxy-server:port
```

**Configurar Certificados SSL:**
```python
# Desabilitar verificação SSL (apenas para teste)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

## Problemas de Performance

### 3. Alto Uso de CPU

#### Sintomas
- Sistema lento
- CPU constantemente acima de 80%
- Agentes demoram para responder

#### Causas Prováveis
- Muitos símbolos sendo monitorados
- Frequência de análise muito alta
- Loops infinitos em agentes
- Vazamentos de memória

#### Soluções

**Verificar Uso de CPU:**
```powershell
# Monitorar processos Python
Get-Process -Name python | Select-Object ProcessName, CPU, WorkingSet

# Verificar threads ativas
Get-WmiObject -Class Win32_Thread | Where-Object { $_.ProcessHandle -eq (Get-Process python).Id }
```

**Otimizar Configurações:**
```json
// Reduzir em config/trading_config.json
{
  "trading": {
    "symbols": ["BTCUSDT", "ETHUSDT"],  // Reduzir número de símbolos
    "analysis_interval": 60,            // Aumentar intervalo
    "max_concurrent_analysis": 2        // Limitar análises simultâneas
  }
}
```

**Implementar Throttling:**
```python
# Adicionar delays nos agentes
import time

def run_cycle(self):
    # Processamento normal
    process_data()
    
    # Throttling para reduzir CPU
    time.sleep(0.1)  # 100ms de pausa
```

### 4. Alto Uso de Memória

#### Sintomas
- Uso de RAM crescendo constantemente
- Erros "Out of Memory"
- Sistema trava ou fica muito lento

#### Causas Prováveis
- Vazamentos de memória
- Cache muito grande
- Histórico de dados não sendo limpo
- Objetos não sendo coletados pelo garbage collector

#### Soluções

**Monitorar Uso de Memória:**
```powershell
# Verificar uso de memória por processo
Get-Process python | Select-Object ProcessName, WorkingSet, VirtualMemorySize

# Monitorar crescimento ao longo do tempo
while ($true) {
    Get-Process python | Select-Object @{Name="Time";Expression={Get-Date}}, WorkingSet
    Start-Sleep 60
}
```

**Implementar Limpeza de Memória:**
```python
import gc
import psutil
import os

def cleanup_memory():
    # Forçar garbage collection
    gc.collect()
    
    # Verificar uso de memória
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    if memory_mb > 500:  # Se usar mais de 500MB
        # Limpar caches
        clear_caches()
        gc.collect()
```

**Configurar Limites de Cache:**
```json
{
  "cache": {
    "max_memory": "128mb",
    "eviction_policy": "allkeys-lru",
    "ttl": 300
  }
}
```

## Problemas de Agentes

### 5. Agente Para de Responder

#### Sintomas
- Agente não processa novos dados
- Status permanece "running" mas sem atividade
- Logs param de ser gerados

#### Causas Prováveis
- Deadlock em threads
- Exceção não tratada
- Dependência externa indisponível
- Corrupção de dados

#### Soluções

**Diagnosticar Agente:**
```powershell
# Verificar status dos agentes
.\scripts\monitor.ps1 -AgentStatus

# Verificar logs específicos do agente
Get-Content "data\logs\agents\market_analysis_agent.log" -Tail 50
```

**Reiniciar Agente Específico:**
```powershell
# Reiniciar agente problemático
.\scripts\monitor.ps1 -RestartAgent MarketAnalysisAgent

# Verificar se reiniciou corretamente
.\scripts\monitor.ps1 -AgentHealth MarketAnalysisAgent
```

**Implementar Watchdog:**
```python
import threading
import time

class AgentWatchdog:
    def __init__(self, agent, timeout=300):  # 5 minutos
        self.agent = agent
        self.timeout = timeout
        self.last_activity = time.time()
        
    def monitor(self):
        while True:
            if time.time() - self.last_activity > self.timeout:
                self.restart_agent()
            time.sleep(60)  # Verificar a cada minuto
    
    def restart_agent(self):
        self.agent.stop()
        time.sleep(5)
        self.agent.start()
        self.last_activity = time.time()
```

### 6. Erros de Sincronização entre Agentes

#### Sintomas
- Dados inconsistentes entre agentes
- Sinais conflitantes
- Erros de "data not found"

#### Causas Prováveis
- Race conditions
- Problemas de timing
- Cache desatualizado
- Falha na comunicação entre agentes

#### Soluções

**Implementar Locks:**
```python
import threading

class DataManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}
    
    def update_data(self, key, value):
        with self._lock:
            self._data[key] = value
    
    def get_data(self, key):
        with self._lock:
            return self._data.get(key)
```

**Configurar Timeouts:**
```json
{
  "agent_coordination": {
    "sync_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5
  }
}
```

## Problemas de Dados

### 7. Dados de Mercado Inconsistentes

#### Sintomas
- Preços muito diferentes do mercado real
- Gaps nos dados históricos
- Timestamps incorretos

#### Causas Prováveis
- Problemas na API da exchange
- Fuso horário incorreto
- Cache corrompido
- Falha na sincronização

#### Soluções

**Validar Dados:**
```python
def validate_market_data(data):
    # Verificar timestamps
    if not is_timestamp_valid(data['timestamp']):
        raise ValueError("Timestamp inválido")
    
    # Verificar preços
    if data['price'] <= 0:
        raise ValueError("Preço inválido")
    
    # Verificar sequência OHLC
    if not (data['low'] <= data['open'] <= data['high'] and
            data['low'] <= data['close'] <= data['high']):
        raise ValueError("Dados OHLC inconsistentes")
```

**Limpar Cache:**
```powershell
# Limpar cache Redis
redis-cli FLUSHALL

# Limpar cache local
Remove-Item "data\cache\*" -Recurse -Force
```

### 8. Falha no Salvamento de Dados

#### Sintomas
- Arquivos não são criados
- Dados não persistem entre reinicializações
- Erros de "Permission denied"

#### Causas Prováveis
- Permissões de arquivo incorretas
- Disco cheio
- Antivírus bloqueando escritas
- Caminho de arquivo inválido

#### Soluções

**Verificar Permissões:**
```powershell
# Verificar permissões do diretório
Get-Acl "data" | Format-List

# Ajustar permissões se necessário
icacls "data" /grant Users:F /T
```

**Verificar Espaço em Disco:**
```powershell
# Verificar espaço disponível
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, FreeSpace, Size
```

**Configurar Exceções no Antivírus:**
```powershell
# Adicionar exceção no Windows Defender
Add-MpPreference -ExclusionPath "C:\ScalpingSystem"
```

## Problemas de Configuração

### 9. Configurações Não Carregadas

#### Sintomas
- Sistema usa valores padrão
- Mudanças na configuração não têm efeito
- Erros de "Configuration not found"

#### Causas Prováveis
- Arquivo de configuração corrompido
- Sintaxe JSON inválida
- Caminho de arquivo incorreto
- Permissões de leitura

#### Soluções

**Validar JSON:**
```powershell
# Verificar sintaxe JSON
python -m json.tool config\trading_config.json
```

**Verificar Carregamento:**
```python
import json

def load_config(config_path):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("Configuração carregada com sucesso")
        return config
    except json.JSONDecodeError as e:
        print(f"Erro de sintaxe JSON: {e}")
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {config_path}")
    except Exception as e:
        print(f"Erro inesperado: {e}")
```

### 10. Problemas de Credenciais

#### Sintomas
- Erros de autenticação
- "Invalid API key" ou "Invalid signature"
- Acesso negado a recursos

#### Soluções

**Verificar Formato das Credenciais:**
```python
def validate_credentials(api_key, api_secret):
    # Verificar comprimento
    if len(api_key) != 64:
        return False, "API key deve ter 64 caracteres"
    
    if len(api_secret) != 64:
        return False, "API secret deve ter 64 caracteres"
    
    # Verificar caracteres válidos
    import re
    if not re.match(r'^[A-Za-z0-9]+$', api_key):
        return False, "API key contém caracteres inválidos"
    
    return True, "Credenciais válidas"
```

**Testar Permissões:**
```python
def test_api_permissions(exchange):
    try:
        # Testar leitura de saldo
        balance = exchange.fetch_balance()
        print("✓ Permissão de leitura OK")
        
        # Testar criação de ordem (modo teste)
        if exchange.sandbox:
            order = exchange.create_limit_buy_order('BTC/USDT', 0.001, 30000)
            exchange.cancel_order(order['id'])
            print("✓ Permissão de trading OK")
            
    except Exception as e:
        print(f"✗ Erro de permissão: {e}")
```

## Problemas de Monitoramento

### 11. Métricas Não Aparecem no Grafana

#### Sintomas
- Dashboards vazios
- Gráficos sem dados
- Erro "No data points"

#### Causas Prováveis
- Prometheus não coletando métricas
- Configuração incorreta do Grafana
- Firewall bloqueando portas
- Serviços não expostos

#### Soluções

**Verificar Prometheus:**
```powershell
# Verificar se Prometheus está coletando dados
curl http://localhost:9091/api/v1/targets

# Verificar métricas específicas
curl "http://localhost:9091/api/v1/query?query=scalping_signals_total"
```

**Verificar Conectividade:**
```powershell
# Testar conectividade entre serviços
Test-NetConnection scalping-system -Port 9090
Test-NetConnection prometheus -Port 9090
```

### 12. Alertas Não Funcionam

#### Sintomas
- Não recebe notificações
- Alertas não disparam
- Status sempre "OK"

#### Soluções

**Verificar Configuração de Alertas:**
```yaml
# monitoring/rules/scalping_alerts.yml
groups:
  - name: scalping.rules
    rules:
      - alert: HighErrorRate
        expr: rate(scalping_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Alta taxa de erros detectada"
```

**Testar Notificações:**
```powershell
# Testar webhook do Discord
curl -X POST "YOUR_DISCORD_WEBHOOK" -H "Content-Type: application/json" -d '{"content": "Teste de notificação"}'

# Testar bot do Telegram
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage?chat_id=YOUR_CHAT_ID&text=Teste"
```

## Comandos Úteis de Diagnóstico

### Verificação Geral do Sistema

```powershell
# Status geral
.\scripts\monitor.ps1 -SystemStatus

# Verificar todos os serviços
Get-Service | Where-Object { $_.Name -like "*scalping*" }

# Verificar processos Python
Get-Process python | Select-Object ProcessName, Id, CPU, WorkingSet

# Verificar conectividade de rede
Test-NetConnection api.binance.com -Port 443
Test-NetConnection localhost -Port 8080
Test-NetConnection localhost -Port 6379
```

### Análise de Logs

```powershell
# Logs de erro das últimas 24 horas
Get-ChildItem "data\logs" -Recurse -Filter "*.log" | 
    ForEach-Object { 
        Select-String -Path $_.FullName -Pattern "ERROR|CRITICAL" | 
        Where-Object { $_.Line -match (Get-Date).AddDays(-1).ToString("yyyy-MM-dd") }
    }

# Top 10 erros mais comuns
Select-String -Path "data\logs\*.log" -Pattern "ERROR" | 
    Group-Object Line | 
    Sort-Object Count -Descending | 
    Select-Object -First 10

# Análise de performance
Select-String -Path "data\logs\performance\*.log" -Pattern "execution_time" | 
    ForEach-Object { 
        if ($_.Line -match "execution_time: ([\d.]+)") { 
            [float]$matches[1] 
        } 
    } | Measure-Object -Average -Maximum -Minimum
```

### Limpeza e Manutenção

```powershell
# Limpeza de logs antigos (mais de 30 dias)
Get-ChildItem "data\logs" -Recurse -Filter "*.log" | 
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | 
    Remove-Item -Force

# Limpeza de cache
Remove-Item "data\cache\*" -Recurse -Force

# Reinicialização completa
.\scripts\deploy.ps1 -Restart -CleanCache
```

## Contato para Suporte

### Informações para Coleta antes do Contato

1. **Versão do Sistema:** Verificar em `VERSION` ou logs
2. **Sistema Operacional:** Windows version
3. **Logs Relevantes:** Últimas 100 linhas dos logs de erro
4. **Configuração:** Arquivos de configuração (sem credenciais)
5. **Reprodução:** Passos para reproduzir o problema

### Canais de Suporte

- **GitHub Issues:** https://github.com/esdrastrade/Market_Manus/issues
- **Documentação:** https://github.com/esdrastrade/Market_Manus/wiki
- **FAQ:** `docs/faq.md`

---

**Nota:** Este guia é atualizado regularmente. Verifique a versão mais recente na documentação online.

