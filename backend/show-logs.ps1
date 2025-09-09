# show-logs.ps1

# This script helps you view logs from different services

param(
    [ValidateSet("docker", "local")]
    [string]$Mode = "docker",
    
    [ValidateSet("all", "backend", "celery", "redis")]
    [string]$Service = "all"
)

Write-Host "📋 ReadBuddy Logs Viewer" -ForegroundColor Blue
Write-Host "Mode: $Mode, Service: $Service" -ForegroundColor Gray
Write-Host "────────────────────────────────────────" -ForegroundColor Gray

if ($Mode -eq "docker") {
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Docker Compose not found. Please install Docker Desktop." -ForegroundColor Red
        exit 1
    }
    
    # Change to docker directory
    Push-Location docker
    
    try {
        switch ($Service) {
            "all" {
                Write-Host "🔍 Showing logs from all Docker services..." -ForegroundColor Green
                docker-compose logs -f
            }
            "backend" {
                Write-Host "🔍 Showing backend logs..." -ForegroundColor Green
                docker-compose logs -f backend
            }
            "celery" {
                Write-Host "🔍 Showing Celery worker logs..." -ForegroundColor Green
                docker-compose logs -f celery-worker
            }
            "redis" {
                Write-Host "🔍 Showing Redis logs..." -ForegroundColor Green
                docker-compose logs -f redis
            }
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "💡 For local setup:" -ForegroundColor Yellow
    Write-Host "  - FastAPI server output: Visible in the main terminal where you ran start-backend.ps1" -ForegroundColor Cyan
    Write-Host "  - Celery worker output: Use .\start-backend.ps1 -ShowLogs to see in separate window" -ForegroundColor Cyan
    Write-Host "  - All print() statements, logger output, and errors are captured in these terminals" -ForegroundColor Cyan
    
    switch ($Service) {
        "all" {
            Write-Host ""
            Write-Host "🔍 Showing Redis container output..." -ForegroundColor Green
            Write-Host "💡 Note: FastAPI and Celery output are in their respective terminal windows" -ForegroundColor Yellow
            docker logs -f readbuddy-redis
        }
        "backend" {
            Write-Host ""
            Write-Host "💡 Backend output (FastAPI server):" -ForegroundColor Green
            Write-Host "  - All print() statements, logger output, and server logs are shown" -ForegroundColor Cyan
            Write-Host "  - Visible in the main terminal where you ran start-backend.ps1" -ForegroundColor Cyan
            Write-Host "  - Includes: HTTP requests, errors, warnings, debug output" -ForegroundColor Cyan
        }
        "celery" {
            Write-Host ""
            Write-Host "💡 Celery worker output:" -ForegroundColor Green
            Write-Host "  - All print() statements, logger output, and task logs are shown" -ForegroundColor Cyan
            Write-Host "  - Use: .\start-backend.ps1 -ShowLogs to see in separate window" -ForegroundColor Cyan
            Write-Host "  - Includes: Task execution, errors, warnings, debug output" -ForegroundColor Cyan
        }
        "redis" {
            Write-Host ""
            Write-Host "🔍 Showing Redis container output..." -ForegroundColor Green
            docker logs -f readbuddy-redis
        }
    }
}
