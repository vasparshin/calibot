# Stream CaliBOT logs from Render.com in real-time
# Usage: .\scripts\stream_logs.ps1

# Configuration
$SERVICE_ID = "srv-ctglj6qj1k6c73fpjbeg"  # CaliBOT service ID
$LOGS_URL = "https://api.render.com/v1/services/$SERVICE_ID/logs"

# Check if API key is set
if (-not $env:RENDER_API_KEY) {
    Write-Host "❌ RENDER_API_KEY environment variable not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 Setup Instructions:" -ForegroundColor Yellow
    Write-Host "1. Get your API key from: https://dashboard.render.com/user/settings"
    Write-Host "2. Set environment variable:"
    Write-Host "   `$env:RENDER_API_KEY = 'your_key_here'"
    Write-Host "3. Run this script: .\scripts\stream_logs.ps1"
    Write-Host ""
    exit 1
}

Write-Host "🔄 Streaming logs from CaliBOT service: $SERVICE_ID" -ForegroundColor Cyan
Write-Host "📡 API endpoint: $LOGS_URL" -ForegroundColor Gray
Write-Host "================================================================================"
Write-Host "✅ Connected to Render log stream" -ForegroundColor Green
Write-Host "🎯 Watching for CaliBOT activity..." -ForegroundColor Yellow
Write-Host "-------------------------------------------------------------------------------"

# Set up headers
$headers = @{
    "Authorization" = "Bearer $env:RENDER_API_KEY"
    "Content-Type" = "application/json"
}

try {
    # Create web request
    $request = [System.Net.WebRequest]::Create($LOGS_URL)
    $request.Method = "GET"
    foreach ($key in $headers.Keys) {
        $request.Headers.Add($key, $headers[$key])
    }
    
    # Get response stream
    $response = $request.GetResponse()
    $stream = $response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    
    # Read stream line by line
    while (-not $reader.EndOfStream) {
        $line = $reader.ReadLine()
        $timestamp = Get-Date -Format "HH:mm:ss"
        
        # Color code important log types
        if ($line -match "🔍 LLM") {
            Write-Host "🔍 $timestamp | $line" -ForegroundColor Blue
        } elseif ($line -match "🚨") {
            Write-Host "🚨 $timestamp | $line" -ForegroundColor Red
        } elseif ($line -match "ERROR") {
            Write-Host "❌ $timestamp | $line" -ForegroundColor Red
        } elseif ($line -match "Target|target") {
            Write-Host "🎯 $timestamp | $line" -ForegroundColor Magenta
        } elseif ($line -match "Bot sending") {
            Write-Host "🤖 $timestamp | $line" -ForegroundColor Green
        } else {
            Write-Host "📝 $timestamp | $line" -ForegroundColor White
        }
    }
} catch {
    Write-Host "❌ Error streaming logs: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    if ($reader) { $reader.Close() }
    if ($response) { $response.Close() }
}
