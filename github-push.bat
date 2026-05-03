@echo off
REM Script para enviar projeto para GitHub (Windows)
REM Use: github-push.bat "Sua mensagem de commit aqui"

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   GitHub Push Script - PocketOption API
echo ========================================
echo.

REM Verificar se git está instalado
git --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Git nao encontrado!
    echo Instale em: https://git-scm.com
    exit /b 1
)

REM Verificar se está no diretório certo
if not exist "api_server.py" (
    echo ERRO: api_server.py nao encontrado!
    echo Execute a partir da pasta raiz do projeto.
    exit /b 1
)

REM Verificar se tem repositório
if not exist ".git" (
    echo.
    echo AVISO: Repositorio local nao encontrado!
    echo.
    echo Primeira vez? Siga:
    echo 1. Crie repositorio em https://github.com/new
    echo 2. Execute: git init
    echo 3. Execute: git remote add origin https://github.com/seu-usuario/seu-repo.git
    echo 4. Execute este script novamente
    echo.
    exit /b 1
)

REM Pegar mensagem de commit
if "%1"=="" (
    set "COMMIT_MSG=Update: minor improvements"
) else (
    set "COMMIT_MSG=%1"
)

echo [1/4] Verificando arquivos...
git status --short
echo.

echo [2/4] Adicionando arquivos...
git add .
if errorlevel 1 (
    echo ERRO ao adicionar arquivos!
    exit /b 1
)

echo [3/4] Fazendo commit: "%COMMIT_MSG%"
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo AVISO: Nada para fazer commit ou erro no commit
    echo Pulando para push...
)

echo [4/4] Fazendo push...
git push
if errorlevel 1 (
    echo ERRO ao fazer push!
    echo Dicas:
    echo - Verifique sua conexao de internet
    echo - Verifique o remote: git remote -v
    echo - Se primeira vez, use: git push -u origin main
    exit /b 1
)

echo.
echo ========================================
echo   SUCESSO! Projeto enviado para GitHub
echo ========================================
echo.
echo Acesse: https://github.com/seu-usuario/seu-repo
echo.

endlocal
