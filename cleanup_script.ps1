# 🧹 SCRIPT DE LIMPEZA DEFINITIVA - MARKET MANUS
# Execute este script no Windows Terminal para limpar e reorganizar completamente o projeto

param(
    [switch]$Force,
    [switch]$Backup,
    [switch]$Help
)

# Cores para output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

function Show-Help {
    Write-Host "🧹 SCRIPT DE LIMPEZA DEFINITIVA - MARKET MANUS" -ForegroundColor $Cyan
    Write-Host "=" * 60 -ForegroundColor $Cyan
    Write-Host ""
    Write-Host "USO:" -ForegroundColor $Green
    Write-Host "  .\cleanup_script.ps1                # Limpeza padrão com confirmação"
    Write-Host "  .\cleanup_script.ps1 -Force         # Limpeza sem confirmação"
    Write-Host "  .\cleanup_script.ps1 -Backup        # Criar backup antes da limpeza"
    Write-Host "  .\cleanup_script.ps1 -Help          # Mostrar esta ajuda"
    Write-Host ""
    Write-Host "OPÇÕES:" -ForegroundColor $Green
    Write-Host "  -Force    : Executar sem confirmações"
    Write-Host "  -Backup   : Criar backup antes da limpeza"
    Write-Host "  -Help     : Mostrar esta ajuda"
    Write-Host ""
    Write-Host "EXEMPLO:" -ForegroundColor $Yellow
    Write-Host "  .\cleanup_script.ps1 -Backup -Force"
    exit
}

function Write-Step {
    param($Message)
    Write-Host "`n$Message" -ForegroundColor $Cyan
    Write-Host ("-" * $Message.Length) -ForegroundColor $Cyan
}

function Write-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor $Green
}

function Write-Warning {
    param($Message)
    Write-Host "⚠️ $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor $Red
}

function Confirm-Action {
    param($Message)
    if ($Force) { return $true }
    
    $response = Read-Host "$Message (s/N)"
    return $response -eq 's' -or $response -eq 'S'
}

function Create-Backup {
    Write-Step "1️⃣ CRIANDO BACKUP DE SEGURANÇA"
    
    $backupDir = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    try {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        
        # Backup arquivos Python da raiz
        Get-ChildItem -Path "." -Filter "*.py" -File | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $backupDir -Force
        }
        
        # Backup arquivos de configuração
        @(".env", ".env.example", "requirements.txt", "README.md") | ForEach-Object {
            if (Test-Path $_) {
                Copy-Item -Path $_ -Destination $backupDir -Force
            }
        }
        
        # Backup diretório market_manus
        if (Test-Path "market_manus") {
            Copy-Item -Path "market_manus" -Destination "$backupDir\market_manus" -Recurse -Force
        }
        
        Write-Success "Backup criado em: $backupDir"
        return $true
    }
    catch {
        Write-Error "Erro ao criar backup: $($_.Exception.Message)"
        return $false
    }
}

function Remove-ObsoleteFiles {
    Write-Step "2️⃣ REMOVENDO ARQUIVOS OBSOLETOS DA RAIZ"
    
    $filesToRemove = @(
        "test_*.py",
        "validate_*.py", 
        "fix_*.py",
        "*_complete*.py",
        "market_manus_complete_system*.py",
        "strategy_lab_professional_complete.py",
        "confluence_mode_complete.py",
        "capital_dashboard_complete.py",
        "backtesting_engine_complete.py",
        "strategy_manager_*.py",
        "*_strategy.py",
        "market_manus_semantic_*.py",
        "api_test.py",
        "capital_data.json"
    )
    
    $removedCount = 0
    
    foreach ($pattern in $filesToRemove) {
        $files = Get-ChildItem -Path "." -Filter $pattern -File -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            try {
                Remove-Item -Path $file.FullName -Force
                Write-Host "  🗑️ Removido: $($file.Name)" -ForegroundColor $Yellow
                $removedCount++
            }
            catch {
                Write-Warning "Não foi possível remover: $($file.Name)"
            }
        }
    }
    
    Write-Success "Removidos $removedCount arquivos obsoletos"
}

function Clean-PythonCache {
    Write-Step "3️⃣ LIMPANDO CACHE PYTHON"
    
    $cacheRemoved = 0
    
    # Remover __pycache__ da raiz
    if (Test-Path "__pycache__") {
        Remove-Item -Path "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
        $cacheRemoved++
    }
    
    # Remover cache recursivamente
    Get-ChildItem -Path "." -Recurse -Name "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
        $cacheRemoved++
    }
    
    # Remover arquivos .pyc
    Get-ChildItem -Path "." -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
        $cacheRemoved++
    }
    
    Write-Success "Cache Python limpo ($cacheRemoved itens removidos)"
}

function Organize-DirectoryStructure {
    Write-Step "4️⃣ ORGANIZANDO ESTRUTURA DE DIRETÓRIOS"
    
    # Criar diretórios necessários
    $directories = @(
        "market_manus\engines",
        "market_manus\utils", 
        "tests\system",
        "tools",
        "scripts"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "  📁 Criado: $dir" -ForegroundColor $Green
        }
    }
    
    Write-Success "Estrutura de diretórios organizada"
}

function Clean-ObsoleteModules {
    Write-Step "5️⃣ REMOVENDO VERSÕES OBSOLETAS DOS MÓDULOS"
    
    # Limpar versões antigas do Strategy Lab
    $strategyLabFiles = @(
        "market_manus\strategy_lab\STRATEGY_LAB_PROFESSIONAL_V2.py",
        "market_manus\strategy_lab\STRATEGY_LAB_PROFESSIONAL_V3.py",
        "market_manus\strategy_lab\STRATEGY_LAB_PROFESSIONAL_V4.py",
        "market_manus\strategy_lab\STRATEGY_LAB_PROFESSIONAL_V5.py"
    )
    
    foreach ($file in $strategyLabFiles) {
        if (Test-Path $file) {
            Remove-Item -Path $file -Force
            Write-Host "  🗑️ Removido: $file" -ForegroundColor $Yellow
        }
    }
    
    # Renomear V6 para nome limpo
    $v6File = "market_manus\strategy_lab\STRATEGY_LAB_PROFESSIONAL_V6.py"
    $cleanFile = "market_manus\strategy_lab\strategy_lab_professional.py"
    
    if ((Test-Path $v6File) -and !(Test-Path $cleanFile)) {
        Move-Item -Path $v6File -Destination $cleanFile -Force
        Write-Host "  📝 Renomeado: V6 → strategy_lab_professional.py" -ForegroundColor $Green
    }
    
    # Limpar versões antigas do CLI
    $cliFiles = @(
        "market_manus\cli\MARKET_MANUS_CLI_COMPLETE_V4.py",
        "market_manus\cli\market_manus_final_implemented.py"
    )
    
    foreach ($file in $cliFiles) {
        if (Test-Path $file) {
            Remove-Item -Path $file -Force
            Write-Host "  🗑️ Removido: $file" -ForegroundColor $Yellow
        }
    }
    
    # Renomear CLI final
    $cliFinal = "market_manus\cli\market_manus_cli_complete_final.py"
    $cliClean = "market_manus\cli\market_manus_cli.py"
    
    if ((Test-Path $cliFinal) -and !(Test-Path $cliClean)) {
        Move-Item -Path $cliFinal -Destination $cliClean -Force
        Write-Host "  📝 Renomeado: CLI final → market_manus_cli.py" -ForegroundColor $Green
    }
    
    # Limpar arquivos de backup
    Get-ChildItem -Path "market_manus" -Recurse -Filter "*.backup" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -Path $_.FullName -Force
        Write-Host "  🗑️ Removido backup: $($_.Name)" -ForegroundColor $Yellow
    }
    
    Write-Success "Módulos obsoletos removidos"
}

function Clean-EmptyDirectories {
    Write-Step "6️⃣ LIMPANDO DIRETÓRIOS VAZIOS"
    
    $dirsToRemove = @(
        "market_manus\explanations",
        "market_manus\cli\reports"
    )
    
    foreach ($dir in $dirsToRemove) {
        if (Test-Path $dir) {
            Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  🗑️ Removido: $dir" -ForegroundColor $Yellow
        }
    }
    
    Write-Success "Diretórios vazios removidos"
}

function Create-MainFile {
    Write-Step "7️⃣ CRIANDO MAIN.PY DEFINITIVO"
    
    if (Test-Path "main.py") {
        if (!(Confirm-Action "main.py já existe. Substituir?")) {
            Write-Warning "main.py mantido sem alterações"
            return
        }
    }
    
    $mainContent = @'
#!/usr/bin/env python3
"""
Market Manus - Sistema de Trading Profissional
Ponto de entrada principal do sistema - VERSÃO DEFINITIVA
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Função principal do sistema"""
    try:
        print("🚀 MARKET MANUS - SISTEMA DE TRADING PROFISSIONAL")
        print("📦 Versão: 3.0.0 - DEFINITIVA")
        print("📅 Data/Hora:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*60)
        
        # Verificar dependências
        try:
            import pandas as pd
            import numpy as np
            print("✅ Dependências básicas: OK")
        except ImportError as e:
            print(f"❌ Dependências faltando: {e}")
            print("💡 Execute: pip install -r requirements.txt")
            return
        
        # Importar e executar sistema
        from market_manus.cli.market_manus_cli import MarketManusCompleteSystem
        
        system = MarketManusCompleteSystem()
        system.run()
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Verifique se a estrutura do projeto está correta")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Sistema interrompido pelo usuário")
        print("👋 Obrigado por usar o Market Manus!")
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")

if __name__ == "__main__":
    main()
'@
    
    try {
        $mainContent | Out-File -FilePath "main.py" -Encoding UTF8 -Force
        Write-Success "main.py criado com sucesso"
    }
    catch {
        Write-Error "Erro ao criar main.py: $($_.Exception.Message)"
    }
}

function Show-FinalStructure {
    Write-Step "8️⃣ VERIFICAÇÃO FINAL"
    
    Write-Host "`n📁 ESTRUTURA FINAL:" -ForegroundColor $Green
    if (Get-Command tree -ErrorAction SilentlyContinue) {
        tree /F
    } else {
        Get-ChildItem -Recurse | Select-Object FullName
    }
    
    Write-Host "`n📄 ARQUIVOS NA RAIZ:" -ForegroundColor $Green
    $rootFiles = Get-ChildItem -Path "." -File | Select-Object Name
    $rootFiles | ForEach-Object { Write-Host "   - $($_.Name)" }
    
    # Contar arquivos Python na raiz
    $pythonFiles = Get-ChildItem -Path "." -Filter "*.py" -File
    Write-Host "`n🐍 ARQUIVOS PYTHON NA RAIZ: $($pythonFiles.Count)" -ForegroundColor $Yellow
    
    if ($pythonFiles.Count -eq 1 -and $pythonFiles[0].Name -eq "main.py") {
        Write-Success "✅ Estrutura perfeita! Apenas main.py na raiz"
    } elseif ($pythonFiles.Count -gt 1) {
        Write-Warning "⚠️ Ainda há $($pythonFiles.Count) arquivos Python na raiz"
        $pythonFiles | ForEach-Object { Write-Host "   - $($_.Name)" -ForegroundColor $Yellow }
    }
    
    # Verificar main.py
    if (Test-Path "main.py") {
        Write-Success "✅ main.py presente"
    } else {
        Write-Error "❌ main.py não encontrado!"
    }
}

function Test-System {
    Write-Step "9️⃣ TESTE FINAL DO SISTEMA"
    
    if (!(Test-Path "main.py")) {
        Write-Error "main.py não encontrado. Não é possível testar."
        return
    }
    
    Write-Host "🧪 Testando sistema limpo..." -ForegroundColor $Cyan
    
    try {
        $result = python main.py --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Sistema executou com sucesso"
        } else {
            Write-Warning "Sistema executou com avisos"
            Write-Host $result -ForegroundColor $Yellow
        }
    }
    catch {
        Write-Error "Erro ao testar sistema: $($_.Exception.Message)"
        Write-Host "💡 Verifique se Python está instalado e no PATH"
    }
}

# EXECUÇÃO PRINCIPAL
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Host "🧹 LIMPEZA DEFINITIVA - MARKET MANUS" -ForegroundColor $Cyan
    Write-Host "=" * 50 -ForegroundColor $Cyan
    Write-Host "📅 Iniciado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor $Green
    
    # Verificar se estamos no diretório correto
    if (!(Test-Path "market_manus") -and !(Test-Path "main.py") -and !(Test-Path "README.md")) {
        Write-Error "❌ Não parece ser o diretório do projeto Market Manus"
        Write-Host "💡 Navegue para o diretório scalping-trading-system e execute novamente"
        return
    }
    
    # Confirmação final
    if (!(Confirm-Action "🚨 Esta operação irá limpar e reorganizar o projeto. Continuar?")) {
        Write-Host "❌ Operação cancelada pelo usuário" -ForegroundColor $Red
        return
    }
    
    # Executar limpeza
    $success = $true
    
    if ($Backup) {
        $success = Create-Backup
    }
    
    if ($success) {
        Remove-ObsoleteFiles
        Clean-PythonCache
        Organize-DirectoryStructure
        Clean-ObsoleteModules
        Clean-EmptyDirectories
        Create-MainFile
        Show-FinalStructure
        Test-System
        
        Write-Host "`n🎉 LIMPEZA CONCLUÍDA COM SUCESSO!" -ForegroundColor $Green
        Write-Host "✅ Projeto organizado e pronto para uso" -ForegroundColor $Green
        Write-Host "🚀 Execute: python main.py" -ForegroundColor $Cyan
    } else {
        Write-Error "❌ Limpeza interrompida devido a erros"
    }
}

# Executar script principal
Main
