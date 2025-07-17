#Requires -Version 5.1
<#
.SYNOPSIS
    Script de Backup e Versionamento do Sistema de Scalping Automatizado
    
.DESCRIPTION
    Este script automatiza o backup de dados, configurações e versionamento do sistema:
    - Backup de dados históricos e logs
    - Backup de configurações
    - Commit automático para Git
    - Compressão e arquivamento
    - Limpeza de arquivos antigos
    
.PARAMETER BackupType
    Tipo de backup (full, incremental, config, data)
    
.PARAMETER Destination
    Diretório de destino para backup
    
.PARAMETER GitCommit
    Fazer commit automático no Git
    
.PARAMETER Compress
    Comprimir arquivos de backup
    
.PARAMETER RetentionDays
    Dias de retenção para backups antigos
    
.EXAMPLE
    .\backup.ps1 -BackupType full
    .\backup.ps1 -BackupType incremental -GitCommit
    .\backup.ps1 -BackupType config -Destination "D:\Backups"
    
.NOTES
    Autor: Manus AI
    Data: 17 de Julho de 2025
    Versão: 1.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("full", "incremental", "config", "data", "logs")]
    [string]$BackupType = "incremental",
    
    [Parameter(Mandatory=$false)]
    [string]$Destination,
    
    [Parameter(Mandatory=$false)]
    [switch]$GitCommit,
    
    [Parameter(Mandatory=$false)]
    [switch]$Compress,
    
    [Parameter(Mandatory=$false)]
    [ValidateRange(1, 365)]
    [int]$RetentionDays = 30,
    
    [Parameter(Mandatory=$false)]
    [switch]$Silent,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
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
    DefaultBackupPath = "backups"
    MaxBackupSize = 1GB
    ExcludePatterns = @("*.tmp", "*.log", "__pycache__", ".git", "node_modules")
    GitRemote = "origin"
    GitBranch = "main"
}

# Estado do backup
$Global:BackupState = @{
    StartTime = Get-Date
    TotalFiles = 0
    TotalSize = 0
    BackupPath = ""
    Errors = @()
    Success = $false
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
        Write-ColorOutput "=" * 60 -Color $Colors.Header
        Write-ColorOutput "  $Title" -Color $Colors.Header
        Write-ColorOutput "=" * 60 -Color $Colors.Header
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

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" -Color $Colors.Warning
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" -Color $Colors.Error
}

function Get-BackupDestination {
    if ($Destination) {
        return $Destination
    }
    
    $defaultPath = Join-Path $Config.ProjectRoot $Config.DefaultBackupPath
    
    if (-not (Test-Path $defaultPath)) {
        New-Item -ItemType Directory -Path $defaultPath -Force | Out-Null
    }
    
    return $defaultPath
}

function Get-BackupFileName {
    param([string]$BackupType)
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $computerName = $env:COMPUTERNAME
    
    return "scalping_backup_$($BackupType)_$($computerName)_$timestamp"
}

function Test-GitRepository {
    Write-Step "Verificando repositório Git..."
    
    try {
        $gitStatus = git status --porcelain 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Não é um repositório Git ou Git não está instalado"
            return $false
        }
        
        Write-Success "Repositório Git encontrado"
        return $true
    }
    catch {
        Write-Warning "Erro ao verificar Git: $($_.Exception.Message)"
        return $false
    }
}

function Get-ChangedFiles {
    Write-Step "Identificando arquivos modificados..."
    
    try {
        # Arquivos modificados no Git
        $gitChanges = @()
        if (Test-GitRepository) {
            $gitStatus = git status --porcelain
            $gitChanges = $gitStatus | ForEach-Object { $_.Substring(3) }
        }
        
        # Arquivos modificados nas últimas 24 horas
        $recentFiles = @()
        $cutoffTime = (Get-Date).AddDays(-1)
        
        $searchPaths = @("agents", "config", "data", "scripts", "docs")
        
        foreach ($path in $searchPaths) {
            $fullPath = Join-Path $Config.ProjectRoot $path
            if (Test-Path $fullPath) {
                $files = Get-ChildItem -Path $fullPath -Recurse -File | Where-Object { 
                    $_.LastWriteTime -gt $cutoffTime -and
                    -not ($Config.ExcludePatterns | Where-Object { $_.Name -like $_ })
                }
                $recentFiles += $files.FullName
            }
        }
        
        # Combinar e remover duplicatas
        $allChanges = ($gitChanges + $recentFiles) | Sort-Object -Unique
        
        Write-Success "Encontrados $($allChanges.Count) arquivos modificados"
        return $allChanges
    }
    catch {
        Write-Error "Erro ao identificar arquivos modificados: $($_.Exception.Message)"
        return @()
    }
}

function Copy-Files {
    param(
        [string[]]$SourceFiles,
        [string]$DestinationPath,
        [string]$BackupType
    )
    
    Write-Step "Copiando arquivos para backup..."
    
    $copiedFiles = 0
    $totalSize = 0
    $errors = @()
    
    foreach ($sourceFile in $SourceFiles) {
        try {
            if (-not (Test-Path $sourceFile)) {
                Write-Warning "Arquivo não encontrado: $sourceFile"
                continue
            }
            
            # Calcular caminho relativo
            $relativePath = $sourceFile.Replace($Config.ProjectRoot, "").TrimStart("\")
            $destFile = Join-Path $DestinationPath $relativePath
            $destDir = Split-Path $destFile -Parent
            
            # Criar diretório de destino se necessário
            if (-not (Test-Path $destDir)) {
                if (-not $DryRun) {
                    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                }
            }
            
            # Copiar arquivo
            if (-not $DryRun) {
                Copy-Item -Path $sourceFile -Destination $destFile -Force
            }
            
            $fileInfo = Get-Item $sourceFile
            $totalSize += $fileInfo.Length
            $copiedFiles++
            
            Write-Verbose "Copiado: $relativePath"
            
        }
        catch {
            $error = "Erro ao copiar $sourceFile`: $($_.Exception.Message)"
            $errors += $error
            Write-Warning $error
        }
    }
    
    $Global:BackupState.TotalFiles = $copiedFiles
    $Global:BackupState.TotalSize = $totalSize
    $Global:BackupState.Errors = $errors
    
    Write-Success "Copiados $copiedFiles arquivos ($([math]::Round($totalSize/1MB, 2)) MB)"
    
    if ($errors.Count -gt 0) {
        Write-Warning "$($errors.Count) erros durante a cópia"
    }
    
    return $copiedFiles -gt 0
}

function Backup-FullSystem {
    param([string]$DestinationPath)
    
    Write-Step "Executando backup completo do sistema..."
    
    $sourcePaths = @(
        "agents",
        "config", 
        "scripts",
        "docs",
        "README.md",
        "requirements.txt",
        ".gitignore"
    )
    
    # Incluir dados se não for muito grande
    $dataPath = Join-Path $Config.ProjectRoot "data"
    if (Test-Path $dataPath) {
        $dataSize = (Get-ChildItem -Path $dataPath -Recurse -File | Measure-Object -Property Length -Sum).Sum
        if ($dataSize -lt $Config.MaxBackupSize) {
            $sourcePaths += "data"
        } else {
            Write-Warning "Diretório data muito grande ($([math]::Round($dataSize/1MB, 2)) MB) - pulando"
        }
    }
    
    $allFiles = @()
    foreach ($path in $sourcePaths) {
        $fullPath = Join-Path $Config.ProjectRoot $path
        if (Test-Path $fullPath) {
            if ((Get-Item $fullPath).PSIsContainer) {
                $files = Get-ChildItem -Path $fullPath -Recurse -File | Where-Object {
                    -not ($Config.ExcludePatterns | Where-Object { $_.Name -like $_ })
                }
                $allFiles += $files.FullName
            } else {
                $allFiles += $fullPath
            }
        }
    }
    
    return Copy-Files -SourceFiles $allFiles -DestinationPath $DestinationPath -BackupType "full"
}

function Backup-IncrementalSystem {
    param([string]$DestinationPath)
    
    Write-Step "Executando backup incremental..."
    
    $changedFiles = Get-ChangedFiles
    
    if ($changedFiles.Count -eq 0) {
        Write-Warning "Nenhum arquivo modificado encontrado"
        return $false
    }
    
    return Copy-Files -SourceFiles $changedFiles -DestinationPath $DestinationPath -BackupType "incremental"
}

function Backup-ConfigOnly {
    param([string]$DestinationPath)
    
    Write-Step "Executando backup de configurações..."
    
    $configFiles = @()
    
    # Arquivos de configuração
    $configPath = Join-Path $Config.ProjectRoot "config"
    if (Test-Path $configPath) {
        $configFiles += (Get-ChildItem -Path $configPath -File).FullName
    }
    
    # Arquivos principais
    $mainFiles = @("README.md", "requirements.txt", ".gitignore")
    foreach ($file in $mainFiles) {
        $fullPath = Join-Path $Config.ProjectRoot $file
        if (Test-Path $fullPath) {
            $configFiles += $fullPath
        }
    }
    
    if ($configFiles.Count -eq 0) {
        Write-Warning "Nenhum arquivo de configuração encontrado"
        return $false
    }
    
    return Copy-Files -SourceFiles $configFiles -DestinationPath $DestinationPath -BackupType "config"
}

function Backup-DataOnly {
    param([string]$DestinationPath)
    
    Write-Step "Executando backup de dados..."
    
    $dataPath = Join-Path $Config.ProjectRoot "data"
    if (-not (Test-Path $dataPath)) {
        Write-Warning "Diretório de dados não encontrado"
        return $false
    }
    
    # Verificar tamanho dos dados
    $dataSize = (Get-ChildItem -Path $dataPath -Recurse -File | Measure-Object -Property Length -Sum).Sum
    if ($dataSize -gt $Config.MaxBackupSize) {
        Write-Warning "Dados muito grandes ($([math]::Round($dataSize/1GB, 2)) GB) - considere usar backup incremental"
        return $false
    }
    
    $dataFiles = Get-ChildItem -Path $dataPath -Recurse -File | Where-Object {
        -not ($Config.ExcludePatterns | Where-Object { $_.Name -like $_ })
    }
    
    return Copy-Files -SourceFiles $dataFiles.FullName -DestinationPath $DestinationPath -BackupType "data"
}

function Backup-LogsOnly {
    param([string]$DestinationPath)
    
    Write-Step "Executando backup de logs..."
    
    $logsPath = Join-Path $Config.ProjectRoot "data\logs"
    if (-not (Test-Path $logsPath)) {
        Write-Warning "Diretório de logs não encontrado"
        return $false
    }
    
    # Backup apenas logs dos últimos 7 dias
    $cutoffTime = (Get-Date).AddDays(-7)
    $logFiles = Get-ChildItem -Path $logsPath -File | Where-Object { 
        $_.LastWriteTime -gt $cutoffTime 
    }
    
    if ($logFiles.Count -eq 0) {
        Write-Warning "Nenhum log recente encontrado"
        return $false
    }
    
    return Copy-Files -SourceFiles $logFiles.FullName -DestinationPath $DestinationPath -BackupType "logs"
}

function Compress-Backup {
    param(
        [string]$BackupPath,
        [string]$BackupName
    )
    
    Write-Step "Comprimindo backup..."
    
    try {
        $zipPath = "$BackupPath.zip"
        
        if (-not $DryRun) {
            # Usar .NET para compressão
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            [System.IO.Compression.ZipFile]::CreateFromDirectory($BackupPath, $zipPath)
            
            # Remover diretório original
            Remove-Item -Path $BackupPath -Recurse -Force
        }
        
        $zipSize = if (Test-Path $zipPath) { (Get-Item $zipPath).Length } else { 0 }
        
        Write-Success "Backup comprimido: $zipPath ($([math]::Round($zipSize/1MB, 2)) MB)"
        
        return $zipPath
    }
    catch {
        Write-Error "Erro ao comprimir backup: $($_.Exception.Message)"
        return $BackupPath
    }
}

function Commit-ToGit {
    Write-Step "Fazendo commit automático no Git..."
    
    try {
        if (-not (Test-GitRepository)) {
            Write-Warning "Repositório Git não disponível"
            return $false
        }
        
        # Verificar se há mudanças
        $status = git status --porcelain
        if (-not $status) {
            Write-Warning "Nenhuma mudança para commit"
            return $true
        }
        
        if (-not $DryRun) {
            # Adicionar arquivos
            git add .
            
            # Commit com mensagem automática
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $commitMessage = "auto: Backup automático - $timestamp"
            
            git commit -m $commitMessage
            
            if ($LASTEXITCODE -ne 0) {
                throw "Falha no commit"
            }
            
            # Push se configurado
            $hasRemote = git remote | Where-Object { $_ -eq $Config.GitRemote }
            if ($hasRemote) {
                Write-Step "Fazendo push para repositório remoto..."
                git push $Config.GitRemote $Config.GitBranch
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Push realizado com sucesso"
                } else {
                    Write-Warning "Falha no push - commit local realizado"
                }
            }
        }
        
        Write-Success "Commit realizado com sucesso"
        return $true
    }
    catch {
        Write-Error "Erro no commit Git: $($_.Exception.Message)"
        return $false
    }
}

function Remove-OldBackups {
    param(
        [string]$BackupDirectory,
        [int]$RetentionDays
    )
    
    Write-Step "Removendo backups antigos (>$RetentionDays dias)..."
    
    try {
        $cutoffDate = (Get-Date).AddDays(-$RetentionDays)
        
        $oldBackups = Get-ChildItem -Path $BackupDirectory -File | Where-Object {
            $_.Name -like "scalping_backup_*" -and $_.LastWriteTime -lt $cutoffDate
        }
        
        if ($oldBackups.Count -eq 0) {
            Write-Success "Nenhum backup antigo encontrado"
            return
        }
        
        $totalSize = ($oldBackups | Measure-Object -Property Length -Sum).Sum
        
        if (-not $DryRun) {
            $oldBackups | Remove-Item -Force
        }
        
        Write-Success "Removidos $($oldBackups.Count) backups antigos ($([math]::Round($totalSize/1MB, 2)) MB liberados)"
        
    }
    catch {
        Write-Error "Erro ao remover backups antigos: $($_.Exception.Message)"
    }
}

function Show-BackupSummary {
    param([string]$BackupPath)
    
    Write-Header "RESUMO DO BACKUP"
    
    $duration = (Get-Date) - $Global:BackupState.StartTime
    
    Write-ColorOutput "Tipo: " -Color $Colors.Info -NoNewline
    Write-ColorOutput $BackupType.ToUpper() -Color $Colors.Header
    
    Write-ColorOutput "Destino: " -Color $Colors.Info -NoNewline
    Write-ColorOutput $BackupPath -Color $Colors.Header
    
    Write-ColorOutput "Arquivos: " -Color $Colors.Info -NoNewline
    Write-ColorOutput $Global:BackupState.TotalFiles -Color $Colors.Success
    
    Write-ColorOutput "Tamanho: " -Color $Colors.Info -NoNewline
    Write-ColorOutput "$([math]::Round($Global:BackupState.TotalSize/1MB, 2)) MB" -Color $Colors.Success
    
    Write-ColorOutput "Duração: " -Color $Colors.Info -NoNewline
    Write-ColorOutput "$([math]::Round($duration.TotalSeconds, 1))s" -Color $Colors.Success
    
    if ($Global:BackupState.Errors.Count -gt 0) {
        Write-ColorOutput "Erros: " -Color $Colors.Info -NoNewline
        Write-ColorOutput $Global:BackupState.Errors.Count -Color $Colors.Error
        
        Write-Host ""
        Write-ColorOutput "DETALHES DOS ERROS:" -Color $Colors.Error
        foreach ($error in $Global:BackupState.Errors) {
            Write-ColorOutput "  • $error" -Color $Colors.Error
        }
    }
    
    Write-Host ""
    
    if ($DryRun) {
        Write-ColorOutput "⚠️  MODO DRY-RUN - Nenhuma operação foi executada" -Color $Colors.Warning
    } else {
        Write-ColorOutput "✅ Backup concluído com sucesso!" -Color $Colors.Success
    }
}

#endregion

#region Função Principal

function Start-Backup {
    Write-Header "SISTEMA DE SCALPING - BACKUP E VERSIONAMENTO"
    
    if ($DryRun) {
        Write-ColorOutput "🔍 MODO DRY-RUN ATIVADO - Simulando operações" -Color $Colors.Warning
        Write-Host ""
    }
    
    # Configurar destino do backup
    $backupDestination = Get-BackupDestination
    $backupName = Get-BackupFileName -BackupType $BackupType
    $backupPath = Join-Path $backupDestination $backupName
    
    $Global:BackupState.BackupPath = $backupPath
    
    Write-ColorOutput "Iniciando backup: " -Color $Colors.Info -NoNewline
    Write-ColorOutput $BackupType.ToUpper() -Color $Colors.Header
    Write-ColorOutput "Destino: " -Color $Colors.Info -NoNewline
    Write-ColorOutput $backupPath -Color $Colors.Header
    Write-Host ""
    
    # Mudar para diretório do projeto
    Set-Location $Config.ProjectRoot
    
    # Criar diretório de backup
    if (-not $DryRun -and -not (Test-Path $backupPath)) {
        New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    }
    
    # Executar backup baseado no tipo
    $success = switch ($BackupType) {
        "full" { Backup-FullSystem -DestinationPath $backupPath }
        "incremental" { Backup-IncrementalSystem -DestinationPath $backupPath }
        "config" { Backup-ConfigOnly -DestinationPath $backupPath }
        "data" { Backup-DataOnly -DestinationPath $backupPath }
        "logs" { Backup-LogsOnly -DestinationPath $backupPath }
        default { 
            Write-Error "Tipo de backup inválido: $BackupType"
            $false
        }
    }
    
    if (-not $success) {
        Write-Error "Backup falhou"
        return
    }
    
    $Global:BackupState.Success = $true
    
    # Comprimir se solicitado
    if ($Compress) {
        $backupPath = Compress-Backup -BackupPath $backupPath -BackupName $backupName
    }
    
    # Commit Git se solicitado
    if ($GitCommit) {
        Commit-ToGit | Out-Null
    }
    
    # Limpeza de backups antigos
    Remove-OldBackups -BackupDirectory $backupDestination -RetentionDays $RetentionDays
    
    # Mostrar resumo
    Show-BackupSummary -BackupPath $backupPath
}

#endregion

# Execução principal
try {
    Start-Backup
}
catch {
    Write-Error "Erro durante o backup: $($_.Exception.Message)"
    Write-ColorOutput "Stack trace:" -Color $Colors.Error
    Write-ColorOutput $_.ScriptStackTrace -Color $Colors.Error
    exit 1
}

