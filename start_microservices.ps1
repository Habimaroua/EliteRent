# Script de lancement des microservices EliteRent (Version Plate)
Write-Host "--- Demarrage de l ecosysteme Microservices EliteRent ---" -ForegroundColor Cyan

# 1. AI Service (FastAPI)
Write-Host "--- Lancement de AI_SERVICE (Port 8000) ---"
Start-Process powershell -ArgumentList "cd AI_SERVICE; python main.py" -WindowStyle Normal

# 2. Location Service (Django)
Write-Host "--- Lancement de LOCATION_SERVICE (Port 8001) ---"
Start-Process powershell -ArgumentList "cd LOCATION_SERVICE; python manage.py runserver 8001" -WindowStyle Normal

# 3. Diagnostic Service (Django)
Write-Host "--- Lancement de DIAGNOSTIC_SERVICE (Port 8002) ---"
Start-Process powershell -ArgumentList "cd DIAGNOSTIC_SERVICE; python manage.py runserver 8002" -WindowStyle Normal

# 4. Payment Service (FastAPI)
Write-Host "--- Lancement de PAYMENT_SERVICE (Port 8003) ---"
Start-Process powershell -ArgumentList "cd PAYMENT_SERVICE; python main.py" -WindowStyle Normal

# 5. Report Service (FastAPI)
Write-Host "--- Lancement de REPORT_SERVICE (Port 8004) ---"
Start-Process powershell -ArgumentList "cd REPORT_SERVICE; python main.py" -WindowStyle Normal

# 6. Gateway (Django Master)
Write-Host "--- Lancement de la GATEWAY (Port 8080) ---"
Start-Process powershell -ArgumentList "cd GATEWAY; python manage.py runserver 8080" -WindowStyle Normal

Write-Host "Tous les services sont lances (Architecture a plat)." -ForegroundColor Green
Write-Host "Fichier responsable des liens : microservices_urls.json" -ForegroundColor Yellow
