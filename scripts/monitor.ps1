#Requires -Version 5.1
<#
.SYNOPSIS
    Script de Monitoramento do Sistema de Scalping Automatizado
    
.DESCRIPTION
    Este script monitora continuamente o sistema de scalping, verificando:
    - Status dos agentes
    - Performance do sistema
    - Alertas e notificações
    - Métricas em tempo real
    - Saúde geral do sistema
    
.PARAMETER Environment
    Ambiente de monitoramento (development, production)
    
.PARAMETER Interval
    Intervalo de monitoramento em segundos (padrão: 60)
    
.PARAMETER Dashboard
    Exibir dashboard em tempo real
    
.PARAMETER LogLevel
    Nível de log (Info, Warning, Error)
    
.EXAMPLE
    .\monitor.ps1 -Environment production
    .\monitor.ps1 -Environment development -Interval 30 -Dashboard
    .\monitor.ps1 -LogLevel Warning
    
.NOTES
    Autor: Manus AI
    Data: 17 de Julho de 2025
    Versão: 1.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("development", "production")]
    [string]$Environment = "development",
    
    [Parameter(Mandatory=$false)]
    [ValidateRange(10, 3600)]
    [int]$Interval = 60,
    
    [Parameter(Mandatory=$false)]
    [switch]$Dashboard,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("Info", "Warning", "Error")]
    [string]$LogLevel = "Info",
    
    [Parameter(Mandatory=$false)]
    [switch]$Silent,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputFile
)

# Configurações globais
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Cores para output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
    Critical = "DarkRed"
    Good = "DarkGreen"
}

# Configuração do sistema
$Config = @{
    ProjectRoot = $PSScriptRoot | Split-Path -Parent
    LogPath = "data\logs"
    DataPath = "data"
    MetricsPath = "data\metrics"
    AlertsPath = "data\alerts"
    MaxLogLines = 1000
    HealthThresholds = @{
        CriticalMemory = 90
        CriticalCPU = 85
        MaxResponseTime = 30
        MinSuccessRate = 0.8
    }
}

# Estado global do monitoramento
$Global:MonitoringState = @{
    StartTime = Get-Date
    TotalChecks = 0
    Alerts = @()
    LastMetrics = @{}
    SystemHealth = "Unknown"
    IsRunning = $true
}

#region Funções Auxiliares

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    
    if (-not $Silent) {
        if ($NoNewline) {
            Write-Host $Message -ForegroundColor $Color -NoNewline
        } else {
            Write-Host $Message -ForegroundColor $Color
        }
    }
    
    # Log para arquivo se especificado
    if ($OutputFile) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "$timestamp - $Message" | Out-File -FilePath $OutputFile -Append -Encoding UTF8
    }
}

function Write-Header {
    param([string]$Title)
    
    if (-not $Silent) {
        Clear-Host
        Write-Host ""
        Write-ColorOutput "=" * 80 -Color $Colors.Header
        Write-ColorOutput "  $Title" -Color $Colors.Header
        Write-ColorOutput "=" * 80 -Color $Colors.Header
        Write-Host ""
    }
}

function Write-MonitorLog {
    param(
        [string]$Message,
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Verificar se deve exibir baseado no LogLevel
    $levelPriority = @{ "Info" = 1; "Warning" = 2; "Error" = 3 }
    $currentPriority = $levelPriority[$LogLevel]
    $messagePriority = $levelPriority[$Level]
    
    if ($messagePriority -ge $currentPriority) {
        $color = switch ($Level) {
            "Info" { $Colors.Info }
            "Warning" { $Colors.Warning }
            "Error" { $Colors.Error }
            default { "White" }
        }
        
        Write-ColorOutput $logMessage -Color $color
    }
    
    # Sempre salvar no log
    $logFile = Join-Path $Config.ProjectRoot "$($Config.LogPath)\monitor.log"
    $logMessage | Out-File -FilePath $logFile -Append -Encoding UTF8
}

function Get-AgentStatus {
    Write-MonitorLog "Verificando status dos agentes..." -Level "Info"
    
    $agents = @{
        "market_analysis" = @{ Name = "Market Analysis"; Schedule = "*/5 * * * *" }
        "risk_management" = @{ Name = "Risk Management"; Schedule = "*/1 * * * *" }
        "notification" = @{ Name = "Notification"; Schedule = "event_driven" }
        "performance" = @{ Name = "Performance"; Schedule = "0 */6 * * *" }
        "backtesting" = @{ Name = "Backtesting"; Schedule = "0 2 * * *" }
        "orchestrator" = @{ Name = "Orchestrator"; Schedule = "continuous" }
    }
    
    $agentStatus = @{}
    
    foreach ($agentKey in $agents.Keys) {
        $agent = $agents[$agentKey]
        $agentPath = Join-Path $Config.ProjectRoot "agents\$($agentKey)_agent.py"
        
        $status = @{
            Name = $agent.Name
            Schedule = $agent.Schedule
            Exists = Test-Path $agentPath
            LastRun = $null
            Status = "Unknown"
            Health = "Unknown"
            Metrics = @{}
        }
        
        # Verificar se arquivo existe
        if (-not $status.Exists) {
            $status.Status = "Missing"
            $status.Health = "Critical"
        } else {
            # Verificar métricas do agente
            $metricsFile = Join-Path $Config.ProjectRoot "$($Config.MetricsPath)\$($agentKey)_current.json"
            
            if (Test-Path $metricsFile) {
                try {
                    $metrics = Get-Content $metricsFile -Raw | ConvertFrom-Json
                    $status.Metrics = $metrics
                    $status.LastRun = $metrics.last_update
                    
                    # Determinar saúde baseado nas métricas
                    $status.Health = Get-AgentHealth -Metrics $metrics -AgentName $agentKey
                    $status.Status = "Active"
                }
                catch {
                    $status.Status = "Error"
                    $status.Health = "Critical"
                    Write-MonitorLog "Erro ao ler métricas do agente $agentKey`: $($_.Exception.Message)" -Level "Error"
                }
            } else {
                $status.Status = "No Metrics"
                $status.Health = "Warning"
            }
            
            # Verificar tarefa agendada (se aplicável)
            if ($Environment -eq "production" -and $agent.Schedule -ne "event_driven" -and $agent.Schedule -ne "continuous") {
                $taskName = "ScalpingSystem_$agentKey"
                $scheduledTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
                
                if ($scheduledTask) {
                    $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction SilentlyContinue
                    if ($taskInfo) {
                        $status.LastRun = $taskInfo.LastRunTime
                        $status.Status = $taskInfo.LastTaskResult -eq 0 ? "Success" : "Failed"
                    }
                }
            }
        }
        
        $agentStatus[$agentKey] = $status
    }
    
    return $agentStatus
}

function Get-AgentHealth {
    param(
        [object]$Metrics,
        [string]$AgentName
    )
    
    try {
        # Verificar timestamp da última atualização
        if ($Metrics.last_update) {
            $lastUpdate = [DateTime]::Parse($Metrics.last_update)
            $timeSinceUpdate = (Get-Date) - $lastUpdate
            
            # Se não atualizou nas últimas 2 horas, considerar problemático
            if ($timeSinceUpdate.TotalHours -gt 2) {
                return "Critical"
            }
            
            # Se não atualizou na última hora, warning
            if ($timeSinceUpdate.TotalHours -gt 1) {
                return "Warning"
            }
        }
        
        # Verificações específicas por agente
        switch ($AgentName) {
            "market_analysis" {
                $signalsCount = $Metrics.signals_generated_today ?? 0
                if ($signalsCount -eq 0) { return "Warning" }
                if ($signalsCount -lt 5) { return "Warning" }
                return "Good"
            }
            
            "risk_management" {
                $currentDrawdown = $Metrics.current_drawdown ?? 0
                if ($currentDrawdown -gt 0.1) { return "Critical" }
                if ($currentDrawdown -gt 0.05) { return "Warning" }
                return "Good"
            }
            
            "performance" {
                $healthScore = $Metrics.system_health.score ?? 0
                if ($healthScore -lt 40) { return "Critical" }
                if ($healthScore -lt 60) { return "Warning" }
                return "Good"
            }
            
            default {
                # Verificação genérica
                if ($Metrics.status -eq "error") { return "Critical" }
                if ($Metrics.status -eq "warning") { return "Warning" }
                return "Good"
            }
        }
    }
    catch {
        Write-MonitorLog "Erro ao avaliar saúde do agente $AgentName`: $($_.Exception.Message)" -Level "Error"
        return "Unknown"
    }
}

function Get-SystemMetrics {
    Write-MonitorLog "Coletando métricas do sistema..." -Level "Info"
    
    $metrics = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        System = @{}
        Agents = @{}
        Alerts = @{}
        Performance = @{}
    }
    
    # Métricas do sistema
    try {
        $cpu = Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
        $memory = Get-WmiObject -Class Win32_OperatingSystem
        $memoryUsed = [math]::Round((($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory) / $memory.TotalVisibleMemorySize) * 100, 2)
        
        $metrics.System = @{
            CPU = [math]::Round($cpu.Average, 2)
            Memory = $memoryUsed
            Uptime = (Get-Date) - $Global:MonitoringState.StartTime
            ProcessCount = (Get-Process).Count
        }
    }
    catch {
        Write-MonitorLog "Erro ao coletar métricas do sistema: $($_.Exception.Message)" -Level "Error"
    }
    
    # Métricas dos agentes
    $agentStatus = Get-AgentStatus
    $metrics.Agents = $agentStatus
    
    # Contar alertas ativos
    $alertsPath = Join-Path $Config.ProjectRoot $Config.AlertsPath
    if (Test-Path $alertsPath) {
        $alertFiles = Get-ChildItem -Path $alertsPath -Filter "*.json" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }
        $metrics.Alerts = @{
            Total = $alertFiles.Count
            Recent = ($alertFiles | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-1) }).Count
        }
    }
    
    # Métricas de performance
    $portfolioFile = Join-Path $Config.ProjectRoot "data\portfolio_history.json"
    if (Test-Path $portfolioFile) {
        try {
            $portfolio = Get-Content $portfolioFile -Raw | ConvertFrom-Json
            $metrics.Performance = @{
                CurrentValue = $portfolio.current_value ?? 0
                LastUpdate = $portfolio.last_update ?? "N/A"
            }
        }
        catch {
            Write-MonitorLog "Erro ao ler dados do portfolio: $($_.Exception.Message)" -Level "Warning"
        }
    }
    
    return $metrics
}

function Get-SystemHealth {
    param([hashtable]$Metrics)
    
    $healthScore = 100
    $issues = @()
    
    # Verificar CPU
    if ($Metrics.System.CPU -gt $Config.HealthThresholds.CriticalCPU) {
        $healthScore -= 20
        $issues += "CPU alto ($($Metrics.System.CPU)%)"
    }
    
    # Verificar memória
    if ($Metrics.System.Memory -gt $Config.HealthThresholds.CriticalMemory) {
        $healthScore -= 20
        $issues += "Memória alta ($($Metrics.System.Memory)%)"
    }
    
    # Verificar agentes
    $criticalAgents = $Metrics.Agents.Values | Where-Object { $_.Health -eq "Critical" }
    $warningAgents = $Metrics.Agents.Values | Where-Object { $_.Health -eq "Warning" }
    
    $healthScore -= ($criticalAgents.Count * 15)
    $healthScore -= ($warningAgents.Count * 5)
    
    if ($criticalAgents.Count -gt 0) {
        $issues += "$($criticalAgents.Count) agente(s) crítico(s)"
    }
    
    if ($warningAgents.Count -gt 0) {
        $issues += "$($warningAgents.Count) agente(s) com warning"
    }
    
    # Verificar alertas recentes
    if ($Metrics.Alerts.Recent -gt 5) {
        $healthScore -= 10
        $issues += "Muitos alertas recentes ($($Metrics.Alerts.Recent))"
    }
    
    # Determinar status
    $status = if ($healthScore -ge 80) { "Excellent" }
              elseif ($healthScore -ge 60) { "Good" }
              elseif ($healthScore -ge 40) { "Fair" }
              else { "Poor" }
    
    return @{
        Score = [math]::Max(0, $healthScore)
        Status = $status
        Issues = $issues
    }
}

function Show-Dashboard {
    param([hashtable]$Metrics)
    
    if ($Dashboard -and -not $Silent) {
        Write-Header "SISTEMA DE SCALPING - DASHBOARD EM TEMPO REAL"
        
        # Informações gerais
        Write-ColorOutput "🕒 Timestamp: " -Color $Colors.Info -NoNewline
        Write-ColorOutput $Metrics.Timestamp -Color "White"
        
        Write-ColorOutput "⏱️  Uptime: " -Color $Colors.Info -NoNewline
        Write-ColorOutput "$([math]::Round($Metrics.System.Uptime.TotalHours, 1))h" -Color "White"
        
        Write-ColorOutput "🔄 Checks: " -Color $Colors.Info -NoNewline
        Write-ColorOutput $Global:MonitoringState.TotalChecks -Color "White"
        
        Write-Host ""
        
        # Saúde do sistema
        $health = Get-SystemHealth -Metrics $Metrics
        $Global:MonitoringState.SystemHealth = $health.Status
        
        Write-ColorOutput "🏥 SAÚDE DO SISTEMA" -Color $Colors.Header
        Write-ColorOutput "   Status: " -Color $Colors.Info -NoNewline
        
        $healthColor = switch ($health.Status) {
            "Excellent" { $Colors.Good }
            "Good" { $Colors.Success }
            "Fair" { $Colors.Warning }
            "Poor" { $Colors.Error }
            default { "White" }
        }
        
        Write-ColorOutput "$($health.Status) ($($health.Score)/100)" -Color $healthColor
        
        if ($health.Issues.Count -gt 0) {
            Write-ColorOutput "   Problemas:" -Color $Colors.Warning
            foreach ($issue in $health.Issues) {
                Write-ColorOutput "     • $issue" -Color $Colors.Warning
            }
        }
        
        Write-Host ""
        
        # Métricas do sistema
        Write-ColorOutput "💻 RECURSOS DO SISTEMA" -Color $Colors.Header
        Write-ColorOutput "   CPU: " -Color $Colors.Info -NoNewline
        $cpuColor = if ($Metrics.System.CPU -gt 80) { $Colors.Error } elseif ($Metrics.System.CPU -gt 60) { $Colors.Warning } else { $Colors.Success }
        Write-ColorOutput "$($Metrics.System.CPU)%" -Color $cpuColor
        
        Write-ColorOutput "   Memória: " -Color $Colors.Info -NoNewline
        $memColor = if ($Metrics.System.Memory -gt 80) { $Colors.Error } elseif ($Metrics.System.Memory -gt 60) { $Colors.Warning } else { $Colors.Success }
        Write-ColorOutput "$($Metrics.System.Memory)%" -Color $memColor
        
        Write-ColorOutput "   Processos: " -Color $Colors.Info -NoNewline
        Write-ColorOutput $Metrics.System.ProcessCount -Color "White"
        
        Write-Host ""
        
        # Status dos agentes
        Write-ColorOutput "🤖 STATUS DOS AGENTES" -Color $Colors.Header
        
        foreach ($agentKey in $Metrics.Agents.Keys) {
            $agent = $Metrics.Agents[$agentKey]
            
            $statusIcon = switch ($agent.Health) {
                "Good" { "✅" }
                "Warning" { "⚠️" }
                "Critical" { "❌" }
                default { "❓" }
            }
            
            $statusColor = switch ($agent.Health) {
                "Good" { $Colors.Success }
                "Warning" { $Colors.Warning }
                "Critical" { $Colors.Error }
                default { "White" }
            }
            
            Write-ColorOutput "   $statusIcon " -Color $statusColor -NoNewline
            Write-ColorOutput "$($agent.Name): " -Color $Colors.Info -NoNewline
            Write-ColorOutput $agent.Status -Color $statusColor
            
            if ($agent.LastRun) {
                $lastRun = try { [DateTime]::Parse($agent.LastRun) } catch { $null }
                if ($lastRun) {
                    $timeSince = (Get-Date) - $lastRun
                    $timeText = if ($timeSince.TotalMinutes -lt 60) { 
                        "$([math]::Round($timeSince.TotalMinutes))m atrás" 
                    } else { 
                        "$([math]::Round($timeSince.TotalHours, 1))h atrás" 
                    }
                    Write-ColorOutput "     Última execução: $timeText" -Color "Gray"
                }
            }
        }
        
        Write-Host ""
        
        # Alertas
        if ($Metrics.Alerts.Total -gt 0) {
            Write-ColorOutput "🚨 ALERTAS" -Color $Colors.Header
            Write-ColorOutput "   Total (24h): " -Color $Colors.Info -NoNewline
            Write-ColorOutput $Metrics.Alerts.Total -Color $Colors.Warning
            
            Write-ColorOutput "   Recentes (1h): " -Color $Colors.Info -NoNewline
            $recentColor = if ($Metrics.Alerts.Recent -gt 5) { $Colors.Error } elseif ($Metrics.Alerts.Recent -gt 0) { $Colors.Warning } else { $Colors.Success }
            Write-ColorOutput $Metrics.Alerts.Recent -Color $recentColor
            
            Write-Host ""
        }
        
        # Performance
        if ($Metrics.Performance.CurrentValue -gt 0) {
            Write-ColorOutput "📊 PERFORMANCE" -Color $Colors.Header
            Write-ColorOutput "   Portfolio: " -Color $Colors.Info -NoNewline
            Write-ColorOutput "$($Metrics.Performance.CurrentValue.ToString('C'))" -Color $Colors.Success
            
            Write-Host ""
        }
        
        # Instruções
        Write-ColorOutput "⌨️  CONTROLES" -Color $Colors.Header
        Write-ColorOutput "   Ctrl+C: Parar monitoramento" -Color "Gray"
        Write-ColorOutput "   Próxima atualização em $Interval segundos..." -Color "Gray"
        
        Write-Host ""
    }
}

function Check-Alerts {
    param([hashtable]$Metrics)
    
    $newAlerts = @()
    
    # Verificar CPU alto
    if ($Metrics.System.CPU -gt $Config.HealthThresholds.CriticalCPU) {
        $newAlerts += @{
            Type = "SystemAlert"
            Level = "Critical"
            Message = "CPU usage crítico: $($Metrics.System.CPU)%"
            Timestamp = Get-Date
        }
    }
    
    # Verificar memória alta
    if ($Metrics.System.Memory -gt $Config.HealthThresholds.CriticalMemory) {
        $newAlerts += @{
            Type = "SystemAlert"
            Level = "Critical"
            Message = "Uso de memória crítico: $($Metrics.System.Memory)%"
            Timestamp = Get-Date
        }
    }
    
    # Verificar agentes críticos
    $criticalAgents = $Metrics.Agents.Values | Where-Object { $_.Health -eq "Critical" }
    foreach ($agent in $criticalAgents) {
        $newAlerts += @{
            Type = "AgentAlert"
            Level = "Critical"
            Message = "Agente $($agent.Name) em estado crítico"
            Timestamp = Get-Date
        }
    }
    
    # Processar novos alertas
    foreach ($alert in $newAlerts) {
        Write-MonitorLog "ALERTA [$($alert.Level)]: $($alert.Message)" -Level "Error"
        
        # Salvar alerta em arquivo
        $alertFile = Join-Path $Config.ProjectRoot "$($Config.AlertsPath)\monitor_alert_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        $alert | ConvertTo-Json | Out-File -FilePath $alertFile -Encoding UTF8
        
        $Global:MonitoringState.Alerts += $alert
    }
    
    # Manter apenas alertas das últimas 24 horas
    $cutoff = (Get-Date).AddHours(-24)
    $Global:MonitoringState.Alerts = $Global:MonitoringState.Alerts | Where-Object { $_.Timestamp -gt $cutoff }
}

function Save-MonitoringMetrics {
    param([hashtable]$Metrics)
    
    try {
        $metricsFile = Join-Path $Config.ProjectRoot "$($Config.MetricsPath)\monitoring_current.json"
        
        # Adicionar informações de monitoramento
        $Metrics.Monitoring = @{
            TotalChecks = $Global:MonitoringState.TotalChecks
            SystemHealth = $Global:MonitoringState.SystemHealth
            ActiveAlerts = $Global:MonitoringState.Alerts.Count
            Uptime = $Global:MonitoringState.StartTime
        }
        
        $Metrics | ConvertTo-Json -Depth 10 | Out-File -FilePath $metricsFile -Encoding UTF8
        
        Write-MonitorLog "Métricas salvas em: $metricsFile" -Level "Info"
    }
    catch {
        Write-MonitorLog "Erro ao salvar métricas: $($_.Exception.Message)" -Level "Error"
    }
}

#endregion

#region Função Principal

function Start-Monitoring {
    Write-MonitorLog "Iniciando monitoramento do sistema de scalping..." -Level "Info"
    Write-MonitorLog "Ambiente: $Environment" -Level "Info"
    Write-MonitorLog "Intervalo: $Interval segundos" -Level "Info"
    Write-MonitorLog "Dashboard: $Dashboard" -Level "Info"
    
    # Configurar handler para Ctrl+C
    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
        Write-MonitorLog "Monitoramento interrompido pelo usuário" -Level "Info"
        $Global:MonitoringState.IsRunning = $false
    }
    
    # Loop principal de monitoramento
    while ($Global:MonitoringState.IsRunning) {
        try {
            $Global:MonitoringState.TotalChecks++
            
            # Coletar métricas
            $metrics = Get-SystemMetrics
            $Global:MonitoringState.LastMetrics = $metrics
            
            # Verificar alertas
            Check-Alerts -Metrics $metrics
            
            # Salvar métricas
            Save-MonitoringMetrics -Metrics $metrics
            
            # Exibir dashboard se solicitado
            Show-Dashboard -Metrics $metrics
            
            # Aguardar próximo ciclo
            Start-Sleep -Seconds $Interval
            
        }
        catch {
            Write-MonitorLog "Erro durante monitoramento: $($_.Exception.Message)" -Level "Error"
            Start-Sleep -Seconds 10  # Pausa menor em caso de erro
        }
    }
    
    Write-MonitorLog "Monitoramento finalizado" -Level "Info"
}

#endregion

# Verificar se diretórios existem
$requiredDirs = @($Config.LogPath, $Config.MetricsPath, $Config.AlertsPath)
foreach ($dir in $requiredDirs) {
    $fullPath = Join-Path $Config.ProjectRoot $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}

# Execução principal
try {
    # Mudar para diretório do projeto
    Set-Location $Config.ProjectRoot
    
    # Iniciar monitoramento
    Start-Monitoring
}
catch {
    Write-MonitorLog "Erro crítico no monitoramento: $($_.Exception.Message)" -Level "Error"
    Write-ColorOutput "Stack trace:" -Color $Colors.Error
    Write-ColorOutput $_.ScriptStackTrace -Color $Colors.Error
    exit 1
}
finally {
    # Cleanup
    $Global:MonitoringState.IsRunning = $false
    Write-MonitorLog "Limpeza finalizada" -Level "Info"
}

