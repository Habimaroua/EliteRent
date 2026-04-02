$ErrorActionPreference = "Stop"

Write-Host "Création et activation de l'environnement virtuel..." -ForegroundColor Cyan
if (-Not (Test-Path ".venv")) {
    python -m venv .venv
}

Write-Host "Installation des dépendances pour l'IA..." -ForegroundColor Cyan
& .\.venv\Scripts\pip install -r .\AI_SERVICE\requirements.txt

Write-Host "Installation des dépendances pour la plateforme WEB..." -ForegroundColor Cyan
& .\.venv\Scripts\pip install -r .\WEB_PLATFORM\requirements.txt

Write-Host "Préparation de la base de données Django..." -ForegroundColor Cyan
cd .\WEB_PLATFORM\diagnostic
& ..\..\.venv\Scripts\python manage.py migrate
cd ..\..

Write-Host "Lancement des serveurs..." -ForegroundColor Green
Write-Host "--> L'API IA sera sur: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "--> Le site Web sera sur: http://localhost:8001" -ForegroundColor Yellow

# On lance les deux serveurs en arrière-plan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit -Command `"cd AI_SERVICE; ..\.venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload`"" -WindowStyle Normal
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit -Command `"`$env:AI_SERVICE_URL='http://127.0.0.1:8000'; cd WEB_PLATFORM\diagnostic; ..\..\.venv\Scripts\python manage.py runserver 0.0.0.0:8001`"" -WindowStyle Normal

Write-Host "Les deux serveurs ont été lancés dans de nouvelles fenêtres ! Allez sur http://localhost:8001 pour tester." -ForegroundColor Green
