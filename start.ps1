# Bot ve Webhook Başlatıcı PowerShell Script
param(
    [switch]$NoWebhook = $false
)

# Renkli çıktı için
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Ana başlık
Clear-Host
Write-ColorOutput Green "================================================"
Write-ColorOutput Green "        BOT VE WEBHOOK BAŞLATICI"
Write-ColorOutput Green "================================================"
Write-Output ""

# Python kontrolü
try {
    $pythonVersion = python --version 2>&1
    Write-ColorOutput Cyan "✓ Python bulundu: $pythonVersion"
} catch {
    Write-ColorOutput Red "✗ HATA: Python bulunamadı!"
    Write-ColorOutput Yellow "Lütfen Python'u yükleyin ve PATH'e ekleyin."
    Read-Host "Devam etmek için Enter'a basın"
    exit 1
}

# Gerekli dosyaların varlığını kontrol et
$requiredFiles = @("main.py", "helius_webhook.py", "requirements.txt")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-ColorOutput Cyan "✓ $file dosyası bulundu"
    } else {
        Write-ColorOutput Red "✗ $file dosyası bulunamadı!"
        Read-Host "Devam etmek için Enter'a basın"
        exit 1
    }
}

# Gerekli kütüphaneleri yükle
Write-Output ""
Write-ColorOutput Yellow "Gerekli kütüphaneler kontrol ediliyor..."
try {
    pip install -r requirements.txt | Out-Null
    Write-ColorOutput Cyan "✓ Kütüphaneler hazır"
} catch {
    Write-ColorOutput Yellow "⚠ Kütüphane yükleme sırasında uyarı"
}

Write-Output ""

# Webhook başlat (eğer isteniyorsa)
$webhookJob = $null
if (-not $NoWebhook) {
    Write-ColorOutput Green "🚀 Webhook başlatılıyor..."
    $webhookJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        python helius_webhook.py
    }
    Start-Sleep -Seconds 2
    Write-ColorOutput Cyan "✓ Webhook arka planda çalışıyor (Job ID: $($webhookJob.Id))"
}

Write-Output ""
Write-ColorOutput Green "🤖 Bot başlatılıyor..."
Write-ColorOutput Yellow "Bot'u durdurmak için Ctrl+C kullanın"
Write-Output ""

# Ana bot'u başlat
try {
    python main.py
} catch {
    Write-ColorOutput Red "Bot çalışırken hata oluştu"
} finally {
    # Cleanup
    Write-Output ""
    Write-ColorOutput Yellow "🛑 Servisler durduruluyor..."

    if ($webhookJob) {
        Stop-Job -Job $webhookJob -Force
        Remove-Job -Job $webhookJob -Force
        Write-ColorOutput Cyan "✓ Webhook durduruldu"
    }

    Write-ColorOutput Green "✓ Tüm servisler temizlendi"
    Write-Output ""
    Read-Host "Çıkmak için Enter'a basın"
}