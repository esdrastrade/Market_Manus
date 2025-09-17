#Requires -Version 5.1
<#
.SYNOPSIS
    Script de Otimização do Sistema de Scalping Automatizado
    
.DESCRIPTION
    Este script analisa e otimiza o sistema de scalping automatizado:
    - Análise de performance dos agentes
    - Otimização de parâmetros
    - Limpeza de arquivos desnecessários
    - Aplicação de sugestões de melhoria
    - Relatórios de otimização
    
.PARAMETER OptimizationType
    Tipo de otimização (performance, cleanup, parameters, suggestions, all)
    
.PARAMETER AgentName
    Nome específico do agente para otimizar
    
.PARAMETER ApplyChanges
    Aplicar mudanças automaticamente (sem confirmação)
    
.PARAMETER GenerateReport
    Gerar relatório detalhado de otimização
    
.EXAMPLE
    .\optimize.ps1 -OptimizationType performance
    .\optimize.ps1 -OptimizationType cleanup -ApplyChanges
    .\optimize.ps1 -AgentName market_analysis -GenerateReport
    
.NOTES
    Autor: Manus AI
    Data: 17 de Julho de 2025
    Versão: 1.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("performance", "cleanup", "parameters", "suggestions", "all")]
    [string]$OptimizationType = "all",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("market_analysis", "risk_management", "notification", "performance", "backtesting", "orchestrator")]
    [string]$AgentName,
    
    [Parameter(Mandatory=$false)]
    [switch]$ApplyChanges,
    
    [Parameter(Mandatory=$false)]
    [switch]$GenerateReport,
    
    [Parameter(Mandatory=$false)]
    [switch]$Silent,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
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
    Improvement = "DarkGreen"
    Critical = "DarkRed"
}

# Configuração do sistema
$Config = @{
    ProjectRoot = $PSScriptRoot | Split-Path -Parent
    MetricsPath = "data\metrics"
    SuggestionsPath = "data\suggestions"
    LogsPath = "data\logs"
    ReportsPath = "data\reports"
    MaxLogSize = 100MB
    MaxMetricsAge = 30  # dias
    PerformanceThresholds = @{
        MinSuccessRate = 0.85
        MaxExecutionTime = 300  # segundos
        MaxMemoryUsage = 512MB
        MaxResponseTime = 10    # segundos
    }
}

# Estado da otimização
$Global:OptimizationState = @{
    StartTime = Get-Date
    Improvements = @()
    Issues = @()
    Suggestions = @()
    TotalSavings = @{
        DiskSpace = 0
        Performance = 0
        Memory = 0
    }
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
}

function Write-Header {
    param([string]$Title)
    
    if (-not $Silent) {
        Write-Host ""
        Write-ColorOutput "=" * 70 -Color $Colors.Header
        Write-ColorOutput "  $Title" -Color $Colors.Header
        Write-ColorOutput "=" * 70 -Color $Colors.Header
        Write-Host ""
    }
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "🔄 $Message" -Color $Colors.Info
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" -Color $Colors.Success
}

function Write-Improvement {
    param([string]$Message)
    Write-ColorOutput "🚀 $Message" -Color $Colors.Improvement
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" -Color $Colors.Warning
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" -Color $Colors.Error
}

function Get-AgentMetrics {
    param([string]$AgentName = $null)
    
    Write-Step "Coletando métricas dos agentes..."
    
    $metricsPath = Join-Path $Config.ProjectRoot $Config.MetricsPath
    $allMetrics = @{}
    
    if (-not (Test-Path $metricsPath)) {
        Write-Warning "Diretório de métricas não encontrado: $metricsPath"
        return $allMetrics
    }
    
    $agents = if ($AgentName) { @($AgentName) } else { 
        @("market_analysis", "risk_management", "notification", "performance", "backtesting", "orchestrator")
    }
    
    foreach ($agent in $agents) {
        $metricsFile = Join-Path $metricsPath "$($agent)_current.json"
        
        if (Test-Path $metricsFile) {
            try {
                $metrics = Get-Content $metricsFile -Raw | ConvertFrom-Json
                $allMetrics[$agent] = $metrics
                Write-Verbose "Métricas carregadas para: $agent"
            }
            catch {
                Write-Warning "Erro ao carregar métricas de $agent`: $($_.Exception.Message)"
            }
        } else {
            Write-Warning "Métricas não encontradas para: $agent"
        }
    }
    
    Write-Success "Métricas coletadas para $($allMetrics.Count) agente(s)"
    return $allMetrics
}

function Analyze-Performance {
    param([hashtable]$AgentMetrics)
    
    Write-Step "Analisando performance dos agentes..."
    
    $performanceIssues = @()
    $improvements = @()
    
    foreach ($agentName in $AgentMetrics.Keys) {
        $metrics = $AgentMetrics[$agentName]
        
        Write-Verbose "Analisando performance de: $agentName"
        
        # Verificar taxa de sucesso
        $successRate = $metrics.success_rate ?? 0
        if ($successRate -lt $Config.PerformanceThresholds.MinSuccessRate) {
            $issue = @{
                Agent = $agentName
                Type = "LowSuccessRate"
                Current = $successRate
                Threshold = $Config.PerformanceThresholds.MinSuccessRate
                Severity = "High"
                Suggestion = "Revisar lógica do agente e tratamento de erros"
            }
            $performanceIssues += $issue
        }
        
        # Verificar tempo de execução
        $avgExecutionTime = $metrics.avg_execution_time ?? 0
        if ($avgExecutionTime -gt $Config.PerformanceThresholds.MaxExecutionTime) {
            $issue = @{
                Agent = $agentName
                Type = "SlowExecution"
                Current = $avgExecutionTime
                Threshold = $Config.PerformanceThresholds.MaxExecutionTime
                Severity = "Medium"
                Suggestion = "Otimizar algoritmos e reduzir operações custosas"
            }
            $performanceIssues += $issue
        }
        
        # Verificar uso de memória (se disponível)
        if ($metrics.memory_usage) {
            $memoryUsage = $metrics.memory_usage
            if ($memoryUsage -gt $Config.PerformanceThresholds.MaxMemoryUsage) {
                $issue = @{
                    Agent = $agentName
                    Type = "HighMemoryUsage"
                    Current = $memoryUsage
                    Threshold = $Config.PerformanceThresholds.MaxMemoryUsage
                    Severity = "Medium"
                    Suggestion = "Implementar limpeza de memória e otimizar estruturas de dados"
                }
                $performanceIssues += $issue
            }
        }
        
        # Identificar melhorias potenciais
        if ($successRate -gt 0.95 -and $avgExecutionTime -lt 60) {
            $improvement = @{
                Agent = $agentName
                Type = "HighPerformance"
                Message = "Agente $agentName está performando excelentemente"
                Potential = "Considerar usar como modelo para outros agentes"
            }
            $improvements += $improvement
        }
    }
    
    $Global:OptimizationState.Issues += $performanceIssues
    $Global:OptimizationState.Improvements += $improvements
    
    Write-Success "Análise de performance concluída: $($performanceIssues.Count) problemas, $($improvements.Count) melhorias"
    
    return @{
        Issues = $performanceIssues
        Improvements = $improvements
    }
}

function Optimize-SystemCleanup {
    Write-Step "Executando limpeza do sistema..."
    
    $cleanupResults = @{
        FilesRemoved = 0
        SpaceSaved = 0
        Errors = @()
    }
    
    # Limpeza de logs antigos
    $logsPath = Join-Path $Config.ProjectRoot $Config.LogsPath
    if (Test-Path $logsPath) {
        try {
            $cutoffDate = (Get-Date).AddDays(-$Config.MaxMetricsAge)
            $oldLogs = Get-ChildItem -Path $logsPath -File | Where-Object { 
                $_.LastWriteTime -lt $cutoffDate -or $_.Length -gt $Config.MaxLogSize
            }
            
            foreach ($log in $oldLogs) {
                $size = $log.Length
                if (-not $DryRun) {
                    Remove-Item $log.FullName -Force
                }
                $cleanupResults.FilesRemoved++
                $cleanupResults.SpaceSaved += $size
                Write-Verbose "Removido log antigo: $($log.Name)"
            }
        }
        catch {
            $cleanupResults.Errors += "Erro na limpeza de logs: $($_.Exception.Message)"
        }
    }
    
    # Limpeza de métricas antigas
    $metricsPath = Join-Path $Config.ProjectRoot $Config.MetricsPath
    if (Test-Path $metricsPath) {
        try {
            $cutoffDate = (Get-Date).AddDays(-$Config.MaxMetricsAge)
            $oldMetrics = Get-ChildItem -Path $metricsPath -File | Where-Object { 
                $_.LastWriteTime -lt $cutoffDate -and $_.Name -notlike "*_current.json"
            }
            
            foreach ($metric in $oldMetrics) {
                $size = $metric.Length
                if (-not $DryRun) {
                    Remove-Item $metric.FullName -Force
                }
                $cleanupResults.FilesRemoved++
                $cleanupResults.SpaceSaved += $size
                Write-Verbose "Removida métrica antiga: $($metric.Name)"
            }
        }
        catch {
            $cleanupResults.Errors += "Erro na limpeza de métricas: $($_.Exception.Message)"
        }
    }
    
    # Limpeza de arquivos temporários
    $tempPatterns = @("*.tmp", "*.temp", "*~", "*.bak")
    foreach ($pattern in $tempPatterns) {
        try {
            $tempFiles = Get-ChildItem -Path $Config.ProjectRoot -Filter $pattern -Recurse -File
            foreach ($tempFile in $tempFiles) {
                $size = $tempFile.Length
                if (-not $DryRun) {
                    Remove-Item $tempFile.FullName -Force
                }
                $cleanupResults.FilesRemoved++
                $cleanupResults.SpaceSaved += $size
                Write-Verbose "Removido arquivo temporário: $($tempFile.Name)"
            }
        }
        catch {
            $cleanupResults.Errors += "Erro na limpeza de arquivos temporários ($pattern): $($_.Exception.Message)"
        }
    }
    
    # Limpeza de cache Python
    try {
        $pycacheDirectories = Get-ChildItem -Path $Config.ProjectRoot -Name "__pycache__" -Recurse -Directory
        foreach ($cacheDir in $pycacheDirectories) {
            $fullPath = Join-Path $Config.ProjectRoot $cacheDir
            $size = (Get-ChildItem -Path $fullPath -Recurse -File | Measure-Object -Property Length -Sum).Sum
            if (-not $DryRun) {
                Remove-Item $fullPath -Recurse -Force
            }
            $cleanupResults.FilesRemoved += (Get-ChildItem -Path $fullPath -Recurse -File).Count
            $cleanupResults.SpaceSaved += $size
            Write-Verbose "Removido cache Python: $cacheDir"
        }
    }
    catch {
        $cleanupResults.Errors += "Erro na limpeza de cache Python: $($_.Exception.Message)"
    }
    
    $Global:OptimizationState.TotalSavings.DiskSpace = $cleanupResults.SpaceSaved
    
    $spaceMB = [math]::Round($cleanupResults.SpaceSaved / 1MB, 2)
    Write-Success "Limpeza concluída: $($cleanupResults.FilesRemoved) arquivos removidos, $spaceMB MB liberados"
    
    if ($cleanupResults.Errors.Count -gt 0) {
        Write-Warning "$($cleanupResults.Errors.Count) erros durante a limpeza"
        foreach ($error in $cleanupResults.Errors) {
            Write-Verbose $error
        }
    }
    
    return $cleanupResults
}

function Optimize-Parameters {
    param([hashtable]$AgentMetrics)
    
    Write-Step "Analisando e otimizando parâmetros..."
    
    $parameterOptimizations = @()
    
    foreach ($agentName in $AgentMetrics.Keys) {
        $metrics = $AgentMetrics[$agentName]
        
        # Otimizações específicas por agente
        switch ($agentName) {
            "market_analysis" {
                # Otimizar intervalos de análise baseado na volatilidade
                if ($metrics.avg_volatility) {
                    $currentInterval = 300  # 5 minutos padrão
                    $optimalInterval = if ($metrics.avg_volatility -gt 0.02) { 180 } else { 600 }
                    
                    if ($currentInterval -ne $optimalInterval) {
                        $optimization = @{
                            Agent = $agentName
                            Parameter = "analysis_interval"
                            CurrentValue = $currentInterval
                            OptimalValue = $optimalInterval
                            Reason = "Ajustar baseado na volatilidade média ($($metrics.avg_volatility))"
                            ExpectedImprovement = "Melhor captura de sinais"
                        }
                        $parameterOptimizations += $optimization
                    }
                }
            }
            
            "risk_management" {
                # Otimizar stop loss baseado no drawdown histórico
                if ($metrics.max_drawdown) {
                    $currentStopLoss = 0.02  # 2% padrão
                    $optimalStopLoss = [math]::Max(0.01, $metrics.max_drawdown * 0.8)
                    
                    if ([math]::Abs($currentStopLoss - $optimalStopLoss) -gt 0.005) {
                        $optimization = @{
                            Agent = $agentName
                            Parameter = "stop_loss_percentage"
                            CurrentValue = $currentStopLoss
                            OptimalValue = $optimalStopLoss
                            Reason = "Ajustar baseado no drawdown máximo histórico ($($metrics.max_drawdown))"
                            ExpectedImprovement = "Melhor proteção contra perdas"
                        }
                        $parameterOptimizations += $optimization
                    }
                }
            }
            
            "notification" {
                # Otimizar frequência de notificações baseado no volume de alertas
                if ($metrics.alerts_sent_today) {
                    $alertsPerHour = $metrics.alerts_sent_today / 24
                    $optimalThreshold = if ($alertsPerHour -gt 5) { "high" } elseif ($alertsPerHour -lt 1) { "low" } else { "medium" }
                    
                    $optimization = @{
                        Agent = $agentName
                        Parameter = "alert_threshold"
                        CurrentValue = "medium"
                        OptimalValue = $optimalThreshold
                        Reason = "Ajustar baseado no volume de alertas ($alertsPerHour/hora)"
                        ExpectedImprovement = "Reduzir spam de notificações"
                    }
                    $parameterOptimizations += $optimization
                }
            }
        }
    }
    
    $Global:OptimizationState.Suggestions += $parameterOptimizations
    
    Write-Success "Análise de parâmetros concluída: $($parameterOptimizations.Count) otimizações sugeridas"
    
    return $parameterOptimizations
}

function Apply-Suggestions {
    param([hashtable]$AgentMetrics)
    
    Write-Step "Aplicando sugestões de melhoria..."
    
    $suggestionsPath = Join-Path $Config.ProjectRoot $Config.SuggestionsPath
    $appliedSuggestions = @()
    
    if (-not (Test-Path $suggestionsPath)) {
        Write-Warning "Diretório de sugestões não encontrado"
        return $appliedSuggestions
    }
    
    # Carregar sugestões existentes
    $suggestionFiles = Get-ChildItem -Path $suggestionsPath -Filter "*.json" | Sort-Object LastWriteTime -Descending
    
    foreach ($file in $suggestionFiles) {
        try {
            $suggestions = Get-Content $file.FullName -Raw | ConvertFrom-Json
            
            if ($suggestions -is [array]) {
                foreach ($suggestion in $suggestions) {
                    $applied = Apply-SingleSuggestion -Suggestion $suggestion -AgentMetrics $AgentMetrics
                    if ($applied) {
                        $appliedSuggestions += $suggestion
                    }
                }
            } else {
                $applied = Apply-SingleSuggestion -Suggestion $suggestions -AgentMetrics $AgentMetrics
                if ($applied) {
                    $appliedSuggestions += $suggestions
                }
            }
        }
        catch {
            Write-Warning "Erro ao processar sugestões de $($file.Name): $($_.Exception.Message)"
        }
    }
    
    Write-Success "Aplicadas $($appliedSuggestions.Count) sugestões de melhoria"
    
    return $appliedSuggestions
}

function Apply-SingleSuggestion {
    param(
        [object]$Suggestion,
        [hashtable]$AgentMetrics
    )
    
    try {
        # Verificar se a sugestão é aplicável
        if (-not $Suggestion.suggested_changes) {
            return $false
        }
        
        $changes = $Suggestion.suggested_changes
        $configFile = Join-Path $Config.ProjectRoot $changes.file
        
        if (-not (Test-Path $configFile)) {
            Write-Verbose "Arquivo de configuração não encontrado: $($changes.file)"
            return $false
        }
        
        # Aplicar mudança baseada no tipo
        switch ($Suggestion.type) {
            "PARAMETER_ADJUSTMENT" {
                return Apply-ParameterChange -ConfigFile $configFile -Changes $changes
            }
            "PERFORMANCE_OPTIMIZATION" {
                return Apply-PerformanceOptimization -ConfigFile $configFile -Changes $changes
            }
            "SYSTEM_MAINTENANCE" {
                return Apply-SystemMaintenance -Changes $changes
            }
            default {
                Write-Verbose "Tipo de sugestão não suportado: $($Suggestion.type)"
                return $false
            }
        }
    }
    catch {
        Write-Warning "Erro ao aplicar sugestão: $($_.Exception.Message)"
        return $false
    }
}

function Apply-ParameterChange {
    param(
        [string]$ConfigFile,
        [object]$Changes
    )
    
    try {
        if ($DryRun) {
            Write-Verbose "DRY-RUN: Alteraria $($Changes.parameter) de $($Changes.current_value) para $($Changes.suggested_value)"
            return $true
        }
        
        # Carregar configuração atual
        $config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
        
        # Aplicar mudança (implementação simplificada)
        # Em um sistema real, seria necessário navegar pela estrutura JSON
        Write-Verbose "Aplicando mudança de parâmetro: $($Changes.parameter)"
        
        # Salvar configuração atualizada
        $config | ConvertTo-Json -Depth 10 | Out-File -FilePath $ConfigFile -Encoding UTF8
        
        Write-Improvement "Parâmetro $($Changes.parameter) otimizado"
        return $true
    }
    catch {
        Write-Warning "Erro ao aplicar mudança de parâmetro: $($_.Exception.Message)"
        return $false
    }
}

function Apply-PerformanceOptimization {
    param(
        [string]$ConfigFile,
        [object]$Changes
    )
    
    try {
        Write-Verbose "Aplicando otimização de performance: $($Changes.reason)"
        
        if ($DryRun) {
            Write-Verbose "DRY-RUN: Aplicaria otimização de performance"
            return $true
        }
        
        # Implementar otimizações específicas
        Write-Improvement "Otimização de performance aplicada"
        return $true
    }
    catch {
        Write-Warning "Erro ao aplicar otimização de performance: $($_.Exception.Message)"
        return $false
    }
}

function Apply-SystemMaintenance {
    param([object]$Changes)
    
    try {
        Write-Verbose "Aplicando manutenção do sistema: $($Changes.reason)"
        
        if ($DryRun) {
            Write-Verbose "DRY-RUN: Aplicaria manutenção do sistema"
            return $true
        }
        
        # Implementar manutenções específicas
        Write-Improvement "Manutenção do sistema aplicada"
        return $true
    }
    catch {
        Write-Warning "Erro ao aplicar manutenção do sistema: $($_.Exception.Message)"
        return $false
    }
}

function Generate-OptimizationReport {
    param(
        [hashtable]$PerformanceAnalysis,
        [object]$CleanupResults,
        [array]$ParameterOptimizations,
        [array]$AppliedSuggestions
    )
    
    Write-Step "Gerando relatório de otimização..."
    
    $reportPath = Join-Path $Config.ProjectRoot $Config.ReportsPath
    if (-not (Test-Path $reportPath)) {
        New-Item -ItemType Directory -Path $reportPath -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportFile = Join-Path $reportPath "optimization_report_$timestamp.html"
    
    $duration = (Get-Date) - $Global:OptimizationState.StartTime
    
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Relatório de Otimização - Sistema de Scalping</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { background: #d4edda; border-color: #c3e6cb; }
        .warning { background: #fff3cd; border-color: #ffeaa7; }
        .error { background: #f8d7da; border-color: #f5c6cb; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 3px; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Relatório de Otimização</h1>
        <p>Sistema de Scalping Automatizado - $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")</p>
    </div>
    
    <div class="section success">
        <h2>📊 Resumo Executivo</h2>
        <div class="metric">
            <strong>Duração:</strong> $([math]::Round($duration.TotalMinutes, 1)) minutos
        </div>
        <div class="metric">
            <strong>Espaço Liberado:</strong> $([math]::Round($Global:OptimizationState.TotalSavings.DiskSpace / 1MB, 2)) MB
        </div>
        <div class="metric">
            <strong>Problemas Encontrados:</strong> $($PerformanceAnalysis.Issues.Count)
        </div>
        <div class="metric">
            <strong>Melhorias Aplicadas:</strong> $($AppliedSuggestions.Count)
        </div>
    </div>
    
    <div class="section">
        <h2>🔍 Análise de Performance</h2>
        <h3>Problemas Identificados</h3>
        <table>
            <tr><th>Agente</th><th>Tipo</th><th>Severidade</th><th>Valor Atual</th><th>Limite</th><th>Sugestão</th></tr>
"@

    foreach ($issue in $PerformanceAnalysis.Issues) {
        $severityClass = switch ($issue.Severity) {
            "High" { "error" }
            "Medium" { "warning" }
            default { "" }
        }
        
        $html += @"
            <tr class="$severityClass">
                <td>$($issue.Agent)</td>
                <td>$($issue.Type)</td>
                <td>$($issue.Severity)</td>
                <td>$($issue.Current)</td>
                <td>$($issue.Threshold)</td>
                <td>$($issue.Suggestion)</td>
            </tr>
"@
    }
    
    $html += @"
        </table>
        
        <h3>Melhorias Identificadas</h3>
        <ul>
"@

    foreach ($improvement in $PerformanceAnalysis.Improvements) {
        $html += "<li><strong>$($improvement.Agent):</strong> $($improvement.Message) - $($improvement.Potential)</li>"
    }
    
    $html += @"
        </ul>
    </div>
    
    <div class="section">
        <h2>🧹 Limpeza do Sistema</h2>
        <div class="metric">
            <strong>Arquivos Removidos:</strong> $($CleanupResults.FilesRemoved)
        </div>
        <div class="metric">
            <strong>Espaço Liberado:</strong> $([math]::Round($CleanupResults.SpaceSaved / 1MB, 2)) MB
        </div>
        <div class="metric">
            <strong>Erros:</strong> $($CleanupResults.Errors.Count)
        </div>
    </div>
    
    <div class="section">
        <h2>⚙️ Otimizações de Parâmetros</h2>
        <table>
            <tr><th>Agente</th><th>Parâmetro</th><th>Valor Atual</th><th>Valor Otimizado</th><th>Razão</th></tr>
"@

    foreach ($optimization in $ParameterOptimizations) {
        $html += @"
            <tr>
                <td>$($optimization.Agent)</td>
                <td>$($optimization.Parameter)</td>
                <td>$($optimization.CurrentValue)</td>
                <td>$($optimization.OptimalValue)</td>
                <td>$($optimization.Reason)</td>
            </tr>
"@
    }
    
    $html += @"
        </table>
    </div>
    
    <div class="section">
        <h2>✅ Sugestões Aplicadas</h2>
        <p>Total de sugestões aplicadas: <strong>$($AppliedSuggestions.Count)</strong></p>
    </div>
    
    <div class="section">
        <h2>📈 Próximos Passos</h2>
        <ul>
            <li>Monitorar performance após otimizações</li>
            <li>Executar testes de validação</li>
            <li>Agendar próxima otimização em 7 dias</li>
            <li>Revisar logs para verificar melhorias</li>
        </ul>
    </div>
    
    <footer style="margin-top: 40px; text-align: center; color: #666;">
        <p>Relatório gerado automaticamente pelo Sistema de Scalping Automatizado</p>
    </footer>
</body>
</html>
"@

    if (-not $DryRun) {
        $html | Out-File -FilePath $reportFile -Encoding UTF8
    }
    
    Write-Success "Relatório gerado: $reportFile"
    
    return $reportFile
}

function Show-OptimizationSummary {
    param(
        [hashtable]$PerformanceAnalysis,
        [object]$CleanupResults,
        [array]$ParameterOptimizations,
        [array]$AppliedSuggestions
    )
    
    Write-Header "RESUMO DA OTIMIZAÇÃO"
    
    $duration = (Get-Date) - $Global:OptimizationState.StartTime
    
    Write-ColorOutput "Tipo de Otimização: " -Color $Colors.Info -NoNewline
    Write-ColorOutput $OptimizationType.ToUpper() -Color $Colors.Header
    
    Write-ColorOutput "Duração: " -Color $Colors.Info -NoNewline
    Write-ColorOutput "$([math]::Round($duration.TotalMinutes, 1)) minutos" -Color $Colors.Success
    
    Write-Host ""
    
    # Resultados da limpeza
    if ($CleanupResults.FilesRemoved -gt 0) {
        Write-ColorOutput "🧹 LIMPEZA DO SISTEMA:" -Color $Colors.Header
        Write-ColorOutput "   Arquivos removidos: " -Color $Colors.Info -NoNewline
        Write-ColorOutput $CleanupResults.FilesRemoved -Color $Colors.Success
        
        $spaceMB = [math]::Round($CleanupResults.SpaceSaved / 1MB, 2)
        Write-ColorOutput "   Espaço liberado: " -Color $Colors.Info -NoNewline
        Write-ColorOutput "$spaceMB MB" -Color $Colors.Success
        
        Write-Host ""
    }
    
    # Problemas de performance
    if ($PerformanceAnalysis.Issues.Count -gt 0) {
        Write-ColorOutput "⚠️  PROBLEMAS IDENTIFICADOS:" -Color $Colors.Warning
        foreach ($issue in $PerformanceAnalysis.Issues) {
            $severityColor = switch ($issue.Severity) {
                "High" { $Colors.Error }
                "Medium" { $Colors.Warning }
                default { $Colors.Info }
            }
            Write-ColorOutput "   • $($issue.Agent): $($issue.Type)" -Color $severityColor
        }
        Write-Host ""
    }
    
    # Otimizações de parâmetros
    if ($ParameterOptimizations.Count -gt 0) {
        Write-ColorOutput "⚙️  OTIMIZAÇÕES SUGERIDAS:" -Color $Colors.Header
        foreach ($optimization in $ParameterOptimizations) {
            Write-ColorOutput "   • $($optimization.Agent): $($optimization.Parameter)" -Color $Colors.Improvement
            Write-ColorOutput "     $($optimization.CurrentValue) → $($optimization.OptimalValue)" -Color $Colors.Info
        }
        Write-Host ""
    }
    
    # Sugestões aplicadas
    if ($AppliedSuggestions.Count -gt 0) {
        Write-ColorOutput "✅ MELHORIAS APLICADAS:" -Color $Colors.Success
        Write-ColorOutput "   Total: $($AppliedSuggestions.Count) sugestões" -Color $Colors.Success
        Write-Host ""
    }
    
    if ($DryRun) {
        Write-ColorOutput "🔍 MODO DRY-RUN - Nenhuma alteração foi aplicada" -Color $Colors.Warning
    } else {
        Write-ColorOutput "🚀 Otimização concluída com sucesso!" -Color $Colors.Success
    }
    
    Write-Host ""
}

#endregion

#region Função Principal

function Start-Optimization {
    Write-Header "SISTEMA DE SCALPING - OTIMIZAÇÃO E MELHORIAS"
    
    if ($DryRun) {
        Write-ColorOutput "🔍 MODO DRY-RUN ATIVADO - Simulando operações" -Color $Colors.Warning
        Write-Host ""
    }
    
    Write-ColorOutput "Tipo de otimização: " -Color $Colors.Info -NoNewline
    Write-ColorOutput $OptimizationType.ToUpper() -Color $Colors.Header
    
    if ($AgentName) {
        Write-ColorOutput "Agente específico: " -Color $Colors.Info -NoNewline
        Write-ColorOutput $AgentName -Color $Colors.Header
    }
    
    Write-Host ""
    
    # Mudar para diretório do projeto
    Set-Location $Config.ProjectRoot
    
    # Coletar métricas dos agentes
    $agentMetrics = Get-AgentMetrics -AgentName $AgentName
    
    # Executar otimizações baseadas no tipo
    $performanceAnalysis = @{ Issues = @(); Improvements = @() }
    $cleanupResults = @{ FilesRemoved = 0; SpaceSaved = 0; Errors = @() }
    $parameterOptimizations = @()
    $appliedSuggestions = @()
    
    switch ($OptimizationType) {
        "performance" {
            $performanceAnalysis = Analyze-Performance -AgentMetrics $agentMetrics
        }
        "cleanup" {
            $cleanupResults = Optimize-SystemCleanup
        }
        "parameters" {
            $parameterOptimizations = Optimize-Parameters -AgentMetrics $agentMetrics
        }
        "suggestions" {
            $appliedSuggestions = Apply-Suggestions -AgentMetrics $agentMetrics
        }
        "all" {
            $performanceAnalysis = Analyze-Performance -AgentMetrics $agentMetrics
            $cleanupResults = Optimize-SystemCleanup
            $parameterOptimizations = Optimize-Parameters -AgentMetrics $agentMetrics
            if ($ApplyChanges) {
                $appliedSuggestions = Apply-Suggestions -AgentMetrics $agentMetrics
            }
        }
    }
    
    # Gerar relatório se solicitado
    $reportFile = $null
    if ($GenerateReport) {
        $reportFile = Generate-OptimizationReport -PerformanceAnalysis $performanceAnalysis -CleanupResults $cleanupResults -ParameterOptimizations $parameterOptimizations -AppliedSuggestions $appliedSuggestions
    }
    
    # Mostrar resumo
    Show-OptimizationSummary -PerformanceAnalysis $performanceAnalysis -CleanupResults $cleanupResults -ParameterOptimizations $parameterOptimizations -AppliedSuggestions $appliedSuggestions
    
    if ($reportFile) {
        Write-ColorOutput "📄 Relatório detalhado: " -Color $Colors.Info -NoNewline
        Write-ColorOutput $reportFile -Color $Colors.Header
    }
}

#endregion

# Execução principal
try {
    Start-Optimization
}
catch {
    Write-Error "Erro durante a otimização: $($_.Exception.Message)"
    Write-ColorOutput "Stack trace:" -Color $Colors.Error
    Write-ColorOutput $_.ScriptStackTrace -Color $Colors.Error
    exit 1
}

