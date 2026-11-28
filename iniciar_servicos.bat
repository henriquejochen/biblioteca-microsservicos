
@echo off

set "PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Ambiente virtual nao encontrado!
    pause
    exit /b 1
)

for %%P in (servico_leitores servico_livros servico_emprestimos servico_multas) do (
    start "%%P" cmd /k "cd /d ""%~dp0%%P"" && ""%PYTHON%"" app.py"
)
