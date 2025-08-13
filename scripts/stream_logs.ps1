# Stream CaliBOT logs from Render.com in real-time
# Usage: .\scripts\stream_logs.ps1

# Configuration
$SERVICE_ID = "srv-ctglj6qj1k6c73fpjbeg"  # CaliBOT service ID
$RENDER_API_KEY = "rnd_m8U9bCF9is6HWxuVbrc5S1rA7VzP"  # Your API key
$LOGS_URL = "https://api.render.com/v1/logs"

Write-Host "🔄 Streaming logs from CaliBOT service: $SERVICE_ID" -ForegroundColor Cyan
Write-Host "📡 API endpoint: $LOGS_URL" -ForegroundColor Gray
Write-Host "================================================================================"
Write-Host "✅ Connected to Render API" -ForegroundColor Green
Write-Host "🎯 Watching for CaliBOT activity..." -ForegroundColor Yellow
Write-Host "-------------------------------------------------------------------------------"

# Set up headers
$headers = @{
    "Authorization" = "Bearer $RENDER_API_KEY"
    "Content-Type" = "application/json"
}

# Function to get logs batch
function Get-LogsBatch {
    param(
        [string]$StartTime = $null
    )
    
    $params = @{
        "resourceId" = $SERVICE_ID
        "limit" = 100
    }
    
    if ($StartTime) {
        $params["startTime"] = $StartTime
    }
    
    # Build URL with parameters
    $paramString = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
    $fullUrl = "$LOGS_URL?$paramString"
    
    try {
        $response = Invoke-RestMethod -Uri $fullUrl -Headers $headers -Method Get
        return $response
    } catch {
        Write-Host "❌ API Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Start streaming from 5 minutes ago
$startTime = (Get-Date).AddMinutes(-5).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
$lastSeenTime = $startTime

try {
    while ($true) {
        $data = Get-LogsBatch -StartTime $lastSeenTime
        
        if ($data -and $data.logs) {
            foreach ($logEntry in $data.logs) {
                $timestamp = $logEntry.timestamp
                $message = $logEntry.message
                
                # Format timestamp for display
                try {
                    $dt = [DateTime]::Parse($timestamp)
                    $displayTime = $dt.ToString("HH:mm:ss")
                } catch {
                    $displayTime = $timestamp.Substring(0, [Math]::Min(8, $timestamp.Length))
                }
                
                # Color code important log types
                if ($message -match "🔍 LLM") {
                    Write-Host "🔍 $displayTime | $message" -ForegroundColor Blue
                } elseif ($message -match "🚨") {
                    Write-Host "🚨 $displayTime | $message" -ForegroundColor Red
                } elseif ($message -match "ERROR") {
                    Write-Host "❌ $displayTime | $message" -ForegroundColor Red
                } elseif ($message -match "Target|target") {
                    Write-Host "🎯 $displayTime | $message" -ForegroundColor Magenta
                } elseif ($message -match "Bot sending") {
                    Write-Host "🤖 $displayTime | $message" -ForegroundColor Green
                } else {
                    Write-Host "📝 $displayTime | $message" -ForegroundColor White
                }
            }
            
            # Update last seen time
            if ($data.logs.Count -gt 0) {
                $lastSeenTime = $data.logs[-1].timestamp
            }
        }
        
        # Wait before next request
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host "❌ Error streaming logs: $($_.Exception.Message)" -ForegroundColor Red
}
