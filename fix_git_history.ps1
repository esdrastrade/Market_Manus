# Script para remover arquivo sensível do histórico do Git
# Execute no PowerShell do Windows como Administrador

Write-Host "🔧 REMOVENDO ARQUIVO SENSÍVEL DO HISTÓRICO DO GIT" -ForegroundColor Cyan
Write-Host "=" * 60

# 1. Instalar git-filter-repo via pip
Write-Host "`n📦 Instalando git-filter-repo..." -ForegroundColor Yellow
pip install git-filter-repo

# 2. Navegar para o diretório do projeto
Set-Location "C:\Users\Esdras\scalping-trading-system"

# 3. Remover o arquivo do histórico (todos os commits)
Write-Host "`n🗑️ Removendo attached_assets/_1759329317438.env do histórico..." -ForegroundColor Yellow
git filter-repo --invert-paths --path attached_assets/_1759329317438.env --force

# 4. Re-adicionar o remote (filter-repo remove automaticamente)
Write-Host "`n🔗 Re-adicionando remote origin..." -ForegroundColor Yellow
git remote add origin https://github.com/esdrastrade/Market_Manus.git

# 5. Force push para atualizar GitHub
Write-Host "`n🚀 Fazendo push com histórico limpo..." -ForegroundColor Yellow
git push origin --force --all
git push origin --force --tags

Write-Host "`n✅ CONCLUÍDO! Histórico limpo e enviado para GitHub" -ForegroundColor Green
Write-Host "`n⚠️ IMPORTANTE: Revogue sua API key antiga no OpenAI!" -ForegroundColor Red
Write-Host "   https://platform.openai.com/api-keys" -ForegroundColor Yellow
