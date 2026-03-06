$env:PGCLIENTENCODING = "GBK"  # Try setting a fallback encoding if UTF8 fails, or force UTF8
$env:PGCLIENTENCODING = "UTF8"
$env:LC_MESSAGES = "C"           # Force English messages to avoid potentially non-UTF8 chars in Spanish messages

Write-Host "Setting environment variables..."
Write-Host "PGCLIENTENCODING: $env:PGCLIENTENCODING"
Write-Host "LC_MESSAGES: $env:LC_MESSAGES"

# Activate virtual environment if not already active
if ($env:VIRTUAL_ENV -eq $null) {
    Write-Host "Activating venv..."
    . .\venv\Scripts\Activate.ps1
}

# Check if database exists (optional but helpful)
# psql -c "SELECT 1" ...

Write-Host "Starting application..."
python -m src.main
