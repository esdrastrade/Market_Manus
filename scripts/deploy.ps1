#Requires -Version 5.1
<#
.SYNOPSIS
    Script de Deployment do Sistema de Scalping Automatizado
    
.DESCRIPTION
    Este script automatiza o deployment, configuração e inicialização do sistema de scalping.
    Inclui verificação de dependências, configuração de ambiente e inicialização dos agentes.
    
.PARAMETER Environment
    Ambiente de deployment (development, production)
    
.PARAMETER AgentName
    Nome específico do agente para executar (opcional)
    
.PARAMETER Force
    Força reinstalação de dependências
    
.EXAMPLE
    .\deploy.ps1 -Environment development
    .\deploy.ps1 -Environment production -Force
    .\deploy.ps1 -AgentName market_analysis
    
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
    [ValidateSet("market_analysis", "risk_management", "notification", "performance", "backtesting", "orchestrator")]
    [string]$AgentName,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDependencies,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

# Configurações globais
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Cores para output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

# Configuração do sistema
$Config = @{
    ProjectRoot = $PSScriptRoot | Split-Path -Parent
    PythonMinVersion = "3.8"
    RequiredPackages = @("pandas", "numpy", "requests", "schedule")
    LogPath = "data\logs"
    DataPath = "data"
    ConfigPath = "config"
}

#region Funções Auxiliares

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    
    if ($NoNewline) {
        Write-Host $Message -ForegroundColor $Color -NoNewline
    } else {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Write-Header {
    param([string]$Title)
    
    Write-Host ""
    Write-ColorOutput "=" * 60 -Color $Colors.Header
    Write-ColorOutput "  $Title" -Color $Colors.Header
    Write-ColorOutput "=" * 60 -Color $Colors.Header
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "🔄 $Message" -Color $Colors.Info
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" -Color $Colors.Success
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" -Color $Colors.Warning
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" -Color $Colors.Error
}

function Test-PythonInstallation {
    Write-Step "Verificando instalação do Python..."
    
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python não encontrado"
        }
        
        $versionMatch = $pythonVersion -match "Python (\d+\.\d+)"
        if (-not $versionMatch) {
            throw "Não foi possível determinar a versão do Python"
        }
        
        $version = [version]$matches[1]
        $minVersion = [version]$Config.PythonMinVersion
        
        if ($version -lt $minVersion) {
            throw "Python $($Config.PythonMinVersion) ou superior é necessário. Versão atual: $version"
        }
        
        Write-Success "Python $version encontrado"
        return $true
    }
    catch {
        Write-Error "Erro na verificação do Python: $($_.Exception.Message)"
        return $false
    }
}

function Install-PythonDependencies {
    param([bool]$Force = $false)
    
    Write-Step "Instalando dependências Python..."
    
    try {
        $requirementsFile = Join-Path $Config.ProjectRoot "requirements.txt"
        
        if (-not (Test-Path $requirementsFile)) {
            Write-Warning "Arquivo requirements.txt não encontrado. Instalando pacotes básicos..."
            
            foreach ($package in $Config.RequiredPackages) {
                Write-Step "Instalando $package..."
                python -m pip install $package --quiet
                if ($LASTEXITCODE -ne 0) {
                    throw "Falha ao instalar $package"
                }
            }
        } else {
            $installArgs = @("-m", "pip", "install", "-r", $requirementsFile, "--quiet")
            if ($Force) {
                $installArgs += "--force-reinstall"
            }
            
            python @installArgs
            if ($LASTEXITCODE -ne 0) {
                throw "Falha ao instalar dependências do requirements.txt"
            }
        }
        
        Write-Success "Dependências Python instaladas com sucesso"
        return $true
    }
    catch {
        Write-Error "Erro na instalação de dependências: $($_.Exception.Message)"
        return $false
    }
}

function Initialize-DirectoryStructure {
    Write-Step "Inicializando estrutura de diretórios..."
    
    $directories = @(
        "data\historical",
        "data\logs", 
        "data\reports",
        "data\signals",
        "data\metrics",
        "data\alerts",
        "data\suggestions",
        "tests\unit_tests",
        "tests\integration_tests",
        "docs"
    )
    
    foreach ($dir in $directories) {
        $fullPath = Join-Path $Config.ProjectRoot $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Verbose "Criado diretório: $dir"
        }
    }
    
    Write-Success "Estrutura de diretórios inicializada"
}

function Test-AgentConfiguration {
    Write-Step "Verificando configurações dos agentes..."
    
    $configFiles = @(
        "config\trading_config.json",
        "config\risk_parameters.json", 
        "config\exchange_settings.json"
    )
    
    $allValid = $true
    
    foreach ($configFile in $configFiles) {
        $fullPath = Join-Path $Config.ProjectRoot $configFile
        
        if (-not (Test-Path $fullPath)) {
            Write-Warning "Arquivo de configuração não encontrado: $configFile"
            $allValid = $false
            continue
        }
        
        try {
            $content = Get-Content $fullPath -Raw | ConvertFrom-Json
            Write-Verbose "Configuração válida: $configFile"
        }
        catch {
            Write-Error "Configuração inválida: $configFile - $($_.Exception.Message)"
            $allValid = $false
        }
    }
    
    if ($allValid) {
        Write-Success "Todas as configurações são válidas"
    }
    
    return $allValid
}

function Start-Agent {
    param(
        [string]$AgentName,
        [string]$Environment
    )
    
    Write-Step "Iniciando agente: $AgentName"
    
    $agentPath = Join-Path $Config.ProjectRoot "agents\$($AgentName)_agent.py"
    
    if (-not (Test-Path $agentPath)) {
        Write-Error "Agente não encontrado: $agentPath"
        return $false
    }
    
    try {
        # Executar agente em modo de teste primeiro
        Write-Step "Testando agente $AgentName..."
        $testResult = python $agentPath --test 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Teste do agente $AgentName falhou: $testResult"
            return $false
        }
        
        Write-Success "Agente $AgentName testado com sucesso"
        
        # Se for ambiente de produção, configurar como serviço/task
        if ($Environment -eq "production") {
            Register-AgentTask -AgentName $AgentName
        }
        
        return $true
    }
    catch {
        Write-Error "Erro ao iniciar agente $AgentName: $($_.Exception.Message)"
        return $false
    }
}

function Register-AgentTask {
    param([string]$AgentName)
    
    Write-Step "Registrando tarefa agendada para $AgentName..."
    
    # Configurações de schedule por agente
    $schedules = @{
        "market_analysis" = "*/5 * * * *"    # A cada 5 minutos
        "risk_management" = "*/1 * * * *"    # A cada 1 minuto  
        "notification" = "event_driven"      # Baseado em eventos
        "performance" = "0 */6 * * *"        # A cada 6 horas
        "backtesting" = "0 2 * * *"          # Diário às 2:00
        "orchestrator" = "continuous"        # Contínuo
    }
    
    $schedule = $schedules[$AgentName]
    if (-not $schedule) {
        Write-Warning "Schedule não definido para $AgentName"
        return
    }
    
    if ($schedule -eq "event_driven" -or $schedule -eq "continuous") {
        Write-Warning "Agente $AgentName requer execução manual ou contínua"
        return
    }
    
    try {
        $taskName = "ScalpingSystem_$AgentName"
        $agentPath = Join-Path $Config.ProjectRoot "agents\$($AgentName)_agent.py"
        $pythonPath = (Get-Command python).Source
        
        # Remover tarefa existente se houver
        $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        }
        
        # Converter schedule cron para Windows Task Scheduler
        $trigger = Convert-CronToTrigger -CronExpression $schedule
        
        $action = New-ScheduledTaskAction -Execute $pythonPath -Argument $agentPath
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Sistema de Scalping - Agente $AgentName"
        
        Write-Success "Tarefa agendada registrada: $taskName"
    }
    catch {
        Write-Error "Erro ao registrar tarefa para $AgentName: $($_.Exception.Message)"
    }
}

function Convert-CronToTrigger {
    param([string]$CronExpression)
    
    # Conversão simplificada de cron para Windows Task Scheduler
    switch -Regex ($CronExpression) {
        "^\*/5 \* \* \* \*$" {
            # A cada 5 minutos
            return New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
        }
        "^\*/1 \* \* \* \*$" {
            # A cada 1 minuto
            return New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1)
        }
        "^0 \*/6 \* \* \*$" {
            # A cada 6 horas
            return New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6)
        }
        "^0 2 \* \* \*$" {
            # Diário às 2:00
            return New-ScheduledTaskTrigger -Daily -At "2:00AM"
        }
        default {
            # Padrão: a cada hora
            return New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)
        }
    }
}

function Start-SystemMonitoring {
    Write-Step "Iniciando monitoramento do sistema..."
    
    $monitorScript = Join-Path $PSScriptRoot "monitor.ps1"
    
    if (Test-Path $monitorScript) {
        try {
            Start-Process powershell -ArgumentList "-File `"$monitorScript`" -Environment $Environment" -WindowStyle Minimized
            Write-Success "Monitoramento iniciado em background"
        }
        catch {
            Write-Warning "Não foi possível iniciar o monitoramento automaticamente: $($_.Exception.Message)"
            Write-ColorOutput "Execute manualmente: .\scripts\monitor.ps1 -Environment $Environment" -Color $Colors.Info
        }
    } else {
        Write-Warning "Script de monitoramento não encontrado: $monitorScript"
    }
}

function Show-DeploymentSummary {
    param(
        [hashtable]$Results,
        [string]$Environment
    )
    
    Write-Header "RESUMO DO DEPLOYMENT"
    
    Write-ColorOutput "Ambiente: " -Color $Colors.Info -NoNewline
    Write-ColorOutput $Environment.ToUpper() -Color $Colors.Header
    
    Write-ColorOutput "Diretório: " -Color $Colors.Info -NoNewline
    Write-ColorOutput $Config.ProjectRoot -Color $Colors.Header
    
    Write-Host ""
    Write-ColorOutput "STATUS DOS COMPONENTES:" -Color $Colors.Header
    
    foreach ($component in $Results.Keys) {
        $status = if ($Results[$component]) { "✅ OK" } else { "❌ FALHA" }
        $color = if ($Results[$component]) { $Colors.Success } else { $Colors.Error }
        
        Write-ColorOutput "  $component`: " -Color $Colors.Info -NoNewline
        Write-ColorOutput $status -Color $color
    }
    
    Write-Host ""
    
    if ($Environment -eq "production") {
        Write-ColorOutput "PRÓXIMOS PASSOS:" -Color $Colors.Header
        Write-ColorOutput "  1. Verificar tarefas agendadas: Get-ScheduledTask -TaskName 'ScalpingSystem_*'" -Color $Colors.Info
        Write-ColorOutput "  2. Monitorar logs: Get-Content data\logs\agents.log -Wait" -Color $Colors.Info
        Write-ColorOutput "  3. Executar monitoramento: .\scripts\monitor.ps1" -Color $Colors.Info
    } else {
        Write-ColorOutput "COMANDOS PARA TESTE:" -Color $Colors.Header
        Write-ColorOutput "  # Testar agente individual" -Color $Colors.Info
        Write-ColorOutput "  python agents\market_analysis_agent.py --test" -Color $Colors.Info
        Write-ColorOutput "  " -Color $Colors.Info
        Write-ColorOutput "  # Executar orquestrador" -Color $Colors.Info
        Write-ColorOutput "  python agents\orchestrator_agent.py --test" -Color $Colors.Info
    }
    
    Write-Host ""
}

#endregion

#region Função Principal

function Start-Deployment {
    Write-Header "SISTEMA DE SCALPING AUTOMATIZADO - DEPLOYMENT"
    
    Write-ColorOutput "Iniciando deployment no ambiente: " -Color $Colors.Info -NoNewline
    Write-ColorOutput $Environment.ToUpper() -Color $Colors.Header
    Write-Host ""
    
    # Mudar para diretório do projeto
    Set-Location $Config.ProjectRoot
    
    # Resultados do deployment
    $results = @{}
    
    # 1. Verificar Python
    $results["Python"] = Test-PythonInstallation
    if (-not $results["Python"]) {
        Write-Error "Python não está instalado ou configurado corretamente"
        return
    }
    
    # 2. Instalar dependências
    if (-not $SkipDependencies) {
        $results["Dependências"] = Install-PythonDependencies -Force:$Force
        if (-not $results["Dependências"]) {
            Write-Error "Falha na instalação de dependências"
            return
        }
    } else {
        Write-Warning "Pulando instalação de dependências"
        $results["Dependências"] = $true
    }
    
    # 3. Inicializar estrutura
    Initialize-DirectoryStructure
    $results["Estrutura"] = $true
    
    # 4. Verificar configurações
    $results["Configurações"] = Test-AgentConfiguration
    
    # 5. Testar agentes
    if ($AgentName) {
        # Testar agente específico
        $results["Agente $AgentName"] = Start-Agent -AgentName $AgentName -Environment $Environment
    } else {
        # Testar todos os agentes
        $agents = @("market_analysis", "risk_management", "notification", "performance", "backtesting")
        
        foreach ($agent in $agents) {
            $results["Agente $agent"] = Start-Agent -AgentName $agent -Environment $Environment
        }
        
        # Orquestrador por último
        $results["Orquestrador"] = Start-Agent -AgentName "orchestrator" -Environment $Environment
    }
    
    # 6. Iniciar monitoramento (apenas em produção)
    if ($Environment -eq "production" -and -not $AgentName) {
        Start-SystemMonitoring
        $results["Monitoramento"] = $true
    }
    
    # 7. Mostrar resumo
    Show-DeploymentSummary -Results $results -Environment $Environment
    
    # Verificar se houve falhas críticas
    $criticalFailures = @("Python", "Dependências")
    $hasCriticalFailures = $criticalFailures | Where-Object { -not $results[$_] }
    
    if ($hasCriticalFailures) {
        Write-Error "Deployment falhou devido a problemas críticos"
        exit 1
    }
    
    Write-Success "Deployment concluído com sucesso!"
}

#endregion

# Execução principal
try {
    Start-Deployment
}
catch {
    Write-Error "Erro durante o deployment: $($_.Exception.Message)"
    Write-ColorOutput "Stack trace:" -Color $Colors.Error
    Write-ColorOutput $_.ScriptStackTrace -Color $Colors.Error
    exit 1
}
finally {
    # Restaurar diretório original
    if ($PWD.Path -ne $originalLocation) {
        Set-Location $originalLocation
    }
}

